"""
リポジトリベースクラス
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Union
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import inspect
from pydantic import BaseModel

from app.db.database import Base

# タイプ変数
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    基本リポジトリクラス - CRUD操作の共通ロジックを提供
    """

    def __init__(self, model: Type[ModelType]):
        """
        モデルクラスで初期化
        """
        self.model = model

    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """
        IDで単一アイテムを取得
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_user_id(self, db: Session, user_id: UUID, id: UUID) -> Optional[ModelType]:
        """
        ユーザーIDとアイテムIDで取得
        """
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.user_id == user_id
        ).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        複数アイテムを取得
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_multi_by_user(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        ユーザーIDで複数アイテムを取得
        """
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType, user_id: UUID) -> ModelType:
        """
        新規アイテムを作成
        """
        obj_in_data = obj_in.model_dump()
        obj_in_data["user_id"] = user_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        アイテムを更新
        """
        obj_data = inspect(db_obj).dict
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: UUID) -> ModelType:
        """
        アイテムを削除
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
