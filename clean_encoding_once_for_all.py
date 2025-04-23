#\!/usr/bin/env python3
import os

# ファイルごとのコンテンツを定義
file_contents = {
    'backend/app/utils/__init__.py': '''"""
ユーティリティモジュール
"""
''',

    'backend/app/utils/gps_utils.py': '''"""
GPS関連ユーティリティ
"""

from typing import List, Tuple, Dict, Any, Optional
import math
import gpxpy
import numpy as np
from geopy.distance import geodesic

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離を計算（メートル単位）
    """
    return geodesic((lat1, lon1), (lat2, lon2)).meters

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の方位角を計算（度単位）
    """
    # ラジアンへ変換
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 方位角計算
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing = math.atan2(y, x)
    
    # 度に変換し、0-360度に正規化
    bearing_deg = math.degrees(bearing)
    return (bearing_deg + 360) % 360

def calculate_speed(distance: float, time_diff: float) -> float:
    """
    距離と時間差から速度を計算（ノット単位）
    """
    if time_diff <= 0:
        return 0.0
    
    # メートル/秒 からノットへ変換
    speed_ms = distance / time_diff
    speed_knots = speed_ms * 1.94384
    
    return speed_knots

def parse_gpx(gpx_content: str) -> List[Dict[str, Any]]:
    """
    GPXファイルの内容を解析しポイントのリストを返す
    """
    try:
        gpx = gpxpy.parse(gpx_content)
        points = []
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append({
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation,
                        'time': point.time,
                        'speed': getattr(point, 'speed', None),
                        'course': getattr(point, 'course', None)
                    })
        
        return points
    except Exception as e:
        raise ValueError(f"GPXデータの解析エラー: {str(e)}")

def interpolate_points(points: List[Dict[str, Any]], interval_seconds: int = 1) -> List[Dict[str, Any]]:
    """
    GPSポイントを指定間隔で補間する
    """
    if not points or len(points) < 2:
        return points
    
    # 時間情報がない場合は補間できない
    if 'time' not in points[0] or points[0]['time'] is None:
        return points
    
    interpolated = []
    for i in range(len(points) - 1):
        current = points[i]
        next_point = points[i + 1]
        
        # 現在のポイントを追加
        interpolated.append(current)
        
        # 時間差（秒）を計算
        time_diff = (next_point['time'] - current['time']).total_seconds()
        
        # 補間が必要な場合のみ処理
        if time_diff > interval_seconds:
            # 補間するポイント数
            num_points = int(time_diff / interval_seconds)
            
            for j in range(1, num_points):
                # 補間係数
                ratio = j / num_points
                
                # 位置の線形補間
                lat = current['latitude'] + ratio * (next_point['latitude'] - current['latitude'])
                lon = current['longitude'] + ratio * (next_point['longitude'] - current['longitude'])
                
                # 時間の補間
                time = current['time'] + (next_point['time'] - current['time']) * ratio
                
                # 速度と方位も補間
                speed = None
                course = None
                if current.get('speed') is not None and next_point.get('speed') is not None:
                    speed = current['speed'] + ratio * (next_point['speed'] - current['speed'])
                if current.get('course') is not None and next_point.get('course') is not None:
                    course = current['course'] + ratio * (next_point['course'] - current['course'])
                
                interpolated.append({
                    'latitude': lat,
                    'longitude': lon,
                    'elevation': current['elevation'] + ratio * (next_point['elevation'] - current['elevation']) if (current['elevation'] is not None and next_point['elevation'] is not None) else None,
                    'time': time,
                    'speed': speed,
                    'course': course,
                    'interpolated': True
                })
    
    # 最後のポイントを追加
    interpolated.append(points[-1])
    
    return interpolated
''',

    'backend/app/models/schemas/project.py': '''"""
プロジェクトスキーマ定義
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """プロジェクトベースモデル"""
    name: str = Field(..., description="プロジェクト名")
    description: Optional[str] = Field(None, description="プロジェクト説明")


class ProjectCreate(ProjectBase):
    """プロジェクト作成モデル"""
    pass


class ProjectUpdate(ProjectBase):
    """プロジェクト更新モデル"""
    name: Optional[str] = Field(None, description="プロジェクト名")


class Project(ProjectBase):
    """プロジェクトモデル"""
    id: UUID = Field(..., description="プロジェクトID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: UUID = Field(..., description="ユーザーID")
    
    class Config:
        from_attributes = True
''',

    'backend/app/models/domain/wind_data.py': '''"""
風データモデル
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WindDataPoint(BaseModel):
    """風データポイント"""
    timestamp: datetime = Field(..., description="タイムスタンプ")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="経度")
    speed: float = Field(..., description="風速（ノット）")
    direction: float = Field(..., description="風向（度）")
    confidence: float = Field(1.0, description="信頼度（0-1）")


class WindEstimationResult(BaseModel):
    """風推定結果"""
    wind_data: List[WindDataPoint] = Field(..., description="風データポイント")
    average_speed: float = Field(..., description="平均風速（ノット）")
    average_direction: float = Field(..., description="平均風向（度）")
    created_at: datetime = Field(..., description="作成日時")
    session_id: Optional[str] = Field(None, description="セッションID")


class WindPattern(BaseModel):
    """風のパターン"""
    pattern_type: str = Field(..., description="パターンタイプ")
    start_time: datetime = Field(..., description="開始時間")
    end_time: datetime = Field(..., description="終了時間")
    average_speed: float = Field(..., description="平均風速（ノット）")
    average_direction: float = Field(..., description="平均風向（度）")
    variation: float = Field(..., description="変動幅（度）")
    description: Optional[str] = Field(None, description="説明")
''',

    'backend/app/models/domain/session.py': '''"""
セッションモデル
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SessionBase(BaseModel):
    """セッションベースモデル"""
    name: str = Field(..., description="セッション名")
    description: Optional[str] = Field(None, description="セッション説明")
    date: datetime = Field(..., description="セッション日時")
    location: Optional[str] = Field(None, description="場所")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="気象条件")


class SessionCreate(SessionBase):
    """セッション作成モデル"""
    project_id: UUID = Field(..., description="プロジェクトID")
    gps_data_file: Optional[str] = Field(None, description="GPSデータファイル")


class SessionUpdate(BaseModel):
    """セッション更新モデル"""
    name: Optional[str] = Field(None, description="セッション名")
    description: Optional[str] = Field(None, description="セッション説明")
    date: Optional[datetime] = Field(None, description="セッション日時")
    location: Optional[str] = Field(None, description="場所")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="気象条件")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    strategy_detection_id: Optional[UUID] = Field(None, description="戦略検出ID")


class Session(SessionBase):
    """セッションモデル"""
    id: UUID = Field(..., description="セッションID")
    project_id: UUID = Field(..., description="プロジェクトID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: UUID = Field(..., description="ユーザーID")
    gps_data_file: Optional[str] = Field(None, description="GPSデータファイル")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    strategy_detection_id: Optional[UUID] = Field(None, description="戦略検出ID")
    
    class Config:
        from_attributes = True
''',

    'backend/app/models/domain/project.py': '''"""
プロジェクトモデル
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """プロジェクトベースモデル"""
    name: str = Field(..., description="プロジェクト名")
    description: Optional[str] = Field(None, description="プロジェクト説明")


class ProjectCreate(ProjectBase):
    """プロジェクト作成モデル"""
    pass


class ProjectUpdate(BaseModel):
    """プロジェクト更新モデル"""
    name: Optional[str] = Field(None, description="プロジェクト名")
    description: Optional[str] = Field(None, description="プロジェクト説明")


class Project(ProjectBase):
    """プロジェクトモデル"""
    id: UUID = Field(..., description="プロジェクトID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: UUID = Field(..., description="ユーザーID")
    
    class Config:
        from_attributes = True
''',

    'backend/app/models/domain/strategy_point.py': '''"""
戦略ポイントモデル
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class StrategyPoint(BaseModel):
    """戦略ポイント"""
    timestamp: datetime = Field(..., description="タイムスタンプ")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="経度")
    strategy_type: str = Field(..., description="戦略タイプ")
    confidence: float = Field(1.0, description="信頼度（0-1）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")


class StrategyDetectionResult(BaseModel):
    """戦略検出結果"""
    strategy_points: List[StrategyPoint] = Field(..., description="戦略ポイント")
    created_at: datetime = Field(..., description="作成日時")
    session_id: Optional[str] = Field(None, description="セッションID")
    track_length: Optional[float] = Field(None, description="航跡の長さ（メートル）")
    total_tacks: Optional[int] = Field(None, description="タックの総数")
    total_jibes: Optional[int] = Field(None, description="ジャイブの総数")
    upwind_percentage: Optional[float] = Field(None, description="アップウィンド割合（%）")
    downwind_percentage: Optional[float] = Field(None, description="ダウンウィンド割合（%）")
    reaching_percentage: Optional[float] = Field(None, description="リーチング割合（%）")
    performance_score: Optional[float] = Field(None, description="パフォーマンススコア（0-100）")
    recommendations: Optional[List[str]] = Field(None, description="推奨事項")


class StrategyDetectionInput(BaseModel):
    """戦略検出入力"""
    session_id: UUID = Field(..., description="セッションID")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    detection_sensitivity: Optional[float] = Field(0.5, description="検出感度（0-1）")
    min_tack_angle: Optional[float] = Field(45.0, description="最小タック角度（度）")
    min_jibe_angle: Optional[float] = Field(45.0, description="最小ジャイブ角度（度）")
''',

    'backend/app/db/repositories/base_repository.py': '''"""
リポジトリベースクラス
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Union
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import inspect
from pydantic import BaseModel

from app.db.database import Base

# タイプ変数
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    基本リポジトリクラス - CRUD操作の共通ロジックを提供
    """

    def __init__(self, model: Type[ModelType]):
        """
        モデルクラスで初期化
        """
        self.model = model

    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """
        IDで単一アイテムを取得
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_user_id(self, db: Session, user_id: UUID, id: UUID) -> Optional[ModelType]:
        """
        ユーザーIDとアイテムIDで取得
        """
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.user_id == user_id
        ).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        複数アイテムを取得
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_multi_by_user(
        self, db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        ユーザーIDで複数アイテムを取得
        """
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType, user_id: UUID) -> ModelType:
        """
        新規アイテムを作成
        """
        obj_in_data = obj_in.model_dump()
        obj_in_data["user_id"] = user_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        アイテムを更新
        """
        obj_data = inspect(db_obj).dict
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: UUID) -> ModelType:
        """
        アイテムを削除
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
'''
}

def save_files():
    """すべてのファイルを保存"""
    for file_path, content in file_contents.items():
        full_path = os.path.join(os.getcwd(), file_path)
        print(f"修正: {full_path}")
        
        # 安全のためディレクトリが存在することを確認
        directory = os.path.dirname(full_path)
        os.makedirs(directory, exist_ok=True)
        
        # 新しいコンテンツで保存
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    save_files()
    print("すべてのファイルのエンコーディングを修正しました")
