import sqlite3
import os

class RaffleDatabase:
    def __init__(self, db_name="raffle.db"):
        self.db_name = db_name
        self.init_database()
        
    def get_connection(self):
            return sqlite3.connect(self.db_name)
        
    def init_database(self):
            with self.get_connection() as cann:
                cursor = cann.cursor()
                
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
                        ('cart 1', 'card 2', 'card 3', 'card 4')
                    ]
                    cursor.executemany(
                        "INSERT INTO prizes (name, desxription) VALUES (?,?,?)",
                        default_prizes
                    
                    )
                    cann.commit()
                    
    def get_available_prizes(self):
                 with self.get_connection() as conn:
                     cursor = conn.cursor()
                     cursor.execute(
                         "SELECT id, name, image, description FROM prizes available = 1"
                     )      
                     prizes = cursor.fetcall()
                     return [
                         {
                             'id': p[0],
                             'name': p[1],
                             'image': p[2],
                             "description": p[3]
                                                         
                         }
                         for p in prizes
                     ]
                     
    def has_user_played(self, nickname):
                 with self.get_connection()  as conn:
                     cursor = conn.cursor()
                     cursor.execute(
                         "SELECT prize_id FROM winners WHERE nickname = ?",
                         (nickname,)
                     )
                 result = cursor.fetchone()
                 return result[0] if result else None
                     
    def draw_prize(self, nickname):
                 with self.get_connection() as conn:
                     cursor = conn.cursor()
                     
                     cursor.execute("BEGIN TRANSACTION")
                     
                     try:
                         cursor.execute("""
                                        SELECT id, name, image
                                        FROM prizes
                                        WHERE availble = 1
                                        ORDER BY RANDOM()
                                        LIMIT 1
                                        """)
                         prize = cursor.fetchone()
                         
                         if not prize:
                             conn.rollblack()
                             return {'success': False, 'massage': 'Все призы выданы'}
                         
                         cursor.execute(
                             "UPDATE prazes SET available = 0 WHERE id = ?",
                             (prize[0],)
                         )
                         
                         cursor.execute(
                             "INSERET INFO winners (nickname, prize_id) VALUES (?, ?)",
                             (nickname, prize[0])
                         )
                         
                         conn.commit()
                         
                         return{
                             'success': True,
                             'prize':{
                                 'id': prize [0],
                                 'name': prize[1],
                                 'image': prize[2]
                             }
                         }
                         
                     except sqlite3.IntegrityError:
                         conn.rollback()
                         old_prize_id = self.has_user_played(nickname)
                         cursor.execute(
                             "SELECT name FROM prizes WHERE id = ?",
                             (old_prize_id,)
                         )
                         prize_name =cursor.fetchone()[0]
                         return{
                             'success': False,
                             'message': f'Ты ужк забрал свой приз: {prize_name}'
                         }
             
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
                         
                         
                         
                                 
                           
        
        