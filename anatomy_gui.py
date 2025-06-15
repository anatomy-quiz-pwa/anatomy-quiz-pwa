import tkinter as tk
from tkinter import scrolledtext
import smtplib
import csv
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from datetime import datetime, timedelta
import imaplib
import email
from email.header import decode_header
import re
from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd

gmail_user = 'paopaopainting@gmail.com'
gmail_app_password = 'xxbepecvlfdogyfm'
to_email = 'paopaopainting@gmail.com'
csv_file = os.path.join('解剖力小程式', 'anatomy_questions2.csv')
record_file = os.path.join('解剖力小程式', 'practice_record.json')

# 資料庫操作

def load_or_create_record():
    if os.path.exists(record_file):
        with open(record_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        record = {
            'email': to_email,
            'first_date': datetime.now().strftime('%Y-%m-%d'),
            'total_questions': 0,
            'total_answers': 0,
            'correct_answers': 0,
            'wrong_answers': 0,
            'last_question_date': None,
            'last_question': None,
            'last_options': None,
            'last_answer': None
        }
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return record

def update_record(record):
    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        return '郵件發送成功！'
    except Exception as e:
        return f'發送郵件失敗：{str(e)}'

def extract_answer_from_brackets(text):
    match = re.search(r'本日答案是[「『]([1-4])[」』]', text)
    if match:
        return match.group(1).strip()
    return None

def check_answer(user_answer, correct_answer):
    return user_answer.strip() == correct_answer.strip()

# GUI功能

def send_question():
    try:
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            questions = [row for row in reader if len(row) >= 3]
    except Exception as e:
        return f'讀取題庫失敗：{str(e)}'
    if not questions:
        return '題庫為空或格式錯誤，請檢查 anatomy_questions2.csv'
    record = load_or_create_record()
    today = datetime.now().strftime('%Y-%m-%d')
    if record.get('last_question_date') == today:
        return '今天已經寄過題目，請勿重複寄送。'
    record['total_questions'] += 1
    record['last_question_date'] = today
    q = random.choice(questions)
    question, options, answer = q[0], q[1], q[2].strip()
    record['last_question'] = question
    record['last_options'] = options
    record['last_answer'] = answer
    update_record(record)
    first_date = datetime.strptime(record['first_date'], '%Y-%m-%d')
    current_date = datetime.now()
    practice_days = (current_date - first_date).days + 1
    subject = f"解剖力練習第{practice_days}天"
    body = f"""又是提升解剖力的一天！\n\n這是你進行解剖力練習的第{practice_days}天\n你已經成功回答{record['total_answers']}題！\n正確率：{record['correct_answers']}/{record['total_answers']} ({int(record['correct_answers']/record['total_answers']*100 if record['total_answers'] > 0 else 0)}%)\n\n本日（{today}）的解剖力題目是：\n{question}\n\n選項：\n{options}\n\n請複製下方這段文字，並在『』內填寫你的答案（1/2/3/4），回覆此郵件：\n本日答案是『1』\n"""
    result = send_email(subject, body)
    return f"{result}\n題目已寄出，請回覆郵件作答。"

def check_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_app_password)
        mail.select("inbox")
        date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(UNSEEN SINCE {date})')
        message_numbers = messages[0].split()
        for num in message_numbers[-10:]:
            try:
                _, msg = mail.fetch(num, "(RFC822)")
                email_body = msg[0][1]
                email_message = email.message_from_bytes(email_body)
                subject = decode_header(email_message["subject"])[0][0]
                if isinstance(subject, bytes):
                    try:
                        subject = subject.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            subject = subject.decode('big5')
                        except UnicodeDecodeError:
                            subject = subject.decode('gbk', errors='ignore')
                if "解剖力練習" in subject:
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode('utf-8')
                                except UnicodeDecodeError:
                                    try:
                                        body = part.get_payload(decode=True).decode('big5')
                                    except UnicodeDecodeError:
                                        body = part.get_payload(decode=True).decode('gbk', errors='ignore')
                                break
                    else:
                        try:
                            body = email_message.get_payload(decode=True).decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                body = email_message.get_payload(decode=True).decode('big5')
                            except UnicodeDecodeError:
                                body = email_message.get_payload(decode=True).decode('gbk', errors='ignore')
                    user_answer = extract_answer_from_brackets(body)
                    if user_answer:
                        record = load_or_create_record()
                        if not record:
                            return '找不到練習記錄，請先寄出題目。'
                        record['total_answers'] += 1
                        is_correct = check_answer(user_answer, record['last_answer'])
                        if is_correct:
                            record['correct_answers'] += 1
                            result = "正確"
                        else:
                            record['wrong_answers'] += 1
                            result = "錯誤"
                        update_record(record)
                        first_date = datetime.strptime(record['first_date'], '%Y-%m-%d')
                        current_date = datetime.now()
                        practice_days = (current_date - first_date).days + 1
                        reply_subject = f"解剖力練習答案回覆 - {result}"
                        reply_body = f"""哇你這麼快就回覆了！一起來看看答案是什麼\n\n題目是：\n{record['last_question']}\n\n選項：\n{record['last_options']}\n\n您的答案是：\n{user_answer}\n\n正確答案是：\n{record['last_answer']}\n\n結果：{result}\n\n目前統計：\n總題數：{record['total_questions']}\n已回答：{record['total_answers']}\n正確率：{record['correct_answers']}/{record['total_answers']} ({int(record['correct_answers']/record['total_answers']*100 if record['total_answers'] > 0 else 0)}%)\n\n繼續加油！"""
                        send_email(reply_subject, reply_body)
                        mail.store(num, '+FLAGS', '\\Seen')
                        mail.close()
                        mail.logout()
                        return '已自動回覆並標記郵件為已讀。'
            except Exception as e:
                continue
        mail.close()
        mail.logout()
        return '沒有找到新的回覆郵件。'
    except Exception as e:
        return f'檢查郵件時發生錯誤：{str(e)}'

# 建立GUI
root = tk.Tk()
root.title('解剖力自動寄題目小工具')
root.geometry('500x350')

frame = tk.Frame(root)
frame.pack(pady=20)

result_text = scrolledtext.ScrolledText(root, width=60, height=10, font=('Arial', 12))
result_text.pack(pady=10)

def show_result(msg):
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, msg)

btn_send = tk.Button(frame, text='寄出今日題目', font=('Arial', 14), width=18, command=lambda: show_result(send_question()))
btn_send.grid(row=0, column=0, padx=10)

btn_check = tk.Button(frame, text='檢查答案並自動回覆', font=('Arial', 14), width=22, command=lambda: show_result(check_emails()))
btn_check.grid(row=0, column=1, padx=10)

root.mainloop()

app = Flask(__name__)
app.secret_key = "your_secret_key"

questions_df = pd.read_csv("anatomy_questions2.csv")
user_db = {}  # email: {紀錄}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form["email"]
        session["email"] = email
        if email not in user_db:
            user_db[email] = {
                "total_attempts": 0,
                "correct_answers": 0,
                "streak": 0,
                "last_answer_date": None
            }
        return redirect(url_for("quiz"))
    return render_template("login.html")

@app.route("/quiz")
def quiz():
    email = session.get("email")
    if not email:
        return redirect(url_for("index"))
    q = questions_df.sample(1).iloc[0]
    question = q[0]
    options = q[1].split("  ")
    correct_index = int(q[2])
    return render_template("quiz.html", question=question, options=options, correct=correct_index)

@app.route("/submit", methods=["POST"])
def submit():
    email = session.get("email")
    if not email:
        return redirect(url_for("index"))
    selected = int(request.form["option"])
    correct = int(request.form["correct"])
    today = datetime.date.today()
    user_data = user_db[email]
    if user_data["last_answer_date"] == today:
        message = "今天你已經答過題了，明天再來挑戰！"
    else:
        user_data["total_attempts"] += 1
        if selected == correct:
            user_data["correct_answers"] += 1
            message = "答對了！太棒了！"
        else:
            message = "答錯了，下次再接再厲！"
        if user_data["last_answer_date"] == today - datetime.timedelta(days=1):
            user_data["streak"] += 1
        else:
            user_data["streak"] = 1
        user_data["last_answer_date"] = today
    accuracy = user_data["correct_answers"] / user_data["total_attempts"] * 100
    return render_template("result.html", message=message, streak=user_data["streak"], accuracy=round(accuracy, 1)) 