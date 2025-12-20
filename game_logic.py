import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pytz
import google.generativeai as genai
from config import GEMINI_API_KEY, RABBIT_SYSTEM_INSTRUCTION

# --- Core Logic & Database ---
# Gemini Model (Lazy loaded)
model = None

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
    base_date = datetime(2023, 1, 22, tzinfo=pytz.timezone("Asia/Tokyo"))
    current_date = datetime.now(pytz.timezone("Asia/Tokyo"))

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
    user_data, doc_ref = get_or_create_user(user_id)

    today_date = datetime.now(pytz.timezone("Asia/Tokyo")).date()
    today_str = today_date.strftime("%Y-%m-%d")
    last_login_str = user_data.get("last_login")

    # If already logged in today
    if last_login_str == today_str:
        return "今日はもう人参あげましたよ！また明日ね🥕"

    # Calculate streak
    current_streak = user_data.get("current_streak", 0)
    my_items = user_data.get("items", [])
    new_streak = 1
    streak_message = ""

    if last_login_str:
        last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
        delta = (today_date - last_login_date).days

        if delta == 1:
            # Consecutive login
            new_streak = current_streak + 1
            streak_message = f"\n🔥 {new_streak}日連続早起き中！すごい！"
        elif delta > 1:
            # Streak broken, check for doll
            if "substitute_doll" in my_items:
                my_items.remove("substitute_doll")
                new_streak = current_streak + 1
                streak_message = f"\n🧸 身代わり人形が身代わりになりました！\n連続記録({new_streak}日)は守られた！"
            else:
                new_streak = 1
                streak_message = "\n😢 連続記録が途切れちゃいました...\nまた今日から頑張りましょう！"
    else:
        streak_message = "\n今日から早起きチャレンジスタート！"

    # Update DB
    new_carrot_count = user_data.get("carrot_count", 0) + 1
    doc_ref.update({
        "carrot_count": new_carrot_count,
        "last_login": today_str,
        "current_streak": new_streak,
        "items": my_items
    })

    return f"おはようございます！☀️\n早起きのご褒美の人参です！🥕{streak_message}"

def process_purchase(user_id, item_key, price, item_name):
    """Generic logic for purchasing an item."""
    user_data, doc_ref = get_or_create_user(user_id)
    my_items = user_data.get("items", [])
    carrot_count = user_data.get("carrot_count", 0)

    if item_key in my_items:
        # Check if single-item policy applies (it does for all current items)
        if item_key == "substitute_doll":
             return "もう一つ持ってますよ！\n保険は1つあれば十分です🧸"
        return f"もう持ってますよ！\nアイテムを使うにはコマンドを送ってね。"

    if carrot_count < price:
        return "人参が足りませんっ！🐰💦"

    # Execute purchase
    new_carrot_count = carrot_count - price
    my_items.append(item_key)
    doc_ref.update({"carrot_count": new_carrot_count, "items": my_items})

    return f"まいどあり！{item_name}をお買い上げ！\n(残り人参: {new_carrot_count}本)"

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
