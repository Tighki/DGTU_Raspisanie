"""
Клиент для работы с API расписания университетов
"""
import logging
import requests
from typing import Dict, Any
from constants import TPI_DGTY_API_URL, DGTY_API_URL, AUTH_PATH, GET_STUDENT_PATH, GET_TEACHER_PATH

logger = logging.getLogger(__name__)


class TimetableAPI:
    """Класс для работы с API расписания"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'DGTY-Timetable-Bot/1.0'
        })
    
    def _get_university_url(self, university_type: str) -> str:
        """Получить URL API университета"""
        if university_type.startswith('T'):
            return TPI_DGTY_API_URL
        elif university_type.startswith('D'):
            return DGTY_API_URL
        return ""
    
    def auth_user(self, university_type: str, username: str, password: str) -> Dict[str, Any]:
        """Авторизация пользователя"""
        url = self._get_university_url(university_type) + AUTH_PATH
        
        payload = {
            "username": username,
            "password": password
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка авторизации: {e}")
            raise
    
    def get_student_group_id(self, university_type: str, access_token: str, student_id: str) -> int:
        """Получить ID группы студента"""
        url = self._get_university_url(university_type) + GET_STUDENT_PATH
        
        cookies = {'authToken': access_token}
        params = {'studentID': student_id}
        
        try:
            response = self.session.get(url, cookies=cookies, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['data']['group']['item2']
        except Exception as e:
            logger.error(f"Ошибка получения ID группы: {e}")
            raise
    
    def get_teacher_id(self, university_type: str, access_token: str, user_id: str) -> int:
        """Получить ID преподавателя"""
        url = self._get_university_url(university_type) + GET_TEACHER_PATH
        
        cookies = {'authToken': access_token}
        params = {'userID': user_id}
        
        try:
            response = self.session.get(url, cookies=cookies, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['data']['teacherID']
        except Exception as e:
            logger.error(f"Ошибка получения ID преподавателя: {e}")
            raise
    
    def get_timetable(self, storage_value: str) -> Dict[str, Any]:
        """Получить расписание"""
        from constants import get_current_date
        
        # Определяем тип запроса
        if storage_value.endswith('T'):
            param_name = 'idTeacher'
            value = storage_value[:-1]  # Убираем последний 'T'
        else:
            param_name = 'idGroup'
            value = storage_value
        
        # Убираем префикс университета
        if value.startswith('T') or value.startswith('D'):
            value = value[1:]
        
        university_type = storage_value[0] if storage_value else 'D'
        base_url = self._get_university_url(university_type)
        
        url = f"{base_url}/Rasp"
        params = {
            param_name: value,
            'sdate': get_current_date()
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения расписания: {e}")
            return {'data': {'rasp': []}, 'state': -1, 'msg': str(e)}
