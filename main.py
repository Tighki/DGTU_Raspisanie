#!/usr/bin/env python3
import asyncio
import logging
from bot.bot import TelegramBot
from bot.config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():
    try:
        config = Config()
        bot = TelegramBot(config)
        await bot.start()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
