import os
import logging

from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

API_TOKEN = os.getenv("RINGOBOT_API_TOKEN")

subscribers = {}  # stores user.id: user.username


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="logging.log",
)


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    output_message = f"{user.username} sent {message.text} in {'private chat' if chat.type == Chat.PRIVATE else chat.title}"

    await context.bot.send_message(chat_id=user.id, text=output_message)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if user.id in subscribers:
        output_message = f"@{user.username} already subscribed"
    else:
        subscribers[user.id] = f"@{user.username}" 
        output_message = f"@{user.username} subscribed"

    await context.bot.send_message(chat_id=chat.id, text=output_message)

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if user.id in subscribers:
        subscribers.pop(user.id)
        output_message = f"@{user.username} unsubscribed"
    else:
        output_message = f"@{user.username} not subscribed"

    await context.bot.send_message(chat_id=chat.id, text=output_message)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    await context.bot.send_message(chat_id=chat.id, text=list(subscribers.values()))

if __name__ == "__main__":
    application = ApplicationBuilder().token(API_TOKEN).build()

    handlers = []

    handlers.append(CommandHandler("test", test))
    handlers.append(CommandHandler("sub", subscribe))
    handlers.append(CommandHandler("unsub", unsubscribe))
    handlers.append(CommandHandler("check_sub", check_subscription))

    
    application.add_handlers(handlers)

    application.run_polling()
