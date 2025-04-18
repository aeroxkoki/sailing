"""
�������-�����
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional, Union


class Settings(BaseSettings):
    """�������-���"""
    
    # �������h,-�
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    PROJECT_NAME: str = Field(default="����&e�����")
    API_V1_STR: str = Field(default="/api/v1")
    
    # CORSn1����-�
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    
    # ������-�
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/sailing_analyzer")
    
    # Supabase-�
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_KEY: Optional[str] = Field(default=None)
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None)
    
    # ����ƣ-�
    SECRET_KEY: str = Field(default="secret_key_for_development_only")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # �����-�
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # CORSn-��W���k	�
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# -����n\
settings = Settings()
