from telegram import ReplyKeyboardMarkup


def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📖 Сегодня", "📖 Завтра"],
        ["📖 Неделя", "ℹ Помощь"],
        ["🚪 Выход"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_login_menu() -> ReplyKeyboardMarkup:
    keyboard = [["🔑 Авторизация"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
