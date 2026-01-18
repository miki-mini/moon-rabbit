![Rabbit Bot](https://img.shields.io/badge/Concept-Virtual_Pet_Rabbit-FF69B4?style=for-the-badge&logo=target)
![Moon Phase](https://img.shields.io/badge/Feature-Moon_Phase_Sync-4B0082?style=for-the-badge&logo=nasa)
![Gemini](https://img.shields.io/badge/AI-Gemini_Powered-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)

🌕 月うさぎからのおくりもの 🥕 (Moon Rabbit Bot)

毎朝の早起きを楽しく習慣化するための、LINEボット形式の育成ゲーム・コミュニケーションアプリです。
ユーザーは月うさぎの「飼い主」となり、毎日の挨拶を通じて通貨（人参）を集め、アイテム購入や着せ替えを楽しむことができます。

📱 概要 (Features)

ただの会話ボットではなく、**「データベースによるステータス管理」** と **「生成AIによる動的な会話」** を組み合わせた、ゲーム性の高いアプリケーションです。

🐰 主な機能
1.  **早起きストリーク（継続）機能**
    * 毎朝「おはよう」と挨拶することで、通貨（人参）を獲得。
    * 連続ログイン日数（ストリーク）をFirestoreで管理し、継続を応援。
2.  **月面コンビニ（ショップ機能）**
    * 貯めた人参を消費してアイテム（サングラス、染め粉、身代わり人形）を購入可能。
    * LINE Flex Messageを使用したカルーセルUIによる商品棚の実装。
3.  **着せ替えシステム**
    * 購入したアイテムに応じて、「会員証」に表示されるうさぎの画像が変化。
    * データベース上の所持品ステータスと連携した動的なUI変更。
4.  **身代わり人形（救済ロジック）**
    * ログインが途切れても、アイテムを消費して連続記録を自動で守るロジックを実装。
5.  **リアルタイム月齢計算**
    * 「おやすみ」の挨拶に対し、Pythonで現在時刻から月齢（満月・三日月など）を計算し、実際の空と同じ月を表示。
6.  **AIうさぎとの会話**
    * Google Gemini APIを活用し、特定のコマンド以外は「月のうさぎ」というペルソナ（人格）で自然な雑談が可能。

🛠️ 技術スタック (Tech Stack)

モダンなサーバーレスアーキテクチャを採用し、スケーラビリティと運用コストの最適化を図っています。

* **Language:** Python 3.11+
* **Framework:** FastAPI
* **Infrastructure:** Google Cloud Run (Serverless)
* **Database:** Google Cloud Firestore (NoSQL)
* **Storage:** Google Cloud Storage (画像ホスティング)
* **AI Model:** Google Gemini API (gemini-2.5-flash)
* **Interface:** LINE Messaging API (Flex Message)
* **Library:** firebase-admin, line-bot-sdk, pytz

## 🏗️ アーキテクチャ (Architecture)

```mermaid
graph TD
    User((User)) -- LINE App --> LINE_Platform
    LINE_Platform -- Webhook --> Cloud_Run["Google Cloud Run<br>(FastAPI / Python)"]

    subgraph Google Cloud
        Cloud_Run -- Read/Write --> Firestore[("Firestore<br>User Data")]
        Cloud_Run -- Chat --> Gemini[Gemini API]
        Cloud_Run -- Get Image --> GCS[Cloud Storage]
    end
```

💡 こだわったポイント

* **ステータス管理の厳密さ:**
    * 「人参が足りない時は買えない」「既に持っているアイテムは二重購入させない」といった条件分岐を実装し、データの整合性を保っています。
* **UX（ユーザー体験）の向上:**
    * テキストだけでなく、Flex Messageを活用して視覚的に楽しめる「会員証」や「ショップ」を作成しました。
* **ハイブリッドな応答システム:**
    * 「コマンド（ショップ、会員証）」と「AIによる自由会話」を共存させ、実用性とエンターテイメント性を両立させました。
* **セキュリティ:**
    * APIキーなどの機密情報は環境変数（Environment Variables）で管理し、コード上には一切ハードコーディングしていません。

📸 スクリーンショット

| 会員証 | ショップ画面 |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/3815b7eb-3955-40bc-bd1e-1e88ecc63973" width="200"> | <img src="https://github.com/user-attachments/assets/3861ef35-3a60-4626-8f2f-bf32fe6ed1bf" width="200"> |

🚀 今後の展望
* ユーザーランキング機能の実装
* レベルアップ機能の実装
* 季節限定アイテムの追加
---

English Summary

Concept: An interactive virtual pet bot that combines gamified daily routines with real-world environmental sync (moon phases).

Features: Includes a Daily Streak system for morning greetings, a shop for character customization, and AI-driven chat powered by Gemini.

Development: Developed with a focus on user engagement and state management using FastAPI and Firebase.

---
Created by miki-mini