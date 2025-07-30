from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils import database
from app.utils.database import PostgresConnectionFactory

bp = Blueprint('quiz', __name__)

@bp.route('/quizzes')
def quizzes():
    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
    topics = [topic[0] for topic in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('quiz/quizzes_list.html', topics=topics)

@bp.route('/select_difficulty/<topic>')
def select_difficulty(topic):
    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT grade FROM quizzes WHERE topic = %s ORDER BY grade", (topic,))
    grades = [grade[0] for grade in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template('quiz/select_difficulty.html', topic=topic, grades=grades)

@bp.route("/select_grade/<topic>")
def select_grade(topic):
    if "user_id" in session:
        grades = database.get_grades_for_topic(topic)
        return render_template("quiz/select_grade.html", topic=topic, grades=grades)
    else:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("auth.login"))

@bp.route("/quizzes/<topic>/<grade>")
def start_quiz(topic, grade):
    if "user_id" in session:
        session["current_topic"] = topic
        session["current_grade"] = grade
        return redirect(url_for("quiz.quiz_continuous"))
    else:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("auth.login"))

@bp.route("/quiz", methods=["GET", "POST"])
def quiz_continuous():
    if "user_id" not in session:
        flash("Você precisa estar logado para acessar os quizzes.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    role = database.get_user_role()
    topic = session.get("current_topic")
    grade = session.get("current_grade")

    if request.method == "POST":
        quiz_id = session.get("current_quiz_id")
        user_answer = request.form["answer"]

        # Obter a questão atual
        conn = PostgresConnectionFactory.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
        quiz = cursor.fetchone()
        cursor.close()

        if quiz:
            # Mapear a resposta do usuário (a/b/c/d) para o texto da alternativa
            option_map = {
                'a': quiz[3],  # option1
                'b': quiz[4],  # option2  
                'c': quiz[5],  # option3
                'd': quiz[6]   # option4
            }
            
            user_answer_text = option_map.get(user_answer, "")
            correct_answer_text = quiz[2]  # correct_answer
            
            # Comparar os textos das respostas
            is_correct = user_answer_text.strip() == correct_answer_text.strip()
            
            if is_correct:
                # Atualizar pontos do usuário
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_points (user_id, quiz_id, points, is_correct) VALUES (%s, %s, %s, %s)",
                    (user_id, quiz_id, quiz[9], 1)  # quiz[9] é points
                )
                conn.commit()
                cursor.close()
                
                flash("Resposta correta! Pontos adicionados.", "success")
                correct_answer = None
            else:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_points (user_id, quiz_id, points, is_correct) VALUES (%s, %s, %s, %s)",
                    (user_id, quiz_id, 0, 0)
                )
                conn.commit()
                cursor.close()
                
                # Encontrar qual letra corresponde à resposta correta
                correct_letter = ""
                for letter, option_text in option_map.items():
                    if option_text.strip() == correct_answer_text.strip():
                        correct_letter = letter.upper()
                        break
                
                correct_answer = f"{correct_letter}) {correct_answer_text}"

            if role == "admin":
                quiz = database.get_random_quiz_admin(topic, grade)
            else:
                quiz = database.get_random_quiz(user_id, topic, grade)

            if quiz:
                session["current_quiz_id"] = quiz[0]
                
                # Converter tupla do banco para dicionário compatível com o template
                question_data = {
                    'id': quiz[0],
                    'pergunta': quiz[1],
                    'alternativa_a': quiz[3],
                    'alternativa_b': quiz[4], 
                    'alternativa_c': quiz[5],
                    'alternativa_d': quiz[6],
                    'materia': quiz[7]
                }
                
                return render_template("quiz/quiz.html", question=question_data, correct_answer=correct_answer)
            else:
                session.pop("current_quiz_id", None)
                session.pop("current_topic", None)
                session.pop("current_grade", None)
                flash("Você respondeu todas as perguntas deste tópico e série.", "info")
                return redirect(url_for("auth.dashboard"))
    
    # Método GET
    if role == "admin":
        quiz = database.get_random_quiz_admin(topic, grade)
    else:
        quiz = database.get_random_quiz(user_id, topic, grade)

    if quiz:
        session["current_quiz_id"] = quiz[0]
        
        # Converter tupla do banco para dicionário compatível com o template
        question_data = {
            'id': quiz[0],
            'pergunta': quiz[1],
            'alternativa_a': quiz[3],
            'alternativa_b': quiz[4], 
            'alternativa_c': quiz[5],
            'alternativa_d': quiz[6],
            'materia': quiz[7]
        }
        
        return render_template("quiz/quiz.html", question=question_data, correct_answer=None)
    else:
        flash("Não há perguntas disponíveis para este tópico e série.", "info")
        return redirect(url_for("auth.dashboard"))

@bp.route("/suggest_question", methods=["GET", "POST"])
def suggest_question():
    if "user_id" not in session:
        flash("Você precisa estar logado para sugerir uma questão.", "warning")
        return redirect(url_for("auth.login"))

    conn = PostgresConnectionFactory.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT topic FROM quizzes")
    topics = [row[0] for row in c.fetchall()]
    grades = ["6º ano", "7º ano", "8º ano", "9º ano", "1º ano EM", "2º ano EM", "3º ano EM"]

    if request.method == "POST":
        try:
            question = request.form.get("question")
            correct_answer = request.form.get("correct_answer")
            option1 = request.form.get("option1")
            option2 = request.form.get("option2")
            option3 = request.form.get("option3")
            option4 = request.form.get("option4")
            points = request.form.get("points")
            topic = request.form.get("topic")
            if topic == "novo_tema":
                topic = request.form.get("new_topic")
            grade = request.form.get("grade")
            difficulty = request.form.get("difficulty")

            if not all([question, correct_answer, option1, option2, option3, option4, points, topic, grade, difficulty]):
                flash("Todos os campos são obrigatórios!", "danger")
                return render_template("quiz/suggest_question.html", topics=topics, grades=grades)

            c.execute(
                """
                INSERT INTO suggested_questions 
                (user_id, question, correct_answer, option1, option2, option3, option4, topic, grade, points, difficulty, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendente')
                """,
                (session["user_id"], question, correct_answer, option1, option2, option3, option4, topic, grade, points, difficulty)
            )
            conn.commit()
            flash("Sua sugestão foi enviada para revisão!", "success")
            return redirect(url_for("auth.dashboard"))
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir no banco:", e)
            flash("Erro ao salvar sua sugestão. Tente novamente!", "danger")

    return render_template("quiz/suggest_question.html", topics=topics, grades=grades)

@bp.route("/animation-demo")
def animation_demo():
    """Página de demonstração das animações Khan Academy style"""
    return render_template("quiz/animation-demo.html", title="Demonstração de Animações")
