from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, List
from .log_config import logger
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    # Seurity & Fundamental
    SECRET_KEY: str = str(os.environ.get('SECRET_KEY'))
    DEBUG: bool = bool(os.environ.get('DEBUG', True))
    GEMINI_API_KEY: str = str(os.environ.get('GEMINI_API_KEY'))
    MAYAR_BASE_URL: str =  "https://api.mayar.club/hl/v1"
    MAYAR_API_KEY: str = str(os.environ.get("MAYAR_API_KEY"))
    MAYAR_WEBHOOK_TOKEN: str = str(os.environ.get("MAYAR_WEBHOOK_TOKEN"))
    
    # EMAIL BROKER
    SMTP_HOST: str = "smtp-relay.brevo.com" 
    PORT_SMTP: int = 587
    SMTP_EMAIL: str = "mi167269@gmail.com" 
    API_KEY_BREVO: str = str(os.environ.get("API_KEY_BREVO")) 
    
    # DB Connection
    POSTGRES_USERNAME: str = str(os.environ.get('POSTGRES_USERNAME'))
    POSTGRES_PASSWORD: str = str(os.environ.get('POSTGRES_PASSWORD'))
    POSTGRES_HOST: str = str(os.environ.get('POSTGRES_HOST'))
    POSTGRES_PORT: int = int(os.environ.get('POSTGRES_PORT', 5432))
    POSTGRES_DB: str = str(os.environ.get('POSTGRES_DB'))
    if not all([POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_DB]):
        raise ValueError("Variabel database belum terisi lengkap di file .env!")
    POSTGRES_URI: str = f"postgresql+psycopg://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Redis Broker & Result
    REDIS_URI: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8"
    )

configs = Config()

if configs.DEBUG == True:
    logger.warning(f"[*] Konfigurasi Mode Development, Harap tidak menggunakannya dalam mode Production!")
else:
    logger.info(f"[*] Konfigurasi Dalam Mode Productions!")
    