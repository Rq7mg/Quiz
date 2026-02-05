import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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
        ".add <soru> | <A,B,C,D> | <cevap> | <zor/orta/kolay> → Admin için yeni soru ekleme"
    )

# -----------------------
# .quiz komutu
# -----------------------
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
# .add komutu (admin)
# -----------------------
async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    try:
        soru, opts, answer, difficulty = text.split("|")
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
# Ana fonksiyon
# -----------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("add", add_question))

    print("Bot başlatıldı...")
    app.run_polling()

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    main()
