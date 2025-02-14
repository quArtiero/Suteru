import psycopg2
import os
from flask import session
from werkzeug.security import generate_password_hash

POINTS_TO_KG = 10  # This configures the number of points to kg


def get_topics():
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        c = conn.cursor()
        with conn.cursor() as c:
            c.execute("SELECT DISTINCT topic FROM quizzes")
            topics = [row[0] for row in c.fetchall()]
    return topics


def get_grades_for_topic(topic):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute("SELECT DISTINCT grade FROM quizzes WHERE topic = %s", (topic,))
            grades = [row[0] for row in c.fetchall()]
    grade_order = [
        "6º ano",
        "7º ano",
        "8º ano",
        "9º ano",
        "1º ano EM",
        "2º ano EM",
        "3º ano EM",
    ]
    grades.sort(
        key=lambda x: grade_order.index(x) if x in grade_order else len(grade_order)
    )
    return grades


def get_user_role():
    if "user_id" in session:
        with psycopg2.connect(os.environ["internal_db_url"]) as conn:
            with conn.cursor() as c:
                c = conn.cursor()
                c.execute("SELECT role FROM users WHERE id = %s", (session["user_id"],))
                result = c.fetchone()

                role = result[0] if result else None
        return role
    return None


def get_user(username, email=None):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            if email is not None:
                c.execute(
                    "SELECT * FROM users WHERE username = %s OR email = %s",
                    (username, email),
                )
            else:
                c.execute("SELECT * FROM users WHERE username = %s", (username,))
            return c.fetchone()


def get_all_user_points():
    db_error = False
    data = {"total_points": 0, "total_kg_donated": 0}
    try:
        with psycopg2.connect(os.environ["internal_db_url"]) as conn:
            with conn.cursor() as c:
                c.execute("SELECT SUM(points) FROM user_points")
                data["total_points"] = c.fetchone()[0] or 0
                data["total_kg_donated"] = data["total_points"] // POINTS_TO_KG
    except psycopg2.DatabaseError as e:
        print(f"Erro no banco de dados: {e}")
        db_error = True

    return db_error, data


def get_user_points(user_id):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute(
                "SELECT SUM(points) FROM user_points " "WHERE user_id = %s",
                (user_id,),
            )
            total_points = c.fetchone()[0] or 0
            food_donation = total_points // POINTS_TO_KG
            return total_points, food_donation


def update_user_role(username, role):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
            conn.commit()
            print(f"O usuário '{username}' agora é um administrador.")


def delete_selected_questions_db(selected_questions):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            placeholders = ",".join("%s" for _ in selected_questions)
            query = f"DELETE FROM quizzes WHERE id IN ({placeholders})"
            c.execute(query, selected_questions)
            conn.commit()


def create_new_user(username, email, password):
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

    # Role is always set as user, to avoid someone creating an admin
    # In order to set a user as admin, an admin that was created when the site is created
    # should change the role manually of said user, preferably using a page dedicated to
    # admins
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO users (username, email, password, role) "
                "VALUES (%s, %s, %s, %s)",
                (username, email, hashed_password, "user"),
            )
            conn.commit()


def add_quiz_db(request):
    question = request.form["question"]
    correct_answer = request.form["correct_answer"]
    option1 = request.form["option1"]
    option2 = request.form["option2"]
    option3 = request.form["option3"]
    option4 = request.form["option4"]
    points = int(request.form["points"])
    topic = request.form["topic"]
    if topic == "novo_tema":
        topic = request.form["new_topic"]
    grade = request.form["grade"]

    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                    INSERT INTO quizzes (question, correct_answer,
                    option1, option2, option3, option4, points, topic,
                    grade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    question,
                    correct_answer,
                    option1,
                    option2,
                    option3,
                    option4,
                    points,
                    topic,
                    grade,
                ),
            )
            conn.commit()


def get_specific_quiz(quiz_id, user_id, answer):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
            quiz = c.fetchone()

            is_correct = answer == quiz[2]
            points = quiz[9] if is_correct else 0

            c.execute(
                "INSERT INTO user_points "
                "(user_id, quiz_id, points, is_correct) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, quiz_id, points, is_correct),
            )
            conn.commit()
            return is_correct, quiz


def get_random_quiz(user_id, topic, grade):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT q.*
                FROM quizzes q
                LEFT JOIN (
                    SELECT quiz_id FROM user_points WHERE user_id = %s
                ) up ON q.id = up.quiz_id
                WHERE q.topic = %s AND q.grade = %s AND up.quiz_id IS NULL
                ORDER BY RANDOM()
                LIMIT 1
            """,
                (user_id, topic, grade),
            )
            quiz = c.fetchone()
            return quiz


def get_leaderboard():
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT u.username, SUM(up.points) as total_points,
                CAST(SUM(up.points) / 10 AS INTEGER) as total_kg
                FROM users u
                JOIN user_points up ON u.id = up.user_id
                GROUP BY u.username
                ORDER BY total_points DESC
                LIMIT 10
            """
            )
            leaderboard = c.fetchall()
            return leaderboard


def create_suggestion(request):
    question = request.form["question"]
    correct_answer = request.form["correct_answer"]
    option1 = request.form["option1"]
    option2 = request.form["option2"]
    option3 = request.form["option3"]
    option4 = request.form["option4"]
    points = request.form["points"]
    topic = request.form["topic"]
    grade = request.form["grade"]

    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                    INSERT INTO suggestions (question, correct_answer, option1, option2, option3, option4, points, topic, grade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    question,
                    correct_answer,
                    option1,
                    option2,
                    option3,
                    option4,
                    points,
                    topic,
                    grade,
                ),
            )
            conn.commit()


def execute_fetch(*args):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            return c.execute(args).fetchall()


def execute_commit(*args, **kwargs):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            if kwargs.get("many", False):
                c.executemany(args)
            else:
                c.execute(args)
            conn.commit()


def upload_questions_db(csv_input):
    with psycopg2.connect(os.environ["internal_db_url"]) as conn:
        with conn.cursor() as c:
            for idx, row in enumerate(csv_input):
                if len(row) != 9:
                    continue
                # Assumindo a ordem das colunas no CSV:
                # question, correct_answer, option1, option2, option3, option4, points, topic, grade
                execute_commit(
                    """
                    INSERT INTO quizzes (question, correct_answer, option1, option2, option3, option4, points, topic, grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    tuple(row),
                )
        conn.commit()


def create_database():
    # Verifica se o arquivo de banco de dados já existe e o remove
    # Conecta ao banco de dados (será criado um novo)
    conn = psycopg2.connect(os.environ["internal_db_url"])
    c = conn.cursor()

    # Criação da tabela de usuários com a coluna 'email'
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT,
        role TEXT DEFAULT 'user',
        register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    )
    print("Tabela 'users' criada com sucesso.")

    # Criação da tabela de quizzes
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS quizzes (
        id SERIAL PRIMARY KEY,
        question TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        topic TEXT NOT NULL,
        grade TEXT NOT NULL,  
        points INTEGER NOT NULL
    );
"""
    )
    print("Tabela 'quizzes' criada com sucesso.")

    # Criação da tabela de perguntas sugeridas
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS suggested_questions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        points INTEGER NOT NULL,
        status TEXT DEFAULT 'pendente',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    )
    print("Tabela 'suggested_questions' criada com sucesso.")

    # Criação da tabela de pontos de usuários
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS user_points (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        points INTEGER NOT NULL,
        is_correct INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    );
    """
    )
    print("Tabela 'user_points' criada com sucesso.")

    conn.commit()
    conn.close()
    print("Banco de dados criado e todas as tabelas foram configuradas com sucesso.")
