from flask import render_template, redirect, url_for, session, g, request, flash
from markdown import markdown
from datetime import datetime
from random import randint
from app import app
from endpoints import admin, api
from forms import LoginForm
from models import Question, db, UserAnswer
from utils import (find_user, get_user, login_required, back, is_browser_supported, remaining_time,
                   finish_test, shuffle_return as shuffle)


@app.before_request
def before_request():
    g.md = markdown
    g.supported = is_browser_supported()
    g.rand = randint
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
        return redirect(url_for('admin_panel'))
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
    remaining = remaining_time(g.user)
    return render_template('test.html', remaining=int(remaining), answers=None, shuffle=shuffle,
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
            return redirect(back('admin_panel'))
    if request.method == 'POST':
        flash('Тест завершён!', category='success')
        finish_test(user)
        return redirect(url_for('result'))
    if user.end_time is None:
        if user_id is not None:
            flash('Тест ещё не был завершён!')
            return redirect(back('admin_panel'))
        return redirect(url_for('pre_solve'))
    total = 0
    for q in Question.query.all():
        total += q.points
    user_answers = UserAnswer.query.filter_by(user_id=user.id).all()
    failed_questions = [a.question for a in user_answers if not a.answer.is_correct]
    skipped_questions = Question.query.filter(
        ~Question.id.in_([a.question_id for a in user_answers])
    ).order_by(Question.number).all()
    return render_template('result.html', total=total, failed=failed_questions, user=user,
                           show_correct=True, skipped=skipped_questions, shuffle=(lambda x: x),
                           title='Результат тестирования')


app.add_url_rule('/api/answer', view_func=api.save_answer, methods=['POST'])
app.add_url_rule('/api/admin/question', view_func=api.change_question_data, methods=['POST'])

app.add_url_rule('/admin/', view_func=admin.admin_panel)
app.add_url_rule('/admin/users/', view_func=admin.manage_users)
app.add_url_rule('/admin/users/add', view_func=admin.add_users, methods=['GET', 'POST'])
app.add_url_rule('/admin/users/addAdmin', view_func=admin.add_admin, methods=['POST'])
app.add_url_rule('/admin/users/delete/<int:user_id>', view_func=admin.delete_user)
app.add_url_rule('/admin/reset/<int:user_id>', view_func=admin.reset)
app.add_url_rule('/admin/questions/', view_func=admin.manage_questions, methods=['GET', 'POST'])
app.add_url_rule('/admin/questions/<int:question_id>', view_func=admin.edit_question,
                 methods=['GET', 'POST'])
app.add_url_rule('/admin/questions/import', view_func=admin.upload_questions, methods=['POST'])
app.add_url_rule('/admin/questions/export', view_func=admin.export_questions)
app.add_url_rule('/admin/questions/delete/<int:question_id>', view_func=admin.delete_question)


if __name__ == '__main__':
    app.run()
