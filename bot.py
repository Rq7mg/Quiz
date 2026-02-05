import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

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
# Chat bazlı sorular ve skor
# -----------------------
CURRENT_QUESTIONS = {}  # chat_id -> {"answer": "C", "answered_users": set()}
USER_SCORES = {}        # user_id -> score

# -----------------------
# /start
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Quiz Bot hazır!\n\n"
        "Komutlar:\n"
        ".quiz → Rastgele soru başlatır\n"
        "Sorulara cevabı mesaj olarak yazın (A,B,C,D veya 1,2,3,4)\n"
        ".add → Admin için soru ekleme\n"
        ".score → Puanınızı gösterir"
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

        # Chat bazında doğru cevabı ve cevap veren kullanıcıları sakla
        CURRENT_QUESTIONS[update.message.chat_id] = {
            "answer": soru["answer"].strip().lower(),
            "answered_users": set()
        }

# -----------------------
# Kullanıcı cevabını kontrol et
# -----------------------
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    text = update.message.text.strip().lower()

    if chat_id not in CURRENT_QUESTIONS:
        return  # Bu chat’te soru yok

    soru_data = CURRENT_QUESTIONS[chat_id]

    # Daha önce cevap vermiş mi?
    if user_id in soru_data["answered_users"]:
        return  # Tek cevap hakkı

    # Cevabı kontrol et
    correct_answer = soru_data["answer"]
    if text == correct_answer or text == str(ord(correct_answer.lower()) - 96):  # A->1, B->2
        # Puan ver
        USER_SCORES[user_id] = USER_SCORES.get(user_id, 0) + 1
        await update.message.reply_text(f"✅ Doğru! Puanın: {USER_SCORES[user_id]}")
    else:
        await update.message.reply_text(f"❌ Yanlış! Doğru cevap: {correct_answer.upper()}")

    # Kullanıcıyı işaretle
    soru_data["answered_users"].add(user_id)

    # Eğer tüm kullanıcılar cevapladıysa veya istenirse soruyu silebiliriz
    # CURRENT_QUESTIONS.pop(chat_id)  # opsiyonel: soruyu sil

# -----------------------
# .score komutu
# -----------------------
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    score = USER_SCORES.get(user_id, 0)
    await update.message.reply_text(f"📊 Puanınız: {score}")

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

    from telegram.ext import CommandHandler, MessageHandler, filters

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer))
    app.add_handler(MessageHandler(filters.Regex(r"^\.score$"), score))  # .score komutu

    print("Bot başlatıldı...")
    app.run_polling()

# -----------------------
# Entry
# -----------------------
if __name__ == "__main__":
    main()
