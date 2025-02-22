import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    current_app,
)
from werkzeug.security import check_password_hash
from flask_mail import Mail, Message
import database
import psycopg2
from database import PostgresConnectionFactory
import sqlite3


# Remova a importação do OAuth se não estiver usando
# from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "minhachave"  # Substitua por sua chave secreta

# Configurações do Flask-Mail
app.config["MAIL_SERVER"] = "smtp.seu_servidor.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "seu_email@dominio.com"
app.config["MAIL_PASSWORD"] = "sua_senha"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

mail = Mail(app)

# Remova as configurações do OAuth se não estiver usando o login com Google
# oauth = OAuth(app)
# google = oauth.register(
#     name='google',
#     client_id='SEU_CLIENT_ID',
#     client_secret='SEU_CLIENT_SECRET',
#     access_token_url='https://accounts.google.com/o/oauth2/token',
#     authorize_url='https://accounts.google.com/o/oauth2/auth',
#     client_kwargs={
#         'scope': 'openid email profile'
#     }
# )

ALLOWED_EXTENSIONS = {"csv"}

# Funções auxiliares


@app.route("/download_csv_template")
def download_csv_template():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            return send_from_directory(
                directory="static", path="modelo_perguntas.csv", as_attachment=True
            )
        else:
            flash(
                "Acesso negado. Você não tem permissão para baixar este arquivo.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_user_role():
    return dict(get_user_role=database.get_user_role)


# Rotas


@app.route("/")
def home():
    error_occurred, data = database.get_all_user_points()
    if error_occurred:
        flash(
            "Houve um problema com o banco de dados. " "Tente novamente mais tarde.",
            "danger",
        )
        return render_template("index.html", total_kg_donated=0)

    return render_template("index.html", total_kg_donated=data["total_kg_donated"])


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        existing_user = database.get_user(request.form["username"], request.form["email"])

        if existing_user:
            flash("Nome de usuário ou e-mail já existe. " "Escolha outro.", "warning")
            return redirect(url_for("register"))

        database.create_new_user(
            request.form["username"], request.form["email"], request.form["password"]
        )

        flash("Registro realizado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        user = database.get_user(
            request.form["username_or_email"], request.form["username_or_email"]
        )
        if not user:
            flash("Usuário ou senha incorretos", "danger")
            return redirect(url_for("login"))

        # Using user[X] with a hardcoded id X will cause issues if the schema changes,
        # in this case it would be better to change the query to also retrieve
        # the columns of the table
        if check_password_hash(user[3], request.form["password"]):
            session["user_id"] = user[0]
            role = user[4]
            if role == "admin":
                flash(
                    "Login realizado com sucesso! Bem-vindo, " "administrador.", "success"
                )
                return redirect(url_for("admin_dashboard"))
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("dashboard"))


# Remova as rotas de login com o Google se não estiver usando
"""
 @app.route('/login/google')
# def login_google():
#     redirect_uri = url_for('authorize', _external=True)
#     return google.authorize_redirect(redirect_uri)

 @app.route('/authorize')
 def authorize():
     token = google.authorize_access_token()
     resp = google.get('userinfo')
     user_info = resp.json()
     conn = sqlite3.connect('sutēru.db')
     c = conn.cursor()
     c.execute('SELECT * FROM users WHERE email = ?',
               (user_info['email'],))
     user = c.fetchone()

     if user is None:
         c.execute('INSERT INTO users (username, email, role) '
                   'VALUES (?, ?, ?)',
                   (user_info['name'], user_info['email'], 'user'))
         conn.commit()
         user_id = c.lastrowid
     else:
         user_id = user[0]

     conn.close()
     session['user_id'] = user_id
     flash('Login realizado com sucesso!', 'success')
     return redirect(url_for('dashboard'))
"""


@app.route("/dashboard")
def dashboard():
    if "user_id" in session:
        total_points, food_donation = database.get_user_points(session["user_id"])
        return render_template(
            "dashboard.html", total_points=total_points, food_donation=food_donation
        )
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))


@app.route("/quizzes")
def quizzes():
    if "user_id" in session:
        topics = database.get_topics()
        return render_template("quizzes.html", topics=topics)
    else:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("login"))


@app.route("/select_grade/<topic>")
def select_grade(topic):
    if "user_id" in session:
        grades = database.get_grades_for_topic(topic)
        return render_template("select_grade.html", topic=topic, grades=grades)
    else:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("login"))


@app.route("/quizzes/<topic>/<grade>")
def start_quiz(topic, grade):
    if "user_id" in session:
        session["current_topic"] = topic
        session["current_grade"] = grade
        return redirect(url_for("quiz_continuous"))
    else:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("login"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz_continuous():
    if "user_id" not in session:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    role = database.get_user_role()  # Obtém a função do usuário (admin ou user)
    topic = session.get("current_topic")
    grade = session.get("current_grade")

    if request.method == "POST":
        quiz_id = session.get("current_quiz_id")
        user_answer = request.form["answer"]

        is_correct, quiz = database.get_specific_quiz(quiz_id, user_id, user_answer)

        if is_correct:
            flash("Resposta correta! Pontos adicionados.", "success")
        else:
            flash(
                f"Resposta incorreta. A resposta correta era: {quiz[2]}",
                "danger",
            )

    # Admins podem sempre receber perguntas, mesmo repetidas
    if role == "admin":
        quiz = database.get_random_quiz_admin(topic, grade)
    else:
        quiz = database.get_random_quiz(user_id, topic, grade)

    if quiz:
        session["current_quiz_id"] = quiz[0]
        return render_template("quiz.html", quiz=quiz)
    else:
        session.pop("current_quiz_id", None)
        session.pop("current_topic", None)
        session.pop("current_grade", None)
        flash("Você respondeu todas as perguntas deste tópico e série.", "info")
        return redirect(url_for("dashboard"))



@app.route("/admin/delete_selected_questions", methods=["POST"])
def delete_selected_questions():
    if "user_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    role = database.get_user_role()
    if role == "admin":
        selected_questions = request.form.getlist("selected_questions")
        if selected_questions:
            database.delete_selected_questions_db(selected_questions)
            flash("As perguntas selecionadas foram deletadas com sucesso!", "success")
        else:
            flash("Nenhuma pergunta selecionada.", "warning")
        return redirect(url_for("admin_quizzes"))
    else:
        flash("Acesso negado. Você não tem permissão para realizar esta ação.", "danger")
        return redirect(url_for("dashboard"))


@app.route("/add_quiz", methods=["GET", "POST"])
def add_quiz():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            if request.method == "POST":
                database.add_quiz_db(request)

                flash("Quiz adicionado com sucesso!", "success")
                return redirect(url_for("dashboard"))
            else:
                topics = database.get_topics()
                grades = [
                    "6º ano",
                    "7º ano",
                    "8º ano",
                    "9º ano",
                    "1º ano EM",
                    "2º ano EM",
                    "3º ano EM",
                ]
                return render_template("add_quiz.html", topics=topics, grades=grades)
        else:
            flash(
                "Acesso negado. Você não tem permissão para " "adicionar quizzes.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado para adicionar quizzes.", "warning")
        return redirect(url_for("login"))


@app.route("/leaderboard")
def leaderboard():
    leaderboard = database.get_leaderboard()
    return render_template("leaderboard.html", leaderboard=leaderboard)


@app.route("/suggest_question", methods=["GET", "POST"])
def suggest_question():
    if "user_id" not in session:
        flash("Você precisa estar logado para sugerir uma questão.", "warning")
        return redirect(url_for("login"))

    conn = PostgresConnectionFactory.get_connection()
    c = conn.cursor()
    
    # Buscar os tópicos disponíveis no banco
    c.execute("SELECT DISTINCT topic FROM quizzes")
    topics = [row[0] for row in c.fetchall()]

    # Lista fixa de séries escolares
    grades = ["6º ano", "7º ano", "8º ano", "9º ano", "1º ano EM", "2º ano EM", "3º ano EM"]

    print("DEBUG - Grades antes de renderizar:", grades)  # Log para ver se grades está correto

    if request.method == "POST":
        # O conteúdo já virá como HTML
        question = request.form.get("question")
        correct_answer = request.form.get("correct_answer")
        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")
        points = request.form.get("points")
        topic = request.form.get("topic")
        grade = request.form.get("grade")

        # Se o usuário escolheu "Novo Tema", pegar o nome do novo tópico
        if topic == "novo_tema":
            topic = request.form.get("new_topic")

        # Verificar se todos os campos foram preenchidos
        if not all([question, correct_answer, option1, option2, option3, option4, points, topic, grade]):
            flash("Todos os campos são obrigatórios!", "danger")
            return render_template("suggest_question.html", topics=topics, grades=grades)

        # Inserir a sugestão no banco
        try:
            c.execute(
                "INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, points, topic, grade) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (question, correct_answer, option1, option2, option3, option4, points, topic, grade),
            )
            conn.commit()
            flash("Sua sugestão foi enviada para revisão!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir no banco:", e)
            flash("Erro ao salvar sua sugestão. Tente novamente!", "danger")

    return render_template("suggest_question.html", topics=topics, grades=grades)





@app.route("/admin/quizzes")
def admin_quizzes():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            try:
                # Buscar todos os tópicos distintos
                conn = database.PostgresConnectionFactory.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
                topics = [topic[0] for topic in cursor.fetchall()]

                # Pegar parâmetros de filtro
                grade = request.args.get('grade')
                topic = request.args.get('topic')
                difficulty = request.args.get('difficulty')

                # Construir a query base
                query = "SELECT * FROM quizzes"
                params = []
                conditions = []

                # Adicionar condições de filtro
                if grade:
                    conditions.append("grade = %s")
                    params.append(grade)
                if topic:
                    conditions.append("topic = %s")
                    params.append(topic)
                if difficulty:
                    conditions.append("difficulty = %s")
                    params.append(difficulty)

                # Adicionar WHERE se houver condições
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                cursor.execute(query, params)
                quizzes = cursor.fetchall()
                cursor.close()

                # Garantir que quizzes não seja None
                if quizzes is None:
                    quizzes = []

                return render_template(
                    "manage_questions.html",
                    quizzes=quizzes,
                    topics=topics,  # Passar os tópicos para o template
                    selected_grade=grade,
                    selected_topic=topic,
                    selected_difficulty=difficulty
                )

            except Exception as e:
                print(f"Erro ao acessar o banco: {str(e)}")
                flash("Erro ao acessar o banco de dados.", "danger")
                return redirect(url_for("dashboard"))
        else:
            flash("Acesso negado. Você não tem permissão para acessar esta página.", "danger")
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/delete_duplicates", methods=["POST"])
def delete_duplicates():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            # Verificar duplicados
            quizzes = database.execute_fetch("SELECT * FROM quizzes")
            question_counts = {}
            for quiz in quizzes:
                question = quiz[1].strip().lower()
                if question in question_counts:
                    question_counts[question].append(quiz)
                else:
                    question_counts[question] = [quiz]

            duplicates_to_delete = [
                q[0] for qs in question_counts.values() if len(qs) > 1 for q in qs[1:]
            ]  # Deletar todas, exceto a primeira ocorrência

            if duplicates_to_delete:
                database.execute_commit(
                    "DELETE FROM quizzes WHERE id = ?",
                    [(id,) for id in duplicates_to_delete],
                    many=True,
                )
            flash(
                f"Duplicatas deletadas: {len(duplicates_to_delete)} perguntas", "success"
            )
            return redirect(url_for("admin_quizzes"))
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/delete_question/<int:question_id>", methods=['GET', 'POST'])
def delete_question(question_id):
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            try:
                conn = database.PostgresConnectionFactory.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM quizzes WHERE id = %s", (question_id,))
                conn.commit()
                cursor.close()
                
                flash("Questão excluída com sucesso!", "success")
            except Exception as e:
                print(f"Erro ao excluir questão: {str(e)}")
                flash("Erro ao excluir a questão.", "danger")
            
            return redirect(url_for('admin_quizzes'))
        else:
            flash("Acesso negado. Você não tem permissão para excluir questões.", "danger")
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/review_suggestions", methods=["GET", "POST"])
def review_suggestions():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            suggestions = database.execute_fetch(
                """
                SELECT id, question, correct_answer, option1, option2, option3, option4, points, topic, grade
                FROM suggestions
            """
            )
            return render_template("review_suggestions.html", suggestions=suggestions)
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/approve_suggestion/<int:suggestion_id>")
def approve_suggestion(suggestion_id):
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            suggestion = database.execute_fetch(
                "SELECT * FROM suggested_questions WHERE " "id = ?", (suggestion_id,)
            )[0]
            if suggestion:
                database.execute_commit(
                    """
                    INSERT INTO quizzes (question, correct_answer,
                    option1, option2, option3, option4, topic, grade,
                    points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        suggestion[2],
                        suggestion[3],
                        suggestion[4],
                        suggestion[5],
                        suggestion[6],
                        suggestion[7],
                        suggestion[8],
                        suggestion[9],
                        suggestion[10],
                    ),
                )
                database.execute_commit(
                    "UPDATE suggested_questions SET status = ? " "WHERE id = ?",
                    ("aprovada", suggestion_id),
                )
                flash(
                    "Sugestão de pergunta aprovada e adicionada aos " "quizzes!",
                    "success",
                )
            return redirect(url_for("review_suggestions"))
        else:
            flash("Acesso negado.", "danger")
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/reject_suggestion/<int:suggestion_id>")
def reject_suggestion(suggestion_id):
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            database.execute_commit(
                "UPDATE suggested_questions SET status = ? " "WHERE id = ?",
                ("rejeitada", suggestion_id),
            )
            flash("Sugestão de pergunta rejeitada.", "success")
            return redirect(url_for("review_suggestions"))
        else:
            flash("Acesso negado.", "danger")
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin")
def admin_dashboard():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":

            kg_per_day = database.execute_fetch(
                "SELECT date(timestamp) as date, "
                f"SUM(points)/{database.POINTS_TO_KG} as kg_donated FROM user_points "
                "GROUP BY date(timestamp) ORDER BY date(timestamp) "
                "DESC LIMIT 7"
            )
            if kg_per_day is None:
                kg_per_day = 0

            total_users = database.execute_fetch("SELECT COUNT(*) FROM users")
            if total_users is None:
                total_users = 0
            else:
                total_users = total_users[0][0]

            total_quizzes = database.execute_fetch("SELECT COUNT(*) FROM user_points")
            if total_quizzes is None:
                total_quizzes = 0
            else:
                total_quizzes = total_quizzes[0][0]

            quizzes = database.execute_fetch("SELECT * FROM quizzes")

            return render_template(
                "admin_dashboard.html",
                kg_per_day=kg_per_day,
                total_users=total_users,
                total_quizzes=total_quizzes,
                quizzes=quizzes,
            )
        else:
            flash("Acesso negado.", "danger")
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    if "user_id" not in session:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))

    role = database.get_user_role()
    if role != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("dashboard"))

    conn = PostgresConnectionFactory.get_connection()
    c = conn.cursor()

    if request.method == "POST":
        try:
            question = request.form.get("question")
            correct_answer = request.form.get("correct_answer")
            option1 = request.form.get("option1")
            option2 = request.form.get("option2")
            option3 = request.form.get("option3")
            option4 = request.form.get("option4")
            topic = request.form.get("topic")
            if topic == "novo_tema":
                topic = request.form.get("new_topic")
            grade = request.form.get("grade")
            points = request.form.get("points")

            # Validar se os dados foram preenchidos
            if not all([question, correct_answer, option1, option2, option3, option4, topic, grade, points]):
                flash("Todos os campos são obrigatórios!", "danger")
                return redirect(url_for("edit_question", question_id=question_id))

            # Atualizar a questão no banco
            c.execute(
                """
                UPDATE quizzes
                SET question = %s, correct_answer = %s, option1 = %s,
                    option2 = %s, option3 = %s, option4 = %s, topic = %s,
                    grade = %s, points = %s
                WHERE id = %s
                """,
                (
                    question,
                    correct_answer,
                    option1,
                    option2,
                    option3,
                    option4,
                    topic,
                    grade,
                    points,
                    question_id,
                ),
            )
            conn.commit()
            flash("Pergunta atualizada com sucesso!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao atualizar a pergunta: {e}", "danger")

    else:
        c.execute("SELECT * FROM quizzes WHERE id = %s", (question_id,))
        question_data = c.fetchone()

        # Verifica se a pergunta foi encontrada
        if question_data is None:
            flash(f"Erro: Pergunta com ID {question_id} não encontrada!", "danger")
            return redirect(url_for("admin_dashboard"))

        topics = database.get_topics()
        grades = [
            "6º ano",
            "7º ano",
            "8º ano",
            "9º ano",
            "1º ano EM",
            "2º ano EM",
            "3º ano EM",
        ]

        return render_template(
            "edit_question.html",
            question=question_data,
            topics=topics,
            grades=grades,
        )



@app.route("/admin/delete_all_questions", methods=["POST"])
def delete_all_questions():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            database.execute_commit("DELETE FROM quizzes")
            flash("Todas as perguntas foram deletadas com sucesso!", "success")
            return redirect(url_for("admin_quizzes"))
        else:
            flash(
                "Acesso negado. Você não tem permissão para realizar esta ação.", "danger"
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/users")
def admin_users():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            sort_column = request.args.get("sort", "username")
            sort_order = request.args.get("order", "asc")

            valid_columns = ["username", "total_points", "accuracy_rate", "register_date"]
            if sort_column not in valid_columns:
                sort_column = "username"
            if sort_order not in ["asc", "desc"]:
                sort_order = "asc"

            users = database.execute_fetch(
                f"""
                SELECT u.id, u.username, u.email, u.role, 
                       COALESCE(SUM(up.points), 0) as total_points,
                       COALESCE(SUM(up.points) / 10, 0) as total_kg_donated,
                       CASE 
                          WHEN COUNT(up.id) = 0 THEN 0
                          ELSE ROUND(SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(up.id), 0), 2)
                       END AS accuracy_rate,
                       u.register_date
                FROM users u
                LEFT JOIN user_points up ON u.id = up.user_id
                GROUP BY u.id, u.username, u.email, u.role, u.register_date
                ORDER BY {sort_column} {sort_order}
            """
            )
            return render_template(
                "admin_users.html",
                users=users,
                sort_column=sort_column,
                sort_order=sort_order,
            )
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/users/promote/<int:user_id>", methods=["POST"])
def promote_user(user_id):
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            database.execute_commit(
                f"""update users
                    set role = 'admin'
                    where id = '{user_id}'
                """
            )
            flash("Cargo do usuário alterado para administrador", "success")
            return redirect(url_for("admin_users"))
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/users/demote/<int:user_id>", methods=["POST"])
def demote_user(user_id):
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            database.execute_commit(
                f"""update users
                    set role = 'user'
                    where id = '{user_id}'
                """
            )
            flash("Permissões de administrador do usuário revogadas", "success")
            return redirect(url_for("admin_users"))
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            database.execute_commit(
                f"""delete from users
                    where id = '{user_id}'
                """
            )
            flash("Usuário deletado", "success")
            return redirect(url_for("admin_users"))
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


@app.route("/upload_questions", methods=["GET", "POST"])
def upload_questions():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            if request.method == "POST":
                if "csv_file" not in request.files:
                    flash("Nenhum arquivo selecionado.", "warning")
                    return redirect(request.url)
                file = request.files["csv_file"]
                if file.filename == "":
                    flash("Nenhum arquivo selecionado.", "warning")
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    import csv
                    import io

                    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                    csv_input = csv.reader(stream)
                    conn = psycopg2.connect(os.environ["internal_db_url"])
                    c = conn.cursor()
                    try:
                        for idx, row in enumerate(csv_input):
                            if len(row) != 9:
                                flash(
                                    f"Erro na linha {idx + 1}: número incorreto de colunas.",
                                    "danger",
                                )
                                return redirect(request.url)
                            # Assumindo a ordem das colunas no CSV:
                            # question, correct_answer, option1, option2, option3, option4, points, topic, grade
                            c.execute(
                                """
                                INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, points, topic, grade)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                tuple(row),
                            )
                        conn.commit()
                        flash("Perguntas importadas com sucesso!", "success")
                    except Exception as e:
                        flash(f"Ocorreu um erro ao importar as perguntas: {e}", "danger")
                        conn.rollback()
                    finally:
                        conn.close()
                    return redirect(url_for("admin_dashboard"))
                else:
                    flash(
                        "Arquivo não permitido. Apenas arquivos CSV são aceitos.",
                        "danger",
                    )
                    return redirect(request.url)
            else:
                return render_template("upload_questions.html")
        else:
            flash(
                "Acesso negado. Você não tem permissão para acessar esta página.",
                "danger",
            )
            return redirect(url_for("dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
