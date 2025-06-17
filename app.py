from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
from flask_dance.contrib.google import make_google_blueprint, google
import os
import gspread
from google.oauth2.service_account import Credentials
import re
import logging
import datetime
from PIL import Image
import pytesseract
import openai
from notion_client import Client
import shutil
import uuid

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

# 學生行為紀錄 Google Sheet
LOG_SHEET_ID = '1PuzGPp5EOvc4zA6YQrEbn95BOinQIZEaK-oZp1IF0eY'  # 學生行為紀錄表格ID

# 設定你的 API 金鑰
openai.api_key = '你的OpenAI API金鑰'
notion = Client(auth="你的Notion整合金鑰")

# Notion page/database id
NOTION_PAGE_ID = "你的Notion頁面ID"

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

@app.route('/api/log_answer', methods=['POST'])
def log_answer():
    data = request.json
    row = [
        data.get('user_id'),
        data.get('question_id'),
        data.get('answer_given'),
        data.get('is_correct'),
        data.get('timestamp', datetime.datetime.utcnow().isoformat()),
        data.get('time_spent'),
        data.get('question_topic'),
        data.get('question_difficulty'),
        data.get('quiz_mode'),
        data.get('session_id'),
        data.get('streak_days'),
        data.get('reaction_after'),
        data.get('retry_count')
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    log_sheet = gc.open_by_key(LOG_SHEET_ID).sheet1
    log_sheet.append_row(row)
    return jsonify({'status': 'success'})

def convert_to_jpeg(src_folder):
    for fname in os.listdir(src_folder):
        if not fname.lower().endswith(('.jpg', '.jpeg')):
            img_path = os.path.join(src_folder, fname)
            try:
                img = Image.open(img_path)
                jpeg_path = os.path.splitext(img_path)[0] + '.jpg'
                img.convert('RGB').save(jpeg_path, 'JPEG')
                print(f"已轉換: {jpeg_path}")
            except Exception as e:
                print(f"轉換失敗: {img_path}, {e}")

def ocr_images(src_folder):
    texts = []
    for fname in os.listdir(src_folder):
        if fname.lower().endswith('.jpg'):
            img_path = os.path.join(src_folder, fname)
            try:
                text = pytesseract.image_to_string(Image.open(img_path), lang='chi_tra+eng')
                texts.append((fname, text))
            except Exception as e:
                print(f"OCR失敗: {img_path}, {e}")
    return texts

def gpt_translate_and_summarize(text):
    prompt = f"請將下列內容翻譯成中文並摘要重點：\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def write_to_notion(page_id, content):
    notion.pages.create(
        parent={"page_id": page_id},
        properties={"title": {"title": [{"text": {"content": "OCR翻譯整理"}}]}},
        children=[{"object": "block", "type": "paragraph", "paragraph": {"text": [{"type": "text", "text": {"content": content}}]}}]
    )

def ocr_convert():
    desktop = os.path.expanduser("~/Desktop")
    input_dir = os.path.join(desktop, "book", "input")
    output_dir = os.path.join(desktop, "book", "output")
    processed_base_dir = os.path.join(desktop, "book", "processed")

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(processed_base_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.tif', '.bmp')):
            continue

        filepath = os.path.join(input_dir, filename)
        temp_jpg_path = None

        try:
            # 轉為 RGB 並存成暫存 JPG
            with Image.open(filepath) as img:
                rgb_img = img.convert("RGB")
                temp_jpg_path = os.path.join(input_dir, f"temp_{uuid.uuid4().hex}.jpg")
                rgb_img.save(temp_jpg_path, "JPEG")

            # OCR 辨識
            with Image.open(temp_jpg_path) as temp_img:
                text = pytesseract.image_to_string(temp_img, lang='eng')

            output_text = (
                "請幫我將以下英文翻譯成繁體中文，保留原文段落、逐段對照，"
                "最後幫我摘要整理，必要時可加上表格：\n\n"
                "------ 以下為英文原文 ------\n\n" + text.strip()
            )
            output_filename = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)

            # 移動原始圖片
            today = datetime.today().strftime('%Y-%m-%d')
            processed_dir = os.path.join(processed_base_dir, today)
            os.makedirs(processed_dir, exist_ok=True)
            shutil.move(filepath, os.path.join(processed_dir, filename))

            print(f"✅ 已處理：{filename}")

        except Exception as e:
            print(f"❌ 處理失敗 {filename}：{e}")

        finally:
            if temp_jpg_path and os.path.exists(temp_jpg_path):
                os.remove(temp_jpg_path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 