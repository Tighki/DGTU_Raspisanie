import os


class Config:
    def __init__(self):
        self.bot_token: str = self._get_env('BOT_TOKEN', '')
        self.mongo_uri: str = self._get_env('MONGO_URI', 'mongodb://mongo:3zzc8t1bephxkkvn@192.168.1.182:27019/')
        self.mongo_db: str = self._get_env('MONGO_DB', 'ras')
        self.mongo_collection: str = self._get_env('MONGO_COLLECTION', 'sessions')
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN обязателен для работы бота")
    
    @staticmethod
    def _get_env(key: str, default: str = '') -> str:
        return os.getenv(key, default)
