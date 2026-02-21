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
    import traceback
    print("\n" + "="*60)
    print("🔥 ПОЛУЧЕН POST ЗАПРОС НА /api/play")
    
    try:
      
        print(f"Заголовки: {dict(request.headers)}")
        
      
        raw_data = request.get_data(as_text=True)
        print(f"Сырые данные: {raw_data}")
        
      
        data = request.get_json()
        print(f"JSON данные: {data}")
        
        nickname = data.get('nickname')
        print(f"Ник из запроса: '{nickname}'")
        
        if not nickname or not nickname.strip():
            print("❌ Ник пустой")
            return jsonify({'success': False, 'message': 'Введите имя'})
        
        nickname = nickname.strip()
        print(f"✅ Ник после очистки: '{nickname}'")
        
      
        print(f"🔍 Проверяем has_user_played для '{nickname}'")
        existing_prize = db.has_user_played(nickname)
        print(f"Результат has_user_played: {existing_prize}")
        
        if existing_prize:
            print("❌ Пользователь уже играл")
            return jsonify({'success': False, 'message': f'Ты уже играл'})
        
       
        print(f"🎲 Вызываем draw_prize для '{nickname}'")
        result = db.draw_prize(nickname)
        print(f"📦 Результат draw_prize: {result}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Твой приз: {result["prize"]["name"]}',
                'prize': result['prize']
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        print(f"🔥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Ошибка сервера: {str(e)}'}), 500

    
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