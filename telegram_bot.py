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

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Local backend API
API_URL = "https://ai-socail-chatbot-86on.onrender.com/chat"

# -------------------------
# /start command
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "I'm your AI Assistant 🤖\n"
        "Send me any message and I will respond."
    )


# -------------------------
# Handle messages
# -------------------------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text

    payload = {
        "message": user_message
    }

    try:

        response = requests.post(API_URL, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            reply = data.get("reply", "⚠ AI returned empty response.")

        else:
            reply = "⚠ Backend returned an error."

    except requests.exceptions.ConnectionError:
        reply = "⚠ Cannot connect to AI server."

    except Exception as e:
        reply = f"⚠ Unexpected error: {str(e)}"

    await update.message.reply_text(reply)


# -------------------------
# Main bot function
# -------------------------
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
