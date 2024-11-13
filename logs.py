import logging
import traceback
import html
import json
import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import RetryAfter

from config import LOGS_CHANNEL_ID

message_queue = asyncio.Queue()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    await context.bot.send_message(
        chat_id=LOGS_CHANNEL_ID, text=message
    )

async def send_message_ratelimiter(chat_id, text, bot):
    await bot.send_message(chat_id=chat_id, text=text)

async def message_sender(bot):
    while True:
        chat_id, text = await message_queue.get()
        try:
            await send_message_ratelimiter(chat_id, text, bot)
        except RetryAfter as e:
            delay = e.retry_after  # Delay in seconds from the error message
            print(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
            await asyncio.sleep(delay)
            await send_message_ratelimiter(chat_id, text, bot)
        except Exception as e:
            logging.error(f"Unhandled error using custom rate limiter: {e}")
        await asyncio.sleep(1.5)

async def add_message_to_queue(chat_id, text):
    await message_queue.put((chat_id, text))