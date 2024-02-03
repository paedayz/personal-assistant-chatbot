from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Replace these values with your LINE Channel Access Token and Channel Secret
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.get("/health")
async def healthCheck(request: Request):
    return JSONResponse(content={"status": "OK"})

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature")

    # Get the request body as text
    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return JSONResponse(content={"success": True})


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # Handle text messages
    text = event.message.text
    reply_text = f"You said: {text}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
