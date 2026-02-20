from flask import Flask, render_template, jsonify, request
from database import RaffleDatabase
import os

app = Flask(__name__)
db = RaffleDatabase()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/prizes')
def get_prizes():
    prizes = db.get_available_ptizes()
    return jsonify({
        'success': True,
        'prazes': prizes
    })
    
@app.route('/api/play', methods=['POST'])
def play():
    data = request.get_json()
    nickname = data.get('nackname')
        
    if not nickname or not nickname.script():
        return jsonify({
            'success': False,
            'message': 'Введите имя'
                    })  
            
    nickname = nickname.script()
        
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
    
import os  # ← ЭТОТ ИМПОРТ ДОЛЖЕН БЫТЬ ВВЕРХУ ФАЙЛА!

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)  # ← ВАЖНО: host="0.0.0.0"