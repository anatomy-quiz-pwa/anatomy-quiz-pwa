import smtplib
import csv
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from datetime import datetime

# ====== 使用前請填寫下列資訊 ======
gmail_user = 'paopaopainting@gmail.com'
gmail_app_password = 'xxbepecvlfdogyfm'
to_email = 'paopaopainting@gmail.com'
csv_file = os.path.join('解剖力小程式', 'anatomy_questions2.csv')
record_file = os.path.join('解剖力小程式', 'practice_record.json')
# ===================================

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
        print('郵件發送成功！')
        return True
    except Exception as e:
        print(f'發送郵件失敗：{str(e)}')
        return False

# 讀取題目
try:
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        questions = [row for row in reader if len(row) >= 3]
        print(f"成功讀取到 {len(questions)} 個題目")
except FileNotFoundError:
    print(f"錯誤：找不到檔案 {csv_file}")
    raise
except Exception as e:
    print(f"讀取檔案時發生錯誤：{str(e)}")
    raise

if not questions:
    raise Exception('題庫為空或格式錯誤，請檢查 anatomy_questions2.csv')

record = load_or_create_record()
today = datetime.now().strftime('%Y-%m-%d')

# 判斷今天是否已經寄過題目
if record.get('last_question_date') == today:
    print("今天已經寄過題目，請勿重複寄送。")
    exit(0)

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

print("正在發送今日題目...")
send_email(subject, body)
print("題目已寄出，請回覆郵件作答。") 