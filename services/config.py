from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, List
from .log_config import logger
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    # Seurity & Fundamental
    SECRET_KEY: str = str(os.environ.get('SECRET_KEY'))
    DEBUG: bool = False
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
    POSTGRES_URI: str = str(os.environ.get("POSTGRES_URI"))
    
    # Redis Broker & Result
    REDIS_URI: str = str(os.environ.get("REDIS_URI"))
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8",
        extra='ignore'
    )

configs = Config()

if configs.DEBUG == True:
    logger.warning(f"[*] Konfigurasi Mode Development, Harap tidak menggunakannya dalam mode Production!")
else:
    logger.info(f"[*] Konfigurasi Dalam Mode Productions!")
    