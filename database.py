import sqlite3
import os

def create_database():
    # Verifica se o arquivo de banco de dados já existe e o remove
    if os.path.exists('sutēru.db'):
        os.remove('sutēru.db')
        print("Banco de dados existente removido.")
    else:
        print("Nenhum banco de dados existente encontrado. Criando um novo.")

    # Conecta ao banco de dados (será criado um novo)
    conn = sqlite3.connect('sutēru.db')
    c = conn.cursor()

    # Criação da tabela de usuários com a coluna 'email'
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT,
        role TEXT DEFAULT 'user',
        register_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("Tabela 'users' criada com sucesso.")

    # Criação da tabela de quizzes
    c.execute('''
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    topic TEXT NOT NULL,
    grade TEXT NOT NULL,  
    points INTEGER NOT NULL
)
''')
    print("Tabela 'quizzes' criada com sucesso.")

    # Criação da tabela de perguntas sugeridas
    c.execute('''
    CREATE TABLE suggested_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    print("Tabela 'suggested_questions' criada com sucesso.")

    # Criação da tabela de pontos de usuários
    c.execute('''
    CREATE TABLE user_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        points INTEGER NOT NULL,
        is_correct INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
    )
    ''')
    print("Tabela 'user_points' criada com sucesso.")

    conn.commit()
    conn.close()
    print("Banco de dados criado e todas as tabelas foram configuradas com sucesso.")

if __name__ == "__main__":
    create_database()
