import smtplib
import csv
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time
import json
from datetime import datetime, timedelta
import imaplib
import email
from email.header import decode_header
import re
import unicodedata

print("程式開始執行...")

# ====== 使用前請填寫下列資訊 ======
gmail_user = 'paopaopainting@gmail.com'  # 你的 Gmail 帳號
gmail_app_password = 'xxbepecvlfdogyfm'  # 你的應用程式密碼
to_email = 'paopaopainting@gmail.com'  # 收件人信箱
csv_file = os.path.join('解剖力小程式', 'anatomy_questions2.csv')  # 題庫檔案路徑
record_file = os.path.join('解剖力小程式', 'practice_record.json')  # 練習記錄檔案
# ===================================

# 讀取或建立練習記錄
def load_or_create_record():
    if os.path.exists(record_file):
        with open(record_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 建立新的記錄
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
        # 儲存記錄
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return record

# 更新練習記錄
def update_record(record):
    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

# 發送郵件
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

# 檢查答案
def check_answer(user_answer, correct_answer):
    # 只比對 1/2/3/4
    return user_answer.strip() == correct_answer.strip()

def extract_answer_from_brackets(text):
    # 尋找第一個『』內的內容，只取1/2/3/4
    match = re.search(r'本日答案是[「『]([1-4])[」』]', text)
    if match:
        return match.group(1).strip()
    return None

# 檢查新郵件
def check_new_emails():
    try:
        print("正在連接到 Gmail...")
        # 連接到 Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        print("正在登入...")
        mail.login(gmail_user, gmail_app_password)
        print("正在選擇收件匣...")
        mail.select("inbox")

        # 搜尋最近24小時內的未讀郵件
        print("正在搜尋最近24小時內的未讀郵件...")
        date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(UNSEEN SINCE {date})')
        message_numbers = messages[0].split()
        print(f"找到 {len(message_numbers)} 封未讀郵件")
        
        # 只處理最近的10封郵件
        for num in message_numbers[-10:]:
            try:
                print(f"正在處理郵件 {num.decode()}...")
                _, msg = mail.fetch(num, "(RFC822)")
                email_body = msg[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # 檢查是否為回覆郵件
                subject = decode_header(email_message["subject"])[0][0]
                if isinstance(subject, bytes):
                    try:
                        subject = subject.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            subject = subject.decode('big5')
                        except UnicodeDecodeError:
                            subject = subject.decode('gbk', errors='ignore')
                
                print(f"郵件主旨: {subject}")
                
                if "解剖力練習" in subject:
                    print("找到解剖力練習的回覆郵件！")
                    # 取得郵件內容
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
                    
                    print(f"郵件內容: {body}")
                    
                    # 只抓取『』內的內容
                    user_answer = extract_answer_from_brackets(body)
                    print(f"擷取到的答案: {user_answer}")
                    if not user_answer:
                        user_answer = body.strip().split('\n')[0]  # fallback: 第一行
                    
                    # 更新記錄
                    record = load_or_create_record()
                    record['total_answers'] += 1
                    
                    # 檢查答案
                    print(f"正在比對答案...")
                    print(f"使用者答案: {user_answer}")
                    print(f"正確答案: {record['last_answer']}")
                    is_correct = check_answer(user_answer, record['last_answer'])
                    if is_correct:
                        record['correct_answers'] += 1
                        result = "正確"
                    else:
                        record['wrong_answers'] += 1
                        result = "錯誤"
                    
                    print(f"答案比對結果: {result}")
                    update_record(record)
                    
                    # 計算練習天數
                    first_date = datetime.strptime(record['first_date'], '%Y-%m-%d')
                    current_date = datetime.now()
                    practice_days = (current_date - first_date).days + 1
                    
                    # 回覆結果
                    reply_subject = f"解剖力練習答案回覆 - {result}"
                    reply_body = f"""哇你這麼快就回覆了！一起來看看答案是什麼

題目是：
{record['last_question']}

選項：
{record['last_options']}

您的答案是：
{user_answer}

正確答案是：
{record['last_answer']}

結果：{result}

目前統計：
總題數：{record['total_questions']}
已回答：{record['total_answers']}
正確率：{record['correct_answers']}/{record['total_answers']} ({int(record['correct_answers']/record['total_answers']*100 if record['total_answers'] > 0 else 0)}%)

繼續加油！"""
                    
                    print("正在發送回覆郵件...")
                    send_email(reply_subject, reply_body)
                    
                    # 標記郵件為已讀
                    print("正在標記郵件為已讀...")
                    mail.store(num, '+FLAGS', '\\Seen')
                    print("處理完成！")
                    break  # 找到並處理完一封回覆就停止
            except Exception as e:
                print(f"處理郵件 {num.decode()} 時發生錯誤：{str(e)}")
                continue
        
        mail.close()
        mail.logout()
        print("郵件檢查完成！")
        
    except Exception as e:
        print(f"檢查郵件時發生錯誤：{str(e)}")
        print("請確認：")
        print("1. Gmail 帳號是否正確")
        print("2. 應用程式密碼是否正確")
        print("3. 是否已開啟 Gmail 的 IMAP 存取")
        print("4. 網路連線是否正常")

# 檢查檔案是否存在
if not os.path.exists(csv_file):
    print(f"錯誤：找不到檔案 {csv_file}")
    print(f"目前工作目錄：{os.getcwd()}")
    print("請確認檔案位置是否正確")
    exit(1)

print(f"正在讀取檔案：{csv_file}")

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

# 讀取練習記錄
record = load_or_create_record()
today = datetime.now().strftime('%Y-%m-%d')

# 判斷今天是否已經寄過題目
if record.get('last_question_date') == today:
    print("今天已經寄過題目，開始檢查回覆信箱...")
    check_new_emails()
    print("流程結束。")
    exit(0)

# 還沒寄過題目，寄出新題目
record['total_questions'] += 1
record['last_question_date'] = today

# 隨機選一題
q = random.choice(questions)
question, options, answer = q[0], q[1], q[2].strip()
record['last_question'] = question
record['last_options'] = options
record['last_answer'] = answer
update_record(record)

# 計算練習天數
first_date = datetime.strptime(record['first_date'], '%Y-%m-%d')
current_date = datetime.now()
practice_days = (current_date - first_date).days + 1

# 組信件
subject = f"解剖力練習第{practice_days}天"
body = f"""又是提升解剖力的一天！

這是你進行解剖力練習的第{practice_days}天
你已經成功回答{record['total_answers']}題！
正確率：{record['correct_answers']}/{record['total_answers']} ({int(record['correct_answers']/record['total_answers']*100 if record['total_answers'] > 0 else 0)}%)

本日（{today}）的解剖力題目是：
{question}

選項：
{options}

請複製下方這段文字，並在『』內填寫你的答案（1/2/3/4），回覆此郵件：
本日答案是『1』
"""

print("正在發送今日題目...")
send_email(subject, body)
print("題目已寄出，請回覆郵件作答。\n將自動等待你的回覆...")

# 自動等待回覆
max_wait_minutes = 10
interval_seconds = 10
waited = 0
found = False

def check_and_break():
    global found
    class FoundAnswer(Exception): pass
    try:
        def check_new_emails_once():
            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(gmail_user, gmail_app_password)
                mail.select("inbox")
                date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
                _, messages = mail.search(None, f'(UNSEEN SINCE {date})')
                message_numbers = messages[0].split()
                for num in message_numbers[-10:]:
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
                            # 執行原本的自動回覆流程
                            record = load_or_create_record()
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
                            found = True
                            raise FoundAnswer()
                mail.close()
                mail.logout()
            except Exception as e:
                print(f"檢查郵件時發生錯誤：{str(e)}")
        check_new_emails_once()
    except FoundAnswer:
        pass

# 在寄出題目後自動等待回覆
waited = 0
while waited < max_wait_minutes * 60:
    print(f"第{waited//interval_seconds+1}次檢查信箱...")
    check_and_break()
    if found:
        print("已收到你的回覆並自動驗證，流程結束！")
        break
    time.sleep(interval_seconds)
    waited += interval_seconds
if not found:
    print(f"等待{max_wait_minutes}分鐘內未收到回覆，請確認是否已寄出答案，或再執行一次本程式。")
