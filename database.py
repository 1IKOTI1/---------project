import sqlite3
import random
import json
import hashlib
import secrets

class RaffleDatabase:
    
    def _hash_password(self, password):
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def _verify_password(self, password, hashed):
        if not hashed or ':' not in hashed:
            return False
        salt, hash_value = hashed.split(':')
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    
    def register_with_password(self, nickname, password, telegram=None, site_url=None):
    
        print(f"📝 Регистрация с паролем: {nickname}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем уникальность
            if self.check_nickname_exists(nickname):
                return {'success': False, 'message': 'Никнейм уже занят'}
            
            if telegram and self.check_telegram_exists(telegram):
                return {'success': False, 'message': 'Telegram уже зарегистрирован'}
            
            if site_url and self.check_site_url_exists(site_url):
                return {'success': False, 'message': 'Ссылка уже зарегистрирована'}
            
            # Хешируем пароль
            hashed_password = self._hash_password(password)
            
            try:
                cursor.execute('''
                    INSERT INTO users (nickname, password, telegram, site_url, shadow_coins)
                    VALUES (?, ?, ?, ?, 0)
                ''', (nickname, hashed_password, telegram, site_url))
                conn.commit()
                
                cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
                user = cursor.fetchone()
                
                return {
                    'success': True,
                    'user': {
                        'id': user[0],
                        'nickname': user[1],
                        'telegram': user[3],
                        'site_url': user[4],
                        'shadow_coins': user[5]
                    }
                }
            except Exception as e:
                return {'success': False, 'message': f'Ошибка регистрации: {str(e)}'}
            
    def login_with_password(self, nickname, password):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'message': 'Пользователь не найден'}
            
            # Проверяем пароль (user[2] - это поле password)
            if not self._verify_password(password, user[2]):
                return {'success': False, 'message': 'Неверный пароль'}
            
            # Обновляем время последнего входа
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE nickname = ?",
                (nickname,)
            )
            conn.commit()
            
            return {
                'success': True,
                'user': {
                    'id': user[0],
                    'nickname': user[1],
                    'telegram': user[3],
                    'site_url': user[4],
                    'shadow_coins': user[5]
                }
            } 
            
    def check_site_url_exists(self, site_url):
        if not site_url:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE site_url = ?", (site_url,))
            return cursor.fetchone() is not None          
    def check_telegram_exists(self, telegram):
        if not telegram:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE telegram = ?", (telegram,))
            return cursor.fetchone() is not None
    def check_nickname_exists(self, nickname):
    
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE nickname = ?", (nickname,))
            return cursor.fetchone() is not None               

    def __init__(self, db_name="raffle.db"):
        self.db_name = db_name
        self.init_database()
        
    def get_connection(self):
        return sqlite3.connect(self.db_name)
        
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,  
                    telegram TEXT UNIQUE,
                    site_url TEXT UNIQUE,
                    shadow_coins INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица призов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prizes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image TEXT NOT NULL,
                    description TEXT,
                    available BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица победителей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prize_id INTEGER NOT NULL,
                    won_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (prize_id) REFERENCES prizes (id)
                )
            ''')
            
            # Таблица транзакций теневых монет
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS coin_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    reason TEXT,
                    admin_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Проверяем, есть ли призы
            cursor.execute("SELECT COUNT(*) FROM prizes")
            count = cursor.fetchone()[0]
            
            if count == 0:
                default_prizes = [
                    ('Теневая карта #1', 'card1.png', 'Редкая теневая карта'),
                    ('Теневая карта #2', 'card2.png', 'Очень редкая теневая карта'),
                    ('Теневая карта #3', 'card3.png', 'Легендарная теневая карта'),
                    ('Теневая карта #4', 'card4.png', 'Мифическая теневая карта'),
                    ('Теневая карта #5', 'card5.png', 'Древняя теневая карта')
                ]
                cursor.executemany(
                    "INSERT INTO prizes (name, image, description) VALUES (?, ?, ?)",
                    default_prizes
                )
                conn.commit()
                print("✅ Начальные призы добавлены")
    
    # ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========
    
    def register_or_login(self, nickname, telegram=None, site_url=None):
        """Регистрация или вход пользователя (без стартовых монет)"""
        print(f"📝 Регистрация/вход: {nickname}, tg: {telegram}, url: {site_url}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
            user = cursor.fetchone()
            
            if user:
                # Обновляем время последнего входа
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE nickname = ?",
                    (nickname,)
                )
                conn.commit()
                
                # Получаем обновленные данные
                cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
                user = cursor.fetchone()
                
                return {
                    'success': True,
                    'new_user': False,
                    'user': {
                        'id': user[0],
                        'nickname': user[1],
                        'telegram': user[3],
                        'site_url': user[4],
                        'shadow_coins': user[5]
                    }
                }
            else:
                # Создаем нового пользователя (без монет!)
                try:
                    cursor.execute('''
                        INSERT INTO users (nickname, telegram, site_url, shadow_coins)
                        VALUES (?, ?, ?, 0)
                    ''', (nickname, telegram, site_url))
                    conn.commit()
                    
                    cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
                    user = cursor.fetchone()
                    
                    return {
                        'success': True,
                        'new_user': True,
                        'user': {
                            'id': user[0],
                            'nickname': user[1],
                            'telegram': user[3],
                            'site_url': user[4],
                            'shadow_coins': user[5]
                        }
                    }
                except sqlite3.IntegrityError as e:
                    return {'success': False, 'message': 'Никнейм уже занят'}
    
    def get_user_by_nickname(self, nickname):
        """Получить пользователя по нику"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'nickname': user[1],
                    'telegram': user[3],
                    'site_url': user[4],
                    'shadow_coins': user[5]
                }
            return None
    
    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'nickname': user[1],
                    'telegram': user[2],
                    'site_url': user[3],
                    'shadow_coins': user[4]
                }
            return None
    
    # ========== РАБОТА С ТЕНЕВЫМИ МОНЕТАМИ ==========
    
    def get_user_coins(self, user_id):
        """Получить баланс теневых монет"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT shadow_coins FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def add_shadow_coins(self, user_id, amount, reason="", admin_id=None):
        """Добавить теневые монеты пользователю (только для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Обновляем баланс
            cursor.execute(
                "UPDATE users SET shadow_coins = shadow_coins + ? WHERE id = ?",
                (amount, user_id)
            )
            
            # Записываем транзакцию
            cursor.execute('''
                INSERT INTO coin_transactions (user_id, amount, reason, admin_id)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, reason, admin_id))
            
            conn.commit()
            return True
    
    def spend_shadow_coin(self, user_id):
        """Потратить 1 теневую монету на прокрутку"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем баланс
            cursor.execute("SELECT shadow_coins FROM users WHERE id = ?", (user_id,))
            current = cursor.fetchone()[0]
            
            if current < 1:
                return False
            
            # Списываем монету
            cursor.execute(
                "UPDATE users SET shadow_coins = shadow_coins - 1 WHERE id = ?",
                (user_id,)
            )
            
            # Записываем транзакцию
            cursor.execute('''
                INSERT INTO coin_transactions (user_id, amount, reason)
                VALUES (?, ?, ?)
            ''', (user_id, -1, 'Прокрутка рулетки'))
            
            conn.commit()
            return True
    
    # ========== РОЗЫГРЫШ ==========
    
    def get_available_prizes(self):
        """Получить доступные призы"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, image, description FROM prizes WHERE available = 1"
            )      
            prizes = cursor.fetchall()
            return [
                {
                    'id': p[0],
                    'name': p[1],
                    'image': p[2],
                    'description': p[3] if p[3] else ''
                }
                for p in prizes
            ]
    
    def draw_prize(self, user_id):
        """Розыгрыш приза (1 попытка = 1 монета)"""
        print(f"🎲 draw_prize для user_id: {user_id}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем баланс
                cursor.execute("SELECT shadow_coins FROM users WHERE id = ?", (user_id,))
                user_coins = cursor.fetchone()[0]
                
                if user_coins < 1:
                    return {'success': False, 'message': 'Недостаточно теневых монет'}
                
                # Получаем доступные призы
                cursor.execute("SELECT id, name, image FROM prizes WHERE available = 1")
                available_prizes = cursor.fetchall()
                
                if not available_prizes:
                    return {'success': False, 'message': 'Призы закончились'}
                
                # Списываем монету
                cursor.execute(
                    "UPDATE users SET shadow_coins = shadow_coins - 1 WHERE id = ?",
                    (user_id,)
                )
                
                # Выбираем случайный приз
                prize = random.choice(available_prizes)
                
                # Помечаем приз как недоступный
                cursor.execute("UPDATE prizes SET available = 0 WHERE id = ?", (prize[0],))
                
                # Записываем победителя
                cursor.execute('''
                    INSERT INTO winners (user_id, prize_id) 
                    VALUES (?, ?)
                ''', (user_id, prize[0]))
                
                # Записываем транзакцию
                cursor.execute('''
                    INSERT INTO coin_transactions (user_id, amount, reason)
                    VALUES (?, ?, ?)
                ''', (user_id, -1, f'Выигрыш: {prize[1]}'))
                
                conn.commit()
                
                # Получаем обновленный баланс
                cursor.execute("SELECT shadow_coins FROM users WHERE id = ?", (user_id,))
                new_balance = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'message': f'Поздравляем! Ты выиграл: {prize[1]}',
                    'prize': {
                        'id': prize[0],
                        'name': prize[1],
                        'image': prize[2]
                    },
                    'new_balance': new_balance
                }
                
        except Exception as e:
            print(f"🔥 Ошибка в draw_prize: {e}")
            return {'success': False, 'message': 'Ошибка при розыгрыше'}
    
    # ========== ИСТОРИЯ ВЫИГРЫШЕЙ ==========
    
    def get_user_wins(self, user_id):
        """Получить историю выигрышей конкретного пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    p.name as prize_name,
                    p.image as prize_image,
                    p.description,
                    w.won_at
                FROM winners w
                JOIN prizes p ON w.prize_id = p.id
                WHERE w.user_id = ?
                ORDER BY w.won_at DESC
            ''', (user_id,))
            return cursor.fetchall()
    
    # ========== ТАБЛИЦА ПОБЕДИТЕЛЕЙ (ПУБЛИЧНАЯ) ==========
    
    def get_public_winners(self):
        """Публичная таблица победителей (только ники и призы)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.nickname,
                    p.name as prize_name,
                    w.won_at
                FROM winners w
                JOIN users u ON w.user_id = u.id
                JOIN prizes p ON w.prize_id = p.id
                ORDER BY w.won_at DESC
                LIMIT 50
            ''')  
            return cursor.fetchall()
    
    # ========== ПОЛНАЯ ТАБЛИЦА ПОБЕДИТЕЛЕЙ (ДЛЯ АДМИНА) ==========
    
    def get_full_winners(self):
        """Полная таблица победителей с контактами (только для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.nickname,
                    u.telegram,
                    u.site_url,
                    p.name as prize_name,
                    w.won_at
                FROM winners w
                JOIN users u ON w.user_id = u.id
                JOIN prizes p ON w.prize_id = p.id
                ORDER BY w.won_at DESC
            ''')  
            return cursor.fetchall()
    
    # ========== АДМИН-ФУНКЦИИ ==========
    
    def add_prize(self, name, image, description):
        """Добавить новый приз (для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prizes (name, image, description, available)
                VALUES (?, ?, ?, 1)
            ''', (name, image, description))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_users_admin(self):
        """Получить всех пользователей с контактами (для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nickname, telegram, site_url, shadow_coins, created_at, last_login
                FROM users
                ORDER BY shadow_coins DESC
            ''')
            return cursor.fetchall()
    
    def get_all_prizes_admin(self):
        """Все призы (включая разыгранные) для админа"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, image, description, available, created_at
                FROM prizes
                ORDER BY created_at DESC
            ''')
            return cursor.fetchall()
    
    def get_transactions(self, user_id=None):
        """Получить транзакции (для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    SELECT * FROM coin_transactions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT * FROM coin_transactions 
                    ORDER BY created_at DESC
                    LIMIT 100
                ''')
            return cursor.fetchall()
                         
                               
                   
        
           