"""
����ݸ������
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import Base


# ���n��
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD�\n�,��
    
    �������\n�,�j��ɒЛW~Y
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Base repository model
        
        Args:
            model: A SQLAlchemy model class
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """IDg�ָ��Ȓ֗Y�"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """p�ָ��Ȓ֗Y�"""
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """���ָ��Ȓ\Y�"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
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
        """�ָ��Ȓ��Y�"""
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
    
    def remove(self, db: Session, *, id: int) -> ModelType:
        """�ָ��ȒJdY�"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


class SupabaseRepository:
    """
    Supabase�(W_�ݸ��n�,��
    
    Supabasen�����\n_�n�,��ɒЛW~Y
    """
    
    def __init__(self, table_name: str):
        """
        Args:
            table_name: Supabasen����
        """
        self.table_name = table_name
    
    async def get(self, supabase_client, id: str) -> Dict:
        """IDg�ָ��Ȓ֗Y�"""
        response = supabase_client.table(self.table_name).select("*").eq("id", id).execute()
        if response.data:
            return response.data[0]
        return None
    
    async def get_multi(
        self, supabase_client, *, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """p�ָ��Ȓ֗Y�"""
        response = supabase_client.table(self.table_name).select("*").range(skip, skip + limit - 1).execute()
        return response.data
    
    async def create(self, supabase_client, *, obj_in: Dict) -> Dict:
        """���ָ��Ȓ\Y�"""
        response = supabase_client.table(self.table_name).insert(obj_in).execute()
        if response.data:
            return response.data[0]
        return None
    
    async def update(self, supabase_client, *, id: str, obj_in: Dict) -> Dict:
        """�ָ��Ȓ��Y�"""
        response = supabase_client.table(self.table_name).update(obj_in).eq("id", id).execute()
        if response.data:
            return response.data[0]
        return None
    
    async def remove(self, supabase_client, *, id: str) -> Dict:
        """�ָ��ȒJdY�"""
        response = supabase_client.table(self.table_name).delete().eq("id", id).execute()
        if response.data:
            return response.data[0]
        return None
