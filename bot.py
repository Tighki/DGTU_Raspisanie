"""
Основной класс Telegram бота
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from config import Config
from handlers import Handlers
from storage import get_storage

logger = logging.getLogger(__name__)


class TelegramBot:
    """Класс для управления Telegram ботом"""
    
    def __init__(self, config: Config):
        self.config = config
        self.storage = get_storage(config)
        self.handlers = Handlers(self.storage)
        
        # Создаем приложение
        self.application = Application.builder().token(config.bot_token).build()
        
        # Регистрируем обработчики
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация всех обработчиков команд и сообщений"""
        from menu import get_main_menu, get_login_menu, get_login_options
        
        # Команды
        self.application.add_handler(CommandHandler("start", self.handlers.start_handler))
        self.application.add_handler(CommandHandler("l", self.handlers.login_command))
        self.application.add_handler(CommandHandler("login", self.handlers.login_handler))
        
        # Кнопки меню
        menu = get_main_menu()
        login_menu = get_login_menu()
        login_options, btn_tpi, btn_dgty = get_login_options()
        
        self.application.add_handler(MessageHandler(filters.Regex("^📖 Сегодня$"), self.handlers.today_handler))
        self.application.add_handler(MessageHandler(filters.Regex("^📖 Завтра$"), self.handlers.tomorrow_handler))
        self.application.add_handler(MessageHandler(filters.Regex("^📖 Неделя$"), self.handlers.week_handler))
        self.application.add_handler(MessageHandler(filters.Regex("^ℹ Помощь$"), self.handlers.help_handler))
        self.application.add_handler(MessageHandler(filters.Regex("^🧹 Очистить чат$"), self.handlers.clear_chat_handler))
        self.application.add_handler(MessageHandler(filters.Regex("^🔑 Авторизация$"), self.handlers.login_handler))
        self.application.add_handler(MessageHandler(filters.Regex("^🚪 Выход$"), self.handlers.logout_handler))
        
        # Inline кнопки выбора университета
        self.application.add_handler(CallbackQueryHandler(
            self.handlers.inline_tpi_handler,
            pattern="^tpi$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            self.handlers.inline_dgty_handler,
            pattern="^dgty$"
        ))
        
        # Обработчик текстовых сообщений для пошаговой авторизации (должен быть последним)
        # Используем фильтр, чтобы не перехватывать команды и кнопки меню
        self.application.add_handler(MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & ~filters.Regex("^(📖 Сегодня|📖 Завтра|📖 Неделя|ℹ Помощь|🧹 Очистить чат|🔑 Авторизация|🚪 Выход)$"),
            self.handlers.text_message_handler,
        ))
    
    async def start(self):
        """Запуск бота"""
        import asyncio
        
        logger.info("Запуск бота...")
        try:
            # Инициализация и запуск polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            logger.info("Бот запущен и готов к работе!")
            
            # Ожидание бесконечно (до получения сигнала остановки)
            # Используем бесконечный цикл с проверкой каждую секунду
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Получен сигнал отмены")
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки (KeyboardInterrupt)")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            # Остановка бота
            logger.info("Остановка бота...")
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                logger.error(f"Ошибка при остановке: {e}")
            logger.info("Бот остановлен")
