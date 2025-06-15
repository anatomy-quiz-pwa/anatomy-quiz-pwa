from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
from flask_dance.contrib.google import make_google_blueprint, google
import os
import gspread
from google.oauth2.service_account import Credentials
import re
import logging

logging.basicConfig(level=logging.INFO)

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

# Google Sheet 設定
SHEET_ID = '1mKfdSTLMrqyLu2GW_Km5ErboyPgjcyJ4q9Mqn8DkwCE'
SHEET_NAME = '題庫'  # 這裡改成你的工作表名稱
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = '/etc/secrets/hypnotic-bounty-463007-n4-42afd732fc72.json'

def get_questions_from_sheet():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    rows = worksheet.get_all_values()
    questions = []
    header = rows[0]
    for row in rows[1:]:
        # 依照新欄位順序：分類, 題目, 選項1, 選項2, 選項3, 選項4, 正確答案, 補充資料
        category, question, opt1, opt2, opt3, opt4, correct, extra = row
        option_list = [opt1, opt2, opt3, opt4]
        correct_index = int(correct.strip()) - 1  # 轉成 0-based index
        questions.append({
            'category': category,
            'question': question,
            'options': option_list,
            'correct_index': correct_index,
            'correct': option_list[correct_index] if 0 <= correct_index < len(option_list) else '',
            'extra': extra
        })
    return questions

@app.route('/')
def quiz():
    user = None
    if google.authorized:
        resp = google.get("/oauth2/v2/userinfo")
        if resp.ok:
            user = resp.json()
    questions = get_questions_from_sheet()
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
    question = next((q for q in get_questions_from_sheet() if q['id'] == question_id), None)
    if question and answer == question['correct']:
        return jsonify({"correct": True, "message": "答對了！"})
    return jsonify({"correct": False, "message": f"答錯了！正確答案是：{question['correct']}"})

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 