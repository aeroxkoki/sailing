# -*- coding: utf-8 -*-
"""
ユーザー管理API

ユーザー情報の管理機能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any
from uuid import UUID

from app.core.dependencies import get_current_user, get_db

router = APIRouter()

@router.get(
    "/me",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="現在のユーザー情報取得",
    description="ログイン中のユーザー自身の情報を取得します",
)
async def get_current_user_info(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    """
    現在ログインしているユーザーの情報を取得します
    
    戻り値:
    - user: ユーザー情報
    """
    # 注: ここに実際のユーザー情報取得処理を実装
    # 現段階では仮実装
    
    return {
        "user_id": str(user_id),
        "username": "demo_user",
        "email": "demo@example.com"
    }
