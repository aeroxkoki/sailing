#\!/usr/bin/env python3
import os

def recreate_file(file_path, content):
    """ファイルを最初から作り直す"""
    try:
        # ファイルが存在する場合は削除
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 新しいファイルを作成して内容を書き込む
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"再作成完了: {file_path}")
        return True
    except Exception as e:
        print(f"エラー ({file_path}): {e}")
        return False

# 各ファイルのコンテンツ
wind_estimation_content = """\"\"\"
Wind Estimation API Endpoints
\"\"\"

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.schemas.wind_estimation import WindEstimationResult, WindEstimationInput
from app.services.wind_estimation_service import estimate_wind

router = APIRouter()

@router.post(
    "/estimate",
    response_model=WindEstimationResult,
    status_code=status.HTTP_200_OK,
    summary="風速推定を実行",
    description="GPSデータから風向風速を推定します",
)
async def perform_wind_estimation(
    db: Session = Depends(get_db),
    gps_data: UploadFile = File(...),
    params: WindEstimationInput = Depends(),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    \"\"\"
    GPSデータから風向風速を推定します。
    
    パラメータ:
    - gps_data: GPSデータファイル
    - params: 風速推定パラメータ
    
    戻り値:
    - 風向風速推定結果
    \"\"\"
    try:
        # ファイルの内容を読み込む
        contents = await gps_data.read()
        
        # 風速推定サービスを呼び出す
        result = estimate_wind(
            gps_data=contents,
            params=params,
            user_id=user_id,
            db=db
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"風速推定処理でエラーが発生しました: {str(e)}"
        )
"""

strategy_detection_content = """\"\"\"
Strategy Detection API Endpoints
\"\"\"

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.schemas.strategy_detection import StrategyDetectionResult, StrategyDetectionInput
from app.services.strategy_detection_service import detect_strategies

router = APIRouter()

@router.post(
    "/detect",
    response_model=StrategyDetectionResult,
    status_code=status.HTTP_200_OK,
    summary="戦略検出を実行",
    description="航跡データから戦略を検出します",
)
async def perform_strategy_detection(
    params: StrategyDetectionInput,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
) -> Any:
    \"\"\"
    航跡データと風向風速データから戦略を検出します。
    
    パラメータ:
    - params: 戦略検出パラメータ
    
    戻り値:
    - 戦略検出結果
    \"\"\"
    try:
        # 戦略検出サービスを呼び出す
        result = detect_strategies(
            params=params,
            user_id=user_id,
            db=db
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"戦略検出処理でエラーが発生しました: {str(e)}"
        )
"""

health_content = """\"\"\"
ヘルスチェックAPI
\"\"\"

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.health_service import check_database, check_api_services

router = APIRouter()

@router.get(
    "/",
    response_class=JSONResponse,
    summary="システム状態を確認",
    description="APIサーバーの状態を確認します",
)
async def health_check():
    \"\"\"
    システムの健全性をチェックします
    
    戻り値:
    - status: システム状態
    - version: APIバージョン
    - services: 各サービスのステータス
    \"\"\"
    # データベース接続チェック
    db_status = await check_database()
    
    # 外部APIサービスチェック
    api_status = await check_api_services()
    
    return {
        "status": "ok",
        "version": settings.API_VERSION,
        "services": {
            "database": db_status,
            "api_services": api_status
        }
    }

@router.get(
    "/ping",
    response_class=JSONResponse,
    summary="簡易接続チェック",
    description="APIサーバーへの簡易接続チェック",
)
async def ping():
    \"\"\"
    シンプルな接続チェック
    
    戻り値:
    - ping: "pong"
    \"\"\"
    return {
        "ping": "pong"
    }
"""

projects_content = """\"\"\"
プロジェクト管理API
\"\"\"

from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.crud.project import create_project, get_project, get_projects, update_project, delete_project
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
    \"\"\"
    新しいプロジェクトを作成します。
    
    パラメータ:
    - project_in: プロジェクト作成情報
    
    戻り値:
    - 作成されたプロジェクト情報
    \"\"\"
    project = create_project(db=db, obj_in=project_in, user_id=user_id)
    return project

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
    \"\"\"
    ユーザーのプロジェクト一覧を取得します。
    
    パラメータ:
    - skip: スキップする件数
    - limit: 取得する最大件数
    - name: プロジェクト名による検索（オプション）
    
    戻り値:
    - プロジェクト一覧
    \"\"\"
    projects = get_projects(db=db, user_id=user_id, skip=skip, limit=limit, name=name)
    return projects

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
    \"\"\"
    指定されたプロジェクトの詳細情報を取得します。
    
    パラメータ:
    - project_id: プロジェクトID
    
    戻り値:
    - プロジェクト詳細情報
    \"\"\"
    project = get_project(db=db, project_id=project_id, user_id=user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    return project

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
    \"\"\"
    プロジェクト情報を更新します。
    
    パラメータ:
    - project_id: プロジェクトID
    - project_in: 更新するプロジェクト情報
    
    戻り値:
    - 更新されたプロジェクト情報
    \"\"\"
    project = get_project(db=db, project_id=project_id, user_id=user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    
    project = update_project(db=db, db_obj=project, obj_in=project_in)
    return project

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
    \"\"\"
    プロジェクトを削除します。
    
    パラメータ:
    - project_id: 削除するプロジェクトのID
    
    戻り値:
    - なし
    \"\"\"
    project = get_project(db=db, project_id=project_id, user_id=user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="プロジェクトが見つかりません"
        )
    
    delete_project(db=db, project_id=project_id)
    return None
"""

# ファイルを再作成
files_to_recreate = {
    "/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/backend/app/api/endpoints/wind_estimation.py": wind_estimation_content,
    "/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/backend/app/api/endpoints/strategy_detection.py": strategy_detection_content,
    "/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/backend/app/api/endpoints/health.py": health_content,
    "/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/backend/app/api/endpoints/projects.py": projects_content,
}

# 各ファイルを再作成
for file_path, content in files_to_recreate.items():
    recreate_file(file_path, content)

print("全ファイルの再作成が完了しました")
