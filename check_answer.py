import imaplib
import email
from email.header import decode_header
import re
import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

gmail_user = 'paopaopainting@gmail.com'
gmail_app_password = 'xxbepecvlfdogyfm'
to_email = 'paopaopainting@gmail.com'
record_file = os.path.join('解剖力小程式', 'practice_record.json')

def load_or_create_record():
    if os.path.exists(record_file):
        with open(record_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return None

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

def extract_answer_from_brackets(text):
    match = re.search(r'本日答案是[「『]([1-4])[」』]', text)
    if match:
        return match.group(1).strip()
    return None

def check_answer(user_answer, correct_answer):
    return user_answer.strip() == correct_answer.strip()

def check_new_emails():
    try:
        print("正在連接到 Gmail...")
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
                            print('找不到練習記錄，請先寄出題目。')
                            return
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
                        print('已自動回覆並標記郵件為已讀。')
                        break
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

if __name__ == "__main__":
    check_new_emails() 