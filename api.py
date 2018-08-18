from flask_restful import Resource, abort
from flask import request, g

from models import Question, Answer, db
from utils import save_answer, error


class SaveAnswer(Resource):
    @staticmethod
    def post():
        answer_id = request.form.get('a')
        user_id = request.form.get('u', None)
        success = save_answer(answer_id, user_id)
        result = {'ok': success}
        if not success:
            return abort(error(result))
        return result


class ChangeQuestionData(Resource):
    @staticmethod
    def post():
        e = {'ok': False}
        if not g.user:
            return abort(error(e, 401))
        if not g.user.is_admin:
            return abort(error(e, 403))
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
            return abort(error(e, 404))
        if r is None:
            return abort(error(e, 404))
        if correct_answer.question_id != question.id:  # Maybe we can check instances?
            return abort(error(e))
        prev_correct = Answer.query.filter_by(question_id=question.id, is_correct=True).first()
        prev_correct.is_correct = False
        correct_answer.is_correct = True
        db.session.commit()
        e['ok'] = True
        return e
