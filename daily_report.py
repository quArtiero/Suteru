from app import app, mail
from flask_mail import Message
import sqlite3

with app.app_context():
    conn = sqlite3.connect('sutēru.db')
    c = conn.cursor()
    c.execute('SELECT email FROM users')
    emails = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT SUM(points) FROM user_points WHERE DATE(timestamp) = DATE("now")')
    total_points_today = c.fetchone()[0] or 0
    total_kg_today = total_points_today // 10
    conn.close()

    for email in emails:
        msg = Message('Relatório Diário - Šutēru',
                      sender='seu_email@dominio.com',
                      recipients=[email])
        msg.body = f'Total de quilos doados hoje: {total_kg_today} kg'
        mail.send(msg)
