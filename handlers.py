"""
Обработчики команд и сообщений бота
"""
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from storage import Storage
from timetable_api import TimetableAPI
from utils import validate_email
from localizer import localize
from menu import get_main_menu, get_login_menu, get_login_options

logger = logging.getLogger(__name__)


class Handlers:
    """Класс с обработчиками команд бота"""
    
    def __init__(self, storage: Storage):
        self.storage = storage
        self.api = TimetableAPI()
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        menu = get_login_menu()
        text = localize("StartHandler", {"BtnLogin": "🔑 Авторизация"})
        await update.message.reply_text(text, reply_markup=menu)
    
    async def login_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопки авторизации"""
        inline_keyboard, _, _ = get_login_options()
        text = localize("ChooseUniversity", {})
        await update.message.reply_text(text, reply_markup=inline_keyboard)
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /l или /login - начинает процесс авторизации"""
        user = update.effective_user
        
        # Получаем тип университета из хранилища
        user_university = self.storage.get(str(user.id)) or ""
        
        if not user_university:
            # Если университет не выбран, показываем выбор
            inline_keyboard, _, _ = get_login_options()
            text = localize("ChooseUniversity", {})
            await update.message.reply_text(text, reply_markup=inline_keyboard)
            return
        
        # Устанавливаем состояние ожидания логина
        self.storage.set(f"{user.id}:login_state", "waiting_login")
        self.storage.set(f"{user.id}:login_university", user_university)
        
        text = localize("LoginHandler", {})
        await update.message.reply_text(text)
    
    async def inline_tpi_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора ПИ ДГТУ"""
        user = update.effective_user
        self.storage.delete(str(user.id))
        self.storage.set(str(user.id), "T")
        
        # Устанавливаем состояние ожидания логина
        self.storage.set(f"{user.id}:login_state", "waiting_login")
        self.storage.set(f"{user.id}:login_university", "T")
        
        text = localize("LoginHandler", {})
        await update.callback_query.edit_message_text(text)
    
    async def inline_dgty_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора ДГТУ"""
        user = update.effective_user
        self.storage.delete(str(user.id))
        self.storage.set(str(user.id), "D")
        
        # Устанавливаем состояние ожидания логина
        self.storage.set(f"{user.id}:login_state", "waiting_login")
        self.storage.set(f"{user.id}:login_university", "D")
        
        text = localize("LoginHandler", {})
        await update.callback_query.edit_message_text(text)
    
    async def logout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выхода"""
        user = update.effective_user
        if not self.storage.get(str(user.id)):
            await update.message.reply_text(localize("LogoutNotAuthError", {}))
            return
        
        self.storage.delete(str(user.id))
        menu = get_login_menu()
        await update.message.reply_text(localize("LogoutCompleteMessage", {}), reply_markup=menu)
    
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик помощи"""
        text = localize("HelpHandler", {
            "BtnToday": "📖 Сегодня",
            "BtnTomorrow": "📖 Завтра",
            "BtnWeek": "📖 Неделя"
        })
        await update.message.reply_text(text)

    async def clear_chat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопки очистки чата.
        
        Важно: Telegram не позволяет боту «по-настоящему» очистить историю,
        поэтому здесь мы даём пользователю понятную инструкцию.
        """
        instructions = (
            "🧹 <b>Как очистить чат</b>\n\n"
            "Telegram не даёт боту полностью удалить историю переписки.\n"
            "Вы можете сделать это вручную:\n\n"
            "1) Нажмите на имя бота вверху экрана.\n"
            "2) Откройте меню (⋮ или ⋯).\n"
            "3) Выберите пункт <b>\"Очистить историю\"</b> или <b>\"Удалить чат\"</b>.\n\n"
            "После этого чат будет полностью очищен на вашем устройстве."
        )
        await update.message.reply_text(instructions, parse_mode="HTML")
    
    async def today_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расписания на сегодня"""
        await self._send_timetable(update, "today")
    
    async def tomorrow_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расписания на завтра"""
        await self._send_timetable(update, "tomorrow")
    
    async def week_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расписания на неделю"""
        await self._send_timetable(update, "week")
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений для пошаговой авторизации"""
        user = update.effective_user
        user_id = str(user.id)
        text = update.message.text.strip()
        
        # Проверяем состояние авторизации
        login_state = self.storage.get(f"{user_id}:login_state")
        
        if login_state == "waiting_login":
            # Сохраняем логин и запрашиваем пароль
            self.storage.set(f"{user_id}:login_username", text)
            self.storage.set(f"{user_id}:login_state", "waiting_password")
            
            await update.message.reply_text(localize("LoginEnterPassword", {}))
            
        elif login_state == "waiting_password":
            # Получаем сохраненные данные
            username = self.storage.get(f"{user_id}:login_username")
            user_university = self.storage.get(f"{user_id}:login_university")
            password = text
            
            # Очищаем временные данные состояния
            self.storage.delete(f"{user_id}:login_state")
            self.storage.delete(f"{user_id}:login_username")
            self.storage.delete(f"{user_id}:login_university")
            
            if not username or not user_university:
                await update.message.reply_text(localize("TryLaterError", {}))
                return
            
            # Авторизация через API
            try:
                token_info = self.api.auth_user(user_university, username, password)
                
                if token_info.get('state') == -1:
                    await update.message.reply_text(localize("LoginWrongLoginOrPasswordError", {}))
                    return
                
                access_token = token_info['data']['accessToken']
                api_user_id = str(token_info['data']['data']['id'])
                
                # Определяем тип пользователя
                if not validate_email(username):
                    # Преподаватель
                    teacher_id = self.api.get_teacher_id(user_university, access_token, api_user_id)
                    storage_value = f"{user_university}{teacher_id}T"
                else:
                    # Студент
                    group_id = self.api.get_student_group_id(user_university, access_token, api_user_id)
                    storage_value = f"{user_university}{group_id}"
                
                # Сохраняем в хранилище
                self.storage.set(user_id, storage_value)
                
                menu = get_main_menu()
                text = localize("LoginCompleteMessage", {"BtnLogout": "🚪 Выход"})
                await update.message.reply_text(text, reply_markup=menu)
                
            except Exception as e:
                logger.error(f"Ошибка авторизации: {e}")
                await update.message.reply_text(localize("TryLaterError", {}))
    
    async def _send_timetable(self, update: Update, period: str):
        """Общая функция для отправки расписания"""
        user = update.effective_user
        storage_value = self.storage.get(str(user.id))
        
        if not storage_value:
            await update.message.reply_text(localize("TimetableLoginFirstError", {}))
            return
        
        try:
            timetable = self.api.get_timetable(storage_value)
            text, parse_mode = self._format_timetable(timetable, storage_value, period)
            
            if not text or text.strip() == "":
                await update.message.reply_text(localize("TimetableEmpty", {}))
            else:
                await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Ошибка получения расписания: {e}")
            await update.message.reply_text(localize("TryLaterError", {}))
    
    def _format_timetable(self, timetable: dict, storage_value: str, period: str):
        """Форматирование расписания для отправки с HTML разметкой"""
        from datetime import datetime
        from constants import get_current_date, get_tomorrow_date
        
        if not timetable or 'data' not in timetable or 'rasp' not in timetable['data']:
            return "", None
        
        items = timetable['data']['rasp']
        is_teacher = storage_value.endswith('T')
        
        # Фильтрация по периоду
        if period == "today":
            current_date = get_current_date()
            filtered_items = [item for item in items if item.get('дата', '').startswith(current_date)]
        elif period == "tomorrow":
            tomorrow_date = get_tomorrow_date()
            filtered_items = [item for item in items if item.get('дата', '').startswith(tomorrow_date)]
        else:  # week
            filtered_items = items
        
        if not filtered_items:
            return "", None
        
        # Форматирование с HTML
        lines = []
        if period == "week":
            # Группировка по дням недели
            from collections import defaultdict
            by_day = defaultdict(list)
            for item in filtered_items:
                day_num = item.get('деньНедели', 0)
                if 1 <= day_num <= 7:
                    by_day[day_num].append(item)
            
            for day_num in sorted(by_day.keys()):
                day_items = by_day[day_num]
                if day_items:
                    day_name = day_items[0].get('день_недели', '')
                    # Убираем эмодзи календаря если оно есть в названии дня
                    if day_name.startswith('📅 '):
                        day_name = day_name[2:]
                    # Убираем дату из названия дня (например, "Понедельник 17" -> "Понедельник")
                    import re
                    day_name = re.sub(r'\s+\d+$', '', day_name).strip()
                    lines.append(f"\n<b>{day_name}</b>\n")
                    for idx, item in enumerate(day_items):
                        lines.append(self._format_item(item, is_teacher, idx + 1))
                        # Две пустые строки между парами для лучшей читаемости
                        if idx < len(day_items) - 1:
                            lines.append("")
                            lines.append("")
        else:
            # Для сегодня/завтра добавляем заголовок
            if period == "today":
                lines.append(f"<b>Сегодня</b>")
            elif period == "tomorrow":
                lines.append(f"<b>Завтра</b>")
            
            for idx, item in enumerate(filtered_items):
                lines.append(self._format_item(item, is_teacher, idx + 1))
                # Две пустые строки между парами для лучшей читаемости
                if idx < len(filtered_items) - 1:
                    lines.append("")
                    lines.append("")
        
        return "\n".join(lines), "HTML"
    
    def _format_item(self, item: dict, is_teacher: bool, number: int = 0) -> str:
        """Форматирование одного занятия (компактно и читабельно)"""
        from utils import get_lecture_icon
        
        discipline = item.get('дисциплина', '')
        icon = get_lecture_icon(discipline)
        
        if is_teacher:
            group = item.get('группа', '')
            teacher_part = f"👤 <b>{group}</b>"
        else:
            teacher = item.get('преподаватель', '')
            teacher_part = f"👤 <b>{teacher}</b>"
        
        start = item.get('начало', '')
        end = item.get('конец', '')
        audience = item.get('аудитория', '')

        # Улучшенное форматирование: убираем дублирование иконок
        number_prefix = f"<b>{number}.</b> " if number > 0 else ""
        
        # Определяем тип занятия и выбираем цветной кружок
        discipline_lower = discipline.lower()
        if discipline_lower.startswith('лек'):
            type_emoji = "🟢"  # Лекция
            type_text = "лек"
        elif discipline_lower.startswith('лаб'):
            type_emoji = "🔵"  # Лабораторная (синий кружок)
            type_text = "лаб"
        elif discipline_lower.startswith('пр'):
            type_emoji = "🟠"  # Практика
            type_text = "пр"
        else:
            type_emoji = "⚪"  # Другие занятия (белый кружок)
            type_text = ""
        
        # Компактный формат: номер, иконка типа, название предмета
        line1 = f"{number_prefix}{type_emoji} <b>{discipline}</b>"
        
        # Вторая строка: преподаватель и время в одной строке
        time_part = f"{start}–{end}" if start and end else f"{start or end}"
        line2 = f"{teacher_part}  🕒 <code>{time_part}</code>"
        
        # Третья строка: только аудитория
        line3 = f"📍 <i>{audience}</i>" if audience else ""
        
        # Объединяем строки, убирая пустые
        lines = [line1, line2]
        if line3:
            lines.append(line3)
        
        return "\n".join(lines)
