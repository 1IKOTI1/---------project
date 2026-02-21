from flask import Flask, render_template, jsonify, request
from database import RaffleDatabase
import os
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logging.info("Запуск приложения...")

app = Flask(__name__)
db = RaffleDatabase()

@app.route('/')
def index():
    app.logger.info("Кто-то зашел на главную страницу")
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Ошибка при рендеринге шаблона: {e}")
        return f"Ошибка: {e}", 500


@app.route('/api/prizes')
def get_prizes():
    app.logger.info("Запрос списка призов")
    try:
        prizes = db.get_available_prizes()
        return jsonify({'success': True, 'prizes': prizes})
    except Exception as e:
        app.logger.error(f"Ошибка при получении призов: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/play', methods=['POST'])
def play():
    data = request.get_json()
    nickname = data.get('nickname')
        
    if not nickname or not nickname.scrip():
        return jsonify({
            'success': False,
            'message': 'Введите имя'
                    })  
            
    nickname = nickname.scrip()
        
    existing_prize = db.has_user_played(nickname)
    if existing_prize:
        return jsonify({
            'success': False,
            'message': f'Ты уже играл'
            })
        
    result = db.draw_prize(nickname)
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': f'Твой приз: {result["prize"]["name"]}',
            'prize': result['prize']
        })
    else:
        return jsonify(result)

    
@app.route('/api/admin/winners')
def  get_winners():
    winners = db.get_all_winners()
    return jsonify({
        'success': True,
        'winners': [
            {'nickname': w[0], 'prize': w[1], 'date': w[2]}
             for w in winners
        ]
    }) 

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)  