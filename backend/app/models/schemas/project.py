"""
�����ȹ�������
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# qn^'�d�����
class ProjectBase(BaseModel):
    """������n�,^'"""
    name: str = Field(..., min_length=1, max_length=100, description="������")
    description: Optional[str] = Field(None, max_length=500, description="������n�")
    is_public: bool = Field(False, description="l�-�truegl�	")


# ������\ꯨ��(
class ProjectCreate(ProjectBase):
    """������\���"""
    pass


# ��������ꯨ��(
class ProjectUpdate(BaseModel):
    """�����������"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="������")
    description: Optional[str] = Field(None, max_length=500, description="������n�")
    is_public: Optional[bool] = Field(None, description="l�-�truegl�	")


# ������K�֗W_�������1���(
class ProjectInDB(ProjectBase):
    """�������n���������"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# API���(����ƣ
n1g ��1�d	
class Project(ProjectInDB):
    """API���(���������"""
    
    class Config:
        orm_mode = True


# ������ ����(
class ProjectList(BaseModel):
    """������ ����"""
    items: List[Project]
    total: int
    skip: int
    limit: int
