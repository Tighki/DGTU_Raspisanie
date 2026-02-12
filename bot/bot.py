import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from bot.config import Config
from bot.handlers import Handlers

logger = logging.getLogger(__name__)

MENU_BUTTONS = ["📖 Сегодня", "📖 Завтра", "📖 Неделя", "ℹ Помощь", "🔑 Авторизация", "🚪 Выход"]


class TelegramBot:
    def __init__(self, config: Config):
        self.handlers = Handlers(config)
        self.application = Application.builder().token(config.bot_token).build()
        self._register_handlers()
    
    def _register_handlers(self):
        command_handlers = [
            ("start", self.handlers.start_handler),
            ("l", self.handlers.login_command),
            ("login", self.handlers.login_handler),
        ]
        
        for command, handler in command_handlers:
            self.application.add_handler(CommandHandler(command, handler))
        
        menu_handlers = [
            ("^📖 Сегодня$", self.handlers.today_handler),
            ("^📖 Завтра$", self.handlers.tomorrow_handler),
            ("^📖 Неделя$", self.handlers.week_handler),
            ("^ℹ Помощь$", self.handlers.help_handler),
            ("^🔑 Авторизация$", self.handlers.login_handler),
            ("^🚪 Выход$", self.handlers.logout_handler),
        ]
        
        for pattern, handler in menu_handlers:
            self.application.add_handler(MessageHandler(filters.Regex(pattern), handler))
        
        menu_pattern = "|".join(f"^{btn}$" for btn in MENU_BUTTONS)
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Regex(f"^({menu_pattern})$"),
            self.handlers.text_message_handler
        ))
    
    async def start(self):
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            await asyncio.Event().wait()
            
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            await self._shutdown()
    
    async def _shutdown(self):
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        except Exception as e:
            logger.error(f"Ошибка при остановке: {e}")
