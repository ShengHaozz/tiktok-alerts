import logging
import os
from telegram_connector import TelegramConnector

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    filename="logging.log"
)

API_TOKEN = os.getenv("RINGOBOT_API_TOKEN")

telegramConn = TelegramConnector(API_TOKEN)
telegramConn.run()