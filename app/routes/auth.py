from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.utils import database
from app.forms import LoginForm, RegisterForm

bp = Blueprint('auth', __name__)



@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        existing_user = database.get_user(form.username.data, form.email.data)

        if existing_user:
            flash("Nome de usuário ou e-mail já existe. Escolha outro.", "warning")
            return render_template("auth/register.html", form=form)

        database.create_new_user(
            form.username.data, form.email.data, form.password.data
        )

        flash("Registro realizado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/register.html", form=form)

@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        # Verificar se o input é email ou username
        username_or_email = form.username_or_email.data
        if "@" in username_or_email:
            # É um email, buscar por email
            user = database.get_user(username_or_email, username_or_email)
        else:
            # É um username, buscar apenas por username
            user = database.get_user(username_or_email)
        
        if not user:
            flash("Usuário/email ou senha incorretos", "danger")
            return render_template("auth/login.html", form=form)

        if check_password_hash(user[3], form.password.data):
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["user_role"] = user[4]
            role = user[4]
            if role == "admin":
                flash("Login realizado com sucesso! Bem-vindo, administrador.", "success")
                return redirect(url_for("admin.dashboard"))
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("auth.dashboard"))
        
        flash("Usuário/email ou senha incorretos", "danger")
        return render_template("auth/login.html", form=form)
    
    return render_template("auth/login.html", form=form)

@bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))

@bp.route("/dashboard")
def dashboard():
    if "user_id" in session:
        total_points, food_donation_grams, food_donation_meals, approximate_questions = database.get_user_points(session["user_id"])
        
        # Get user's leaderboard position (temporarily replacing full leaderboard view)
        user_position = database.get_user_leaderboard_position(session["user_id"])
        
        return render_template(
            "auth/dashboard.html", 
            total_points=total_points, 
            food_donation_grams=food_donation_grams,
            food_donation_meals=food_donation_meals,
            approximate_questions=approximate_questions,
            user_position=user_position  # Add position for dashboard display
        )
    else:
        return redirect(url_for("auth.login"))

@bp.route("/conquistas")
def achievements():
    if "user_id" in session:
        total_points, food_donation_grams, food_donation_meals, approximate_questions = database.get_user_points(session["user_id"])
        subject_achievements = database.get_user_subject_achievements(session["user_id"])
        return render_template(
            "auth/achievements.html", 
            total_points=total_points, 
            food_donation_grams=food_donation_grams,
            food_donation_meals=food_donation_meals,
            approximate_questions=approximate_questions,
            subject_achievements=subject_achievements
        )
    else:
        flash("Você precisa estar logado para ver suas conquistas.", "warning")
        return redirect(url_for("auth.login"))
