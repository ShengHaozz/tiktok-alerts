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

        self.application = ApplicationBuilder().token(self._token).build()

        handlers = []

        handlers.append(CommandHandler("test", self._test))
        handlers.append(CommandHandler("sub", self._subscribe))
        handlers.append(CommandHandler("unsub", self._unsubscribe))
        handlers.append(CommandHandler("check_sub", self._check_subscription))

        self.application.add_handlers(handlers)

    async def _send_message(
        self,
        chat_id: int,
        message: str,
    ):
        bot = self.application.bot
        await bot.send_message(chat_id=chat_id, text=message)

    async def _test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message

        output_message = f"{user.username} sent {message.text} in {'private chat' if chat.type == Chat.PRIVATE else chat.title}"
        self.logger.info(output_message)
        await self._send_message(user.id, output_message)

    async def _subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat

        if user.id in self.subscribers:
            output_message = f"@{user.username} already subscribed"
        else:
            self.subscribers[user.id] = f"@{user.username}"
            output_message = f"@{user.username} subscribed"
        self.logger.info(output_message)
        await self._send_message(chat.id, output_message)

    async def _unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat

        if user.id in self.subscribers:
            self.subscribers.pop(user.id)
            output_message = f"@{user.username} unsubscribed"
        else:
            output_message = f"@{user.username} not subscribed"
        self.logger.info(output_message)
        await self._send_message(chat.id, output_message)

    async def _check_subscription(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        chat = update.effective_chat
        await self._send_message(chat.id, "\n".join(self.subscribers.values()))

    async def broadcast(self, message):
        await asyncio.gather(*[self._send_message(id, message) for id in self.subscribers.keys()])

    def run(self):
        self.application.run_polling()

    def stop(self):
        self.application.stop_running()
