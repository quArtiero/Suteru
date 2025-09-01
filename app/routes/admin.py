from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from app.utils import database
from app.utils.database import PostgresConnectionFactory, GRAMS_PER_POINT, points_to_grams, points_to_meals
from app.config import Config
import os
import csv

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
                f"SUM(points) * {GRAMS_PER_POINT} as grams_doados FROM user_points "
                "GROUP BY date(timestamp) ORDER BY date(timestamp) "
                "DESC LIMIT 7"
            )
            if graos_per_day is None:
                graos_per_day = 0

            total_users = database.execute_fetch("SELECT COUNT(*) FROM users")
            total_users = total_users[0][0] if total_users else 0

            total_quizzes = database.execute_fetch("SELECT COUNT(*) FROM user_points")
            total_quizzes = total_quizzes[0][0] if total_quizzes else 0

            # Total de questões no banco
            total_questions = database.execute_fetch("SELECT COUNT(*) FROM quizzes")
            total_questions = total_questions[0][0] if total_questions else 0

            # Total de pontos acumulados
            total_points = database.execute_fetch("SELECT SUM(points) FROM user_points")
            total_points = total_points[0][0] if total_points and total_points[0][0] else 0

            # Total de refeições doadas
            total_meals = total_points / 1000 if total_points else 0

            # Taxa de acerto geral
            accuracy_stats = database.execute_fetch(
                "SELECT "
                "COUNT(CASE WHEN is_correct = 1 THEN 1 END) as correct, "
                "COUNT(*) as total FROM user_points"
            )
            if accuracy_stats and accuracy_stats[0][1] > 0:
                general_accuracy = (accuracy_stats[0][0] / accuracy_stats[0][1]) * 100
            else:
                general_accuracy = 0

            # Sugestões pendentes
            pending_suggestions = database.execute_fetch("SELECT COUNT(*) FROM question_suggestions WHERE status = 'pending'")
            pending_suggestions = pending_suggestions[0][0] if pending_suggestions else 0

            # Top 5 usuários mais ativos (por questões respondidas)
            top_users = database.execute_fetch(
                """
                SELECT u.username, COUNT(up.id) as questions_answered, SUM(up.points) as total_points
                FROM users u 
                JOIN user_points up ON u.id = up.user_id 
                WHERE u.username != 'pedroquart'
                GROUP BY u.id, u.username 
                ORDER BY questions_answered DESC 
                LIMIT 5
                """
            )

            # Estatísticas por matéria
            subject_stats = database.execute_fetch(
                """
                SELECT q.topic, 
                       COUNT(up.id) as total_answered,
                       COUNT(CASE WHEN up.is_correct = 1 THEN 1 END) as correct_answers,
                       CASE 
                          WHEN COUNT(up.id) = 0 THEN 0
                          ELSE ROUND(COUNT(CASE WHEN up.is_correct = 1 THEN 1 END) * 100.0 / COUNT(up.id), 1)
                       END as accuracy_rate
                FROM quizzes q 
                LEFT JOIN user_points up ON q.id = up.quiz_id 
                GROUP BY q.topic 
                ORDER BY total_answered DESC
                """
            )

            quizzes = database.execute_fetch("SELECT * FROM quizzes")

            return render_template(
                "admin/admin_dashboard.html",
                graos_per_day=graos_per_day,
                total_users=total_users,
                total_quizzes=total_quizzes,
                total_questions=total_questions,
                total_points=total_points,
                total_meals=total_meals,
                general_accuracy=general_accuracy,
                pending_suggestions=pending_suggestions,
                top_users=top_users,
                subject_stats=subject_stats,
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
                       COALESCE(SUM(up.points), 0) * %s as total_grams_doados,
                       CASE 
                          WHEN COUNT(up.id) = 0 THEN 0
                          ELSE ROUND(SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(up.id), 0), 2)
                       END AS accuracy_rate,
                       u.register_date
                FROM users u
                LEFT JOIN user_points up ON u.id = up.user_id
                GROUP BY u.id, u.username, u.email, u.role, u.register_date
                ORDER BY """ + sort_column + " " + sort_order,
                (GRAMS_PER_POINT,)
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
            # Get filter parameters
            grade = request.args.get("grade")
            topic = request.args.get("topic")
            points_min = request.args.get("points_min", type=int)
            points_max = request.args.get("points_max", type=int)
            sort_by = request.args.get("sort_by", "id_desc")
            search_text = request.args.get("search", "").strip()
            page = request.args.get("page", 1, type=int)
            per_page = 10

            # Base query
            base_query = """
                SELECT id, question, correct_answer, option1, option2, option3, option4, 
                       grade, topic, points
                FROM quizzes
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) FROM quizzes WHERE 1=1"
            params = []

            # Apply filters
            if grade:
                base_query += " AND grade = %s"
                count_query += " AND grade = %s"
                params.append(grade)
            
            if topic:
                base_query += " AND topic = %s"
                count_query += " AND topic = %s"
                params.append(topic)
            
            if points_min is not None:
                base_query += " AND points >= %s"
                count_query += " AND points >= %s"
                params.append(points_min)
            
            if points_max is not None:
                base_query += " AND points <= %s"
                count_query += " AND points <= %s"
                params.append(points_max)
            
            if search_text:
                search_pattern = f"%{search_text}%"
                base_query += " AND (question ILIKE %s OR correct_answer ILIKE %s OR option1 ILIKE %s OR option2 ILIKE %s OR option3 ILIKE %s OR option4 ILIKE %s)"
                count_query += " AND (question ILIKE %s OR correct_answer ILIKE %s OR option1 ILIKE %s OR option2 ILIKE %s OR option3 ILIKE %s OR option4 ILIKE %s)"
                params.extend([search_pattern] * 6)
                params.extend([search_pattern] * 6)

            # Get total count
            conn = PostgresConnectionFactory.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(count_query, params)
                total_records = cursor.fetchone()[0]
                total_pages = (total_records + per_page - 1) // per_page

                # Ensure page is within valid range
                page = max(1, min(page, total_pages))
                offset = (page - 1) * per_page

                # Add ordering based on sort_by parameter
                order_by = {
                    "id_desc": "id DESC",
                    "id_asc": "id ASC",
                    "points_desc": "points DESC",
                    "points_asc": "points ASC",
                    "grade_asc": "grade ASC",
                    "grade_desc": "grade DESC"
                }.get(sort_by, "id DESC")

                base_query += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
                params.extend([per_page, offset])

                # Execute main query
                cursor.execute(base_query, params)
                quizzes = cursor.fetchall()

                # Get unique topics for filter dropdown
                cursor.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
                db_topics = [row[0] for row in cursor.fetchall()]
                topics = ['SAT'] + db_topics
            finally:
                cursor.close()
                conn.close()

            return render_template(
                "admin/manage_questions.html",
                quizzes=quizzes,
                topics=topics,
                grades=["6º ano", "7º ano", "8º ano", "9º ano", "1º ano EM", "2º ano EM", "3º ano EM"],
                selected_grade=grade,
                selected_topic=topic,
                points_min=points_min,
                points_max=points_max,
                sort_by=sort_by,
                search_text=search_text,
                page=page,
                total_pages=total_pages,
                max=max,
                min=min,
                total_questions=total_records
            )

        except Exception as e:
            print(f"Error in quizzes route: {str(e)}")
            flash("Erro ao carregar questões", "error")
            return redirect(url_for("admin.dashboard"))
        finally:
            if 'conn' in locals():
                conn.close()
    
    flash("Acesso negado.", "danger")
    return redirect(url_for("auth.dashboard"))

@bp.route("/admin/delete_question/<int:question_id>", methods=['GET', 'POST'])
def delete_question(question_id):
    if "user_id" in session and database.get_user_role() == "admin":
        try:
            conn = database.PostgresConnectionFactory.get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM quizzes WHERE id = %s", (question_id,))
                    conn.commit()
                flash("Questão excluída com sucesso!", "success")
            finally:
                conn.close()
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

            # Option4 is optional for SAT questions
            required_fields = [question, correct_answer, option1, option2, option3, topic, grade, points]
            if not topic.startswith("SAT"):
                required_fields.append(option4)  # Only required for non-SAT questions
                
            if not all(required_fields):
                flash("Todos os campos obrigatórios devem ser preenchidos!", "danger")
                return redirect(url_for("admin.edit_question", question_id=question_id))

            c.execute(
                """
                UPDATE quizzes
                SET question = %s, correct_answer = %s, option1 = %s,
                    option2 = %s, option3 = %s, option4 = %s, topic = %s,
                    grade = %s, points = %s
                WHERE id = %s
                """,
                (question, correct_answer, option1, option2, option3, option4 or "", topic, grade, points, question_id)
            )
            conn.commit()
            flash("Pergunta atualizada com sucesso!", "success")
            return redirect(url_for("admin.dashboard"))
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao atualizar a pergunta: {e}", "danger")

    c.execute("SELECT * FROM quizzes WHERE id = %s", (question_id,))
    quiz = c.fetchone()

    if quiz is None:
        flash(f"Erro: Pergunta com ID {question_id} não encontrada!", "danger")
        return redirect(url_for("admin.dashboard"))

    topics = database.get_topics()
    grades = [
        "6º ano", "7º ano", "8º ano", "9º ano",
        "1º ano EM", "2º ano EM", "3º ano EM"
    ]

    return render_template(
        "admin/edit_question.html",
        quiz=quiz,
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
            flash("Nenhum arquivo selecionado.", "danger")
            return redirect(request.url)
        
        file = request.files["csv_file"]
        if file.filename == "":
            flash("Nenhum arquivo selecionado.", "danger")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            conn = PostgresConnectionFactory.get_connection()
            try:
                c = conn.cursor()
                # Resetar a sequência do ID
                c.execute("SELECT setval('quizzes_id_seq', (SELECT MAX(id) FROM quizzes));")
                
                # Ler o arquivo CSV
                csv_data = file.read().decode('utf-8').splitlines()
                reader = csv.reader(csv_data)
                next(reader)  # Pular o cabeçalho
                
                for row in reader:
                    if len(row) != 9:  # Agora esperamos 9 colunas
                        flash(f"Erro: A linha deve conter exatamente 9 colunas. Linha atual: {row}", "danger")
                        continue
                        
                    # Inserir os dados da questão
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
                conn.rollback()
                flash(f"Ocorreu um erro ao importar as perguntas: {e}", "danger")
            finally:
                c.close()
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
                   topic, grade, points, difficulty 
            FROM suggested_questions 
            WHERE id = %s
        """, (suggestion_id,))
        suggestion = cursor.fetchone()
        
        if suggestion:
            # Insere na tabela quizzes (only first 9 fields, option4 can be empty)
            cursor.execute("""
                INSERT INTO quizzes 
                (question, correct_answer, option1, option2, option3, option4, topic, grade, points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, suggestion[:9])  # First 9 fields only
            
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

            # Option4 is optional for SAT questions  
            required_fields = [question, correct_answer, option1, option2, option3, topic, grade, points]
            if not topic.startswith("SAT"):
                required_fields.append(option4)
                
            if not all(required_fields):
                flash("Todos os campos obrigatórios devem ser preenchidos!", "danger")
                return redirect(url_for("admin.add_quiz"))

            c.execute(
                """
                INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, topic, grade, points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (question, correct_answer, option1, option2, option3, option4 or "", topic, grade, points)
            )
            conn.commit()
            flash("Pergunta adicionada com sucesso!", "success")
            return redirect(url_for("admin.dashboard"))
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao adicionar a pergunta: {e}", "danger")

    c.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
    db_topics = [topic[0] for topic in c.fetchall()]
    
    # Add SAT to admin topics
    topics = ['SAT'] + db_topics
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
