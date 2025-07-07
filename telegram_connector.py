import logging
import asyncio

from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


class TelegramConnector:
    def __init__(self, api_token, tick_duration=5):
        self._token = api_token
        self.subscribers = {}  # stores user.id: user.username
        self.logger = logging.getLogger(__name__)
        self.tick_duration = tick_duration

    async def _test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message

        output_message = f"{user.username} sent {message.text} in {'private chat' if chat.type == Chat.PRIVATE else chat.title}"
        self.logger.info(output_message)
        await context.bot.send_message(chat_id=user.id, text=output_message)

    async def _subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat

        if user.id in self.subscribers:
            output_message = f"@{user.username} already subscribed"
        else:
            self.subscribers[user.id] = f"@{user.username}"
            output_message = f"@{user.username} subscribed"
        self.logger.info(output_message)
        await context.bot.send_message(chat_id=chat.id, text=output_message)

    async def _unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat

        if user.id in self.subscribers:
            self.subscribers.pop(user.id)
            output_message = f"@{user.username} unsubscribed"
        else:
            output_message = f"@{user.username} not subscribed"
        self.logger.info(output_message)
        await context.bot.send_message(chat_id=chat.id, text=output_message)

    async def _check_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        await context.bot.send_message(chat_id=chat.id, text=list(self.subscribers.values()))


    async def _tick(self, context: ContextTypes.DEFAULT_TYPE):
        subscribers_id = self.subscribers.keys()
        await asyncio.gather(
            *[
                context.bot.send_message(chat_id=user_id, text="tick")
                for user_id in subscribers_id
            ]
        )

    def run(self):
        application = ApplicationBuilder().token(self._token).build()

        handlers = []

        handlers.append(CommandHandler("test", self._test))
        handlers.append(CommandHandler("sub", self._subscribe))
        handlers.append(CommandHandler("unsub", self._unsubscribe))
        handlers.append(CommandHandler("check_sub", self._check_subscription))

        application.add_handlers(handlers)
        application.job_queue.run_repeating(self._tick, self.tick_duration, name="ticker")

        application.run_polling()
