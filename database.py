import sqlite3
import random  # Добавим для случайного выбора

class RaffleDatabase:
    def __init__(self, db_name="raffle.db"):
        self.db_name = db_name
        self.init_database()
        
    def get_connection(self):
        return sqlite3.connect(self.db_name)
        
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Создание таблицы призов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prizes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image TEXT NOT NULL,
                    description TEXT,
                    available BOOLEAN DEFAULT 1
                )
            ''')
            
            # Создание таблицы победителей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT UNIQUE NOT NULL,
                    prize_id INTEGER,
                    won_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prize_id) REFERENCES prizes (id)
                )
            ''')
            
            # Проверяем, есть ли призы
            cursor.execute("SELECT COUNT(*) FROM prizes")
            count = cursor.fetchone()[0]
            
            # Если призов нет - добавляем
            if count == 0:
                default_prizes = [
                    ('сard', 'card.png.webp'),
                    ('сard', 'tshirt.png',),
                    ('сard', 'tshirt.png',),
                    ('card', 'tshirt.png',),
                    
                ]
                cursor.executemany(
                    "INSERT INTO prizes (name, image,) VALUES (?, ?,)",
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
                    'description': p[3]
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
        print(f"🎲 draw_prize с ником: {nickname}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, играл ли уже
            cursor.execute("SELECT prize_id FROM winners WHERE nickname = ?", (nickname,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("SELECT name FROM prizes WHERE id = ?", (existing[0],))
                prize_name = cursor.fetchone()[0]
                return {
                    'success': False,
                    'message': f'Ты уже играл! Твой приз: {prize_name}'
                }
            
            # Получаем доступные призы
            cursor.execute("""
                SELECT id, name, image
                FROM prizes
                WHERE available = 1
            """)
            available_prizes = cursor.fetchall()
            
            if not available_prizes:
                return {'success': False, 'message': 'Все призы выданы'}
            
            # Выбираем случайный приз
            prize = random.choice(available_prizes)
            
            # Помечаем как недоступный
            cursor.execute(
                "UPDATE prizes SET available = 0 WHERE id = ?",
                (prize[0],)
            )
            
            # Записываем победителя
            cursor.execute(
                "INSERT INTO winners (nickname, prize_id) VALUES (?, ?)",
                (nickname, prize[0])
            )
            
            conn.commit()
            
            return {
                'success': True,
                'message': f'Поздравляем! Ты выиграл: {prize[1]}',
                'prize': {
                    'id': prize[0],
                    'name': prize[1],
                    'image': prize[2]
                }
            }

                         
                                
                   
        
           