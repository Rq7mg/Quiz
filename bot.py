import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# -----------------------
# Ayarlar
# -----------------------
TOKEN = os.environ.get("TOKEN")
QUESTIONS_FILE = "questions.json"

# -----------------------
# Soruları yükle
# -----------------------
def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

QUESTIONS = load_questions()

# -----------------------
# /start komutu
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Quiz Bot hazır!\n\n"
        "Komutlar:\n"
        ".quiz → Rastgele soru başlat\n"
    )

# -----------------------
# .quiz komutu
# -----------------------
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.lower().startswith(".quiz"):
        if not QUESTIONS:
            await update.message.reply_text("⚠️ Quiz soruları yüklenemedi!")
            return
        soru = random.choice(QUESTIONS)
        options = soru["options"]
        msg = f"❓ {soru['question']}\n\n"
        for idx, opt in enumerate(options, 1):
            msg += f"{idx}. {opt}\n"
        await update.message.reply_text(msg)

# -----------------------
# .add komutu
# -----------------------
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.lower().startswith(".add"):
        try:
            content = text[4:].strip()  # .add kısmını at
            soru, opts, answer, difficulty = content.split("|")
            options = [o.strip() for o in opts.split(",")]
            soru_dict = {
                "question": soru.strip(),
                "options": options,
                "answer": answer.strip(),
                "difficulty": difficulty.strip()
            }
            QUESTIONS.append(soru_dict)
            with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(QUESTIONS, f, ensure_ascii=False, indent=2)
            await update.message.reply_text("✅ Soru eklendi!")
        except Exception:
            await update.message.reply_text(
                "❌ Hatalı format! Örnek:\n.add Soru | A,B,C,D | Cevap | zor"
            )

# -----------------------
# Main
# -----------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # /start komutu için MessageHandler yerine CommandHandler kullanabiliriz
    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("start", start))

    # .quiz ve .add komutlarını MessageHandler ile yakala
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_command))

    print("Bot başlatıldı...")
    app.run_polling()

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    main()
