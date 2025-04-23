"""
プロジェクトCRUD操作
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.repositories.base_repository import BaseRepository
from app.models.schemas.project import ProjectCreate, ProjectUpdate
from app.db.models.project import Project


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    """プロジェクトリポジトリ"""
    pass


# リポジトリインスタンス
project_repository = ProjectRepository(Project)


def get_project(db: Session, project_id: UUID, user_id: UUID) -> Optional[Project]:
    """
    特定のプロジェクトを取得
    
    Args:
        db: データベースセッション
        project_id: プロジェクトID
        user_id: ユーザーID
        
    Returns:
        Project: プロジェクト情報
    """
    return project_repository.get_by_user_id(db=db, user_id=user_id, id=project_id)


def get_projects(
    db: Session, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 100,
    name: Optional[str] = None
) -> List[Project]:
    """
    ユーザーのプロジェクト一覧を取得
    
    Args:
        db: データベースセッション
        user_id: ユーザーID
        skip: スキップする件数
        limit: 取得する最大件数
        name: 名前で検索（部分一致）
        
    Returns:
        List[Project]: プロジェクト一覧
    """
    query = db.query(Project).filter(Project.user_id == user_id)
    
    if name:
        query = query.filter(Project.name.ilike(f"%{name}%"))
    
    return query.offset(skip).limit(limit).all()


def create_project(db: Session, obj_in: ProjectCreate, user_id: UUID) -> Project:
    """
    新しいプロジェクトを作成
    
    Args:
        db: データベースセッション
        obj_in: 作成するプロジェクト情報
        user_id: ユーザーID
        
    Returns:
        Project: 作成されたプロジェクト
    """
    return project_repository.create(db=db, obj_in=obj_in, user_id=user_id)


def update_project(db: Session, db_obj: Project, obj_in: ProjectUpdate) -> Project:
    """
    プロジェクト情報を更新
    
    Args:
        db: データベースセッション
        db_obj: 更新対象のプロジェクト
        obj_in: 更新する情報
        
    Returns:
        Project: 更新されたプロジェクト
    """
    return project_repository.update(db=db, db_obj=db_obj, obj_in=obj_in)


def delete_project(db: Session, project_id: UUID) -> Project:
    """
    プロジェクトを削除
    
    Args:
        db: データベースセッション
        project_id: 削除するプロジェクトID
        
    Returns:
        Project: 削除されたプロジェクト
    """
    return project_repository.remove(db=db, id=project_id)
