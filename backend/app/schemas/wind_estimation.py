"""
風向風速推定スキーマ

風向風速推定APIで使用するスキーマを定義
"""

from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class FileFormat(str, Enum):
    """ファイル形式"""
    CSV = "csv"
    GPX = "gpx"
    FIT = "fit"


class BoatType(str, Enum):
    """ボート種類"""
    DEFAULT = "default"
    LASER = "laser"
    OPTIMIST = "optimist"
    YACHT = "yacht"
    WINDSURFER = "windsurfer"
    CUSTOM = "custom"


class WindEstimationInput(BaseModel):
    """風向風速推定入力パラメータ"""
    file_format: FileFormat = Field(..., description="ファイル形式（csv, gpx, fit）")
    boat_type: BoatType = Field(BoatType.DEFAULT, description="ボート種類")
    min_tack_angle: float = Field(45.0, description="最小タック角度（度）")
    use_bayesian: bool = Field(True, description="ベイジアン推定を使用するかどうか")
    project_id: Optional[UUID] = Field(None, description="プロジェクトID")
    session_name: Optional[str] = Field(None, description="セッション名")
    time_interval: Optional[int] = Field(None, description="時間間隔（秒）")

    class Config:
        use_enum_values = True
