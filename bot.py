import os
import json
import random
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)

TOKEN = os.environ.get("TOKEN")
ADMIN_IDS = [6563936773, 6030484208]

QUESTION_TIME = 20
QUESTIONS_FILE = "questions.json"

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

GAMES = {}      # chat_id -> game
SCORES = {}     # chat_id -> {user_id: score}
USERNAMES = {}  # user_id -> username


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Süreli Quiz Botu\n\n"
        "Admin:\n"
        ".quiz → Oyunu başlat\n"
        ".son → Oyunu bitir\n\n"
        "Cevap:\n"
        "A/B/C/D veya 1/2/3/4\n"
        "⏱ Süre: 20 saniye\n\n"
        "ℹ️ Sonuçlar süre bitince açıklanır"
    )


# ---------- QUIZ CORE ----------
async def send_question(chat_id, context):
    q = random.choice(QUESTIONS)

    question_text = f"❓ {q['question']}\n\n"
    for i, opt in enumerate(q["options"], 1):
        question_text += f"{i}. {opt}\n"

    await context.bot.send_message(chat_id, question_text)

    GAMES[chat_id] = {
        "answer": q["answer"].lower().strip(),
        "answers": {},      # user_id -> answer
        "correct": set()
    }

    await asyncio.sleep(QUESTION_TIME)

    game = GAMES.get(chat_id)
    if not game:
        return

    for uid, ans in game["answers"].items():
        if ans == game["answer"]:
            game["correct"].add(uid)
            SCORES.setdefault(chat_id, {})
            SCORES[chat_id][uid] = SCORES[chat_id].get(uid, 0) + 1

    if game["correct"]:
        users = "\n".join(
            f"@{USERNAMES.get(uid, uid)}"
            for uid in game["correct"]
        )
        result_text = (
            f"⏰ Süre doldu!\n"
            f"✅ Doğru cevap: {game['answer'].upper()}\n\n"
            f"🎉 Doğru bilenler:\n{users}"
        )
    else:
        result_text = (
            f"⏰ Süre doldu!\n"
            f"✅ Doğru cevap: {game['answer'].upper()}\n\n"
            f"❌ Kimse doğru bilemedi."
        )

    await context.bot.send_message(chat_id, result_text)

    if chat_id in GAMES:
        await send_question(chat_id, context)


# ---------- MESSAGE HANDLER ----------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat_id
    user = update.message.from_user
    user_id = user.id
    text = update.message.text.strip().lower()

    USERNAMES[user_id] = user.username or f"user{user_id}"

    # ADMIN: QUIZ BAŞLAT
    if text == ".quiz" and user_id in ADMIN_IDS:
        if chat_id in GAMES:
            return
        await context.bot.send_message(chat_id, "🎮 Quiz başladı!")
        await send_question(chat_id, context)
        return

    # ADMIN: SON
    if text == ".son" and user_id in ADMIN_IDS:
        if chat_id not in GAMES:
            return

        del GAMES[chat_id]

        scores = SCORES.get(chat_id, {})
        if not scores:
            await context.bot.send_message(chat_id, "🛑 Oyun bitti.\nKimse puan alamadı.")
            return

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        msg = "🏆 Leaderboard\n\n"
        for i, (uid, score) in enumerate(sorted_scores[:10], 1):
            msg += f"{i}. @{USERNAMES.get(uid, uid)} — {score} puan\n"

        await context.bot.send_message(chat_id, msg)
        return

    # CEVAPLAR
    if chat_id not in GAMES:
        return

    game = GAMES[chat_id]

    # Aynı soruya ikinci cevap yok
    if user_id in game["answers"]:
        await update.message.reply_text("⛔ Bu soruya zaten cevap verdin.")
        return

    convert = {"1": "a", "2": "b", "3": "c", "4": "d"}
    if text in convert:
        text = convert[text]

    if text not in ["a", "b", "c", "d"]:
        return

    game["answers"][user_id] = text

    # Emoji / geri bildirim (sonuç yok)
    await update.message.reply_text("🕐 Cevabın alındı.")


# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 Quiz bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
