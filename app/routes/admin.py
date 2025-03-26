from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from app.utils import database
from app.utils.database import PostgresConnectionFactory
from app.config import Config
import os

bp = Blueprint('admin', __name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@bp.route("/admin")
def dashboard():
    if "user_id" in session:
        role = database.get_user_role()
        if role == "admin":
            graos_per_day = database.execute_fetch(
                "SELECT date(timestamp) as date, "
                "SUM(points) as graos_doados FROM user_points "
                "GROUP BY date(timestamp) ORDER BY date(timestamp) "
                "DESC LIMIT 7"
            )
            if graos_per_day is None:
                graos_per_day = 0

            total_users = database.execute_fetch("SELECT COUNT(*) FROM users")
            total_users = total_users[0][0] if total_users else 0

            total_quizzes = database.execute_fetch("SELECT COUNT(*) FROM user_points")
            total_quizzes = total_quizzes[0][0] if total_quizzes else 0

            quizzes = database.execute_fetch("SELECT * FROM quizzes")

            return render_template(
                "admin/admin_dashboard.html",
                graos_per_day=graos_per_day,
                total_users=total_users,
                total_quizzes=total_quizzes,
                quizzes=quizzes,
            )
        else:
            flash("Acesso negado.", "danger")
            return redirect(url_for("auth.dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("auth.login"))

@bp.route("/admin/users")
def users():
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
                """
                SELECT u.id, u.username, u.email, u.role, 
                       COALESCE(SUM(up.points), 0) as total_points,
                       COALESCE(SUM(up.points), 0) as total_graos_doados,
                       CASE 
                          WHEN COUNT(up.id) = 0 THEN 0
                          ELSE ROUND(SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(up.id), 0), 2)
                       END AS accuracy_rate,
                       u.register_date
                FROM users u
                LEFT JOIN user_points up ON u.id = up.user_id
                GROUP BY u.id, u.username, u.email, u.role, u.register_date
                ORDER BY """ + sort_column + " " + sort_order,
                ()
            )
            return render_template(
                "admin/admin_users.html",
                users=users,
                sort_column=sort_column,
                sort_order=sort_order,
            )
        else:
            flash("Acesso negado.", "danger")
            return redirect(url_for("auth.dashboard"))
    else:
        flash("Você precisa estar logado.", "warning")
        return redirect(url_for("auth.login"))

@bp.route("/admin/users/promote/<int:user_id>", methods=["POST"])
def promote_user(user_id):
    if "user_id" in session and database.get_user_role() == "admin":
        database.execute_commit(
            f"""update users
                set role = 'admin'
                where id = '{user_id}'
            """
        )
        flash("Cargo do usuário alterado para administrador", "success")
        return redirect(url_for("admin.users"))
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/users/demote/<int:user_id>", methods=["POST"])
def demote_user(user_id):
    if "user_id" in session and database.get_user_role() == "admin":
        database.execute_commit(
            "UPDATE users SET role = 'user' WHERE id = %s",
            (user_id,)
        )
        flash("Permissões de administrador do usuário revogadas", "success")
        return redirect(url_for("admin.users"))
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user_id" in session and database.get_user_role() == "admin":
        database.execute_commit(
            "DELETE FROM users WHERE id = %s",
            (user_id,)
        )
        flash("Usuário deletado", "success")
        return redirect(url_for("admin.users"))
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/quizzes")
def quizzes():
    if "user_id" in session and database.get_user_role() == "admin":
        try:
            conn = database.PostgresConnectionFactory.get_connection()
            cursor = conn.cursor()
            
            # Obter todos os tópicos distintos
            cursor.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
            topics = [topic[0] for topic in cursor.fetchall()]

            # Obter filtros da URL
            grade = request.args.get('grade')
            topic = request.args.get('topic')
            difficulty = request.args.get('difficulty')

            # Construir a query com os filtros
            query = """
                SELECT q.id, q.question, q.correct_answer, q.option1, q.option2, q.option3, q.option4,
                       q.topic, q.grade, q.points, q.difficulty
                FROM quizzes q
                WHERE 1=1
            """
            params = []

            if grade:
                query += " AND grade = %s"
                params.append(grade)
            if topic:
                query += " AND topic = %s"
                params.append(topic)
            if difficulty:
                query += " AND difficulty = %s"
                params.append(difficulty)

            query += " ORDER BY id DESC"

            # Executar a query
            cursor.execute(query, params)
            quizzes = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template(
                "admin/manage_questions.html",
                quizzes=quizzes,
                topics=topics,
                selected_grade=grade,
                selected_topic=topic,
                selected_difficulty=difficulty
            )

        except Exception as e:
            print(f"Erro ao acessar o banco: {str(e)}")
            flash("Erro ao acessar o banco de dados.", "danger")
            return redirect(url_for("auth.dashboard"))
    
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/delete_question/<int:question_id>", methods=['GET', 'POST'])
def delete_question(question_id):
    if "user_id" in session and database.get_user_role() == "admin":
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
        
        return redirect(url_for('admin.quizzes'))
    
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

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

            if not all([question, correct_answer, option1, option2, option3, option4, topic, grade, points]):
                flash("Todos os campos são obrigatórios!", "danger")
                return redirect(url_for("admin.edit_question", question_id=question_id))

            c.execute(
                """
                UPDATE quizzes
                SET question = %s, correct_answer = %s, option1 = %s,
                    option2 = %s, option3 = %s, option4 = %s, topic = %s,
                    grade = %s, points = %s
                WHERE id = %s
                """,
                (question, correct_answer, option1, option2, option3, option4, topic, grade, points, question_id)
            )
            conn.commit()
            flash("Pergunta atualizada com sucesso!", "success")
            return redirect(url_for("admin.dashboard"))
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao atualizar a pergunta: {e}", "danger")

    c.execute("SELECT * FROM quizzes WHERE id = %s", (question_id,))
    question_data = c.fetchone()

    if question_data is None:
        flash(f"Erro: Pergunta com ID {question_id} não encontrada!", "danger")
        return redirect(url_for("admin.dashboard"))

    topics = database.get_topics()
    grades = [
        "6º ano", "7º ano", "8º ano", "9º ano",
        "1º ano EM", "2º ano EM", "3º ano EM"
    ]

    return render_template(
        "admin/edit_question.html",
        question=question_data,
        topics=topics,
        grades=grades,
    )

@bp.route("/download_csv_template")
def download_csv_template():
    if "user_id" in session and database.get_user_role() == "admin":
        return send_from_directory(
            directory="static", path="modelo_perguntas.csv", as_attachment=True
        )
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/upload_questions", methods=["GET", "POST"])
def upload_questions():
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

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
            conn = PostgresConnectionFactory.get_connection()
            c = conn.cursor()
            
            try:
                # Pula a primeira linha (cabeçalho)
                next(csv_input)
                
                for idx, row in enumerate(csv_input, start=2):  # start=2 porque já pulamos a primeira linha
                    if len(row) != 9:
                        flash(f"Erro na linha {idx}: número incorreto de colunas.", "danger")
                        return redirect(request.url)
                    
                    c.execute(
                        """
                        INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, topic, grade, points)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                    )
                conn.commit()
                flash("Perguntas importadas com sucesso!", "success")
            except Exception as e:
                flash(f"Ocorreu um erro ao importar as perguntas: {e}", "danger")
                conn.rollback()
            finally:
                conn.close()
            return redirect(url_for("admin.dashboard"))
        
        flash("Arquivo não permitido. Apenas arquivos CSV são aceitos.", "danger")
        return redirect(request.url)

    return render_template("admin/upload_questions.html")

@bp.route("/admin/review_suggestions")
def review_suggestions():
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sq.*, u.username 
        FROM suggested_questions sq 
        LEFT JOIN users u ON sq.user_id = u.id 
        WHERE sq.status = 'pendente'
        ORDER BY sq.id DESC
    """)
    
    suggestions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("admin/review_suggestions.html", suggestions=suggestions)

@bp.route("/admin/approve_suggestion/<int:suggestion_id>")
def approve_suggestion(suggestion_id):
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    try:
        # Primeiro, busca os dados da sugestão
        cursor.execute("""
            SELECT question, correct_answer, option1, option2, option3, option4, 
                   topic, grade, points 
            FROM suggested_questions 
            WHERE id = %s
        """, (suggestion_id,))
        suggestion = cursor.fetchone()
        
        if suggestion:
            # Insere na tabela quizzes
            cursor.execute("""
                INSERT INTO quizzes 
                (question, correct_answer, option1, option2, option3, option4, topic, grade, points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, suggestion)
            
            # Atualiza o status da sugestão
            cursor.execute("""
                UPDATE suggested_questions 
                SET status = 'aprovado' 
                WHERE id = %s
            """, (suggestion_id,))
            
            conn.commit()
            flash("Sugestão aprovada com sucesso!", "success")
        else:
            flash("Sugestão não encontrada.", "danger")
            
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao aprovar sugestão: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("admin.review_suggestions"))

@bp.route("/admin/reject_suggestion/<int:suggestion_id>")
def reject_suggestion(suggestion_id):
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE suggested_questions 
            SET status = 'rejeitado' 
            WHERE id = %s
        """, (suggestion_id,))
        conn.commit()
        flash("Sugestão rejeitada com sucesso!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao rejeitar sugestão: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("admin.review_suggestions"))

@bp.route("/admin/add_quiz", methods=["GET", "POST"])
def add_quiz():
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

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

            if not all([question, correct_answer, option1, option2, option3, option4, topic, grade, points]):
                flash("Todos os campos são obrigatórios!", "danger")
                return redirect(url_for("admin.add_quiz"))

            c.execute(
                """
                INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, topic, grade, points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (question, correct_answer, option1, option2, option3, option4, topic, grade, points)
            )
            conn.commit()
            flash("Pergunta adicionada com sucesso!", "success")
            return redirect(url_for("admin.dashboard"))
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao adicionar a pergunta: {e}", "danger")

    c.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
    topics = [topic[0] for topic in c.fetchall()]
    grades = ["6º ano", "7º ano", "8º ano", "9º ano", "1º ano EM", "2º ano EM", "3º ano EM"]

    return render_template("admin/add_quiz.html", topics=topics, grades=grades)

@bp.route("/admin/delete_selected_questions", methods=["POST"])
def delete_selected_questions():
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

    selected_questions = request.form.getlist("selected_questions")
    
    if not selected_questions:
        flash("Nenhuma questão selecionada.", "warning")
        return redirect(url_for("admin.quizzes"))

    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM quizzes WHERE id = ANY(%s)",
            (selected_questions,)
        )
        conn.commit()
        flash(f"{len(selected_questions)} questões foram deletadas com sucesso!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao deletar questões: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("admin.quizzes"))

@bp.route("/admin/delete_duplicates", methods=["POST"])
def delete_duplicates():
    if "user_id" not in session or database.get_user_role() != "admin":
        flash("Acesso negado.", "danger")
        return redirect(url_for("auth.dashboard"))

    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    try:
        # Identifica e deleta duplicatas mantendo o registro mais antigo
        cursor.execute("""
            DELETE FROM quizzes
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY question, correct_answer, option1, option2, option3, option4
                               ORDER BY id
                           ) as rnum
                    FROM quizzes
                ) t
                WHERE t.rnum > 1
            )
        """)
        deleted_count = cursor.rowcount
        conn.commit()
        flash(f"{deleted_count} questões duplicadas foram removidas.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao remover duplicatas: {e}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("admin.quizzes"))
