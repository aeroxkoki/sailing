# -*- coding: utf-8 -*-
"""
プロジェクト管理API
"""

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.crud.project import project
from app.schemas.project import Project, ProjectCreate, ProjectUpdate

router = APIRouter()

@router.post(
    "/",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="新規プロジェクト作成",
    description="新しいプロジェクトを作成します",
)
def create_new_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    """
    新しいプロジェクトを作成します。
    
    パラメータ:
    - project_in: プロジェクト作成情報
    
    戻り値:
    - 作成されたプロジェクト情報
    """
    return project.create(db=db, obj_in=project_in, user_id=user_id)

@router.get(
    "/",
    response_model=List[Project],
    status_code=status.HTTP_200_OK,
    summary="プロジェクト一覧取得",
    description="ユーザーのプロジェクト一覧を取得します",
)
def read_projects(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None, description="プロジェクト名による検索"),
) -> Any:
    """
    ユーザーのプロジェクト一覧を取得します。
    
    パラメータ:
    - skip: スキップする件数
    - limit: 取得する最大件数
    - name: プロジェクト名による検索（オプション）
    
    戻り値:
    - プロジェクト一覧
    """
    if name:
        return project.get_by_name(db=db, name=name, user_id=user_id)
    return project.get_by_user(db=db, user_id=user_id, skip=skip, limit=limit)

@router.get(
    "/{project_id}",
    response_model=Project,
    status_code=status.HTTP_200_OK,
    summary="プロジェクト詳細取得",
    description="プロジェクトの詳細情報を取得します",
)
def read_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    """
    指定されたプロジェクトの詳細情報を取得します。
    
    パラメータ:
    - project_id: プロジェクトID
    
    戻り値:
    - プロジェクト詳細情報
    """
    db_project = project.get(db=db, id=project_id)
    if not db_project or db_project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    return db_project

@router.put(
    "/{project_id}",
    response_model=Project,
    status_code=status.HTTP_200_OK,
    summary="プロジェクト更新",
    description="プロジェクト情報を更新します",
)
def update_project_info(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    """
    プロジェクト情報を更新します。
    
    パラメータ:
    - project_id: プロジェクトID
    - project_in: 更新するプロジェクト情報
    
    戻り値:
    - 更新されたプロジェクト情報
    """
    db_project = project.get(db=db, id=project_id)
    if not db_project or db_project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    
    return project.update(db=db, db_obj=db_project, obj_in=project_in)

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="プロジェクト削除",
    description="プロジェクトを削除します",
)
def delete_project_by_id(
    project_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    """
    プロジェクトを削除します。
    
    パラメータ:
    - project_id: 削除するプロジェクトのID
    
    戻り値:
    - なし
    """
    db_project = project.get(db=db, id=project_id)
    if not db_project or db_project.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    
    project.remove(db=db, id=project_id)
    return None
