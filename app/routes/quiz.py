from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils import database  
from app.utils.database import PostgresConnectionFactory
from werkzeug.utils import secure_filename
import random
import os

# Safe PIL import
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL/Pillow não disponível - funcionalidade de imagens desabilitada")

bp = Blueprint('quiz', __name__)

# Image upload configuration
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_upload(file, suggestion_id):
    """Process and save uploaded image for a suggestion"""
    if not file or not allowed_file(file.filename):
        print(f"❌ Invalid file or file not allowed: {file.filename if file else 'None'}")
        return None
        
    if not PIL_AVAILABLE:
        print("⚠️ PIL not available - saving file directly")
        
    try:
        # Generate secure filename
        filename = f"suggestion_{suggestion_id}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        print(f"💾 Saving image to: {filepath}")
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        if PIL_AVAILABLE:
            # Open and process image with PIL
            image = Image.open(file)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large (max 1200px width)
            if image.width > 1200:
                ratio = 1200 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((1200, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            image.save(filepath, 'JPEG', quality=85, optimize=True)
        else:
            # Fallback: save file directly
            file.save(filepath)
        
        print(f"✅ Image saved successfully: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Erro ao processar imagem: {e}")
        import traceback
        traceback.print_exc()
        return None

def move_suggestion_image_to_quiz(suggestion_id, quiz_id):
    """Move image from suggestion to quiz when approved"""
    try:
        old_path = os.path.join(UPLOAD_FOLDER, f"suggestion_{suggestion_id}.jpg")
        new_path = os.path.join(UPLOAD_FOLDER, f"quiz_{quiz_id}.jpg")
        
        print(f"🔄 Moving image: {old_path} → {new_path}")
        print(f"📁 Source exists: {os.path.exists(old_path)}")
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"✅ Image moved successfully: suggestion_{suggestion_id}.jpg → quiz_{quiz_id}.jpg")
            return True
        else:
            print(f"❌ Source image not found: suggestion_{suggestion_id}.jpg")
    except Exception as e:
        print(f"❌ Erro ao mover imagem: {e}")
        import traceback
        traceback.print_exc()
    return False

def clean_html(text):
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def check_question_image(quiz_id):
    """Check if image exists for a quiz question"""
    image_path = os.path.join(UPLOAD_FOLDER, f"quiz_{quiz_id}.jpg")
    print(f"🔍 Checking image for quiz {quiz_id}: {image_path}")
    print(f"📁 Image exists: {os.path.exists(image_path)}")
    if os.path.exists(image_path):
        print(f"✅ Image found: quiz_{quiz_id}.jpg")
        return f"quiz_{quiz_id}.jpg"
    print(f"❌ No image found for quiz {quiz_id}")
    return None

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
                
                # Check if image exists for this question
                question_image = check_question_image(quiz[0])
                return render_template("quiz/quiz.html", question=question_data, correct_answer=correct_answer, rational=rational, question_image=question_image)
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
        
        # Check if image exists for this question
        question_image = check_question_image(quiz[0])
        return render_template("quiz/quiz.html", question=question_data, correct_answer=None, question_image=question_image)
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (question, correct_answer, option1, option2, option3, "", topic, grade, int(points))
                )
                quiz_id = c.fetchone()[0]
                conn.commit()
                
                # Process image upload for direct submission
                if 'question_image' in request.files:
                    file = request.files['question_image']
                    if file and file.filename and allowed_file(file.filename):
                        # For direct submission, save as quiz image directly
                        filename = f"quiz_{quiz_id}.jpg"
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        
                        # Ensure upload directory exists
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        print(f"💾 Saving admin/colaborador image to: {filepath}")
                        
                        if PIL_AVAILABLE:
                            try:
                                image = Image.open(file)
                                if image.mode in ('RGBA', 'LA', 'P'):
                                    image = image.convert('RGB')
                                if image.width > 1200:
                                    ratio = 1200 / image.width
                                    new_height = int(image.height * ratio)
                                    image = image.resize((1200, new_height), Image.Resampling.LANCZOS)
                                image.save(filepath, 'JPEG', quality=85, optimize=True)
                                print(f"✅ Admin image saved with PIL: {filename}")
                            except Exception as e:
                                print(f"❌ Erro ao salvar imagem: {e}")
                        else:
                            # Fallback: save file directly without processing
                            file.save(filepath)
                            print(f"✅ Admin image saved directly: {filename}")
                
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendente') RETURNING id
                """,
                (session["user_id"], question, correct_answer, option1, option2, option3, "", topic, grade, points, difficulty)
            )
            suggestion_id = c.fetchone()[0]
            conn.commit()
            
            # Process image upload if present
            if 'question_image' in request.files:
                file = request.files['question_image']
                if file and file.filename and allowed_file(file.filename):
                    process_image_upload(file, suggestion_id)
                    
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

@bp.route("/debug/images")
def debug_images():
    """Debug route to check uploaded images"""
    if not ("user_role" in session and session["user_role"] in ["admin", "colaborador"]):
        return "Access denied", 403
        
    import glob
    upload_path = os.path.join(UPLOAD_FOLDER, "*.jpg")
    images = glob.glob(upload_path)
    
    html = "<h2>🔍 Debug: Uploaded Images</h2>"
    html += f"<p><strong>Upload folder:</strong> {UPLOAD_FOLDER}</p>"
    html += f"<p><strong>Folder exists:</strong> {os.path.exists(UPLOAD_FOLDER)}</p>"
    html += f"<p><strong>Images found:</strong> {len(images)}</p><br>"
    
    for img_path in images:
        img_name = os.path.basename(img_path)
        img_size = os.path.getsize(img_path)
        html += f"<div style='border: 1px solid #ccc; padding: 10px; margin: 10px;'>"
        html += f"<strong>{img_name}</strong> ({img_size} bytes)<br>"
        html += f"<img src='/static/uploads/{img_name}' style='max-width: 300px; height: auto;' />"
        html += f"</div>"
    
    return html
