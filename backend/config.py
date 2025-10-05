"""
Configuration centralisée de l'application
Gestion des variables d'environnement et settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import secrets


class Settings(BaseSettings):
    """Configuration de l'application avec validation"""
    
    # Serveur
    PORT: int = Field(default=8000, env='PORT')
    HOST: str = Field(default='0.0.0.0', env='HOST')
    ENV: str = Field(default='production', env='ENV')
    DEBUG: bool = Field(default=False, env='DEBUG')
    
    # Sécurité
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = Field(default='HS256')
    JWT_EXPIRATION_HOURS: int = Field(default=24)
    ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    # CORS
    ALLOWED_ORIGINS: str = Field(
        default='http://localhost:3000',
        env='ALLOWED_ORIGINS'
    )
    
    @validator('ALLOWED_ORIGINS')
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Redis
    REDIS_URL: str = Field(default='redis://localhost:6379/0', env='REDIS_URL')
    REDIS_PASSWORD: str = Field(default='', env='REDIS_PASSWORD')
    SESSION_EXPIRATION_SECONDS: int = Field(default=86400)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000)
    
    # OpenRouter
    OPENROUTER_API_KEY: str = Field(default='', env='OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL: str = Field(
        default='https://openrouter.ai/api/v1',
        env='OPENROUTER_BASE_URL'
    )
    
    # Selenium
    SELENIUM_HEADLESS: bool = Field(default=True)
    SELENIUM_TIMEOUT_SECONDS: int = Field(default=30)
    WEBDRIVER_PATH: str = Field(default='/usr/local/bin/chromedriver')
    
    # Logs
    LOG_LEVEL: str = Field(default='INFO')
    LOG_FILE: str = Field(default='logs/app.log')
    
    # Pronote
    PRONOTE_DEFAULT_ACCOUNT_TYPE: int = Field(default=3)  # 3 = élève
    PRONOTE_REQUEST_TIMEOUT: int = Field(default=30)
    
    # Monitoring
    SENTRY_DSN: str = Field(default='', env='SENTRY_DSN')
    ENABLE_METRICS: bool = Field(default=True)
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True


# Instance globale des settings
settings = Settings()


# Validation au démarrage
def validate_config():
    """Valide la configuration au démarrage de l'application"""
    errors = []
    
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY doit faire au moins 32 caractères")
    
    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        errors.append("JWT_SECRET_KEY doit faire au moins 32 caractères")
    
    if settings.ENV == 'production' and settings.DEBUG:
        errors.append("DEBUG ne doit pas être activé en production")
    
    if not settings.OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY est requis pour l'IA")
    
    if errors:
        raise ValueError(f"Erreurs de configuration:\n" + "\n".join(f"- {e}" for e in errors))
    
    return True
