import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LINE Bot Settings
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

# Google Gemini Settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Persona Settings
RABBIT_SYSTEM_INSTRUCTION = """
あなたは月に住んでいる不思議なうさぎです。
語尾に「ぴょん」や「だうさ」をつけて話します。
性格は優しくて、少し丁寧です。
ユーザーは地球に住んでいるあなたの飼い主です。
短めの文章で、絵文字を使って可愛く返事をしてください。
"""

# Image Assets
IMAGE_URLS = {
    "normal": "https://storage.googleapis.com/rabbit-bot-images/1763963316554.png",
    "sunglasses": "https://storage.googleapis.com/rabbit-bot-images/1763962242709.png",
    "pink": "https://storage.googleapis.com/rabbit-bot-images/1763963253084.png",
    "shop_doll": "https://cdn-icons-png.flaticon.com/512/3769/3769037.png",
    "shop_sunglasses": "https://cdn-icons-png.flaticon.com/512/1169/1169992.png",
    "shop_dye": "https://cdn-icons-png.flaticon.com/512/2919/2919740.png"
}
