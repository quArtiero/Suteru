from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils import database
from app.utils.database import PostgresConnectionFactory
import random

bp = Blueprint('quiz', __name__)

@bp.route('/quizzes')
def quizzes():
    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT topic FROM quizzes ORDER BY topic")
    db_topics = [topic[0] for topic in cursor.fetchall()]
    
    # Add SAT as special topic at the beginning
    topics = ['SAT'] + db_topics
    
    cursor.close()
    conn.close()
    
    return render_template('quiz/quizzes_list.html', topics=topics)

@bp.route('/sat/<section>')
def sat_section(section):
    """Route para seções SAT (english ou math)"""
    if section not in ['english', 'math']:
        flash("Seção SAT inválida.", "danger")
        return redirect(url_for('quiz.quizzes'))
    
    # Níveis SAT simples
    levels = ['Level 1', 'Level 2', 'Level 3']
    section_title = 'English Reading & Writing' if section == 'english' else 'Math'
    
    return render_template('quiz/sat_levels.html', 
                         section=section, 
                         section_title=section_title, 
                         levels=levels)

@bp.route('/sat/<section>/<level>')
def sat_quiz(section, level):
    """Route para iniciar quiz SAT específico"""
    if section not in ['english', 'math'] or level not in ['Level 1', 'Level 2', 'Level 3']:
        flash("Seção ou nível SAT inválido.", "danger")
        return redirect(url_for('quiz.quizzes'))
    
    # Check if user is logged in
    if "user_id" not in session:
        flash("Você precisa estar logado para fazer quiz.", "warning")
        return redirect(url_for("auth.login"))
    
    # Set up session for SAT quiz
    section_name = 'English' if section == 'english' else 'Math'
    session['current_topic'] = f'SAT {section_name}'
    session['current_grade'] = level
    session['sat_section'] = section
    session['sat_level'] = level
    
    # Redirect to the continuous quiz system
    return redirect(url_for('quiz.quiz_continuous'))

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
            # Use stored options from session for consistency (SAT questions)
            stored_options = session.get('current_quiz_options', {})
            
            if stored_options:
                # Use exact mapping shown to user
                option_map = stored_options
            else:
                # Fallback: dynamic mapping for older questions
                option_map = {}
                if quiz[3] and quiz[3].strip():  # option1
                    option_map['a'] = quiz[3]
                if quiz[4] and quiz[4].strip():  # option2
                    option_map['b'] = quiz[4]
                if quiz[5] and quiz[5].strip():  # option3
                    option_map['c'] = quiz[5]
                if quiz[6] and quiz[6].strip():  # option4 (only if not empty)
                    option_map['d'] = quiz[6]
            
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
                rational = None  # No rational needed when user is correct
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
                
                # Add rational for SAT questions when user gets it wrong
                rational = None
                if topic and topic.startswith('SAT'):
                    rational = f"""
                    <p><strong>📚 Explicação SAT:</strong></p>
                    <p>Esta questão requer análise cuidadosa do texto apresentado.</p>
                    <p><strong>✅ A resposta correta é:</strong> {correct_answer_text}</p>
                    <p><strong>💡 Estratégia:</strong> Releia o texto e identifique as palavras-chave que fundamentam a resposta correta.</p>
                    <p><strong>📖 Dica SAT:</strong> Sempre baseie sua resposta em evidências específicas do texto.</p>
                    <p><em>Continue praticando para melhorar sua pontuação no SAT! 🎯</em></p>
                    """

            if role == "admin":
                quiz = database.get_random_quiz_admin(topic, grade)
            else:
                quiz = database.get_random_quiz(user_id, topic, grade)

            if quiz:
                session["current_quiz_id"] = quiz[0]
                
                # Smart option arrangement for SAT vs regular questions (POST method)
                if topic and topic.startswith('SAT'):
                    # For SAT: Mix correct answer with incorrect options
                    correct_answer_db = quiz[2]
                    incorrect_options = [quiz[3], quiz[4], quiz[5], quiz[6]]
                    valid_incorrect = [opt for opt in incorrect_options if opt and opt.strip()]
                    
                    # Create shuffled options list
                    all_options = [correct_answer_db] + valid_incorrect
                    random.shuffle(all_options)
                    
                    # Ensure we have 4 positions
                    while len(all_options) < 4:
                        all_options.append('')
                    
                    question_data = {
                        'id': quiz[0],
                        'pergunta': quiz[1],
                        'alternativa_a': all_options[0],
                        'alternativa_b': all_options[1],
                        'alternativa_c': all_options[2],
                        'alternativa_d': all_options[3],
                        'materia': quiz[7]
                    }
                    
                    # Store the option mapping for consistency
                    session['current_quiz_options'] = {
                        'a': all_options[0],
                        'b': all_options[1],
                        'c': all_options[2],
                        'd': all_options[3]
                    }
                else:
                    # Regular questions: use original structure
                    question_data = {
                        'id': quiz[0],
                        'pergunta': quiz[1],
                        'alternativa_a': quiz[3],
                        'alternativa_b': quiz[4], 
                        'alternativa_c': quiz[5],
                        'alternativa_d': quiz[6],
                        'materia': quiz[7]
                    }
                    
                    # Store regular options mapping
                    session['current_quiz_options'] = {
                        'a': quiz[3],
                        'b': quiz[4],
                        'c': quiz[5],
                        'd': quiz[6]
                    }
                
                return render_template("quiz/quiz.html", question=question_data, correct_answer=correct_answer, rational=rational)
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
        
        # Smart option arrangement for SAT vs regular questions
        if topic and topic.startswith('SAT'):
            # For SAT: Mix correct answer with incorrect options
            correct_answer = quiz[2]
            incorrect_options = [quiz[3], quiz[4], quiz[5], quiz[6]]
            valid_incorrect = [opt for opt in incorrect_options if opt and opt.strip()]
            
            # Create shuffled options list
            all_options = [correct_answer] + valid_incorrect
            random.shuffle(all_options)
            
            # Ensure we have 4 positions (pad with empty if needed)
            while len(all_options) < 4:
                all_options.append('')
            
            question_data = {
                'id': quiz[0],
                'pergunta': quiz[1],
                'alternativa_a': all_options[0],
                'alternativa_b': all_options[1],
                'alternativa_c': all_options[2],
                'alternativa_d': all_options[3],
                'materia': quiz[7]
            }
            
            # Store the option mapping for answer validation
            session['current_quiz_options'] = {
                'a': all_options[0],
                'b': all_options[1],
                'c': all_options[2],
                'd': all_options[3]
            }
        else:
            # Regular questions: use original structure
            question_data = {
                'id': quiz[0],
                'pergunta': quiz[1],
                'alternativa_a': quiz[3],
                'alternativa_b': quiz[4], 
                'alternativa_c': quiz[5],
                'alternativa_d': quiz[6],
                'materia': quiz[7]
            }
            
            # Store regular options mapping
            session['current_quiz_options'] = {
                'a': quiz[3],
                'b': quiz[4],
                'c': quiz[5],
                'd': quiz[6]
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

    # Check bypass privileges (admin or colaborador)
    can_bypass = database.can_bypass_review()
    user_role = database.get_user_role()
    is_admin = user_role == "admin"
    is_colaborador = user_role == "colaborador"

    conn = PostgresConnectionFactory.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT topic FROM quizzes")
    db_topics = [row[0] for row in c.fetchall()]
    
    # Add SAT to suggestion form topics
    topics = ['SAT'] + db_topics
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
            elif topic == "SAT":
                # For SAT, combine section and level into topic
                sat_section = request.form.get("sat_section")
                sat_level = request.form.get("sat_level")
                if sat_section and sat_level:
                    section_name = 'English' if sat_section == 'english' else 'Math'
                    topic = f"SAT {section_name}"
                    grade = sat_level  # Use SAT level as grade
                else:
                    flash("Por favor, selecione seção e nível SAT.", "danger")
                    return render_template("quiz/suggest_question.html", topics=topics, grades=grades, can_bypass=can_bypass, is_admin=is_admin, is_colaborador=is_colaborador)
            else:
                grade = request.form.get("grade")
                
            # Default values for simplified UX
            difficulty = request.form.get("difficulty", "medio")  # Default to medium
            points = request.form.get("points", "10")  # Default to 10 points

            # Simplified validation (difficulty and points have defaults)
            if not all([question, correct_answer, option1, option2, option3, topic, grade]):
                flash("Todos os campos são obrigatórios!", "danger")
                return render_template("quiz/suggest_question.html", topics=topics, grades=grades, can_bypass=can_bypass, is_admin=is_admin, is_colaborador=is_colaborador)

            # BYPASS REVIEW - Add directly to quizzes table (admin or colaborador)
            if can_bypass:
                c.execute(
                    """
                    INSERT INTO quizzes 
                    (question, correct_answer, option1, option2, option3, option4, topic, grade, points) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (question, correct_answer, option1, option2, option3, "", topic, grade, int(points))
                )
                conn.commit()
                if is_admin:
                    flash("✅ Questão adicionada diretamente ao banco de dados!", "success") 
                    return redirect(url_for("admin.quizzes"))
                else:  # is_colaborador
                    flash("✅ Questão adicionada diretamente como colaborador!", "success")
                    return redirect(url_for("auth.dashboard"))
            else:
                # REGULAR USER - Add to suggestions for review
                c.execute(
                    """
                    INSERT INTO suggested_questions 
                    (user_id, question, correct_answer, option1, option2, option3, option4, topic, grade, points, difficulty, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendente')
                    """,
                    (session["user_id"], question, correct_answer, option1, option2, option3, "", topic, grade, points, difficulty)
                )
                conn.commit()
                flash("Sua sugestão foi enviada para revisão!", "success")
                return redirect(url_for("auth.dashboard"))
                
        except Exception as e:
            conn.rollback()
            print("Erro ao inserir no banco:", e)
            flash("Erro ao salvar sua questão. Tente novamente!", "danger")

    return render_template("quiz/suggest_question.html", topics=topics, grades=grades, can_bypass=can_bypass, is_admin=is_admin, is_colaborador=is_colaborador)

@bp.route("/animation-demo")
def animation_demo():
    """Página de demonstração das animações Khan Academy style"""
    return render_template("quiz/animation-demo.html", title="Demonstração de Animações")
