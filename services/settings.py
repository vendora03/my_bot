from datetime import datetime
from services.database import DB_Set_Bot_Settings, DB_Get_Bot_Settings
from config import SETTINGS_SCHEMA
class Settings:
    _cache = {}
    
    # ---------- internal ----------
    @classmethod
    def _load(cls, key: str, default=None):
        if key not in cls._cache:
            value = DB_Get_Bot_Settings(key)
            cls._cache[key] = value if value is not None else default
        return cls._cache[key]

    @classmethod
    def _set(cls, key: str, value):
        DB_Set_Bot_Settings(key, str(value), datetime.now())
        cls._cache[key] = str(value)
        
    @staticmethod
    def _to_bool(value, default=False):
        if value is None:
            return default
        return value.lower() == "true"

    @classmethod
    def set(cls, key: str, value: str):
        value_type = SETTINGS_SCHEMA[key]

        if value_type == "bool":
            value = value.lower()

        cls._set(key, value)

    @classmethod
    def get(cls, key: str):
        if key not in SETTINGS_SCHEMA:
            return None
        return cls._load(key)

     # ---------- DEBUG ----------
   
    @classmethod
    def is_logging(cls) -> bool:
        return cls._to_bool(cls._load("debug", "false"))

    # ---------- START INFO ----------
    @classmethod
    def start_info_enabled(cls) -> bool:
        return cls._to_bool(cls._load("start_info_state", "false"))

    @classmethod
    def get_start_info(cls) -> str:
        return cls._load("start_info", "")


    # ---------- VIP INFO ----------
    @classmethod
    def vip_info_enabled(cls) -> bool:
        return cls._to_bool(cls._load("vip_info_state", "false"))

    @classmethod
    def get_vip_info(cls) -> str:
        return cls._load("vip_info", "")

    @classmethod
    def get_group(cls) -> str:
        return cls._load("group", "")
        
   
        
        
        