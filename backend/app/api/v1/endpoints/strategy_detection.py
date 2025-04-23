"""
Strategy Detection API Endpoints
"""

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
    """
    航跡データと風向風速データから戦略を検出します。
    
    パラメータ:
    - params: 戦略検出パラメータ
    
    戻り値:
    - 戦略検出結果
    """
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
