from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
from flask_dance.contrib.google import make_google_blueprint, google
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')

# Google OAuth 設定
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # 允許 http 測試
GOOGLE_CLIENT_ID = '48013299231-e9ji91djj8khlghj0hb66ib0g2c104v6.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"],
    redirect_url="https://anatomy-quiz-pwa.onrender.com/login/callback"
)
app.register_blueprint(google_bp, url_prefix="/login")

# 解剖學題庫
questions = [
    {
        "id": 1,
        "question": "人體最大的器官是什麼？",
        "options": ["心臟", "肝臟", "皮膚", "肺臟"],
        "correct": "皮膚"
    },
    {
        "id": 2,
        "question": "人體有多少塊骨頭？",
        "options": ["206塊", "186塊", "216塊", "196塊"],
        "correct": "206塊"
    },
    {
        "id": 3,
        "question": "負責輸送氧氣的細胞是什麼？",
        "options": ["白血球", "紅血球", "血小板", "淋巴球"],
        "correct": "紅血球"
    }
]

@app.route('/')
def quiz():
    user = None
    if google.authorized:
        resp = google.get("/oauth2/v2/userinfo")
        if resp.ok:
            user = resp.json()
    return render_template('quiz.html', questions=questions, user=user)

@app.route('/login')
def login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    return redirect(url_for('quiz'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('quiz'))

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')
    question = next((q for q in questions if q['id'] == question_id), None)
    if question and answer == question['correct']:
        return jsonify({"correct": True, "message": "答對了！"})
    return jsonify({"correct": False, "message": f"答錯了！正確答案是：{question['correct']}"})

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 