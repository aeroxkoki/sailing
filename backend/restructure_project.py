# -*- coding: utf-8 -*-
#\!/usr/bin/env python3
"""
プロジェクト構造の再編成スクリプト
このスクリプトは、FastAPIとディレクトリ構造のベストプラクティスに基づいて
セーリング戦略分析システムのバックエンドコードを再編成します。
"""

import os
import shutil
from pathlib import Path
import re

# ベースディレクトリ
BASE_DIR = Path(__file__).parent

# 新しいディレクトリ構造
NEW_DIRECTORIES = [
    "app/api/v1",
    "app/api/v1/endpoints",
    "app/core",
    "app/crud",
    "app/db",
    "app/db/base",
    "app/models",
    "app/schemas",
    "app/services",
    "app/utils",
    "migrations",
    "tests/api",
    "tests/crud",
    "tests/services",
]

# 既存ファイルのマッピング
FILE_MAPPINGS = {
    # Core設定ファイル
    "app/core/config.py": "app/core/config.py",
    "app/core/security.py": "app/core/security.py",
    "app/core/dependencies.py": "app/core/dependencies.py",
    
    # データベース関連
    "app/db/database.py": "app/db/session.py",
    "app/db/repositories/base_repository.py": "app/crud/base.py",
    
    # モデルとスキーマ
    "app/models/schemas/project.py": "app/schemas/project.py",
    "app/models/domain/project.py": "app/models/project.py",
    "app/models/schemas/session.py": "app/schemas/session.py",
    "app/models/domain/session.py": "app/models/session.py",
    "app/models/schemas/wind_data.py": "app/schemas/wind_data.py",
    "app/models/domain/wind_data.py": "app/models/wind_data.py",
    "app/models/schemas/strategy_point.py": "app/schemas/strategy_point.py",
    "app/models/domain/strategy_point.py": "app/models/strategy_point.py",
    
    # API エンドポイント
    "app/api/endpoints/health.py": "app/api/v1/endpoints/health.py",
    "app/api/endpoints/projects.py": "app/api/v1/endpoints/projects.py",
    "app/api/endpoints/sessions.py": "app/api/v1/endpoints/sessions.py",
    "app/api/endpoints/users.py": "app/api/v1/endpoints/users.py",
    "app/api/endpoints/data_import.py": "app/api/v1/endpoints/data_import.py",
    "app/api/endpoints/wind_estimation.py": "app/api/v1/endpoints/wind_estimation.py",
    "app/api/endpoints/strategy_detection.py": "app/api/v1/endpoints/strategy_detection.py",
    
    # サービス
    "app/services/project_service.py": "app/services/project_service.py",
    "app/services/wind_estimation_service.py": "app/services/wind_estimation_service.py",
    "app/services/strategy_detection_service.py": "app/services/strategy_detection_service.py",
    "app/services/data_import_service.py": "app/services/data_import_service.py",
    
    # ユーティリティ
    "app/utils/encoding_utils.py": "app/utils/encoding_utils.py",
    "app/utils/gps_utils.py": "app/utils/gps_utils.py",
    "app/utils/validation.py": "app/utils/validation.py",
}

# 新しい初期化ファイル
INIT_FILES = [
    "app/__init__.py",
    "app/api/__init__.py",
    "app/api/v1/__init__.py",
    "app/api/v1/endpoints/__init__.py",
    "app/core/__init__.py",
    "app/crud/__init__.py",
    "app/db/__init__.py",
    "app/db/base/__init__.py",
    "app/models/__init__.py",
    "app/schemas/__init__.py",
    "app/services/__init__.py",
    "app/utils/__init__.py",
]

# 新しく作成するファイル
NEW_FILES = {
    "app/api/v1/api.py": '''"""
APIルータ設定
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    projects,
    sessions,
    users,
    data_import,
    wind_estimation,
    strategy_detection,
)

api_router = APIRouter()

# ヘルスチェック
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# プロジェクト管理
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

# セッション管理
api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"]
)

# ユーザー管理
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# データインポート
api_router.include_router(
    data_import.router,
    prefix="/data-import",
    tags=["data-import"]
)

# 風速推定
api_router.include_router(
    wind_estimation.router,
    prefix="/wind-estimation",
    tags=["wind-estimation"]
)

# 戦略検出
api_router.include_router(
    strategy_detection.router,
    prefix="/strategy-detection",
    tags=["strategy-detection"]
)
''',
    
    "app/db/base/base_class.py": '''"""
ベースSQLAlchemyモデル
"""

from typing import Any
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


@as_declarative()
class Base:
    """
    SQLAlchemyベースクラス
    """
    id: Any
    __name__: str
    
    # テーブル名をクラス名から自動生成
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
    
    # 共通カラム
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
''',
    
    "app/db/base/__init__.py": '''# SQLAlchemy Base をインポート
from app.db.base.base_class import Base  # noqa

# すべてのモデルをインポート
from app.models.project import Project  # noqa
from app.models.session import Session  # noqa
# 他のモデルも必要に応じてインポート
''',

    "app/db/init_db.py": '''"""
データベース初期化
"""

import logging
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine


def init_db(db: Session) -> None:
    """初期データベース設定"""
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    # ここに初期データ投入ロジックを追加
    logging.info("データベース初期化完了")
''',

    "app/crud/project.py": '''"""
プロジェクトCRUD操作
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """プロジェクト用CRUD操作"""
    
    def get_by_user(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """ユーザーIDでプロジェクトを取得"""
        return (
            db.query(self.model)
            .filter(Project.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_name(
        self, db: Session, *, name: str, user_id: Optional[UUID] = None
    ) -> List[Project]:
        """名前でプロジェクトを検索"""
        query = db.query(self.model).filter(
            Project.name.ilike(f"%{name}%")
        )
        
        if user_id:
            query = query.filter(Project.user_id == user_id)
            
        return query.all()


# CRUDクラスのインスタンス
project = CRUDProject(Project)
''',

    "app/crud/base.py": '''"""
CRUD基本クラス
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base.base_class import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    基本CRUD操作のジェネリックベースクラス
    """
    
    def __init__(self, model: Type[ModelType]):
        """モデルクラスで初期化"""
        self.model = model

    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """IDでアイテムを取得"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """複数アイテムを取得"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType, user_id: UUID = None) -> ModelType:
        """新規アイテムを作成"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        
        # user_idがあれば設定
        if user_id is not None and hasattr(self.model, "user_id"):
            db_obj.user_id = user_id
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """アイテムを更新"""
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: UUID) -> ModelType:
        """アイテムを削除"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
''',

    "app/main.py": '''"""
FastAPI メインアプリケーション
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS設定
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Gzip圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# APIルータ登録
app.include_router(api_router, prefix=settings.API_V1_STR)

# ルートパス
@app.get("/")
async def root():
    """
    ルートパスへのアクセス
    """
    return {
        "message": "セーリング戦略分析システム API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }
'''
}

def create_directory_structure():
    """新しいディレクトリ構造を作成"""
    print("ディレクトリ構造を作成中...")
    
    # バックアップディレクトリを作成
    backup_dir = BASE_DIR / "backup_structure"
    backup_dir.mkdir(exist_ok=True)
    
    # 新しいディレクトリを作成
    for directory in NEW_DIRECTORIES:
        path = BASE_DIR / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"作成: {path}")

def create_init_files():
    """__init__.pyファイルを作成"""
    print("\n__init__.pyファイルを作成中...")
    
    for file_path in INIT_FILES:
        path = BASE_DIR / file_path
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                f.write('"""初期化ファイル"""\n')
            print(f"作成: {path}")

def create_new_files():
    """新しいファイルを作成"""
    print("\n新しいファイルを作成中...")
    
    for file_path, content in NEW_FILES.items():
        path = BASE_DIR / file_path
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"作成: {path}")

def migrate_existing_files():
    """既存ファイルを新しい場所に移動"""
    print("\n既存ファイルを移行中...")
    
    for src_path, dest_path in FILE_MAPPINGS.items():
        src = BASE_DIR / src_path
        dest = BASE_DIR / dest_path
        
        # ソースファイルが存在する場合のみ処理
        if src.exists():
            # 宛先ディレクトリが存在しない場合は作成
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルをコピー
            if not dest.exists() or not files_are_identical(src, dest):
                shutil.copy2(src, dest)
                print(f"コピー: {src} -> {dest}")
            else:
                print(f"スキップ: {src} (同一ファイル)")

def files_are_identical(file1, file2):
    """2つのファイルが同一かどうかをチェック"""
    if not file1.exists() or not file2.exists():
        return False
        
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        return f1.read() == f2.read()

def main():
    """メイン実行関数"""
    print("セーリング戦略分析システム - プロジェクト構造再編成")
    print("=" * 50)
    
    create_directory_structure()
    create_init_files()
    create_new_files()
    migrate_existing_files()
    
    print("\n完了: プロジェクト構造の再編成が完了しました")
    print("\n次のステップ:")
    print("1. git add . && git commit -m \"プロジェクト構造の再編成\"")
    print("2. git push")
    print("3. Renderでの再デプロイ")

if __name__ == "__main__":
    main()
