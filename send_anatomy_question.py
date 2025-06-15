import smtplib
import csv
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ====== 使用前請填寫下列資訊 ======
gmail_user = 'paopaopainting@gmail.com'  # TODO: 請填寫你的 Gmail 帳號
gmail_app_password = 'xxbepecvlfdogyfm'  # 已填入你的應用程式密碼
to_email = 'paopaopainting@gmail.com'  # TODO: 請填寫收件人信箱
csv_file = 'anatomy_questions2.csv'  # TODO: 若檔案不在同目錄請填完整路徑
# ===================================

# 讀取題目
with open(csv_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    questions = [row for row in reader if len(row) == 2]

if not questions:
    raise Exception('題庫為空或格式錯誤，請檢查 anatomy_questions.csv')

# 隨機選一題
question, answer = random.choice(questions)

# 組信件
subject = "今日解剖學題目"
body = f"題目：{question}\n答案：{answer}"

msg = MIMEMultipart()
msg['From'] = gmail_user
msg['To'] = to_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

# 發送
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
    print('Email sent!')
except Exception as e:
    print('Failed to send email:', e) 