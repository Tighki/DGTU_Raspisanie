"""
Модуль для работы с хранилищем данных
Поддерживает: memory, sqlite, redis, mongo
"""
import logging
from typing import Optional
from abc import ABC, abstractmethod
from config import Config

logger = logging.getLogger(__name__)


class Storage(ABC):
    """Абстрактный класс для хранилища"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Сохранить значение по ключу"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Удалить значение по ключу"""
        pass


class MemoryStorage(Storage):
    """Хранилище в памяти"""
    
    def __init__(self):
        self._data: dict[str, str] = {}
        logger.info("Используется хранилище в памяти")
    
    def get(self, key: str) -> Optional[str]:
        return self._data.get(key)
    
    def set(self, key: str, value: str) -> None:
        self._data[key] = value
    
    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class SQLiteStorage(Storage):
    """SQLite хранилище"""
    
    def __init__(self, db_path: str):
        import sqlite3
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()
        logger.info(f"Используется SQLite хранилище: {db_path}")
    
    def _init_table(self):
        """Создание таблицы если её нет"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.commit()
    
    def get(self, key: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM sessions WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def set(self, key: str, value: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()
    
    def delete(self, key: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE key = ?", (key,))
        self.conn.commit()


class RedisStorage(Storage):
    """Redis хранилище"""
    
    def __init__(self, host: str, port: int):
        try:
            import redis
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            # Проверка подключения
            self.client.ping()
            logger.info(f"Используется Redis хранилище: {host}:{port}")
        except ImportError:
            raise ImportError("Для использования Redis установите: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Не удалось подключиться к Redis: {e}")
    
    def get(self, key: str) -> Optional[str]:
        value = self.client.get(key)
        return value if value else None
    
    def set(self, key: str, value: str) -> None:
        self.client.set(key, value)
    
    def delete(self, key: str) -> None:
        self.client.delete(key)


class MongoStorage(Storage):
    """MongoDB хранилище"""

    def __init__(self, uri: str, db_name: str, collection_name: str):
        try:
            from pymongo import MongoClient, errors  # type: ignore

            self.client = MongoClient(uri)
            # Лёгкая проверка подключения
            self.client.admin.command("ping")

            self.db = self.client[db_name]
            self.collection = self.db[collection_name]

            # Индекс по _id создаётся автоматически, но лог для ясности
            logger.info(f"Используется MongoDB хранилище: {uri}, db={db_name}, collection={collection_name}")
        except ImportError:
            raise ImportError("Для использования MongoDB установите: pip install pymongo")
        except Exception as e:
            raise ConnectionError(f"Не удалось подключиться к MongoDB: {e}")

    def get(self, key: str) -> Optional[str]:
        doc = self.collection.find_one({"_id": key})
        if not doc:
            return None
        # Храним строку в поле value
        return doc.get("value")

    def set(self, key: str, value: str) -> None:
        self.collection.update_one(
            {"_id": key},
            {"$set": {"value": value}},
            upsert=True,
        )

    def delete(self, key: str) -> None:
        self.collection.delete_one({"_id": key})


def get_storage(config: Config) -> Storage:
    """Фабрика для создания хранилища в зависимости от типа"""
    storage_type = config.storage_type.lower()
    
    if storage_type == 'redis':
        return RedisStorage(config.redis_host, config.redis_port)
    elif storage_type == 'mongo':
        return MongoStorage(config.mongo_uri, config.mongo_db, config.mongo_collection)
    elif storage_type == 'sqlite':
        return SQLiteStorage(config.sqlite_path)
    else:  # memory или по умолчанию
        return MemoryStorage()
