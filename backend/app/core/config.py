"""
セーリング戦略分析システム - 設定ファイル
"""

import os
from pydantic import Field, BaseSettings
from typing import List, Optional, Union


class Settings(BaseSettings):
    """アプリケーション設定クラス"""
    
    # 基本設定
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    PROJECT_NAME: str = Field(default="セーリング戦略分析システム")
    API_V1_STR: str = Field(default="/api/v1")
    API_VERSION: str = Field(default="0.1.0")
    
    # CORS設定
    CORS_ORIGINS: Union[List[str], str] = Field(default=["http://localhost:3000"])
    
    # データベース設定
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/sailing_analyzer")
    
    # Supabase設定
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_KEY: Optional[str] = Field(default=None)
    SUPABASE_JWT_SECRET: Optional[str] = Field(default=None)
    
    # 認証設定
    SECRET_KEY: str = Field(default="secret_key_for_development_only")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # ファイル設定
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    
    # エンコーディング設定
    ENCODING: str = Field(default="utf-8")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        # 環境変数からCORS_ORIGINSを直接取得して処理する
        if "CORS_ORIGINS" in os.environ:
            cors_env = os.environ.get("CORS_ORIGINS")
            if cors_env:
                kwargs["CORS_ORIGINS"] = [origin.strip() for origin in cors_env.split(",")]
        
        super().__init__(**kwargs)
        
        # 初期化後も文字列の場合はリストに変換
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 設定インスタンスの生成
settings = Settings()
