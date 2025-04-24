# -*- coding: utf-8 -*-
"""
Wind Estimation API Endpoints
"""

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
    """
    GPSデータから風向風速を推定します。
    
    パラメータ:
    - gps_data: GPSデータファイル
    - params: 風速推定パラメータ
    
    戻り値:
    - 風向風速推定結果
    """
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
