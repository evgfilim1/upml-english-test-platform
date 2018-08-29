from flask import g, Response, redirect, url_for, flash, request
from json import dumps
from functools import wraps
from datetime import datetime, timedelta
from app import app
from models import User, Answer, UserAnswer, db


def find_user(name):
    return User.query.filter_by(name=name).one_or_none()


def get_user(user_id):
    return User.query.get(user_id)


def is_browser_supported():
    ua = request.user_agent
    v = tuple(map(int, ua.version.split('.')))[:2]
    return ua.browser in ('chrome', 'firefox') and v >= (60, 0)


def remaining_time(user):
    time_to_solve = app.config.get('TIME_TO_SOLVE', 3600)
    if user.start_time is None:
        return time_to_solve
    max_end_time = user.start_time + timedelta(seconds=time_to_solve)
    return (max_end_time - datetime.utcnow()).total_seconds()


def finish_test(user):
    if user.end_time is None:
        user.end_time = datetime.utcnow()
        user.points = 0
        for a in user.answers:
            if a.is_correct:
                user.points += a.question.points
        db.session.commit()


def save_answer(answer_id, user_id=None):
    if user_id is None:
        user = g.user
    else:
        user = get_user(user_id)
    if answer_id is None or user is None:
        return 'Not found', 2
    if user.end_time is not None:
        return 'Test finished', 1
    if remaining_time(user) <= 0:
        return 'Test timed out', 3
    answer = Answer.query.get(answer_id)
    if answer is None:
        return 'Not found', 2
    user_answer = UserAnswer.query.filter_by(user_id=user.id,
                                             question_id=answer.question_id).first()
    if user_answer is not None:
        user_answer.answer_id = answer_id
        user_answer.receive_time = datetime.utcnow()
    else:
        user_answer = UserAnswer(user_id=user.id, question_id=answer.question_id,
                                 answer_id=answer_id, receive_time=datetime.utcnow())
        db.session.add(user_answer)
    db.session.commit()
    return True


def back(default='welcome'):
    return request.referrer or url_for(default)


def response(data, status=200, mimetype=None, **kwargs):
    return Response(response=data, status=status, mimetype=mimetype, **kwargs)


def json_response(data, status=200, **kwargs):
    if not isinstance(data, str):
        data = dumps(data)
    return response(data, status, 'application/json', **kwargs)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash('Ты не вошёл в аккаунт!')
            return redirect(url_for('welcome'))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash('Вы не вошли в аккаунт')
            return redirect(url_for('welcome'))
        if not g.user.is_admin:
            flash('Нет доступа')
            return redirect(url_for('welcome'))
        return fn(*args, **kwargs)
    return wrapper
