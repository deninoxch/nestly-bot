from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    SUPERADMIN_ID: int
    DATABASE_URL: str = 'sqlite+aiosqlite:///nestly.db'
    DEBUG: bool = False 
    COMPANY_CONTACT_USERNAME: str = "nestly_support"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='UTF-8')

settings = Settings()