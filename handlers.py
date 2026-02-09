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
        """Обработчик команды /l <логин> <пароль>"""
        user = update.effective_user
        args = context.args
        
        if not args or len(args) < 2:
            await update.message.reply_text(localize("LoginError", {}))
            return
        
        username, password = args[0], args[1]
        
        # Получаем тип университета из хранилища
        user_university = self.storage.get(str(user.id)) or ""
        
        if not user_university:
            await update.message.reply_text(localize("LoginError", {}))
            return
        
        # Авторизация через API
        try:
            token_info = self.api.auth_user(user_university, username, password)
            
            if token_info.get('state') == -1:
                await update.message.reply_text(localize("LoginWrongLoginOrPasswordError", {}))
                return
            
            access_token = token_info['data']['accessToken']
            user_id = str(token_info['data']['data']['id'])
            
            # Определяем тип пользователя
            if not validate_email(username):
                # Преподаватель
                teacher_id = self.api.get_teacher_id(user_university, access_token, user_id)
                storage_value = f"{user_university}{teacher_id}T"
            else:
                # Студент
                group_id = self.api.get_student_group_id(user_university, access_token, user_id)
                storage_value = f"{user_university}{group_id}"
            
            # Сохраняем в хранилище
            self.storage.set(str(user.id), storage_value)
            
            menu = get_main_menu()
            text = localize("LoginCompleteMessage", {"BtnLogout": "🚪 Выход"})
            await update.message.reply_text(text, reply_markup=menu)
            
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            await update.message.reply_text(localize("TryLaterError", {}))
    
    async def inline_tpi_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора ПИ ДГТУ"""
        user = update.effective_user
        self.storage.delete(str(user.id))
        self.storage.set(str(user.id), "T")
        await update.callback_query.edit_message_text(localize("LoginHandler", {}))
    
    async def inline_dgty_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора ДГТУ"""
        user = update.effective_user
        self.storage.delete(str(user.id))
        self.storage.set(str(user.id), "D")
        await update.callback_query.edit_message_text(localize("LoginHandler", {}))
    
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
    
    async def today_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расписания на сегодня"""
        await self._send_timetable(update, "today")
    
    async def tomorrow_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расписания на завтра"""
        await self._send_timetable(update, "tomorrow")
    
    async def week_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расписания на неделю"""
        await self._send_timetable(update, "week")
    
    async def _send_timetable(self, update: Update, period: str):
        """Общая функция для отправки расписания"""
        user = update.effective_user
        storage_value = self.storage.get(str(user.id))
        
        if not storage_value:
            await update.message.reply_text(localize("TimetableLoginFirstError", {}))
            return
        
        try:
            timetable = self.api.get_timetable(storage_value)
            text = self._format_timetable(timetable, storage_value, period)
            
            if not text or text.strip() == "":
                await update.message.reply_text(localize("TimetableEmpty", {}))
            else:
                await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"Ошибка получения расписания: {e}")
            await update.message.reply_text(localize("TryLaterError", {}))
    
    def _format_timetable(self, timetable: dict, storage_value: str, period: str) -> str:
        """Форматирование расписания для отправки"""
        from datetime import datetime
        from constants import get_current_date, get_tomorrow_date
        
        if not timetable or 'data' not in timetable or 'rasp' not in timetable['data']:
            return ""
        
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
            return ""
        
        # Форматирование
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
                    lines.append(f"\n{day_name}")
                    for item in day_items:
                        lines.append(self._format_item(item, is_teacher))
        else:
            for item in filtered_items:
                lines.append(self._format_item(item, is_teacher))
        
        return "\n".join(lines)
    
    def _format_item(self, item: dict, is_teacher: bool) -> str:
        """Форматирование одного занятия"""
        from utils import get_lecture_icon
        
        discipline = item.get('дисциплина', '')
        icon = get_lecture_icon(discipline)
        
        if is_teacher:
            group = item.get('группа', '')
            teacher_part = f"👤 {group}"
        else:
            teacher = item.get('преподаватель', '')
            teacher_part = f"👤 {teacher}"
        
        start = item.get('начало', '')
        end = item.get('конец', '')
        audience = item.get('аудитория', '')
        
        return f"{teacher_part}\n{icon} {discipline}\n🕒 {start} / {end}\n📍 Аудитория: {audience}"
