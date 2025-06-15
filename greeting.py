import pandas as pd
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ✅ 1. 載入題庫
df = pd.read_csv("anatomy_questions.csv")
question = random.choice(df.to_dict("records"))

# ✅ 2. 準備信件內容
sender_email = "paopaopainting@gmail.com"
receiver_email = "paopaopainting@gmail.coml@gmail.com"  # 先寄給你自己測試
app_password = "xxbe pecv lfdo gyfm"  # 注意：不是 Gmail 密碼！

subject = "今日解剖挑戰題 ✨"
body = f"""
💀【每日解剖挑戰】💀

📍 今日問題：
{question['question']}

請直接回覆這封信並回答你的答案 😊

-- 
系統將比對你回信中的內容是否包含正解關鍵字：
正解為：{question['answer']}（實際寄出前可隱藏）

祝你解剖順利！🦴
"""

# ✅ 3. 建立信件
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

# ✅ 4. 寄出信件（透過 Gmail SMTP）
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(sender_email, app_password)
    server.send_message(message)

print("✅ 信件已成功寄出！")
