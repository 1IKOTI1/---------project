import sqlite3
import random
import json

class RaffleDatabase:
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
                    telegram TEXT UNIQUE,
                    site_url TEXT UNIQUE,
                    coins INTEGER DEFAULT 10,
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
                    price INTEGER DEFAULT 1,
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
                    spent_coins INTEGER DEFAULT 1,
                    won_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (prize_id) REFERENCES prizes (id)
                )
            ''')
            
            # Таблица транзакций валюты (для админа)
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
                    ('Карточка 1', 'card1.png', 'Редкая карточка #1', 1),
                    ('Карточка 2', 'card2.png', 'Редкая карточка #2', 2),
                    ('Карточка 3', 'card3.png', 'Редкая карточка #3', 3),
                    ('Карточка 4', 'card4.png', 'Редкая карточка #4', 4),
                    ('Карточка 5', 'card5.png', 'Редкая карточка #5', 5)
                ]
                cursor.executemany(
                    "INSERT INTO prizes (name, image, description, price) VALUES (?, ?, ?, ?)",
                    default_prizes
                )
                conn.commit()
                print("✅ Начальные призы добавлены")
    
    # ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========
    
    def register_or_login(self, nickname, telegram=None, site_url=None):
        """Регистрация или вход пользователя"""
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
                        'telegram': user[2],
                        'site_url': user[3],
                        'coins': user[4]
                    }
                }
            else:
                # Создаем нового пользователя
                try:
                    cursor.execute('''
                        INSERT INTO users (nickname, telegram, site_url, coins)
                        VALUES (?, ?, ?, 10)
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
                            'telegram': user[2],
                            'site_url': user[3],
                            'coins': user[4]
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
                    'telegram': user[2],
                    'site_url': user[3],
                    'coins': user[4]
                }
            return None
    
    # ========== РАБОТА С ВАЛЮТОЙ ==========
    
    def get_user_coins(self, user_id):
        """Получить баланс пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def add_coins(self, user_id, amount, reason="", admin_id=None):
        """Добавить монеты пользователю (для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Обновляем баланс
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (amount, user_id)
            )
            
            # Записываем транзакцию
            cursor.execute('''
                INSERT INTO coin_transactions (user_id, amount, reason, admin_id)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, reason, admin_id))
            
            conn.commit()
            return True
    
    def spend_coins(self, user_id, amount):
        """Потратить монеты (при розыгрыше)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем баланс
            cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
            current = cursor.fetchone()[0]
            
            if current < amount:
                return False
            
            # Списываем монеты
            cursor.execute(
                "UPDATE users SET coins = coins - ? WHERE id = ?",
                (amount, user_id)
            )
            
            # Записываем транзакцию
            cursor.execute('''
                INSERT INTO coin_transactions (user_id, amount, reason)
                VALUES (?, ?, ?)
            ''', (user_id, -amount, 'Розыгрыш приза'))
            
            conn.commit()
            return True
    
    # ========== РАБОТА С ПРИЗАМИ ==========
    
    def get_available_prizes(self):
        """Получить доступные призы"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, image, description, price FROM prizes WHERE available = 1"
            )      
            prizes = cursor.fetchall()
            return [
                {
                    'id': p[0],
                    'name': p[1],
                    'image': p[2],
                    'description': p[3] if p[3] else '',
                    'price': p[4]
                }
                for p in prizes
            ]
    
    def draw_prize(self, user_id):
        """Розыгрыш приза для пользователя"""
        print(f"🎲 draw_prize для user_id: {user_id}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем доступные призы
                cursor.execute("SELECT id, name, image, price FROM prizes WHERE available = 1")
                available_prizes = cursor.fetchall()
                
                if not available_prizes:
                    return {'success': False, 'message': 'Призы закончились'}
                
                # Проверяем баланс пользователя
                cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
                user_coins = cursor.fetchone()[0]
                
                # Выбираем случайный приз
                prize = random.choice(available_prizes)
                
                if user_coins < prize[3]:
                    return {'success': False, 'message': f'Недостаточно монет. Нужно: {prize[3]}'}
                
                # Списываем монеты
                cursor.execute(
                    "UPDATE users SET coins = coins - ? WHERE id = ?",
                    (prize[3], user_id)
                )
                
                # Помечаем приз как недоступный
                cursor.execute("UPDATE prizes SET available = 0 WHERE id = ?", (prize[0],))
                
                # Записываем победителя
                cursor.execute('''
                    INSERT INTO winners (user_id, prize_id, spent_coins) 
                    VALUES (?, ?, ?)
                ''', (user_id, prize[0], prize[3]))
                
                conn.commit()
                
                # Получаем обновленный баланс
                cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
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
    
    # ========== ТАБЛИЦА ПОБЕДИТЕЛЕЙ ==========
    
    def get_all_winners(self):
        """Полная таблица победителей с их контактами"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.nickname,
                    u.telegram,
                    u.site_url,
                    p.name as prize_name,
                    p.image as prize_image,
                    w.spent_coins,
                    w.won_at
                FROM winners w
                JOIN users u ON w.user_id = u.id
                JOIN prizes p ON w.prize_id = p.id
                ORDER BY w.won_at DESC
            ''')  
            return cursor.fetchall()
    
    # ========== АДМИН-ФУНКЦИИ ==========
    
    def add_prize(self, name, image, description, price):
        """Добавить новый приз (для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prizes (name, image, description, price, available)
                VALUES (?, ?, ?, ?, 1)
            ''', (name, image, description, price))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_users(self):
        """Получить всех пользователей (для админа)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nickname, telegram, site_url, coins, created_at, last_login
                FROM users
                ORDER BY coins DESC
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
                         
                               
                   
        
           