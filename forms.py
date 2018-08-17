from flask_wtf import FlaskForm
from wtforms import (SubmitField, StringField, TextAreaField, PasswordField, IntegerField,
                     FileField, ValidationError)
from wtforms.validators import DataRequired, InputRequired
from wtforms import widgets
from utils import find_user
import json


class _NumberInput(widgets.Input):
    input_type = 'number'


class _NumberField(IntegerField):
    widget = _NumberInput()


class LoginForm(FlaskForm):
    login = StringField('Фамилия и имя', validators=[DataRequired()])
    password = PasswordField('Персональный код', validators=[DataRequired()])
    submit = SubmitField('Войти')

    @staticmethod
    def validate_login(cls, field):
        if find_user(field.data) is None:
            raise ValidationError('Неверное имя пользователя')

    def validate_password(self, field):
        user = find_user(self.login.data)
        if user is None:
            return  # Another validator will fail
        if not user.verify_password(field.data):
            raise ValidationError('Неверный пароль')


class AddForm(FlaskForm):
    submit = SubmitField('Добавить')


class AddUsersForm(AddForm):
    users = TextAreaField('Фамилия и имя каждого пользователя, по одному на строку',
                          validators=[DataRequired()])


class AddAdminForm(AddForm):
    login = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])

    @staticmethod
    def validate_login(cls, field):
        if find_user(field.data) is not None:
            raise ValidationError('Пользователь с таким именем уже существует!')


class AddQuestionForm(AddForm):
    question = StringField('Вопрос', validators=[DataRequired()])
    caption = TextAreaField('Описание (не обязательно)')
    points = _NumberField('Баллы', validators=[InputRequired()])
    answers = TextAreaField('Ответы, по одному на строку. Перед правильным ответом поставьте «+».',
                            validators=[DataRequired()])
    number = _NumberField('Номер вопроса (используется для сортировки, рекомендуется устанавливать'
                          ' номер вопроса с шагом 10)',
                          validators=[InputRequired()])

    @staticmethod
    def validate_points(cls, field):
        if int(field.data) < 0:
            raise ValidationError('Отнимать баллы за верный ответ? Вы уверены?')

    @staticmethod
    def validate_answers(cls, field):
        correct_count = 0
        for answer in field.data.split('\n'):
            if answer.startswith('+'):
                correct_count += 1
        if correct_count == 0:
            raise ValidationError('Не указан правильный ответ')
        elif correct_count > 1:
            raise ValidationError('Указано более одного правильного ответа')


class ImportQuestionsForm(AddForm):
    file = FileField('Выберите файл в формате JSON...', validators=[DataRequired()])

    @staticmethod
    def validate_file(cls, field):
        if field.data.mimetype != 'application/json':
            raise ValidationError('Тип файла не совпадает')
        try:
            data = json.load(field.data.stream)
            field.data.stream.seek(0)
        except (EOFError, json.JSONDecodeError):
            raise ValidationError('Выбран неверный файл') from None
        try:
            for o in data:
                o['num']
                o['statement']
                o['extra']
                o['choices']
                o['points']
                o['correct']
        except LookupError:
            raise ValidationError('Файл не может быть распознан') from None
