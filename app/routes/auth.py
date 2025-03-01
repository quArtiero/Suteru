from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.utils import database

bp = Blueprint('auth', __name__)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = database.get_user(request.form["username"], request.form["email"])

        if existing_user:
            flash("Nome de usuário ou e-mail já existe. Escolha outro.", "warning")
            return redirect(url_for("auth.register"))

        database.create_new_user(
            request.form["username"], request.form["email"], request.form["password"]
        )

        flash("Registro realizado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    if request.method == "POST":
        user = database.get_user(
            request.form["username_or_email"], request.form["username_or_email"]
        )
        if not user:
            flash("Usuário ou senha incorretos", "danger")
            return redirect(url_for("auth.login"))

        if check_password_hash(user[3], request.form["password"]):
            session["user_id"] = user[0]
            role = user[4]
            if role == "admin":
                flash("Login realizado com sucesso! Bem-vindo, administrador.", "success")
                return redirect(url_for("admin.dashboard"))
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("auth.dashboard"))
        
        flash("Usuário ou senha incorretos", "danger")
        return redirect(url_for("auth.login"))

@bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))

@bp.route("/dashboard")
def dashboard():
    if "user_id" in session:
        total_points, food_donation = database.get_user_points(session["user_id"])
        return render_template(
            "auth/dashboard.html", total_points=total_points, food_donation=food_donation
        )
    else:
        return redirect(url_for("auth.login"))
