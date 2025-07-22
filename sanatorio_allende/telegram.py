import asyncio
import logging

import telegram

logger = logging.getLogger(__name__)


def send_message(message: str, token: str, chat_id: int) -> None:
    async def _send(message):
        bot = telegram.Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message)

    asyncio.run(_send(message))
