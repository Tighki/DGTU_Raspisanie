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

# Подавляем предупреждения о CancelledError (это нормальное поведение для updater.idle())
logging.getLogger('telegram.ext.Application').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    config = Config()
    
    if not config.bot_token:
        logger.error("BOT_TOKEN не установлен! Установите переменную окружения BOT_TOKEN")
        return
    
    bot = TelegramBot(config)
    await bot.start()


if __name__ == '__main__':
    asyncio.run(main())
