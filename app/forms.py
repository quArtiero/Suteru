from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    class Meta:
        csrf = False
    
    username_or_email = StringField('Usuário ou Email', validators=[DataRequired()], 
                                   render_kw={"placeholder": "Nome de usuário ou email"})
    password = PasswordField('Senha', validators=[DataRequired()], 
                           render_kw={"placeholder": "Sua senha secreta"})
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    class Meta:
        csrf = False
    
    username = StringField('Nome de usuário', validators=[DataRequired(), Length(min=3, max=20)], 
                          render_kw={"placeholder": "Seu nome de usuário"})
    email = StringField('Email', validators=[DataRequired(), Email()], 
                       render_kw={"placeholder": "Seu melhor email", "type": "email"})
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)], 
                           render_kw={"placeholder": "Crie uma senha forte"})
    confirm_password = PasswordField('Confirmar Senha', 
                                   validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais')], 
                                   render_kw={"placeholder": "Confirme sua senha"})
    accept_terms = BooleanField('Aceito os termos de uso', validators=[DataRequired()])
    submit = SubmitField('Criar Conta') 