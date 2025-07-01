import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
JWT_HASH_ALGORITHM = os.getenv("JWT_HASH_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS"))
HASH_ALGORITHM = os.getenv("HASH_ALGORITHM")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")


# PostgreSQL Database connection
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
)

# Async PostgreSQL Database connection
ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
)

# Chat settings
DEFAULT_CHAT_MODEL = os.getenv("DEFAULT_CHAT_MODEL", "gemini-2.0-flash")
DEFAULT_SYSTEM_PROMPT = os.getenv("DEFAULT_SYSTEM_PROMPT", "You are a helpful AI assistant.")

class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "Deckoviz AI"
    debug: bool = DEBUG
    secret_key: str = SECRET_KEY
    database_url: str = DATABASE_URL
    async_database_url: str = ASYNC_DATABASE_URL
    default_chat_model: str = DEFAULT_CHAT_MODEL
    default_system_prompt: str = DEFAULT_SYSTEM_PROMPT
    jwt_hash_algorithm: str = JWT_HASH_ALGORITHM
    jwt_access_token_expire_minutes: int = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    jwt_refresh_token_expire_days: int = JWT_REFRESH_TOKEN_EXPIRE_DAYS
    hash_algorithm: str = os.getenv("HASH_ALGORITHM", "bcrypt")
    
    # Server settings
    server_name: str = os.getenv("SERVER_NAME", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "7862"))

    # Google Gemini API key
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Langsmith API key
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    
    # Runware API key
    runware_api_key: str = os.getenv("RUNWARE_API_KEY", "")
    
    # AssemblyAI API key
    assemblyai_api_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    
    # Elevenlabs API key
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    # AWS 
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_bucket_name: str = os.getenv("AWS_BUCKET_NAME", "")
    aws_region: str = os.getenv("AWS_REGION", "")
    
    # Database connection settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_name: str = os.getenv("DB_NAME", "postgres")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")

    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: str = os.getenv("REDIS_PASSWORD", None)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # SQLite settings
    sqlite_url: str = os.getenv("SQLITE_URL", "sqlite:///data/chat_history.db")
    async_sqlite_url: str = os.getenv("ASYNC_SQLITE_URL", "sqlite+aiosqlite:///data/chat_history.db")
    
    # Celery settings
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Pinecone API keys
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    
    # Milvus settings
    milvus_token: str = os.getenv("MILVUS_TOKEN", "")
    milvus_uri: str = os.getenv("MILVUS_URI", "")
    
    # Twilio settings
    twilio_sid: str = os.getenv("TWILIO_SID", "")
    twilio_token: str = os.getenv("TWILIO_TOKEN", "")
    twilio_phone: str = os.getenv("TWILIO_PHONE", "")


    # MongoDB settings
    mongo_db_url: str = os.getenv("MONGO_DB_URL", "")

    # AWS settings
    aws_base_url: str = os.getenv("AWS_BASE_URL", "")

    # Replicate API key
    replicate_api_token: str = os.getenv("REPLICATE_API_TOKEN", "")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    """Get cached settings"""
    return Settings()

# Function to clear the settings cache when needed
def clear_settings_cache():
    """Invalidate the settings cache to pick up new environment variables"""
    get_settings.cache_clear()
 

