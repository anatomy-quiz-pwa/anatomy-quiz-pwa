from linebot import LineBotApi
import os
from user_management import get_active_users
from line_bot import send_question_to_user

# Line Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '你的Line Channel Access Token')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def send_questions_to_all_users():
    """發送題目給所有活躍用戶"""
    users = get_active_users()
    print(f"找到 {len(users)} 個活躍用戶")
    
    for user_id in users:
        try:
            send_question_to_user(user_id)
            print(f"成功發送題目給用戶 {user_id}")
        except Exception as e:
            print(f"發送題目給用戶 {user_id} 失敗：{str(e)}")

if __name__ == "__main__":
    send_questions_to_all_users() 