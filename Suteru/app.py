import sqlite3
from flask import Flask, render_template, request, redirect, \
    url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, \
    check_password_hash
import os
from flask_mail import Mail, Message
# Remova a importação do OAuth se não estiver usando
# from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = 'minhachave'  # Substitua por sua chave secreta

# Configurações do Flask-Mail 
app.config['MAIL_SERVER'] = 'smtp.seu_servidor.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'seu_email@dominio.com'
app.config['MAIL_PASSWORD'] = 'sua_senha'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

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

ALLOWED_EXTENSIONS = {'csv'}

# Funções auxiliares

def get_topics():
    conn = sqlite3.connect('sutēru.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT topic FROM quizzes')
    topics = [row[0] for row in c.fetchall()]
    conn.close()
    return topics

def get_grades_for_topic(topic):
    conn = sqlite3.connect('sutēru.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT grade FROM quizzes WHERE topic = ?', (topic,))
    grades = [row[0] for row in c.fetchall()]
    conn.close()
    grade_order = ['6º ano', '7º ano', '8º ano', '9º ano',
                   '1º ano EM', '2º ano EM', '3º ano EM']
    grades.sort(key=lambda x: grade_order.index(x)
                if x in grade_order else len(grade_order))
    return grades
from flask import send_from_directory

@app.route('/download_csv_template')
def download_csv_template():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            return send_from_directory(directory='static', path='modelo_perguntas.csv', as_attachment=True)
        else:
            flash('Acesso negado. Você não tem permissão para baixar este arquivo.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

def get_user_role():
    if 'user_id' in session:
        conn = sqlite3.connect('sutēru.db')
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
        result = c.fetchone()
        role = result[0] if result else None
        conn.close()
        return role
    return None


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_user_role():
    return dict(get_user_role=get_user_role)

# Rotas

@app.route('/')
def home():
    try:
        conn = sqlite3.connect('sutēru.db')
        c = conn.cursor()
        c.execute('SELECT SUM(points) FROM user_points')
        total_points = c.fetchone()[0] or 0
        total_kg_donated = total_points // 10
        return render_template('index.html',
                               total_kg_donated=total_kg_donated)
    except sqlite3.DatabaseError as e:
        print(f"Erro no banco de dados: {e}")
        flash('Houve um problema com o banco de dados. '
              'Tente novamente mais tarde.', 'danger')
        return render_template('index.html', total_kg_donated=0)
    finally:
        conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password,
                                                 method='pbkdf2:sha256')

        conn = sqlite3.connect('sutēru.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? OR email = ?',
                  (username, email))
        existing_user = c.fetchone()

        if existing_user:
            flash('Nome de usuário ou e-mail já existe. '
                  'Escolha outro.', 'warning')
            conn.close()
            return redirect(url_for('register'))

        role = 'admin' if username == 'admin' else 'user'
        c.execute('INSERT INTO users (username, email, password, role) '
                  'VALUES (?, ?, ?, ?)',
                  (username, email, hashed_password, role))
        conn.commit()
        conn.close()

        flash('Registro realizado com sucesso! Faça login para continuar.',
              'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        conn = sqlite3.connect('sutēru.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? OR email = ?',
                  (username_or_email, username_or_email))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            role = user[4]
            if role == 'admin':
                flash('Login realizado com sucesso! Bem-vindo, '
                      'administrador.', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

# Remova as rotas de login com o Google se não estiver usando
'''
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
'''
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        try:
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute('SELECT SUM(points) FROM user_points '
                      'WHERE user_id = ?', (session['user_id'],))
            total_points = c.fetchone()[0] or 0
            conversion_rate = 10
            food_donation = total_points // conversion_rate
            return render_template('dashboard.html',
                                   total_points=total_points,
                                   food_donation=food_donation)
        finally:
            conn.close()
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

@app.route('/quizzes')
def quizzes():
    if 'user_id' in session:
        topics = get_topics()
        return render_template('quizzes.html', topics=topics)
    else:
        flash('Você precisa estar logado para acessar os quizzes.',
              'warning')
        return redirect(url_for('login'))

@app.route('/select_grade/<topic>')
def select_grade(topic):
    if 'user_id' in session:
        grades = get_grades_for_topic(topic)
        return render_template('select_grade.html',
                               topic=topic, grades=grades)
    else:
        flash('Você precisa estar logado para acessar os quizzes.',
              'warning')
        return redirect(url_for('login'))

@app.route('/quizzes/<topic>/<grade>')
def start_quiz(topic, grade):
    if 'user_id' in session:
        session['current_topic'] = topic
        session['current_grade'] = grade
        return redirect(url_for('quiz_continuous'))
    else:
        flash('Você precisa estar logado para acessar os quizzes.',
              'warning')
        return redirect(url_for('login'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz_continuous():
    if 'user_id' in session:
        try:
            user_id = session['user_id']
            topic = session.get('current_topic')
            grade = session.get('current_grade')

            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()

            if request.method == 'POST':
                quiz_id = session.get('current_quiz_id')
                user_answer = request.form['answer']
                c.execute('SELECT * FROM quizzes WHERE id = ?',
                          (quiz_id,))
                quiz = c.fetchone()

                is_correct = 1 if user_answer == quiz[2] else 0
                points = quiz[9] if is_correct else 0

                c.execute('INSERT INTO user_points '
                          '(user_id, quiz_id, points, is_correct) '
                          'VALUES (?, ?, ?, ?)',
                          (user_id, quiz_id, points, is_correct))
                conn.commit()

                if is_correct:
                    flash('Resposta correta! Pontos adicionados.',
                          'success')
                else:
                    flash('Resposta incorreta. A resposta correta era: '
                          f'{quiz[2]}', 'danger')

            c.execute('''
                SELECT q.*
                FROM quizzes q
                LEFT JOIN (
                    SELECT quiz_id FROM user_points WHERE user_id = ?
                ) up ON q.id = up.quiz_id
                WHERE q.topic = ? AND q.grade = ? AND up.quiz_id IS NULL
                ORDER BY RANDOM()
                LIMIT 1
            ''', (user_id, topic, grade))
            quiz = c.fetchone()

            if quiz:
                session['current_quiz_id'] = quiz[0]
                return render_template('quiz.html', quiz=quiz)
            else:
                session.pop('current_quiz_id', None)
                session.pop('current_topic', None)
                session.pop('current_grade', None)
                flash('Você respondeu todas as perguntas deste '
                      'tópico e série.', 'info')
                return redirect(url_for('dashboard'))
        finally:
            conn.close()
    else:
        flash('Você precisa estar logado para acessar os quizzes.',
              'warning')
        return redirect(url_for('login'))

@app.route('/admin/delete_selected_questions', methods=['POST'])
def delete_selected_questions():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            selected_questions = request.form.getlist('selected_questions')
            if selected_questions:
                conn = sqlite3.connect('sutēru.db')
                c = conn.cursor()
                placeholders = ','.join('?' for _ in selected_questions)
                query = f'DELETE FROM quizzes WHERE id IN ({placeholders})'
                c.execute(query, selected_questions)
                conn.commit()
                conn.close()
                flash('As perguntas selecionadas foram deletadas com sucesso!', 'success')
            else:
                flash('Nenhuma pergunta selecionada.', 'warning')
            return redirect(url_for('admin_quizzes'))
        else:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


@app.route('/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            if request.method == 'POST':
                question = request.form['question']
                correct_answer = request.form['correct_answer']
                option1 = request.form['option1']
                option2 = request.form['option2']
                option3 = request.form['option3']
                option4 = request.form['option4']
                points = int(request.form['points'])
                topic = request.form['topic']
                if topic == 'novo_tema':
                    topic = request.form['new_topic']
                grade = request.form['grade']

                conn = sqlite3.connect('sutēru.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO quizzes (question, correct_answer,
                    option1, option2, option3, option4, points, topic,
                    grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (question, correct_answer, option1, option2,
                      option3, option4, points, topic, grade))
                conn.commit()
                conn.close()

                flash('Quiz adicionado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                topics = get_topics()
                grades = ['6º ano', '7º ano', '8º ano', '9º ano',
                          '1º ano EM', '2º ano EM', '3º ano EM']
                return render_template('add_quiz.html',
                                       topics=topics, grades=grades)
        else:
            flash('Acesso negado. Você não tem permissão para '
                  'adicionar quizzes.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado para adicionar quizzes.',
              'warning')
        return redirect(url_for('login'))

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('sutēru.db')
    c = conn.cursor()
    c.execute('''
        SELECT u.username, SUM(up.points) as total_points,
        CAST(SUM(up.points) / 10 AS INTEGER) as total_kg
        FROM users u
        JOIN user_points up ON u.id = up.user_id
        GROUP BY u.username
        ORDER BY total_points DESC
        LIMIT 10
    ''')
    leaderboard = c.fetchall()
    conn.close()
    return render_template('leaderboard.html',
                           leaderboard=leaderboard)

@app.route('/suggest_question', methods=['POST'])
def suggest_question():
    if 'user_id' in session:
        user_id = session['user_id']
        question = request.form['question']
        correct_answer = request.form['correct_answer']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        points = request.form['points']
        topic = request.form['topic']
        grade = request.form['grade']
        conn = sqlite3.connect('sutēru.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO suggestions (question, correct_answer, option1, option2, option3, option4, points, topic, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (question, correct_answer, option1, option2, option3, option4, points, topic, grade))
        conn.commit()
        conn.close()
        flash('Sugestão enviada para revisão!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


@app.route('/admin/quizzes')
def admin_quizzes():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            topic_filter = request.args.get('topic', '')
            grade_filter = request.args.get('grade', '')
            query = 'SELECT * FROM quizzes WHERE 1=1'
            params = []
            if topic_filter:
                query += ' AND topic LIKE ?'
                params.append(f'%{topic_filter}%')
            if grade_filter:
                query += ' AND grade LIKE ?'
                params.append(f'%{grade_filter}%')

            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()

            # Obter listas de tópicos e séries
            c.execute('SELECT DISTINCT topic FROM quizzes')
            topics = [row[0] for row in c.fetchall()]

            c.execute('SELECT DISTINCT grade FROM quizzes')
            grades = [row[0] for row in c.fetchall()]

            # Aplicar filtros
            c.execute(query, params)
            quizzes = c.fetchall()

            # Verificar duplicados
            question_counts = {}
            for quiz in quizzes:
                question = quiz[1].strip().lower()
                if question in question_counts:
                    question_counts[question].append(quiz)
                else:
                    question_counts[question] = [quiz]

            duplicates = [q for qs in question_counts.values() if len(qs) > 1 for q in qs]
            conn.close()

            return render_template('admin_quizzes.html', quizzes=quizzes, total_quizzes=len(quizzes), duplicates=duplicates, topics=topics, grades=grades)
        else:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

@app.route('/delete_duplicates', methods=['POST'])
def delete_duplicates():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()

            # Verificar duplicados
            c.execute('SELECT * FROM quizzes')
            quizzes = c.fetchall()
            question_counts = {}
            for quiz in quizzes:
                question = quiz[1].strip().lower()
                if question in question_counts:
                    question_counts[question].append(quiz)
                else:
                    question_counts[question] = [quiz]

            duplicates_to_delete = [q[0] for qs in question_counts.values() if len(qs) > 1 for q in qs[1:]]  # Deletar todas, exceto a primeira ocorrência

            if duplicates_to_delete:
                c.executemany('DELETE FROM quizzes WHERE id = ?', [(id,) for id in duplicates_to_delete])
                conn.commit()

            conn.close()
            flash(f'Duplicatas deletadas: {len(duplicates_to_delete)} perguntas', 'success')
            return redirect(url_for('admin_quizzes'))
        else:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))



@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute('DELETE FROM quizzes WHERE id = ?', (question_id,))
            conn.commit()
            conn.close()
            flash('Pergunta excluída com sucesso!', 'success')
            return redirect(url_for('admin_quizzes'))
        else:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


@app.route('/admin/review_suggestions', methods=['GET', 'POST'])
def review_suggestions():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute('''
                SELECT id, question, correct_answer, option1, option2, option3, option4, points, topic, grade
                FROM suggestions
            ''')
            suggestions = c.fetchall()
            conn.close()
            return render_template('review_suggestions.html', suggestions=suggestions)
        else:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


@app.route('/approve_suggestion/<int:suggestion_id>')
def approve_suggestion(suggestion_id):
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute('SELECT * FROM suggested_questions WHERE '
                      'id = ?', (suggestion_id,))
            suggestion = c.fetchone()
            if suggestion:
                c.execute('''
                    INSERT INTO quizzes (question, correct_answer,
                    option1, option2, option3, option4, topic, grade,
                    points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (suggestion[2], suggestion[3], suggestion[4],
                      suggestion[5], suggestion[6], suggestion[7],
                      suggestion[8], suggestion[9], suggestion[10]))
                c.execute('UPDATE suggested_questions SET status = ? '
                          'WHERE id = ?', ('aprovada', suggestion_id))
                conn.commit()
                flash('Sugestão de pergunta aprovada e adicionada aos '
                      'quizzes!', 'success')
            conn.close()
            return redirect(url_for('review_suggestions'))
        else:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

@app.route('/reject_suggestion/<int:suggestion_id>')
def reject_suggestion(suggestion_id):
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute('UPDATE suggested_questions SET status = ? '
                      'WHERE id = ?', ('rejeitada', suggestion_id))
            conn.commit()
            conn.close()
            flash('Sugestão de pergunta rejeitada.', 'success')
            return redirect(url_for('review_suggestions'))
        else:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()

            c.execute('SELECT date(timestamp) as date, '
                      'SUM(points)/10 as kg_donated FROM user_points '
                      'GROUP BY date(timestamp) ORDER BY date(timestamp) '
                      'DESC LIMIT 7')
            kg_per_day = c.fetchall()

            c.execute('SELECT COUNT(*) FROM users')
            total_users = c.fetchone()[0]

            c.execute('SELECT COUNT(*) FROM user_points')
            total_quizzes = c.fetchone()[0]

            c.execute('SELECT * FROM quizzes')
            quizzes = c.fetchall()

            conn.close()
            return render_template('admin_dashboard.html',
                                   kg_per_day=kg_per_day,
                                   total_users=total_users,
                                   total_quizzes=total_quizzes,
                                   quizzes=quizzes)
        else:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

@app.route('/admin/edit_question/<int:question_id>',
           methods=['GET', 'POST'])
def edit_question(question_id):
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            if request.method == 'POST':
                question = request.form['question']
                correct_answer = request.form['correct_answer']
                option1 = request.form['option1']
                option2 = request.form['option2']
                option3 = request.form['option3']
                option4 = request.form['option4']
                topic = request.form['topic']
                if topic == 'novo_tema':
                    topic = request.form['new_topic']
                grade = request.form['grade']
                points = int(request.form['points'])

                c.execute('''
                    UPDATE quizzes
                    SET question = ?, correct_answer = ?, option1 = ?,
                    option2 = ?, option3 = ?, option4 = ?, topic = ?,
                    grade = ?, points = ?
                    WHERE id = ?
                ''', (question, correct_answer, option1, option2,
                      option3, option4, topic, grade, points,
                      question_id))
                conn.commit()
                conn.close()
                flash('Pergunta atualizada com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                c.execute('SELECT * FROM quizzes WHERE id = ?',
                          (question_id,))
                question_data = c.fetchone()
                topics = get_topics()
                grades = ['6º ano', '7º ano', '8º ano', '9º ano',
                          '1º ano EM', '2º ano EM', '3º ano EM']
                conn.close()
                return render_template('edit_question.html',
                                       question=question_data,
                                       topics=topics, grades=grades)
        else:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

@app.route('/admin/delete_all_questions', methods=['POST'])
def delete_all_questions():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute('DELETE FROM quizzes')
            conn.commit()
            conn.close()
            flash('Todas as perguntas foram deletadas com sucesso!', 'success')
            return redirect(url_for('admin_quizzes'))
        else:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


@app.route('/admin/users')
def admin_users():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            sort_column = request.args.get('sort', 'username')
            sort_order = request.args.get('order', 'asc')

            valid_columns = ['username', 'total_points', 'accuracy_rate', 'register_date']
            if sort_column not in valid_columns:
                sort_column = 'username'
            if sort_order not in ['asc', 'desc']:
                sort_order = 'asc'

            conn = sqlite3.connect('sutēru.db')
            c = conn.cursor()
            c.execute(f'''
                SELECT u.id, u.username, u.email, u.role, 
                       COALESCE(SUM(up.points), 0) as total_points,
                       COALESCE(SUM(up.points) / 10, 0) as total_kg_donated,
                       COALESCE(SUM(CASE WHEN up.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(up.id), 0) as accuracy_rate,
                       u.register_date
                FROM users u
                LEFT JOIN user_points up ON u.id = up.user_id
                GROUP BY u.id, u.username, u.email, u.role, u.register_date
                ORDER BY {sort_column} {sort_order}
            ''')
            users = c.fetchall()
            conn.close()
            return render_template('admin_users.html', users=users, sort_column=sort_column, sort_order=sort_order)
        else:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


@app.route('/upload_questions', methods=['GET', 'POST'])
def upload_questions():
    if 'user_id' in session:
        role = get_user_role()
        if role == 'admin':
            if request.method == 'POST':
                if 'csv_file' not in request.files:
                    flash('Nenhum arquivo selecionado.', 'warning')
                    return redirect(request.url)
                file = request.files['csv_file']
                if file.filename == '':
                    flash('Nenhum arquivo selecionado.', 'warning')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    import csv
                    import io
                    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                    csv_input = csv.reader(stream)
                    conn = sqlite3.connect('sutēru.db')
                    c = conn.cursor()
                    try:
                        for idx, row in enumerate(csv_input):
                            if len(row) != 9:
                                flash(f'Erro na linha {idx + 1}: número incorreto de colunas.', 'danger')
                                return redirect(request.url)
                            # Assumindo a ordem das colunas no CSV:
                            # question, correct_answer, option1, option2, option3, option4, points, topic, grade
                            c.execute('''
                                INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, points, topic, grade)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', tuple(row))
                        conn.commit()
                        flash('Perguntas importadas com sucesso!', 'success')
                    except Exception as e:
                        flash(f'Ocorreu um erro ao importar as perguntas: {e}', 'danger')
                        conn.rollback()
                    finally:
                        conn.close()
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Arquivo não permitido. Apenas arquivos CSV são aceitos.', 'danger')
                    return redirect(request.url)
            else:
                return render_template('upload_questions.html')
        else:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
