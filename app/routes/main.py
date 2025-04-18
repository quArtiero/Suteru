from flask import Blueprint, render_template, session
from app.utils.database import PostgresConnectionFactory, POINTS_TO_GRAMS

bp = Blueprint('main', __name__)

@bp.route('/')
def landing():
    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    total_quizzes = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COALESCE(SUM(points), 0) FROM user_points")
    total_points = cursor.fetchone()[0] or 0
    total_graos = total_points * POINTS_TO_GRAMS  # 1 ponto = 2 grãos
    
    cursor.close()
    conn.close()
    
    return render_template('main/landing.html',
                         total_users=total_users,
                         total_quizzes=total_quizzes,
                         total_graos=total_graos)

@bp.route('/sobre')
def about():
    return render_template('main/about.html', title='Sobre Nós')

@bp.route('/leaderboard')
def leaderboard():
    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.username, COALESCE(SUM(up.points), 0) as total_points 
        FROM users u 
        LEFT JOIN user_points up ON u.id = up.user_id 
        GROUP BY u.id, u.username 
        ORDER BY total_points DESC
    """)
    
    leaderboard = [
        {'username': row[0], 'total_points': row[1] or 0}
        for row in cursor.fetchall()
    ]
    
    cursor.close()
    conn.close()
    
    return render_template('main/leaderboard.html', leaderboard=leaderboard)
