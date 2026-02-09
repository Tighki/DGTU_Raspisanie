#!/usr/bin/env python3
"""
DGTY Timetable Telegram Bot - Python Version
Main entry point
"""

import asyncio
import logging
import os
from bot import TelegramBot
from config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Настройка уровня логирования для telegram
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    try:
        config = Config()
        
        if not config.bot_token:
            logger.error("BOT_TOKEN не установлен! Установите переменную окружения BOT_TOKEN")
            return
        
        bot = TelegramBot(config)
        await bot.start()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
