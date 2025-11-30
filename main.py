import os
import sys
from fastapi import FastAPI, Request, BackgroundTasks
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FlexSendMessage,
    CarouselContainer,
    BubbleContainer,
)
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta  # 👈 時間計算用の道具を追加しました！
import pytz
import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv()


# --- 設定まわり ---
# ⚠️ ここにあなたのキーを入れてください！
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")


line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
# ⚠️ さっきコピーしたGeminiのキーをここに貼る！
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# うさぎの人格設定（プロンプト）🐰
# ここを変えると、性格が変わります！
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction="""
あなたは月に住んでいる不思議なうさぎです。
語尾に「ぴょん」や「だうさ」をつけて話します。
性格は優しくて、少し丁寧です。
ユーザーは地球に住んでいるあなたの飼い主です。
短めの文章で、絵文字を使って可愛く返事をしてください。
""",
)

# ... (この下の LINE の設定などはそのまま) ...
# Firestore初期化
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()


# --- 🐰 会員証システム ---
def get_or_create_rabbit_user(user_id):
    doc_ref = db.collection("rabbit_gamers").document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        initial_data = {
            "user_id": user_id,
            "carrot_count": 0,
            "moon_level": 1,
            "current_streak": 0,  # 連続日数
            "last_login": None,
            "items": [],
            "current_look": "normal",
            "created_at": datetime.now(pytz.timezone("Asia/Tokyo")),
        }
        doc_ref.set(initial_data)
        return initial_data


# --- LINE受信部分 ---
@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    body_decode = body.decode("utf-8")

    try:
        handler.handle(body_decode, signature)
    except InvalidSignatureError:
        return "Invalid signature"
    return "OK"


def get_moon_info():
    """今日の月齢を計算して絵文字を返す魔法の関数"""
    # 基準の新月（2023年1月22日）からの経過時間を計算
    base_date = datetime(2023, 1, 22, tzinfo=pytz.timezone("Asia/Tokyo"))
    current_date = datetime.now(pytz.timezone("Asia/Tokyo"))

    diff = current_date - base_date
    days = diff.days + (diff.seconds / 86400)

    # 月齢 (0 〜 29.5)
    moon_age = days % 29.53059

    # 月齢に合わせて絵文字を決める
    if moon_age < 1 or moon_age > 28.5:
        return "🌑 (新月)"
    elif moon_age < 6:
        return "🌒 (三日月)"
    elif moon_age < 9:
        return "🌓 (上弦の月)"
    elif moon_age < 14:
        # 👇 ここを追加しました！
        return "🌔 (十三夜)"
    elif moon_age < 16:
        return "🌕 (満月)"
    elif moon_age < 20:
        # 👇 ここを追加しました！
        return "🌖 (寝待月)"
    elif moon_age < 24:
        return "🌗 (下弦の月)"
    else:
        # 👇 ここを追加しました！
        return "🌘 (有明月)"


# --- メッセージ処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text

    # データを取得
    user_data = get_or_create_rabbit_user(user_id)
    doc_ref = db.collection("rabbit_gamers").document(user_id)

    my_items = user_data.get("items", [])
    current_look = user_data.get("current_look", "normal")
    current_streak = user_data.get("current_streak", 0)

    reply_content = []

    # ==========================================
    # 🌅 「おはよう」処理（ストリーク＆身代わり機能！）
    # ==========================================
    if "おはよう" in text:
        today_date = datetime.now(pytz.timezone("Asia/Tokyo")).date()
        today_str = today_date.strftime("%Y-%m-%d")
        last_login_str = user_data.get("last_login")

        # 今日まだ挨拶してない場合
        if last_login_str != today_str:

            # ストリーク（連続日数）の計算
            streak_message = ""
            new_streak = 1  # デフォルトは1日目に戻る

            if last_login_str:
                last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
                delta = (today_date - last_login_date).days

                if delta == 1:
                    # 昨日もやっている（継続成功！）
                    new_streak = current_streak + 1
                    streak_message = f"\n🔥 {new_streak}日連続早起き中！すごい！"
                elif delta > 1:
                    # 1日以上空いてしまった...
                    # 🧸 身代わり人形チェック！
                    if "substitute_doll" in my_items:
                        # 人形を使う！
                        my_items.remove("substitute_doll")
                        new_streak = current_streak + 1  # 継続！
                        streak_message = f"\n🧸 身代わり人形が身代わりになりました！\n連続記録({new_streak}日)は守られた！"
                        # DBのアイテムリストも更新が必要なので後で保存
                    else:
                        # 人形がない...リセット
                        new_streak = 1
                        streak_message = "\n😢 連続記録が途切れちゃいました...\nまた今日から頑張りましょう！"
            else:
                # 初めての挨拶
                streak_message = "\n今日から早起きチャレンジスタート！"

            # データを更新
            new_carrot_count = user_data["carrot_count"] + 1
            doc_ref.update(
                {
                    "carrot_count": new_carrot_count,
                    "last_login": today_str,
                    "current_streak": new_streak,
                    "items": my_items,  # 人形を使ったかもしれないので保存
                }
            )

            reply_content.append(
                TextSendMessage(
                    text=f"おはようございます！☀️\n早起きのご褒美の人参です！🥕{streak_message}"
                )
            )
        else:
            reply_content.append(
                TextSendMessage(text="今日はもう人参あげましたよ！また明日ね🥕")
            )

    # ==========================================
    # 🛍️ ショップ機能（人形を追加！）
    # ==========================================
    elif text == "ショップ":
        shop_carousel = {
            "type": "carousel",
            "contents": [
                # 🧸 身代わり人形（New!）
                {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://cdn-icons-png.flaticon.com/512/3769/3769037.png",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "fit",
                        "backgroundColor": "#ffffff",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "身代わり人形",
                                "weight": "bold",
                                "size": "xl",
                            },
                            {
                                "type": "text",
                                "text": "早起き失敗しても安心！\n1回だけ記録を守ってくれるよ🧸",
                                "wrap": True,
                                "size": "sm",
                                "color": "#666666",
                            },
                        ],
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#FF9933",
                                "action": {
                                    "type": "message",
                                    "label": "5人参で買う",
                                    "text": "身代わり人形を買う",
                                },
                            }
                        ],
                    },
                },
                # サングラス
                {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://cdn-icons-png.flaticon.com/512/1169/1169992.png",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "fit",
                        "backgroundColor": "#ffffff",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "イケてるサングラス",
                                "weight": "bold",
                                "size": "xl",
                            },
                            {
                                "type": "text",
                                "text": "10人参で買う",
                                "size": "sm",
                                "color": "#666666",
                            },
                        ],
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#FF9933",
                                "action": {
                                    "type": "message",
                                    "label": "10人参で買う",
                                    "text": "サングラスを買う",
                                },
                            }
                        ],
                    },
                },
                # ピンク染め粉
                {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://cdn-icons-png.flaticon.com/512/2919/2919740.png",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "fit",
                        "backgroundColor": "#ffffff",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "魔法のピンク染め粉",
                                "weight": "bold",
                                "size": "xl",
                            },
                            {
                                "type": "text",
                                "text": "20人参で買う",
                                "size": "sm",
                                "color": "#666666",
                            },
                        ],
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#FF9933",
                                "action": {
                                    "type": "message",
                                    "label": "20人参で買う",
                                    "text": "ピンク染め粉を買う",
                                },
                            }
                        ],
                    },
                },
            ],
        }
        reply_content.append(
            FlexSendMessage(alt_text="月面コンビニ", contents=shop_carousel)
        )

    # ==========================================
    # 🛒 レジ打ち処理（人形を追加！）
    # ==========================================
    elif text == "身代わり人形を買う":
        if "substitute_doll" in my_items:
            reply_content.append(
                TextSendMessage(
                    text="もう一つ持ってますよ！\n保険は1つあれば十分です🧸"
                )
            )
        elif user_data["carrot_count"] >= 5:
            new_carrot_count = user_data["carrot_count"] - 5
            my_items.append("substitute_doll")
            doc_ref.update({"carrot_count": new_carrot_count, "items": my_items})

            # 👇 ここの先頭に「f」を付けました！
            reply_content.append(
                TextSendMessage(
                    text=f"まいどあり！🧸\nこれで寝坊しても安心ですね！\n(残り人参: {new_carrot_count}本)"
                )
            )
        else:
            reply_content.append(TextSendMessage(text="人参が足りませんっ！🐰💦"))

    elif text == "サングラスを買う":
        if "sunglasses" in my_items:
            reply_content.append(
                TextSendMessage(
                    text="もう持ってますよ！\n「サングラス装着」と送ってみてね🕶️"
                )
            )
        elif user_data["carrot_count"] >= 10:
            new_carrot_count = user_data["carrot_count"] - 10
            my_items.append("sunglasses")
            doc_ref.update({"carrot_count": new_carrot_count, "items": my_items})
            reply_content.append(
                TextSendMessage(
                    text="まいどあり！🕶️\n「サングラス装着」と送ると着替えるよ！"
                )
            )
        else:
            reply_content.append(TextSendMessage(text="人参が足りませんっ！🐰💦"))

    elif text == "ピンク染め粉を買う":
        if "pink_dye" in my_items:
            reply_content.append(
                TextSendMessage(
                    text="もう持ってますよ！\n「ピンクに変身」と送ってみてね🎀"
                )
            )
        elif user_data["carrot_count"] >= 20:
            new_carrot_count = user_data["carrot_count"] - 20
            my_items.append("pink_dye")
            doc_ref.update({"carrot_count": new_carrot_count, "items": my_items})
            reply_content.append(
                TextSendMessage(
                    text="まいどあり！🎨\n「ピンクに変身」と送ると着替えるよ！"
                )
            )
        else:
            reply_content.append(TextSendMessage(text="人参が足りませんっ！🐰💦"))

    # ==========================================
    # 🪄 お着替えコマンド
    # ==========================================
    elif text == "ピンクに変身":
        if "pink_dye" in my_items:
            doc_ref.update({"current_look": "pink"})
            reply_content.append(
                TextSendMessage(text="✨キラキラ〜✨\nピンク色に変身しました！🐰🎀")
            )
        else:
            reply_content.append(TextSendMessage(text="まだ染め粉を持ってないよ！"))

    elif text == "サングラス装着":
        if "sunglasses" in my_items:
            doc_ref.update({"current_look": "sunglasses"})
            reply_content.append(
                TextSendMessage(text="シャキーン！😎\nサングラスをかけました！")
            )
        else:
            reply_content.append(TextSendMessage(text="まだサングラスを持ってないよ！"))

    elif text == "元に戻す":
        doc_ref.update({"current_look": "normal"})
        reply_content.append(TextSendMessage(text="ポンッ💨\n元の姿に戻りました！🐰"))
    # ... (元に戻す処理のあと) ...

    # 💤 おやすみ処理（月の満ち欠けを表示！）
    elif "おやすみ" in text:
        # さっきの計算機を使う
        moon_emoji = get_moon_info()

        reply_content.append(
            TextSendMessage(
                text=f"おやすみなさいだうさ〜🐰💤\n\n今日の月は【 {moon_emoji} 】だぴょん！\nゆっくり休んでね✨"
            )
        )

    # ... (このあとに else: Geminiとおしゃべり が続きます) ...
    # ==========================================
    # 💬 会員証表示（ストリークも表示！）
    # ==========================================
    elif text == "会員証":  # 👈 「会員証」と言われた時だけ出す！
        # ⚠️ ここにあなたの画像のURLを入れてください！
        url_normal = (
            "https://storage.googleapis.com/rabbit-bot-images/1763963316554.png"
        )
        url_sunglasses = "https://storage.googleapis.com/rabbit-bot-images/1763962242709.png"  # 本当はサングラス画像URL
        url_pink = "https://storage.googleapis.com/rabbit-bot-images/1763963253084.png"  # 本当はピンク画像URL

        display_image = url_normal
        status_text = "ノーマル"

        if current_look == "sunglasses":
            display_image = url_sunglasses
            status_text = "サングラス装着中 😎"
        elif current_look == "pink":
            display_image = url_pink
            status_text = "ピンクに変身中 🎀"

        # 身代わり人形を持ってるかチェック
        doll_status = "なし"
        if "substitute_doll" in my_items:
            doll_status = "あり 🧸"

        status_card = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": display_image,
                "size": "full",
                "aspectRatio": "1:1",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "月うさぎ会員証 🌕",
                        "weight": "bold",
                        "size": "xl",
                    },
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"🥕 所持人参: {user_data['carrot_count']} 本",
                                "size": "sm",
                                "color": "#666666",
                            },
                            {
                                "type": "text",
                                "text": f"🔥 連続記録: {current_streak} 日",
                                "size": "sm",
                                "color": "#666666",
                            },
                            {
                                "type": "text",
                                "text": f"🧸 身代わり人形: {doll_status}",
                                "size": "sm",
                                "color": "#666666",
                            },
                            {
                                "type": "text",
                                "text": f"状態: {status_text}",
                                "size": "sm",
                                "color": "#aaaaaa",
                                "margin": "sm",
                            },
                        ],
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#FF9933",
                        "action": {
                            "type": "message",
                            "label": "ショップを見る",
                            "text": "ショップ",
                        },
                    }
                ],
            },
        }
        reply_content.append(FlexSendMessage(alt_text="会員証", contents=status_card))

    # 🗣️ Geminiとおしゃべり（それ以外の言葉全部！）
    else:
        try:
            # Geminiにチャット履歴（文脈）は渡さず、一問一答で返します（節約のため）
            response = model.generate_content(text)
            reply_text = response.text

            # Geminiの返事をLINEで返す
            reply_content.append(TextSendMessage(text=reply_text))
        except Exception as e:
            # エラーが起きたらとりあえずニコニコしておく
            print(f"Gemini Error: {e}")
            reply_content.append(
                TextSendMessage(text="月との通信が混み合ってるぴょん...🌕💦")
            )

    # 最後にまとめて返信
    if reply_content:
        line_bot_api.reply_message(event.reply_token, reply_content)
