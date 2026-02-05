import os
import json
import random
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("TOKEN")
ADMIN_IDS = [6563936773, 6030484208]  # kendi admin id'lerin

QUESTION_TIME = 20  # saniye
QUESTIONS_FILE = "questions.json"

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

GAMES = {}      # chat_id -> game state
SCORES = {}     # chat_id -> {user_id: score}
USERNAMES = {}  # user_id -> name


async def send_question(chat_id, context):
    q = random.choice(QUESTIONS)

    text = f"❓ {q['question']}\n\n"
    for i, opt in enumerate(q["options"], 1):
        text += f"{i}. {opt}\n"

    await context.bot.send_message(chat_id, text)

    GAMES[chat_id] = {
        "answer": q["answer"],
        "answers": {},  # user_id -> given answer
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
        msg = f"⏰ Süre doldu!\n✅ Doğru cevap: {game['answer'].upper()}\n\n🎉 Doğru bilenler:\n{users}"
    else:
        msg = f"⏰ Süre doldu!\n✅ Doğru cevap: {game['answer'].upper()}\n\n❌ Kimse doğru bilemedi."

    await context.bot.send_message(chat_id, msg)

    if chat_id in GAMES:
        await send_question(chat_id, context)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat_id
    user = update.message.from_user
    user_id = user.id
    text = update.message.text.strip().lower()

    USERNAMES[user_id] = user.username or f"user{user_id}"

    # ADMIN KOMUTLARI
    if text == ".quiz" and user_id in ADMIN_IDS:
        if chat_id in GAMES:
            return
        await context.bot.send_message(chat_id, "🎮 Quiz başladı!")
        await send_question(chat_id, context)
        return

    if text == ".son" and user_id in ADMIN_IDS:
        if chat_id not in GAMES:
            return

        del GAMES[chat_id]

        scores = SCORES.get(chat_id, {})
        if not scores:
            await context.bot.send_message(chat_id, "Oyun bitti.\nKimse puan alamadı.")
            return

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        msg = "🏆 Leaderboard\n\n"
        for i, (uid, score) in enumerate(sorted_scores[:10], 1):
            msg += f"{i}. @{USERNAMES.get(uid, uid)} — {score} puan\n"

        await context.bot.send_message(chat_id, msg)
        return

    # CEVAP KONTROLÜ
    if chat_id not in GAMES:
        return

    game = GAMES[chat_id]

    if user_id in game["answers"]:
        return

    convert = {"1": "a", "2": "b", "3": "c", "4": "d"}
    if text in convert:
        text = convert[text]

    if text not in ["a", "b", "c", "d"]:
        return

    game["answers"][user_id] = text


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    print("🤖 Quiz bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
