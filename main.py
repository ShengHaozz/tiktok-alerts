import logging
import os
from telegram_connector import TelegramConnector
import threading
import time
import asyncio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    filename="logging.log",
)

API_TOKEN = os.getenv("RINGOBOT_API_TOKEN")

telegram_conn = TelegramConnector(API_TOKEN)
telegram_conn_thread = threading.Thread(target=telegram_conn.run)
telegram_conn_thread.start()

time.sleep(5)
telegram_conn.broadcast("5 seconds")
time.sleep(5)
telegram_conn.broadcast("10 seconds")


telegram_conn.stop()
