import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

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
# Tek handler: quiz, add, score, cevap
# -----------------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # .quiz komutu
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
        CURRENT_QUESTIONS[chat_id] = {
            "answer": soru["answer"].strip().lower(),
            "answered_users": set()
        }
        return

    # .add komutu
    if text.lower().startswith(".add"):
        try:
            content = text[4:].strip()
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
        return

    # .score komutu
    if text.lower() == ".score":
        score = USER_SCORES.get(user_id, 0)
        await update.message.reply_text(f"📊 Puanınız: {score}")
        return

    # Cevap kontrolü
    if chat_id in CURRENT_QUESTIONS:
        soru_data = CURRENT_QUESTIONS[chat_id]

        # Daha önce cevap vermiş mi?
        if user_id in soru_data["answered_users"]:
            return

        correct_answer = soru_data["answer"]

        # A->1, B->2, C->3, D->4 kontrolü
        mapping = {"a": "1", "b": "2", "c": "3", "d": "4"}
        user_text = text.lower()
        if user_text in mapping:
            user_text = mapping[user_text]

        if user_text == correct_answer.lower() or user_text == str(ord(correct_answer.lower()) - 96):
            USER_SCORES[user_id] = USER_SCORES.get(user_id, 0) + 1
            await update.message.reply_text(f"✅ Doğru! Puanınız: {USER_SCORES[user_id]}")
        else:
            await update.message.reply_text(f"❌ Yanlış! Doğru cevap: {correct_answer.upper()}")

        # Kullanıcıyı işaretle
        soru_data["answered_users"].add(user_id)
