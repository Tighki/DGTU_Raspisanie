import os


class Config:
    def __init__(self):
        self.bot_token: str = self._get_env('BOT_TOKEN', '')
        self.mongo_uri: str = self._get_env('MONGO_URI', '')
        self.mongo_db: str = self._get_env('MONGO_DB', '')
        self.mongo_collection: str = self._get_env('MONGO_COLLECTION', '')
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN обязателен для работы бота")
    
    @staticmethod
    def _get_env(key: str, default: str = '') -> str:
        return os.getenv(key, default)
