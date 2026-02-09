"""
Меню и кнопки бота
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        ["📖 Сегодня", "📖 Завтра"],
        ["📖 Неделя", "ℹ Помощь"],
        ["🚪 Выход"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_login_menu() -> ReplyKeyboardMarkup:
    """Меню авторизации"""
    keyboard = [["🔑 Авторизация"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_login_options():
    """Inline кнопки выбора университета"""
    keyboard = [
        [
            InlineKeyboardButton("ПИ ДГТУ", callback_data="tpi"),
            InlineKeyboardButton("ДГТУ", callback_data="dgty")
        ]
    ]
    return InlineKeyboardMarkup(keyboard), "tpi", "dgty"
