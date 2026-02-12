import logging
from typing import Optional
from collections import defaultdict
import re
from pymongo import MongoClient, UpdateOne
from telegram import Update
from telegram.ext import ContextTypes
from bot.api.timetable import TimetableAPI
from bot.utils import validate_email
from bot.localizer import localize
from bot.menu import get_main_menu, get_login_menu
from bot.config import Config
from bot.constants import get_current_date, get_tomorrow_date

logger = logging.getLogger(__name__)

MAIN_MENU = get_main_menu()
LOGIN_MENU = get_login_menu()


class Handlers:
    def __init__(self, config: Config):
        try:
            self.client = MongoClient(config.mongo_uri)
            self.client.admin.command("ping")
            self.collection = self.client[config.mongo_db][config.mongo_collection]
        except ImportError:
            raise ImportError("Для использования MongoDB установите: pip install pymongo")
        except Exception as e:
            raise ConnectionError(f"Не удалось подключиться к MongoDB: {e}")
        
        self.api = TimetableAPI()
    
    @staticmethod
    def _get_user_id(user) -> str:
        return str(user.id)
    
    def _get(self, key: str) -> Optional[str]:
        doc = self.collection.find_one({"_id": key})
        return doc.get("value") if doc else None
    
    def _set(self, key: str, value: str) -> None:
        self.collection.update_one(
            {"_id": key},
            {"$set": {"value": value}},
            upsert=True,
        )
    
    def _set_many(self, data: dict[str, str]) -> None:
        operations = [
            UpdateOne({"_id": key}, {"$set": {"value": value}}, upsert=True)
            for key, value in data.items()
        ]
        if operations:
            self.collection.bulk_write(operations)
    
    def _delete(self, key: str) -> None:
        self.collection.delete_one({"_id": key})
    
    def _delete_many(self, keys: list[str]) -> None:
        if keys:
            self.collection.delete_many({"_id": {"$in": keys}})
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = localize("StartHandler", {"BtnLogin": "🔑 Авторизация"})
        await update.message.reply_text(text, reply_markup=LOGIN_MENU)
    
    def _init_login_state(self, user_id: str, university: str = "T"):
        self._set_many({
            user_id: university,
            f"{user_id}:login_state": "waiting_login",
            f"{user_id}:login_university": university
        })
    
    async def login_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self._init_login_state(self._get_user_id(user))
        text = localize("LoginHandler", {})
        await update.message.reply_text(text)
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.login_handler(update, context)
    
    async def logout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self._get_user_id(user)
        
        if not self._get(user_id):
            await update.message.reply_text(localize("LogoutNotAuthError", {}))
            return
        
        self._delete(user_id)
        await update.message.reply_text(localize("LogoutCompleteMessage", {}), reply_markup=LOGIN_MENU)
    
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = localize("HelpHandler", {
            "BtnToday": "📖 Сегодня",
            "BtnTomorrow": "📖 Завтра",
            "BtnWeek": "📖 Неделя"
        })
        await update.message.reply_text(text)
    
    async def today_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_timetable(update, "today")
    
    async def tomorrow_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_timetable(update, "tomorrow")
    
    async def week_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_timetable(update, "week")
    
    def _cleanup_login_state(self, user_id: str):
        self._delete_many([
            f"{user_id}:login_state",
            f"{user_id}:login_username",
            f"{user_id}:login_university"
        ])
    
    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = self._get_user_id(user)
        text = update.message.text.strip()
        
        login_state = self._get(f"{user_id}:login_state")
        
        if login_state == "waiting_login":
            self._set_many({
                f"{user_id}:login_username": text,
                f"{user_id}:login_state": "waiting_password"
            })
            await update.message.reply_text(localize("LoginEnterPassword", {}))
            
        elif login_state == "waiting_password":
            username = self._get(f"{user_id}:login_username")
            user_university = self._get(f"{user_id}:login_university")
            
            if not username or not user_university:
                await update.message.reply_text(localize("TryLaterError", {}))
                return
            
            self._cleanup_login_state(user_id)
            
            try:
                token_info = self.api.auth_user(user_university, username, text)
                
                if token_info.get('state') == -1:
                    await update.message.reply_text(localize("LoginWrongLoginOrPasswordError", {}))
                    return
                
                access_token = token_info['data']['accessToken']
                api_user_id = str(token_info['data']['data']['id'])
                
                if not validate_email(username):
                    teacher_id = self.api.get_teacher_id(user_university, access_token, api_user_id)
                    storage_value = f"{user_university}{teacher_id}T"
                else:
                    group_id = self.api.get_student_group_id(user_university, access_token, api_user_id)
                    storage_value = f"{user_university}{group_id}"
                
                self._set(user_id, storage_value)
                
                await update.message.reply_text(
                    localize("LoginCompleteMessage", {"BtnLogout": "🚪 Выход"}),
                    reply_markup=MAIN_MENU
                )
                
            except Exception as e:
                logger.error(f"Ошибка авторизации: {e}")
                await update.message.reply_text(localize("TryLaterError", {}))
    
    async def _send_timetable(self, update: Update, period: str):
        user = update.effective_user
        user_id = self._get_user_id(user)
        storage_value = self._get(user_id)
        
        if not storage_value:
            await update.message.reply_text(localize("TimetableLoginFirstError", {}))
            return
        
        try:
            timetable = self.api.get_timetable(storage_value)
            text, parse_mode = self._format_timetable(timetable, storage_value, period)
            
            if not text or not text.strip():
                await update.message.reply_text(localize("TimetableEmpty", {}))
            else:
                await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Ошибка получения расписания для пользователя {user_id}: {e}", exc_info=True)
            await update.message.reply_text(localize("TryLaterError", {}))
    
    def _format_timetable(self, timetable: dict, storage_value: str, period: str):
        if not timetable or 'data' not in timetable or 'rasp' not in timetable['data']:
            return "", None
        
        items = timetable['data']['rasp']
        is_teacher = storage_value.endswith('T')
        
        if period == "today":
            current_date = get_current_date()
            filtered_items = [item for item in items if item.get('дата', '').startswith(current_date)]
        elif period == "tomorrow":
            tomorrow_date = get_tomorrow_date()
            filtered_items = [item for item in items if item.get('дата', '').startswith(tomorrow_date)]
        else:
            filtered_items = items
        
        if not filtered_items:
            return "", None
        
        lines = []
        if period == "week":
            by_day = defaultdict(list)
            for item in filtered_items:
                day_num = item.get('деньНедели', 0)
                if 1 <= day_num <= 7:
                    by_day[day_num].append(item)
            
            for day_num in sorted(by_day.keys()):
                day_items = by_day[day_num]
                if day_items:
                    day_name = day_items[0].get('день_недели', '')
                    if day_name.startswith('📅 '):
                        day_name = day_name[2:]
                    day_name = re.sub(r'\s+\d+$', '', day_name).strip()
                    lines.append(f"\n<b>{day_name}</b>\n")
                    for idx, item in enumerate(day_items):
                        lines.append(self._format_item(item, is_teacher, idx + 1))
                        if idx < len(day_items) - 1:
                            lines.append("\n\n")
        else:
            period_titles = {"today": "Сегодня", "tomorrow": "Завтра"}
            if period in period_titles:
                lines.append(f"<b>{period_titles[period]}</b>")
            
            for idx, item in enumerate(filtered_items):
                lines.append(self._format_item(item, is_teacher, idx + 1))
                if idx < len(filtered_items) - 1:
                    lines.append("\n\n")
        
        return "\n".join(lines), "HTML"
    
    def _get_lesson_type_emoji(self, discipline: str) -> str:
        discipline_lower = discipline.lower()
        if discipline_lower.startswith('лек'):
            return "🟢"
        elif discipline_lower.startswith('лаб'):
            return "🔵"
        elif discipline_lower.startswith('пр'):
            return "🟠"
        return "⚪"
    
    def _format_item(self, item: dict, is_teacher: bool, number: int = 0) -> str:
        discipline = item.get('дисциплина', '')
        
        if is_teacher:
            teacher_part = f"👤 <b>{item.get('группа', '')}</b>"
        else:
            teacher_part = f"👤 <b>{item.get('преподаватель', '')}</b>"
        
        start = item.get('начало', '')
        end = item.get('конец', '')
        audience = item.get('аудитория', '')

        number_prefix = f"<b>{number}.</b> " if number > 0 else ""
        type_emoji = self._get_lesson_type_emoji(discipline)
        
        line1 = f"{number_prefix}{type_emoji} <b>{discipline}</b>"
        time_part = f"{start}–{end}" if start and end else (start or end)
        line2 = f"{teacher_part}  🕒 <code>{time_part}</code>"
        
        lines = [line1, line2]
        if audience:
            lines.append(f"📍 <i>{audience}</i>")
        
        return "\n".join(lines)
