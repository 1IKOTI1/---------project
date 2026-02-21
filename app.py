from flask import Flask, render_template, jsonify, request, session
from database import RaffleDatabase
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Для сессий
db = RaffleDatabase()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация или вход пользователя"""
    data = request.get_json()
    
    nickname = data.get('nickname')
    telegram = data.get('telegram')
    site_url = data.get('site_url')
    
    if not nickname:
        return jsonify({'success': False, 'message': 'Введите никнейм'})
    
    if not telegram and not site_url:
        return jsonify({'success': False, 'message': 'Заполните Telegram или ссылку'})
    
    result = db.register_or_login(nickname, telegram, site_url)
    return jsonify(result)

@app.route('/api/prizes')
def get_prizes():
    """Список доступных призов"""
    prizes = db.get_available_prizes()
    return jsonify({'success': True, 'prizes': prizes})

@app.route('/api/draw', methods=['POST'])
def draw():
    """Розыгрыш приза"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    result = db.draw_prize(user_id)
    return jsonify(result)

@app.route('/api/winners')
def get_winners():
    """Таблица победителей"""
    winners = db.get_all_winners()
    return jsonify({
        'success': True,
        'winners': [
            {
                'nickname': w[0],
                'telegram': w[1],
                'site_url': w[2],
                'prize_name': w[3],
                'prize_image': w[4],
                'spent_coins': w[5],
                'won_at': w[6]
            }
            for w in winners
        ]
    })

# ========== АДМИН-МАРШРУТЫ (защитите паролем в реальном проекте) ==========

@app.route('/api/admin/add_coins', methods=['POST'])
def add_coins():
    """Админ: добавить монеты пользователю"""
    data = request.get_json()
    nickname = data.get('nickname')
    amount = data.get('amount', 0)
    reason = data.get('reason', '')
    
    user = db.get_user_by_nickname(nickname)
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    db.add_coins(user['id'], amount, reason, admin_id=1)  # admin_id=1 для примера
    
    # Получаем обновленный баланс
    new_balance = db.get_user_coins(user['id'])
    
    return jsonify({
        'success': True,
        'message': f'Добавлено {amount} монет пользователю {nickname}',
        'new_balance': new_balance
    })

@app.route('/api/admin/add_prize', methods=['POST'])
def add_prize():
    """Админ: добавить новый приз"""
    data = request.get_json()
    prize_id = db.add_prize(
        data.get('name'),
        data.get('image'),
        data.get('description'),
        data.get('price', 1)
    )
    return jsonify({'success': True, 'prize_id': prize_id})

@app.route('/api/admin/users')
def get_users():
    """Админ: список всех пользователей"""
    users = db.get_all_users()
    return jsonify({
        'success': True,
        'users': [
            {
                'id': u[0],
                'nickname': u[1],
                'telegram': u[2],
                'site_url': u[3],
                'coins': u[4],
                'created_at': u[5],
                'last_login': u[6]
            }
            for u in users
        ]
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)