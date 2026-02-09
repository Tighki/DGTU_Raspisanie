"""
Конфигурация бота
"""
import os
from typing import Optional


class Config:
    """Класс для загрузки конфигурации из переменных окружения"""
    
    def __init__(self):
        self.bot_token: str = os.getenv('BOT_TOKEN', '')
        self.storage_type: str = os.getenv('STORAGE_TYPE', 'memory')
        self.sqlite_path: str = os.getenv('SQLITE_PATH', 'sessions.db')
        self.redis_host: str = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN обязателен для работы бота")
