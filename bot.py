import os
import json
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

TOKEN = os.environ.get("TOKEN")
QUESTIONS_FILE = "questions.json"

def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

QUESTIONS = load_questions()

CURRENT_QUESTIONS = {}   # chat_id -> {answer, answered}
USER_SCORES = {}         # user_id -> score
USER_NAMES = {}          # user_id -> name


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 Quiz Bot\n\n"
        ".quiz → Rastgele soru\n"
        "Cevap: A/B/C/D veya 1/2/3/4\n"
        ".score → Kendi puanın\n"
        ".leaderboard → En iyiler"
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat_id
    user = update.message.from_user
    user_id = user.id

    USER_NAMES[user_id] = user.username or f"User {user_id}"

    # Quiz
    if text.lower() == ".quiz":
        q = random.choice(QUESTIONS)

        msg = f"❓ {q['question']}\n\n"
        for i, opt in enumerate(q["options"], 1):
            msg += f"{i}. {opt}\n"

        await update.message.reply_text(msg)

        CURRENT_QUESTIONS[chat_id] = {
            "answer": q["answer"].lower(),
            "answered": set()
        }
        return

    # Score
    if text.lower() == ".score":
        score = USER_SCORES.get(user_id, 0)
        await update.message.reply_text(f"📊 Puanın: {score}")
        return

    # Leaderboard
    if text.lower() == ".leaderboard":
        if not USER_SCORES:
            await update.message.reply_text("Henüz skor yok.")
            return

        sorted_scores = sorted(
            USER_SCORES.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        msg = "🏆 Leaderboard\n\n"
        for i, (uid, score) in enumerate(sorted_scores, 1):
            name = USER_NAMES.get(uid, f"User {uid}")
            msg += f"{i}. @{name} — {score} puan\n"

        await update.message.reply_text(msg)
        return

    # Cevap kontrolü
    if chat_id not in CURRENT_QUESTIONS:
        return

    q = CURRENT_QUESTIONS[chat_id]

    if user_id in q["answered"]:
        return

    ans = text.lower()
    convert = {"1": "a", "2": "b", "3": "c", "4": "d"}
    if ans in convert:
        ans = convert[ans]

    if ans == q["answer"]:
        USER_SCORES[user_id] = USER_SCORES.get(user_id, 0) + 1
        await update.message.reply_text("✅ Doğru!")
    else:
        await update.message.reply_text(f"❌ Yanlış! Doğru cevap: {q['answer'].upper()}")

    q["answered"].add(user_id)


def main():
    if not TOKEN:
        print("TOKEN bulunamadı!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
