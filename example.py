import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import AzureOpenAI

app = Flask(__name__)

# 設定 LINE Bot 的 Channel Access Token 與 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = ("你的 LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = ("你的 LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 取得 Azure OpenAI 的相關參數
endpoint = ("你的endpoint")
deployment = ("你的模型名稱(gpt-35-turbo)")
subscription_key = ("你的金鑰")

# 初始化 Azure OpenAI 服務用戶端
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2024-05-01-preview",
)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # 定義聊天提示，這邊用戶輸入直接接在系統指令之後
    messages = [
        {"role": "system", "content": "您是協助人員尋找資訊的 AI 助理。"},
        {"role": "user", "content": user_text}
    ]
    
    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        reply_text = completion.choices[0].message.content.strip()
    except Exception as e:
        reply_text = "抱歉，目前服務發生錯誤，請稍後再試。"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

if __name__ == "__main__":
    app.run()
