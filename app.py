from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from database import RaffleDatabase
import os
import logging
import uuid
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Для сессий

# Конфигурация загрузки файлов (ПОСЛЕ создания app)
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Создаем папку для загрузок, если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = RaffleDatabase()

# Конфигурация админа
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


# ========== СУЩЕСТВУЮЩИЕ МАРШРУТЫ (НЕ ТРОГАЕМ) ==========

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

# ========== НОВЫЕ ПУБЛИЧНЫЕ МАРШРУТЫ ==========

@app.route('/api/public-winners')
def get_public_winners():
    """Публичная таблица победителей (только ники и призы)"""
    winners = db.get_public_winners()
    return jsonify({
        'success': True,
        'winners': [
            {
                'nickname': w[0],
                'prize_name': w[1],
                'won_at': w[2]
            }
            for w in winners
        ]
    })

@app.route('/api/user-wins')
def get_user_wins():
    """История выигрышей конкретного пользователя"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Не указан пользователь'})
    
    wins = db.get_user_wins(user_id)
    return jsonify({
        'success': True,
        'wins': [
            {
                'name': w[0],
                'image': w[1],
                'description': w[2],
                'won_at': w[3]
            }
            for w in wins
        ]
    })

@app.route('/game')
def game():
    """Страница игры (после регистрации)"""
    return render_template('game.html')

@app.route('/logout')
def logout():
    """Выход из аккаунта"""
    # Просто перенаправляем на главную (фронтенд сам удалит localStorage)
    return redirect(url_for('index'))

# ========== АДМИН-МАРШРУТЫ (С ЗАЩИТОЙ) ==========

def admin_required(f):
    """Декоратор для проверки прав админа"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Страница входа в админ-панель"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Неверные учетные данные')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Выход из админ-панели"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_panel():
    """Главная страница админ-панели"""
    return render_template('admin_panel.html')

# ========== АДМИН-API МАРШРУТЫ ==========

@app.route('/api/admin/users')
@admin_required
def get_users_admin():
    """Список всех пользователей с контактами (только для админа)"""
    users = db.get_all_users_admin()
    return jsonify({
        'success': True,
        'users': [
            {
                'id': u[0],
                'nickname': u[1],
                'telegram': u[2],
                'site_url': u[3],
                'shadow_coins': u[4],
                'created_at': u[5],
                'last_login': u[6]
            }
            for u in users
        ]
    })

@app.route('/api/admin/prizes')
@admin_required
def get_prizes_admin():
    """Все призы (включая разыгранные) для админа"""
    prizes = db.get_all_prizes_admin()
    return jsonify({
        'success': True,
        'prizes': [
            {
                'id': p[0],
                'name': p[1],
                'image': p[2],
                'description': p[3],
                'available': bool(p[4]),
                'created_at': p[5]
            }
            for p in prizes
        ]
    })

@app.route('/api/admin/winners')
@admin_required
def get_winners_admin():
    """Полная таблица победителей с контактами (только для админа)"""
    winners = db.get_full_winners()
    return jsonify({
        'success': True,
        'winners': [
            {
                'nickname': w[0],
                'telegram': w[1],
                'site_url': w[2],
                'prize_name': w[3],
                'won_at': w[4]
            }
            for w in winners
        ]
    })

@app.route('/api/admin/add_coins', methods=['POST'])
@admin_required
def add_coins_admin():
    """Добавить теневые монеты пользователю"""
    data = request.get_json()
    nickname = data.get('nickname')
    amount = data.get('amount', 0)
    reason = data.get('reason', '')
    
    if not nickname:
        return jsonify({'success': False, 'message': 'Введите никнейм'})
    
    # ЗАЩИТА 1: Проверяем, что amount - число
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Количество монет должно быть числом'})
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Введите положительное количество монет'})
    
    # ЗАЩИТА 2: Ограничение на максимальное количество за раз (10 000)
    MAX_PER_TRANSACTION = 10000
    if amount > MAX_PER_TRANSACTION:
        return jsonify({
            'success': False, 
            'message': f'Нельзя добавить больше {MAX_PER_TRANSACTION} монет за раз'
        })
    
    user = db.get_user_by_nickname(nickname)
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    # ЗАЩИТА 3: Проверяем, что у пользователя не слишком много монет
    MAX_TOTAL = 1000000
    if user['shadow_coins'] + amount > MAX_TOTAL:
        return jsonify({
            'success': False,
            'message': f'У пользователя слишком много монет (макс. {MAX_TOTAL})'
        })
    
    db.add_shadow_coins(user['id'], amount, reason, admin_id=1)
    
    # Получаем обновленный баланс
    new_balance = db.get_user_coins(user['id'])
    
    return jsonify({
        'success': True,
        'message': f'Добавлено {amount} теневых монет пользователю {nickname}',
        'new_balance': new_balance
    })
    
@app.route('/api/admin/remove_coins', methods=['POST'])
@admin_required
def remove_coins_admin():
    """Снять теневые монеты у пользователя"""
    data = request.get_json()
    nickname = data.get('nickname')
    amount = data.get('amount', 0)
    reason = data.get('reason', '')
    
    if not nickname:
        return jsonify({'success': False, 'message': 'Введите никнейм'})
    
    # Проверяем, что amount - число
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Количество монет должно быть числом'})
    
    if amount <= 0:
        return jsonify({'success': False, 'message': 'Введите положительное количество монет для снятия'})
    
    # Ограничение на максимальное количество за раз
    MAX_PER_TRANSACTION = 10000
    if amount > MAX_PER_TRANSACTION:
        return jsonify({
            'success': False, 
            'message': f'Нельзя снять больше {MAX_PER_TRANSACTION} монет за раз'
        })
    
    user = db.get_user_by_nickname(nickname)
    if not user:
        return jsonify({'success': False, 'message': 'Пользователь не найден'})
    
    # Проверяем, хватит ли монет
    if user['shadow_coins'] < amount:
        return jsonify({
            'success': False,
            'message': f'Недостаточно монет. Текущий баланс: {user["shadow_coins"]}'
        })
    
    # Снимаем монеты (вызываем метод из database.py)
    success = db.remove_shadow_coins(user['id'], amount, reason, admin_id=1)
    
    if not success:
        return jsonify({'success': False, 'message': 'Ошибка при снятии монет'})
    
    # Получаем обновленный баланс
    new_balance = db.get_user_coins(user['id'])
    
    return jsonify({
        'success': True,
        'message': f'Снято {amount} теневых монет у пользователя {nickname}',
        'new_balance': new_balance
    })

@app.route('/api/admin/add_prize', methods=['POST'])
@admin_required
def add_prize_admin():
    """Добавить новый приз с изображением"""
    try:
        # Получаем данные из формы
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            return jsonify({'success': False, 'message': 'Введите название приза'})
        
        if len(description) > 500:
            return jsonify({'success': False, 'message': 'Описание слишком длинное (макс. 500 символов)'})
        
        # Проверяем наличие файла
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'Не выбрано изображение'})
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Не выбрано изображение'})
        
        # Проверяем расширение файла
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Неподдерживаемый формат файла'})
        
        # Генерируем безопасное имя файла
        filename = secure_filename(file.filename)
        # Добавляем уникальный префикс, чтобы избежать перезаписи
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Сохраняем файл
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        print(f"✅ Файл сохранен: {unique_filename}")
        
        # Добавляем приз в базу данных (сохраняем только имя файла)
        prize_id = db.add_prize(name, unique_filename, description)
        
        return jsonify({'success': True, 'prize_id': prize_id, 'image': unique_filename})
        
    except Exception as e:
        print(f"🔥 Ошибка при добавлении приза: {e}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

@app.route('/api/admin/transactions')
@admin_required
def get_transactions_admin():
    """История транзакций"""
    user_id = request.args.get('user_id')
    transactions = db.get_transactions(int(user_id) if user_id else None)
    return jsonify({
        'success': True,
        'transactions': [
            {
                'id': t[0],
                'user_id': t[1],
                'amount': t[2],
                'reason': t[3],
                'admin_id': t[4],
                'created_at': t[5]
            }
            for t in transactions
        ]
    })

@app.route('/api/admin/stats')
@admin_required
def get_stats_admin():
    """Статистика для админ-панели"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prizes WHERE available = 1")
        available_prizes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM winners")
        total_winners = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(shadow_coins) FROM users")
        total_coins = cursor.fetchone()[0] or 0
        
        # Топ-10 по монетам
        cursor.execute('''
            SELECT nickname, shadow_coins FROM users 
            ORDER BY shadow_coins DESC LIMIT 10
        ''')
        top_users = [{'nickname': u[0], 'coins': u[1]} for u in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'available_prizes': available_prizes,
                'total_winners': total_winners,
                'total_coins': total_coins,
                'top_users': top_users
            }
        })
        
@app.route('/api/register_with_password', methods=['POST'])
def register_with_password():
    """Регистрация с паролем"""
    data = request.get_json()
    
    nickname = data.get('nickname')
    password = data.get('password')
    telegram = data.get('telegram')
    site_url = data.get('site_url')
    
    if not nickname:
        return jsonify({'success': False, 'message': 'Введите никнейм'})
    
    if not password or len(password) < 4:
        return jsonify({'success': False, 'message': 'Пароль должен быть не менее 4 символов'})
    
    if not telegram and not site_url:
        return jsonify({'success': False, 'message': 'Заполните Telegram или ссылку'})
    
    result = db.register_with_password(nickname, password, telegram, site_url)
    return jsonify(result)

@app.route('/api/login_with_password', methods=['POST'])
def login_with_password():
    """Вход с паролем"""
    data = request.get_json()
    nickname = data.get('nickname')
    password = data.get('password')
    
    if not nickname or not password:
        return jsonify({'success': False, 'message': 'Введите никнейм и пароль'})
    
    result = db.login_with_password(nickname, password)
    return jsonify(result) 

@app.route('/api/user-data')
def get_user_data():
    """Получить актуальные данные пользователя"""
    user_id = request.args.get('user_id')
    print(f"📊 Запрос данных пользователя: user_id={user_id}")
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Не указан пользователь'})
    
    try:
        user = db.get_user_by_id(user_id)
        if user:
            print(f"✅ Пользователь найден: {user}")
            return jsonify({'success': True, 'user': user})
        else:
            print(f"❌ Пользователь не найден: {user_id}")
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
    except Exception as e:
        print(f"🔥 Ошибка: {e}")
        return jsonify({'success': False, 'message': str(e)})   
    

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
