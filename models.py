from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, gensalt, checkpw
from app import app

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(), nullable=False)
    points = db.Column(db.Integer(), default=0)
    is_admin = db.Column(db.Boolean(), default=False)
    start_time = db.Column(db.DateTime())
    end_time = db.Column(db.DateTime())
    answers = db.relationship('Answer', secondary='user_answer')

    def set_password(self, password):
        self.password = hashpw(bytes(password, 'UTF-8'), gensalt()).decode('UTF-8')

    def verify_password(self, password):
        return checkpw(bytes(password, 'UTF-8'), bytes(self.password, 'UTF-8'))


class Question(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    text = db.Column(db.String())
    points = db.Column(db.Integer(), nullable=False)
    number = db.Column(db.Integer(), nullable=False, unique=True, autoincrement=True)
    # correct_id = db.Column(db.Integer(), db.ForeignKey('answer.id'))
    # answers = db.relationship('Answer')


class Answer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.String(), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('answers', lazy='dynamic'),
                               foreign_keys=[question_id])
    is_correct = db.Column(db.Boolean(), default=False)


class UserAnswer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    # user = db.relationship('User')
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=False)
    question = db.relationship('Question')
    answer_id = db.Column(db.Integer(), db.ForeignKey('answer.id'), nullable=False)
    answer = db.relationship('Answer')
    receive_time = db.Column(db.DateTime(), nullable=False)


def _init():
    if User.query.get(1) is not None:
        return
    u = User(id=1, name='admin', is_admin=True)
    u.set_password(app.config.get('ADMIN_PASSWORD', 'admin'))
    db.session.add(u)
    db.session.commit()


db.create_all()
_init()
