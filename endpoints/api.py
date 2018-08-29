from flask import request, g
from models import Question, Answer, db
from utils import json_response, save_answer as _save_answer


def save_answer():
    answer_id = request.form.get('a')
    user_id = request.form.get('u', None)
    result = _save_answer(answer_id, user_id)
    success = False
    if result is True:
        success = True
    response = {'ok': success}
    if not success:
        response['error'], response['error_code'] = result
        return json_response(response, 400)
    return json_response(response)


def change_question_data():
    e = {'ok': False}
    if not g.user:
        return json_response(e, 401)
    if not g.user.is_admin:
        return json_response(e, 403)
    f = request.form
    # FIXME when nice and interactive editing is implemented
    q = f.get('q')    # question id
    # a = f.get('a')    # answer id
    # t = f.get('t')    # text
    r = f.get('r')    # correct answer id
    # c = f.get('c')    # caption
    # p = f.get('p')    # points
    # n = f.get('n')    # number
    question = Question.query.get(q)
    correct_answer = Answer.query.get(r)
    if question is None:
        return json_response(e, 404)
    if r is None:
        return json_response(e, 404)
    if correct_answer.question_id != question.id:  # Maybe we can check instances?
        return json_response(e)
    prev_correct = Answer.query.filter_by(question_id=question.id, is_correct=True).first()
    prev_correct.is_correct = False
    correct_answer.is_correct = True
    db.session.commit()
    e['ok'] = True
    return json_response(e)
