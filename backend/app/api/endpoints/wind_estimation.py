"""
¨¨¨šk¢Y‹API¨óÉİ¤óÈ
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
# Ÿ›nŸÅgoånâ¸åüë’(
# from app.models.schemas.wind_data import WindDataCreate, WindData, WindField
# from app.services.wind_estimation_service import wind_estimation_service


router = APIRouter()


@router.post("/estimate", status_code=status.HTTP_202_ACCEPTED)
async def estimate_wind(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    settings: Optional[Dict[str, Any]] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    GPSÇü¿K‰¨¨’¨šY‹
    
    ^æhWf¨¨¨š¸çÖ’{2W¸çÖID’ÔY
    
    Args:
        session_id: æşan»Ã·çóID
        file: GPSÇü¿Õ¡¤ëCSVGPXI	
        settings: ¨¨¨šn-šª×·çó	
    """
    # Õ¡¤ën<Ÿ›nŸÅgos0k<	
    if file.content_type not in ["text/csv", "application/gpx+xml", "application/octet-stream"]:
        raise HTTPException(
            status_code=400,
            detail="File format not supported. Please upload CSV or GPX file."
        )
    
    # »Ã·çóLX(Y‹K¢¯»¹)LB‹Knº
    # Ÿ›nŸÅgoånˆFjÁ§Ã¯’LF
    """
    session = session_service.get(db, id=session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    if session.user_id != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    """
    
    # ¨¨¨š¸çÖn{2
    # Ÿ›nŸÅgo^¿¹¯hWfŸL
    # job_id = wind_estimation_service.start_estimation_job(
    #     db, session_id=session_id, file=file, settings=settings, user_id=current_user["id"]
    # )
    
    # âÃ¯n¸çÖID’ÔY
    job_id = "123e4567-e89b-12d3-a456-426614174000"
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Wind estimation job has been queued and will be processed shortly."
    }


@router.get("/job/{job_id}")
async def get_estimation_job_status(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    ¨¨¨š¸çÖn¹Æü¿¹’Ö—Y‹
    
    Args:
        job_id: ¸çÖID
    """
    # Ÿ›nŸÅgo¸çÖ¹Æü¿¹’Ö—
    # job = wind_estimation_service.get_job(db, job_id=job_id, user_id=current_user["id"])
    # if not job:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="Job not found"
    #     )
    
    # âÃ¯n¸çÖ¹Æü¿¹’ÔY
    job_status = {
        "job_id": str(job_id),
        "status": "processing",  # queued, processing, completed, failed
        "progress": 65,  # Ñü»óÈ
        "started_at": "2025-04-18T12:30:00",
        "estimated_completion": "2025-04-18T12:35:00",
        "message": "Processing GPS data and estimating wind information."
    }
    
    return job_status


@router.get("/session/{session_id}")
async def get_wind_data(
    session_id: UUID,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    »Ã·çón¨¨Çü¿’Ö—Y‹
    
    Args:
        session_id: »Ã·çóID
        start_time: Ö—‹ËB;ISO 8601bª×·çó	
        end_time: Ö—B†B;ISO 8601bª×·çó	
        skip: ¹­Ã×Y‹ì³üÉp
        limit: Ö—Y‹ì³üÉpn
P
    """
    # Ÿ›nŸÅgoÇü¿Ùü¹K‰Çü¿’Ö—
    # data = wind_estimation_service.get_wind_data(
    #     db, session_id=session_id, start_time=start_time, end_time=end_time,
    #     skip=skip, limit=limit, user_id=current_user["id"]
    # )
    
    # âÃ¯Çü¿’ÔY
    mock_data = [
        {
            "id": "223e4567-e89b-12d3-a456-426614174001",
            "timestamp": "2025-04-18T10:00:00",
            "latitude": 35.123,
            "longitude": 139.456,
            "wind_direction": 270.5,
            "wind_speed": 12.3,
            "confidence": 0.85
        },
        {
            "id": "323e4567-e89b-12d3-a456-426614174002",
            "timestamp": "2025-04-18T10:00:15",
            "latitude": 35.1235,
            "longitude": 139.4565,
            "wind_direction": 271.2,
            "wind_speed": 12.5,
            "confidence": 0.87
        },
        {
            "id": "423e4567-e89b-12d3-a456-426614174003",
            "timestamp": "2025-04-18T10:00:30",
            "latitude": 35.124,
            "longitude": 139.457,
            "wind_direction": 272.0,
            "wind_speed": 12.8,
            "confidence": 0.86
        }
    ]
    
    return {
        "session_id": str(session_id),
        "data": mock_data,
        "total": 180,  # ÏÇü¿p
        "skip": skip,
        "limit": limit
    }


@router.get("/field/{session_id}")
async def get_wind_field(
    session_id: UUID,
    timestamp: str,
    resolution: Optional[int] = Query(20, ge=5, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    šW_B;n»Ã·çón¨n4Çü¿’Ö—Y‹
    
    Args:
        session_id: »Ã·çóID
        timestamp: B;ISO 8601b	
        resolution: ãÏ¦°êÃÉµ¤ºª×·çó	
    """
    # Ÿ›nŸÅgoÇü¿Ùü¹K‰¨n4Çü¿’Ö—
    # field = wind_estimation_service.get_wind_field(
    #     db, session_id=session_id, timestamp=timestamp,
    #     resolution=resolution, user_id=current_user["id"]
    # )
    
    # âÃ¯n¨n4Çü¿’ÔY
    # !en_5x5°êÃÉn‹’:Y
    field_data = {
        "grid_size": 0.001,  # ¦XM
        "min_latitude": 35.120,
        "max_latitude": 35.130,
        "min_longitude": 139.450,
        "max_longitude": 139.460,
        "resolution": 5,
        "data": [
            # °êÃÉn¨¨Çü¿
            # format: [latitude, longitude, wind_direction, wind_speed]
            [35.120, 139.450, 270.5, 12.3],
            [35.120, 139.452, 271.2, 12.5],
            [35.120, 139.455, 272.0, 12.8],
            [35.120, 139.458, 271.5, 12.6],
            [35.120, 139.460, 270.8, 12.4],
            
            [35.123, 139.450, 269.5, 12.2],
            [35.123, 139.452, 270.2, 12.4],
            [35.123, 139.455, 271.0, 12.7],
            [35.123, 139.458, 270.5, 12.5],
            [35.123, 139.460, 269.8, 12.3],
            
            [35.125, 139.450, 268.5, 12.1],
            [35.125, 139.452, 269.2, 12.3],
            [35.125, 139.455, 270.0, 12.6],
            [35.125, 139.458, 269.5, 12.4],
            [35.125, 139.460, 268.8, 12.2],
            
            [35.128, 139.450, 267.5, 12.0],
            [35.128, 139.452, 268.2, 12.2],
            [35.128, 139.455, 269.0, 12.5],
            [35.128, 139.458, 268.5, 12.3],
            [35.128, 139.460, 267.8, 12.1],
            
            [35.130, 139.450, 266.5, 11.9],
            [35.130, 139.452, 267.2, 12.1],
            [35.130, 139.455, 268.0, 12.4],
            [35.130, 139.458, 267.5, 12.2],
            [35.130, 139.460, 266.8, 12.0]
        ]
    }
    
    return {
        "session_id": str(session_id),
        "timestamp": timestamp,
        "field": field_data
    }
