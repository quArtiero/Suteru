import sqlite3

def update_user_role(username):
    conn = sqlite3.connect('sutēru.db')
    c = conn.cursor()
    c.execute('UPDATE users SET role = ? WHERE username = ?', ('admin', username))
    conn.commit()
    conn.close()
    print(f"O usuário '{username}' agora é um administrador.")

if __name__ == '__main__':
    update_user_role('pedroquart')
