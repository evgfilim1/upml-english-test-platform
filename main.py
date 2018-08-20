from flask import render_template, redirect, url_for, session, g, request, flash, abort
from flask_restful import Api
from markdown import markdown
from datetime import datetime, timedelta
from random import shuffle
from secrets import randbelow
from app import app
from forms import LoginForm, AddUsersForm, AddAdminForm, AddQuestionForm, ImportQuestionsForm
from models import Question, db, UserAnswer, User, Answer
from utils import find_user, get_user, login_required, admin_required, back, is_browser_supported
from api import SaveAnswer, ChangeQuestionData
import json

api = Api(app)
api.add_resource(SaveAnswer, '/api/answer')
api.add_resource(ChangeQuestionData, '/api/admin/question')


@app.before_request
def before_request():
    g.md = markdown
    g.supported = is_browser_supported()
    u = session.get('user_id')
    if u is not None:
        g.user = get_user(u)
    else:
        g.user = None


@app.route('/', methods=['GET', 'POST'])
def welcome():
    if g.user is not None:
        return redirect(url_for('pre_solve'))
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user(form.login.data)
        session['user_id'] = user.id
        return redirect(url_for('pre_solve'))
    return render_template('main.html', title='Главная', form=form)


@app.route('/logout')
def logout():
    if session.get('user_id') is not None:
        session.pop('user_id')
    return redirect(url_for('welcome'))


@app.route('/ready')
@login_required
def pre_solve():
    if g.user.is_admin:
        return redirect(url_for('admin'))
    if g.user.end_time:
        return redirect(url_for('result'))
    if g.user.start_time:
        return redirect(url_for('solve'))
    return render_template('pre_solve.html')


@app.route('/test')
@login_required
def solve():
    if g.user.end_time:
        return redirect(url_for('result'))
    if str(g.user.id) != request.args.get('u'):
        return redirect(url_for('solve', u=g.user.id))
    if g.user.start_time is None:
        g.user.start_time = datetime.utcnow()
        db.session.commit()
    max_end_time = g.user.start_time + timedelta(seconds=app.config.get('TIME_TO_SOLVE', 3600))
    remaining = max_end_time - datetime.utcnow()
    return render_template('test.html',
                           remaining=int(remaining.total_seconds()), answers=None, shuffle=shuffle,
                           questions=Question.query.order_by(Question.number).all())


@app.route('/admin/result/<int:user_id>')
@app.route('/result', methods=['GET', 'POST'])
@login_required
def result(user_id=None):
    if user_id is not None and not g.user.is_admin:
        flash('Нет доступа')
        return redirect(url_for('welcome'))
    if user_id is None:
        user = g.user
    else:
        user = get_user(user_id)
        if not user:
            flash(f'Пользователь с id={user_id} не найден')
            return redirect(back('admin'))
    if request.method == 'POST':
        flash('Тест завершён!', category='success')
        if user.end_time is None:
            user.end_time = datetime.utcnow()
            user.points = 0
            for a in g.user.answers:
                if a.is_correct:
                    g.user.points += a.question.points
            db.session.commit()
        return redirect(url_for('result'))
    if g.user.end_time is None:
        flash('Тест ещё не был завершён!')
        if user_id is not None:
            return redirect(back('admin'))
        return redirect(url_for('pre_solve'))
    total = 0
    for q in Question.query.all():
        total += q.points
    user_answers = UserAnswer.query.filter_by(user_id=g.user.id).all()
    failed_questions = [a.question for a in user_answers if not a.answer.is_correct]
    skipped_questions = Question.query.filter(
        ~Question.id.in_([a.question_id for a in user_answers])
    ).order_by(Question.number).all()
    return render_template('result.html', total=total, failed=failed_questions, user=user,
                           show_correct=True, skipped=skipped_questions, shuffle=(lambda x: x),
                           title='Результат тестирования')


@app.route('/admin/')
@admin_required
def admin():
    user_list = sorted(User.query.all(), key=lambda x: x.points or 0, reverse=True)
    return render_template('admin.html', users=user_list, title='Панель администратора')


@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def add_users():
    form = AddUsersForm()
    admin_form = AddAdminForm()
    users = {}
    if form.validate_on_submit():
        for name in form.users.data.split('\n'):
            name = name.strip()
            if name == '':
                continue
            if find_user(name) is not None:
                flash(f'Пользователь "{name}" уже существует, пропускаем.', 'warning')
                continue
            user = User(name=name)
            password = str(randbelow(9000) + 1000)
            user.set_password(password)
            users[user] = password
            db.session.add(user)
        db.session.commit()
        form.users.data = ''
    return render_template('add_users.html', new_users=users, form=form,
                           title='Добавить пользователей', admin_form=admin_form)


@app.route('/admin/users/addAdmin', methods=['POST'])
@admin_required
def add_admin():
    form = AddAdminForm()
    if form.validate_on_submit():
        user = User(name=form.login.data, is_admin=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Администратор добавлен!', 'success')
    return redirect(url_for('add_users'))


@app.route('/admin/users/manage')
@app.route('/admin/users/')
@admin_required
def manage_users():
    return render_template('manage_users.html', users=User.query.all(),
                           title='Управление пользователями')


@app.route('/admin/reset/<int:user_id>')
@admin_required
def reset(user_id):
    u = User.query.get(user_id)
    if not u:
        flash(f'Пользователь с id={user_id} не найден')
        return redirect(back('admin'))
    u.points = None
    u.start_time = None
    u.end_time = None
    db.session.commit()
    flash('Результаты сброшены!', 'success')
    return redirect(back('admin'))


@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    u = User.query.get(user_id)
    if not u:
        flash(f'Пользователь с id={user_id} не найден')
        return redirect(back('manage_users'))
    db.session.delete(u)
    db.session.commit()
    flash('Пользователь удалён!', 'success')
    return redirect(back('manage_users'))


@app.route('/admin/questions/', methods=['GET', 'POST'])
@admin_required
def manage_questions():
    form = AddQuestionForm()
    import_form = ImportQuestionsForm()
    if form.validate_on_submit():
        q = Question(title=form.question.data, text=form.caption.data, points=form.points.data,
                     number=form.number.data)
        db.session.add(q)
        db.session.commit()
        for answer in form.answers.data.split('\n'):
            a = Answer(question_id=q.id)
            if answer.startswith('+'):
                answer = answer.replace('+', '', 1).lstrip()
                a.is_correct = True
            a.text = answer
            db.session.add(a)
        db.session.commit()
        return redirect(url_for('manage_questions'))
    q = Question.query.order_by(Question.number).all()
    if not q:
        form.number.data = 0
    else:
        form.number.data = q[-1].number + 10
    form.points.data = 1
    return render_template('questions.html', form=form, questions=Question.query.all(),
                           show_correct=True, editable=True, import_form=import_form)


@app.route('/admin/questions/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    q = Question.query.get(question_id)
    if q is None:
        flash(f'Вопроса с id={question_id} не существует')
        return redirect(back('manage_questions'))
    form = AddQuestionForm()
    if form.validate_on_submit():
        q.title = form.question.data
        q.text = form.caption.data
        q.points = form.points.data
        q.number = form.number.data
        db.session.commit()
        flash('Вопрос отредактирован', 'success')
        return redirect(url_for('manage_questions'))
    form.question.data = q.title
    form.caption.data = q.text
    form.points.data = q.points
    form.answers.data = '+Unsupported...'
    form.number.data = q.number
    return render_template('edit_question.html', form=form)


@app.route('/admin/questions/import', methods=['POST'])
@admin_required
def upload_questions():
    form = ImportQuestionsForm()
    if form.validate_on_submit():
        Question.query.delete(synchronize_session='fetch')
        Answer.query.delete(synchronize_session='fetch')
        UserAnswer.query.delete(synchronize_session='fetch')
        User.query.update({User.points: None, User.start_time: None, User.end_time: None},
                          synchronize_session='fetch')
        db.session.commit()
        with form.file.data.stream as ff:
            x = json.load(ff)
        for question in x:
            q = Question(id=question['num'], title=question['statement'], text=question['extra'],
                         points=question['points'], number=question['num'] * 10)
            for i, answer in enumerate(question['choices']):
                a = Answer(text=answer, is_correct=(i == question['correct']),
                           question_id=question['num'])
                db.session.add(a)
            db.session.add(q)
        db.session.commit()
        flash('Успешно импортировано!', 'success')
    return redirect(url_for('manage_questions'))


@app.route('/admin/questions/delete/<int:question_id>')
@admin_required
def delete_question(question_id):
    q = Question.query.get(question_id)
    if not q:
        flash(f'Вопроса с id={question_id} не существует')
        return redirect(back('manage_questions'))
    db.session.delete(q)
    db.session.commit()
    flash('Вопрос удалён!', 'success')
    return redirect(back('manage_questions'))


if __name__ == '__main__':
    app.run()
