from flask import Blueprint, render_template, session
from app.utils.database import PostgresConnectionFactory, points_to_grams, points_to_meals, points_to_grains

bp = Blueprint('main', __name__)

@bp.route('/')
def landing():
    conn = PostgresConnectionFactory.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COALESCE(SUM(points), 0) FROM user_points")
    total_points = cursor.fetchone()[0] or 0
    
    # Cálculos de impacto
    total_graos = points_to_grains(total_points)      # grãos de arroz
    total_grams = points_to_grams(total_points)       # gramas de alimento
    total_meals = points_to_meals(total_points)       # refeições
    
    # Quizzes calculados com base nas refeições (números balanceados)
    total_quizzes = int(total_meals * 50)             # 50 quizzes por refeição
    
    cursor.close()
    conn.close()
    
    return render_template('main/landing.html',
                         total_users=total_users,
                         total_quizzes=total_quizzes,
                         total_graos=total_graos,
                         total_grams=total_grams,
                         total_meals=total_meals)

@bp.route('/sobre')
def about():
    return render_template('main/about.html', title='Sobre Nós')

@bp.route('/parceiros')
def partners():
    return render_template('main/partners.html', title='Nossos Parceiros')

@bp.route('/leaderboard')
def leaderboard():
    conn = PostgresConnectionFactory.get_connection()
    leaderboard = []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.username, COALESCE(SUM(up.points), 0) as total_points 
                FROM users u 
                LEFT JOIN user_points up ON u.id = up.user_id 
                WHERE u.username != 'pedroquart'
                GROUP BY u.id, u.username 
                ORDER BY total_points DESC
            """)
            
            leaderboard = [
                {
                    'username': row[0], 
                    'total_points': row[1] or 0,
                    'total_meals': points_to_meals(row[1] or 0)
                }
                for row in cursor.fetchall()
            ]
            
    except psycopg2.Error as e:
        print(f"Database connection error in leaderboard: {e}")
        conn.rollback()
        # Return empty leaderboard on error
        leaderboard = []
    
    return render_template('main/leaderboard.html', leaderboard=leaderboard)
