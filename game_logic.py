import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import datetime
import google.generativeai as genai
from config import GEMINI_API_KEY, RABBIT_SYSTEM_INSTRUCTION
from firebase_admin import firestore

# --- Core Logic & Database ---
# Gemini Model (Lazy loaded)
model = None

def get_now_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo"))



def get_model():
    global model
    if model is None:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=RABBIT_SYSTEM_INSTRUCTION,
        )
    return model

# Initialize Firestore safely
db = None

def init_db():
    global db
    if db is None:
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    return db

# We will call init_db() inside functions, or at the bottom if not testing.
# For backward compatibility with the functions I wrote, I'll update get_or_create_user to call init_db()


def get_moon_info():
    """Calculate the current moon phase emoji."""
    base_date = datetime(2023, 1, 22, tzinfo=ZoneInfo("Asia/Tokyo"))

# 2. 現在時刻を取得する場合
    current_date = datetime.now(ZoneInfo("Asia/Tokyo"))

    diff = current_date - base_date
    days = diff.days + (diff.seconds / 86400)
    moon_age = days % 29.53059

    if moon_age < 1 or moon_age > 28.5:
        return "🌑 (新月)"
    elif moon_age < 6:
        return "🌒 (三日月)"
    elif moon_age < 9:
        return "🌓 (上弦の月)"
    elif moon_age < 14:
        return "🌔 (十三夜)"
    elif moon_age < 16:
        return "🌕 (満月)"
    elif moon_age < 20:
        return "🌖 (寝待月)"
    elif moon_age < 24:
        return "🌗 (下弦の月)"
    else:
        return "🌘 (有明月)"

def get_or_create_user(user_id):
    """Retrieve user data from Firestore or create a new profile if not exists."""
    db = init_db() # Ensure DB is valid
    doc_ref = db.collection("rabbit_gamers").document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict(), doc_ref
    else:
        initial_data = {
            "user_id": user_id,
            "carrot_count": 0,
            "moon_level": 1,
            "current_streak": 0,
            "last_login": None,
            "items": [],
            "current_look": "normal",
            "created_at": datetime.now(pytz.timezone("Asia/Tokyo")),
        }
        doc_ref.set(initial_data)
        return initial_data, doc_ref

def process_morning_greeting(user_id):
    """Refactored logic for 'Good Morning' streak processing."""
    db = init_db()
    doc_ref = db.collection("rabbit_gamers").document(user_id)
    transaction = db.transaction()

    today_date = current_date = get_now_jst()
    today_str = today_date.strftime("%Y-%m-%d")

    return _morning_greeting_transaction(transaction, doc_ref, today_str, today_date)

@firestore.transactional
def _morning_greeting_transaction(transaction, doc_ref, today_str, today_date):
    snapshot = doc_ref.get(transaction=transaction)

    if not snapshot.exists:
        # 初回ログイン時の処理
        initial_data = {
            "user_id": doc_ref.id,
            "carrot_count": 1,
            "moon_level": 1,
            "current_streak": 1,
            "last_login": today_str,
            "items": [],
            "current_look": "normal",
            "current_date" = get_now_jst(),
        }
        transaction.set(doc_ref, initial_data)
        return "今日から早起きチャレンジスタート！\n最初のご褒美の人参です！🥕"

    user_data = snapshot.to_dict()
    last_login_str = user_data.get("last_login")

    if last_login_str == today_str:
        return "今日はもう人参あげましたよ！また明日ね🥕"

    current_streak = user_data.get("current_streak", 0)
    my_items = user_data.get("items", [])
    new_streak = 1
    streak_message = ""

    if last_login_str:
        last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
        delta = (today_date - last_login_date).days

        if delta == 1:
            new_streak = current_streak + 1
            streak_message = f"\n🔥 {new_streak}日連続早起き中！すごい！"
        elif delta > 1:
            if "substitute_doll" in my_items:
                my_items.remove("substitute_doll")
                new_streak = current_streak + 1
                streak_message = f"\n🧸 身代わり人形が身代わりになりました！\n連続記録({new_streak}日)は守られた！"
            else:
                new_streak = 1
                streak_message = "\n😢 連続記録が途切れちゃいました...\nまた今日から頑張りましょう！"
    else:
        streak_message = "\n今日から早起きチャレンジスタート！"

    new_carrot_count = user_data.get("carrot_count", 0) + 1
    transaction.update(doc_ref, {
        "carrot_count": new_carrot_count,
        "last_login": today_str,
        "current_streak": new_streak,
        "items": my_items
    })

    return f"おはようございます！☀️\n早起きのご褒美の人参です！🥕{streak_message}"


@firestore.transactional
def _purchase_transaction_inner(transaction, doc_ref, item_key, price, item_name):
    # ①トランザクション（安全な箱）の中で最新のデータを取得
    snapshot = doc_ref.get(transaction=transaction)

    if not snapshot.exists:
        return "ユーザーデータが見つかりません。"

    user_data = snapshot.to_dict()
    my_items = user_data.get("items", [])
    carrot_count = user_data.get("carrot_count", 0)

    if item_key in my_items:
        # Check if single-item policy applies (it does for all current items)
        if item_key == "substitute_doll":
             return "もう一つ持ってますよ！\n保険は1つあれば十分です🧸"
        return f"もう持ってますよ！\nアイテムを使うにはコマンドを送ってね。"

    if carrot_count < price:
        return "人参が足りませんっ！🐰💦"

    # ②購入できたらデータを上書き
    new_carrot_count = carrot_count - price
    my_items.append(item_key)
    transaction.update(doc_ref, {
        "carrot_count": new_carrot_count,
        "items": my_items
    })

    return f"まいどあり！{item_name}をお買い上げ！\n(残り人参: {new_carrot_count}本)"

def process_purchase(user_id, item_key, price, item_name):
    """購入処理のエントリポイント"""
    db = init_db()

    # 買う前にユーザーデータが存在するか確認・作成しておく
    get_or_create_user(user_id)
    doc_ref = db.collection("rabbit_gamers").document(user_id)
    transaction = db.transaction()

    # 内側の関数を呼び出す
    return _purchase_transaction_inner(transaction, doc_ref, item_key, price, item_name)

def process_change_look(user_id, look_key, item_req, message_success, message_fail):
    """Generic logic for changing appearance."""
    user_data, doc_ref = get_or_create_user(user_id)
    my_items = user_data.get("items", [])

    if item_req and item_req not in my_items:
        return message_fail

    doc_ref.update({"current_look": look_key})
    return message_success

def get_gemini_reply(text):
    """Get a response from the Gemini API."""
    try:
        model_instance = get_model()
        response = model_instance.generate_content(text)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "月との通信が混み合ってるぴょん...🌕💦"
