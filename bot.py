
import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")

quiz_state = {}

# -------------------------
# Soru havuzu
# -------------------------
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# -------------------------
# /quiz başlat
# -------------------------
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    question = random.choice(QUESTIONS)
    quiz_state[user_id] = {"question": question, "score": quiz_state.get(user_id, {}).get("score", 0)}

    buttons = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in question["options"]]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(f"❓ {question['question']}", reply_markup=reply_markup)

# -------------------------
# Buton callback
# -------------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in quiz_state:
        await query.edit_message_text("❌ Quiz başlamadı. `.quiz` komutu ile başlat.")
        return

    correct_answer = quiz_state[user_id]["question"]["answer"]

    if query.data == correct_answer:
        quiz_state[user_id]["score"] += 1
        text = f"✅ Doğru! Puanın: {quiz_state[user_id]['score']}"
    else:
        text = f"❌ Yanlış! Doğru cevap: {correct_answer}\nPuanın: {quiz_state[user_id]['score']}"

    await query.edit_message_text(text)

# -------------------------
# /score
# -------------------------
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    score = quiz_state.get(user_id, {}).get("score", 0)
    await update.message.reply_text(f"📊 Puanın: {score}")

# -------------------------
# /stopquiz
# -------------------------
async def stopquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in quiz_state:
        quiz_state.pop(user_id)
        await update.message.reply_text("⛔ Quiz durduruldu")
    else:
        await update.message.reply_text("❌ Önce quiz başlatmalısın")

# -------------------------
# MAIN
# -------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("stopquiz", stopquiz))

    print("Quiz bot başlatıldı...")
    app.run_polling()

if __name__ == "__main__":
    main()
