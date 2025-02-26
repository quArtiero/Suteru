import psycopg2
import os
from flask import session, flash
from werkzeug.security import generate_password_hash

POINTS_TO_GRAMS = 1  # Agora deve ser simplesmente 1 ponto = 1 grão


class PostgresConnectionFactory:
    _connection = None  # Stores a single connection instance

    @staticmethod
    def get_connection():
        """Returns an existing connection or creates a new one if needed."""
        if (
            PostgresConnectionFactory._connection is None
            or PostgresConnectionFactory._connection.closed
        ):
            return PostgresConnectionFactory._create_new_connection()

        # Check if the connection is still alive
        try:
            with PostgresConnectionFactory._connection.cursor() as cursor:
                cursor.execute("SELECT 1;")  # Test query
        except psycopg2.Error:
            print("Connection lost, reconnecting...")
            return PostgresConnectionFactory._create_new_connection()

        return PostgresConnectionFactory._connection

    @staticmethod
    def _create_new_connection():
        """Creates a new database connection."""
        try:
            PostgresConnectionFactory._connection = psycopg2.connect(
                os.environ["internal_db_url"]
            )
            print("New database connection established.")
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            PostgresConnectionFactory._connection = (
                None  # Prevent usage of an invalid connection
            )
        return PostgresConnectionFactory._connection


def get_topics():
    conn = PostgresConnectionFactory.get_connection()
    try:
        c = conn.cursor()
        with conn.cursor() as c:
            c.execute("SELECT DISTINCT topic FROM quizzes")
            topics = [row[0] for row in c.fetchall()]
        return topics
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def get_grades_for_topic(topic):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT DISTINCT grade FROM quizzes WHERE topic = %s", (topic,))
            grades = [row[0] for row in c.fetchall()]
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()
        return None

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
        conn = PostgresConnectionFactory.get_connection()
        try:
            with conn.cursor() as c:
                c = conn.cursor()
                c.execute("SELECT role FROM users WHERE id = %s", (session["user_id"],))
                result = c.fetchone()

                role = result[0] if result else None
                return role
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            conn.rollback()
    return None


def get_user(username, email=None):
    conn = conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            if email is not None:
                c.execute(
                    "SELECT * FROM users WHERE username = %s OR email = %s",
                    (username, email),
                )
            else:
                c.execute("SELECT * FROM users WHERE username = %s", (username,))
            return c.fetchone()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def get_all_user_points():
    db_error = False
    data = {"total_points": 0, "total_graos": 0}
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT SUM(points) FROM user_points")
            data["total_points"] = c.fetchone()[0] or 0
            data["total_graos"] = data["total_points"]  # Relação direta 1:1
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()
        db_error = True

    return db_error, data


def get_user_points(user_id):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute(
                "SELECT SUM(points) FROM user_points " "WHERE user_id = %s",
                (user_id,),
            )
            total_points = c.fetchone()[0] or 0
            food_donation = total_points  # Relação direta 1:1
            return total_points, food_donation
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()
        return 0, 0


def update_user_role(username, role):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
            conn.commit()
            print(f"O usuário '{username}' agora é um administrador.")
            return True
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()
        return False


def delete_selected_questions_db(selected_questions):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            placeholders = ",".join("%s" for _ in selected_questions)
            query = f"DELETE FROM quizzes WHERE id IN ({placeholders})"
            c.execute(query, selected_questions)
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def create_new_user(username, email, password):
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

    # Role is always set as user, to avoid someone creating an admin
    # In order to set a user as admin, an admin that was created when the site is created
    # should change the role manually of said user, preferably using a page dedicated to
    # admins
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO users (username, email, password, role) "
                "VALUES (%s, %s, %s, %s)",
                (username, email, hashed_password, "user"),
            )
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def add_quiz_db(request):
    question = request.form["question"]
    correct_answer = request.form["correct_answer"]
    option1 = request.form["option1"]
    option2 = request.form["option2"]
    option3 = request.form["option3"]
    option4 = request.form["option4"]
    try:
        points = int(request.form["points"])
    except KeyError:
        # Handle missing points field - could set default or raise custom error
        points = 0  # or whatever default value makes sense
    topic = request.form["topic"]
    if topic == "novo_tema":
        topic = request.form["new_topic"]
    grade = request.form["grade"]

    conn = PostgresConnectionFactory.get_connection()
    try:
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
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def get_specific_quiz(quiz_id, user_id, answer):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            # Buscar o quiz pelo ID
            c.execute("SELECT * FROM quizzes WHERE id = %s", (quiz_id,))
            quiz = c.fetchone()

            # Se não encontrou o quiz, retorna None e exibe erro
            if quiz is None:
                print(f"Erro: Quiz com ID {quiz_id} não encontrado!")
                return None, None  # Evita acessar índices de None

            is_correct = 1 if (answer == quiz[2]) else 0
            points = quiz[9] if is_correct else 0

            # Inserir pontos no banco
            c.execute(
                "INSERT INTO user_points "
                "(user_id, quiz_id, points, is_correct) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, quiz_id, points, is_correct),
            )
            conn.commit()
            return is_correct, quiz
    except psycopg2.Error as e:
        print(f"Erro de conexão com o banco: {e}")
        conn.rollback()
        return None, None  # Retorna valores padrão para evitar erro


def get_random_quiz(user_id, topic, grade):
    conn = PostgresConnectionFactory.get_connection()
    try:
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
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()

def get_random_quiz_admin(topic, grade):
    """Retorna uma questão aleatória de um determinado tópico e série para admins."""
    conn = PostgresConnectionFactory.get_connection()
    c = conn.cursor()
    
    c.execute(
        "SELECT * FROM quizzes WHERE topic = %s AND grade = %s ORDER BY RANDOM() LIMIT 1",
        (topic, grade),
    )
    
    return c.fetchone()  # Retorna qualquer pergunta, sem filtro de usuário


def get_leaderboard():
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute(
                """
                SELECT u.username, SUM(up.points) as total_points,
                CAST(SUM(up.points) * 1.0 / 1000 AS DECIMAL(10,2)) as total_kg
                FROM users u
                JOIN user_points up ON u.id = up.user_id
                GROUP BY u.username
                ORDER BY total_points DESC
                LIMIT 10
            """
            )
            leaderboard = c.fetchall()
            return leaderboard
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


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

    conn = PostgresConnectionFactory.get_connection()
    try:
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
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def execute_fetch(*args):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            c.execute(*args)
            try:
                tmp = c.fetchall()
            except psycopg2.ProgrammingError:
                tmp = []
            return tmp
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def execute_commit(*args, **kwargs):
    conn = PostgresConnectionFactory.get_connection()
    try:
        with conn.cursor() as c:
            if kwargs.get("many", False):
                c.executemany(*args)
            else:
                c.execute(*args)
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def upload_questions_db(csv_input):
    conn = PostgresConnectionFactory.get_connection()
    try:
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
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        conn.rollback()


def create_database():
    # Verifica se o arquivo de banco de dados já existe e o remove
    # Conecta ao banco de dados (será criado um novo)
    conn = PostgresConnectionFactory.get_connection()
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
    print("Banco de dados criado e todas as tabelas foram configuradas com sucesso.")
