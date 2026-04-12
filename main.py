import sys
from fastapi import FastAPI, Request, BackgroundTasks
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Import local modules
from config import CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET
import game_logic
import line_messages

# Initialize App & LINE API
app = FastAPI()
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.get("/")
def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "OK", "message": "Rabbit Bot is active!"}

@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks):
    """Handle the webhook request from LINE."""
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    body_decode = body.decode("utf-8")

    try:
        handler.handle(body_decode, signature)
    except InvalidSignatureError:
        return "Invalid signature"
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Main message handler. Routes logic based on user input."""
    user_id = event.source.user_id
    text = event.message.text.strip()

    reply_content = []

    # --- 1. Daily Streak / Morning Greeting ---
    if "おはよう" in text:
        msg_text = game_logic.process_morning_greeting(user_id)
        reply_content.append(TextSendMessage(text=msg_text))

    # --- 2. Shop & Item Display ---
    elif text == "ショップ":
        reply_content.append(line_messages.create_shop_message())

    elif text == "会員証":
        user_data, _ = game_logic.get_or_create_user(user_id)
        reply_content.append(line_messages.create_member_card(user_data))

    # --- 3. Purchase Logic ---
    elif text == "身代わり人形を買う":
        msg_text = game_logic.process_purchase(user_id, "substitute_doll", 5, "身代わり人形🧸")
        reply_content.append(TextSendMessage(text=msg_text))

    elif text == "サングラスを買う":
        msg_text = game_logic.process_purchase(user_id, "sunglasses", 10, "サングラス🕶️")
        reply_content.append(TextSendMessage(text=msg_text + "\n「サングラス装着」と送ると着替えるよ！"))

    elif text == "ピンク染め粉を買う":
        msg_text = game_logic.process_purchase(user_id, "pink_dye", 20, "魔法のピンク染め粉🎨")
        reply_content.append(TextSendMessage(text=msg_text + "\n「ピンクに変身」と送ると着替えるよ！"))

    # --- 4. Change Appearance Logic ---
    elif text == "ピンクに変身":
        msg_text = game_logic.process_change_look(
            user_id,
            "pink",
            "pink_dye",
            "✨キラキラ〜✨\nピンク色に変身しました！🐰🎀",
            "まだ染め粉を持ってないよ！"
        )
        reply_content.append(TextSendMessage(text=msg_text))

    elif text == "サングラス装着":
        msg_text = game_logic.process_change_look(
            user_id,
            "sunglasses",
            "sunglasses",
            "シャキーン！😎\nサングラスをかけました！",
            "まだサングラスを持ってないよ！"
        )
        reply_content.append(TextSendMessage(text=msg_text))

    elif text == "元に戻す":
        # resetting to normal doesn't require an item
        msg_text = game_logic.process_change_look(
            user_id, "normal", None, "ポンッ💨\n元の姿に戻りました！🐰", ""
        )
        reply_content.append(TextSendMessage(text=msg_text))

    # --- 5. Moon Phase / Good Night ---
    elif "おやすみ" in text:
        moon_emoji = game_logic.get_moon_info()
        reply_content.append(
            TextSendMessage(
                text=f"おやすみなさいだうさ〜🐰💤\n\n今日の月は【 {moon_emoji} 】だぴょん！\nゆっくり休んでね✨"
            )
        )

    # --- 6. Fallback: Chat with Gemini ---
    else:
        # If no commands matched, chat with the AI persona
        reply_text = game_logic.get_gemini_reply(text)
        reply_content.append(TextSendMessage(text=reply_text))

    # Send the replies
    if reply_content:
        line_bot_api.reply_message(event.reply_token, reply_content)

