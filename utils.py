"""
Вспомогательные функции
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Проверка, является ли строка email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_lecture_icon(discipline: str) -> str:
    """Получить иконку для типа занятия"""
    discipline_lower = discipline.lower().strip()
    
    # Проверяем различные варианты написания типов занятий
    if 'п/г' in discipline or re.search(r'\* п/г \d+$', discipline):
        return '🔵'
    elif discipline_lower.startswith('лек') or discipline_lower.startswith('фв'):
        return '🟢'
    elif discipline_lower.startswith('пр') or discipline_lower.startswith('пр.'):
        return '📚'  # Практика
    elif discipline_lower.startswith('лаб'):
        return '📚'  # Лабораторная работа
    
    return '📚'
