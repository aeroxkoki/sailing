"""
プロジェクト削除APIのテスト
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schemas.project import ProjectCreate
from app.crud.project import create_project, get_project

def test_delete_project(client: TestClient, db: Session, normal_user_token_headers):
    """
    プロジェクト削除エンドポイントのテスト
    
    ステータスコード204のエンドポイントが正しく動作することを確認
    """
    # テスト用プロジェクトを作成
    project_in = ProjectCreate(
        name="テスト削除プロジェクト",
        description="削除テスト用のプロジェクト"
    )
    
    # ユーザーIDを取得（実際のアプリケーションに合わせて調整）
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")  # テスト用ユーザーIDを設定
    
    # プロジェクトを作成
    project = create_project(db=db, obj_in=project_in, user_id=user_id)
    project_id = project.id
    
    # プロジェクトが作成されたことを確認
    assert get_project(db=db, project_id=project_id, user_id=user_id) is not None
    
    # プロジェクトを削除
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{project_id}",
        headers=normal_user_token_headers,
    )
    
    # 削除が成功し、204 No Content が返ることを確認
    assert response.status_code == 204
    assert response.content == b''  # 204 No Contentではレスポンスボディが空であることを確認
    
    # プロジェクトが削除されたことを確認
    assert get_project(db=db, project_id=project_id, user_id=user_id) is None
