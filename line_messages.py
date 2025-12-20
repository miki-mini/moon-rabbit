from linebot.models import (
    FlexSendMessage,
    CarouselContainer,
    BubbleContainer,
    TextSendMessage,
    BoxComponent,
    ImageComponent,
    TextComponent,
    ButtonComponent
)
from config import IMAGE_URLS

def create_shop_message():
    """Create the shop carousel Flex Message."""
    shop_carousel = {
        "type": "carousel",
        "contents": [
            # Substitution Doll
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": IMAGE_URLS["shop_doll"],
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "fit",
                    "backgroundColor": "#ffffff",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "身代わり人形", "weight": "bold", "size": "xl"},
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
            # Sunglasses
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": IMAGE_URLS["shop_sunglasses"],
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "fit",
                    "backgroundColor": "#ffffff",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "イケてるサングラス", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "10人参で買う", "size": "sm", "color": "#666666"},
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
            # Pink Dye
            {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": IMAGE_URLS["shop_dye"],
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "fit",
                    "backgroundColor": "#ffffff",
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "魔法のピンク染め粉", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "20人参で買う", "size": "sm", "color": "#666666"},
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
    return FlexSendMessage(alt_text="月面コンビニ", contents=shop_carousel)


def create_member_card(user_data):
    """Create the member card Flex Message based on user data."""
    my_items = user_data.get("items", [])
    current_look = user_data.get("current_look", "normal")
    current_streak = user_data.get("current_streak", 0)
    carrot_count = user_data.get("carrot_count", 0)

    # Determine display image and status text
    display_image = IMAGE_URLS["normal"]
    status_text = "ノーマル"

    if current_look == "sunglasses":
        display_image = IMAGE_URLS["sunglasses"]
        status_text = "サングラス装着中 😎"
    elif current_look == "pink":
        display_image = IMAGE_URLS["pink"]
        status_text = "ピンクに変身中 🎀"

    # Check for substitute doll
    doll_status = "あり 🧸" if "substitute_doll" in my_items else "なし"

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
                            "text": f"🥕 所持人参: {carrot_count} 本",
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
    return FlexSendMessage(alt_text="会員証", contents=status_card)
