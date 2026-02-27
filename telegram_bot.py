# import requests
# import os
# from dotenv import load_dotenv
# from telegram import Update
# from telegram.ext import (
#      ApplicationBuilder,
#      CommandHandler,
#      MessageHandler,
#      ContextTypes,
#      filters
#  )

# load_dotenv()

# BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# API_URL = "http://127.0.0.1:8000/chat"

#  # /start command
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#      await update.message.reply_text(
#          "👋 Hi! I'm an AI chatbot.\n\nJust send me a message 😊"
#      )

#  # Handle normal messages
# async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
#      user_message = update.message.text

#      payload = {
#          "user_id": str(update.effective_user.id),
#          "message": user_message,
#          "mode": "fast"
#      }

#      try:
#          response = requests.post(API_URL, json=payload, timeout=60)
#          reply = response.json().get("reply", "⚠ Error from AI")

#      except Exception as e:
#          reply = "⚠ Backend server not responding."

#      await update.message.reply_text(reply)

# def main():
#      app = ApplicationBuilder().token(BOT_TOKEN).build()

#      app.add_handler(CommandHandler("start", start))
#      app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

#      print("🤖 Telegram bot is running...")
#      app.run_polling()

# if __name__ == "__main__":
#      main()
import requests
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/chat"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your AI assistant.\n\nSend me any message 😊"
    )

# Handle user messages
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    payload = {
        "message": user_message   # ✅ Only what backend needs
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=60)

        if response.status_code == 200:
            reply = response.json().get("reply", "⚠ AI returned empty response.")
        else:
            reply = "⚠ Backend error."

    except requests.exceptions.ConnectionError:
        reply = "⚠ Cannot connect to backend server."

    except Exception:
        reply = "⚠ Unexpected error."

    await update.message.reply_text(reply)

def main():
    if not BOT_TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🤖 Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()