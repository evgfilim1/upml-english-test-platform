import json
from flask import render_template, flash, redirect, url_for, request
from secrets import randbelow
from forms import AddQuestionForm, AddAdminForm, AddUsersForm, ImportQuestionsForm
from models import db, User, UserAnswer, Question, Answer
from utils import admin_required, find_user, back, json_response, remaining_time, finish_test


@admin_required
def admin_panel():
    users = User.query.all()
    for user in users:
        if remaining_time(user) <= 0:
            finish_test(user)
    db.session.commit()
    user_list = sorted(users, key=lambda x: x.points or 0, reverse=True)
    return render_template('admin.html', users=user_list, title='Панель администратора')


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


@admin_required
def manage_users():
    return render_template('manage_users.html', users=User.query.all(),
                           title='Управление пользователями')


@admin_required
def reset(user_id):
    u = User.query.get(user_id)
    full = request.args.get('full', False)
    if not u:
        flash(f'Пользователь с id={user_id} не найден')
        return redirect(back('admin_panel'))
    u.points = None
    u.start_time = None
    u.end_time = None
    if full:
        UserAnswer.query.filter(UserAnswer.user_id == u.id).delete()
    db.session.commit()
    if full:
        flash('Результаты сброшены!', 'success')
    else:
        flash('Таймер сброшен!', 'success')
    return redirect(back('admin_panel'))


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
            q = Question(id=question['num'], title=question['statement'], points=question['points'],
                         text=question['extra'] or None, number=question['num'] * 10)
            for i, answer in enumerate(question['choices']):
                a = Answer(text=answer, is_correct=(i == question['correct']),
                           question_id=question['num'])
                db.session.add(a)
            db.session.add(q)
        db.session.commit()
        flash('Успешно импортировано!', 'success')
    else:
        for err in form.file.errors:
            flash(err)
    return redirect(url_for('manage_questions'))


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


@admin_required
def export_questions():
    questions = Question.query.all()
    data = []
    for q in questions:
        d = {'num': q.id, 'statement': q.title, 'extra': q.text or '', 'choices': [],
             'points': q.points}
        for i, a in enumerate(q.answers):
            d['choices'].append(a.text)
            if a.is_correct:
                d['correct'] = i
        data.append(d)
    json_data = json.dumps(data, indent=4)
    return json_response(json_data, headers={
        'Content-Disposition': 'attachment; filename="tasks.json"'
    })
