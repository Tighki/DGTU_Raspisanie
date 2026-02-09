"""
Константы приложения
"""
from datetime import datetime, timedelta
import pytz

# URL API университетов
TPI_DGTY_API_URL = "https://edu-tpi.donstu.ru/api"
DGTY_API_URL = "https://edu.donstu.ru/api"

# Пути API
AUTH_PATH = "/tokenauth"
GET_STUDENT_PATH = "/UserInfo/Student"
GET_TEACHER_PATH = "/UserInfo/user"

# Часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


def get_current_date() -> str:
    """Получить текущую дату в формате YYYY-MM-DD"""
    return datetime.now(MOSCOW_TZ).strftime('%Y-%m-%d')


def get_tomorrow_date() -> str:
    """Получить завтрашнюю дату в формате YYYY-MM-DD"""
    tomorrow = datetime.now(MOSCOW_TZ) + timedelta(days=1)
    return tomorrow.strftime('%Y-%m-%d')
