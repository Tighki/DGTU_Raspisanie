"""
Конфигурация бота
"""
import os
from typing import Optional


class Config:
    """Класс для загрузки конфигурации из переменных окружения"""
    
    def __init__(self):
        self.bot_token: str = os.getenv('BOT_TOKEN', '')
        self.storage_type: str = os.getenv('STORAGE_TYPE', 'mongo')
        self.sqlite_path: str = os.getenv('SQLITE_PATH', 'sessions.db')
        self.redis_host: str = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port: int = int(os.getenv('REDIS_PORT', '6379'))

        # Настройки MongoDB
        self.mongo_uri: str = os.getenv('MONGO_URI', 'mongodb://mongo:3zzc8t1bephxkkvn@192.168.1.182:27019/')
        self.mongo_db: str = os.getenv('MONGO_DB', 'ras')
        self.mongo_collection: str = os.getenv('MONGO_COLLECTION', 'sessions')
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN обязателен для работы бота")
