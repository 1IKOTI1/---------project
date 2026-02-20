import sqlite3
import random

class RaffleDatabase:
    def __init__(self, db_name="raffle.db"):
        self.db_name = db_name
        self.init_database()
        
    def get_connection(self):
        return sqlite3.connect(self.db_name)
        
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prizes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image TEXT NOT NULL,
                    description TEXT,
                    available BOOLEAN DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT UNIQUE NOT NULL,
                    prize_id INTEGER,
                    won_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prize_id) REFERENCES prizes (id)
                )
            ''')
            
            cursor.execute("SELECT COUNT(*) FROM prizes")
            count = cursor.fetchone()[0]
            
            if count == 0:
                default_prizes = [
                    ('Футболка', 'card.png.webp'),
                    ('Кружка', 'mug.png'),
                    ('Стикерпак', 'stickers.png'),
                    ('Скидка 10%', 'discount.png'),
                    ('Супер-приз', 'gift.png')
                ]
                cursor.executemany(
                    "INSERT INTO prizes (name, image) VALUES (?, ?)",
                    default_prizes
                )
                conn.commit()
                print("✅ Начальные призы добавлены")
                    
    def get_available_prizes(self):
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
                     
    def has_user_played(self, nickname):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT prize_id FROM winners WHERE nickname = ?",
                (nickname,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
                     
    def draw_prize(self, nickname):
        print(f"🎲 draw_prize вызван с ником: '{nickname}'")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Проверяем, играл ли пользователь уже
                cursor.execute("SELECT prize_id FROM winners WHERE nickname = ?", (nickname,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("SELECT name FROM prizes WHERE id = ?", (existing[0],))
                    prize_name = cursor.fetchone()[0]
                    print(f"❌ Пользователь {nickname} уже играл, выиграл: {prize_name}")
                    return {
                        'success': False,
                        'message': f'Ты уже играл! Твой приз: {prize_name}'
                    }
                
                # 2. Получаем доступные призы
                cursor.execute("""
                    SELECT id, name, image
                    FROM prizes
                    WHERE available = 1
                """)
                available_prizes = cursor.fetchall()
                print(f"📦 Доступно призов: {len(available_prizes)}")
                
                if not available_prizes:
                    print("❌ Призы закончились")
                    return {'success': False, 'message': 'Призы закончились'}
                
                # 3. Выбираем случайный приз
                prize = random.choice(available_prizes)
                print(f"🎁 Выбран приз: {prize[1]}")
                
                # 4. Помечаем приз как недоступный
                cursor.execute(
                    "UPDATE prizes SET available = 0 WHERE id = ?",
                    (prize[0],)
                )
                
                # 5. Записываем победителя
                cursor.execute(
                    "INSERT INTO winners (nickname, prize_id) VALUES (?, ?)",
                    (nickname, prize[0])
                )
                
                conn.commit()
                print(f"✅ Победитель {nickname} записан, приз {prize[1]}")
                
                return {
                    'success': True,
                    'message': f'Поздравляем! Ты выиграл: {prize[1]}',
                    'prize': {
                        'id': prize[0],
                        'name': prize[1],
                        'image': prize[2]
                    }
                }
                
        except sqlite3.IntegrityError as e:
            print(f"🔥 Ошибка целостности БД: {e}")
            return {'success': False, 'message': 'Ошибка базы данных'}
        except Exception as e:
            print(f"🔥 Неожиданная ошибка: {e}")
            return {'success': False, 'message': 'Внутренняя ошибка сервера'}
                     
    def get_all_winners(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT w.nickname, p.name, w.won_at
                FROM winners w
                JOIN prizes p ON w.prize_id = p.id
                ORDER BY w.won_at DESC
            ''')  
            return cursor.fetchall()
                         
                               
                   
        
           