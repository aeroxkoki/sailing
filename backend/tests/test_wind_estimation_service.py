"""
風向風速推定サービスのテスト
"""

import pytest
from datetime import datetime
import pandas as pd
import numpy as np
import json
from uuid import uuid4

from app.services.wind_estimation_service import (
    _convert_bytes_to_dataframe,
    _calculate_average_direction,
    _create_wind_estimation_result
)
from app.schemas.wind_estimation import WindEstimationInput, FileFormat, BoatType

def test_convert_bytes_to_dataframe_csv():
    """CSVデータをDataFrameに変換するテスト"""
    # テスト用CSVデータ
    csv_data = """timestamp,latitude,longitude,speed,course
2023-01-01T12:00:00,35.0,139.0,5.2,270.0
2023-01-01T12:01:00,35.01,139.01,5.3,272.0
2023-01-01T12:02:00,35.02,139.02,5.1,268.0
"""
    # バイト列に変換
    csv_bytes = csv_data.encode('utf-8')
    
    # 関数を実行
    df = _convert_bytes_to_dataframe(csv_bytes, 'csv')
    
    # 結果を検証
    assert df is not None
    assert len(df) == 3
    assert list(df.columns) == ['timestamp', 'latitude', 'longitude', 'speed', 'course']
    assert df['latitude'].iloc[0] == 35.0
    assert df['longitude'].iloc[0] == 139.0

def test_calculate_average_direction():
    """平均風向を計算するテスト"""
    # テスト用の風向データ
    directions = np.array([270.0, 280.0, 290.0, 260.0])
    
    # 関数を実行
    avg_direction = _calculate_average_direction(directions)
    
    # 結果を検証
    assert 270.0 <= avg_direction <= 280.0

def test_create_wind_estimation_result():
    """風向風速推定結果をAPI応答形式に変換するテスト"""
    # テスト用のDataFrame
    data = {
        'timestamp': [datetime(2023, 1, 1, 12, 0, 0), datetime(2023, 1, 1, 12, 1, 0)],
        'latitude': [35.0, 35.01],
        'longitude': [139.0, 139.01],
        'wind_speed': [10.5, 11.2],
        'wind_direction': [270.0, 275.0],
        'confidence': [0.8, 0.9]
    }
    wind_df = pd.DataFrame(data)
    
    # セッションID
    session_id = str(uuid4())
    
    # 関数を実行
    result = _create_wind_estimation_result(wind_df, session_id)
    
    # 結果を検証
    assert 'wind_data' in result
    assert len(result['wind_data']) == 2
    assert 'average_speed' in result
    assert 'average_direction' in result
    assert 'created_at' in result
    assert 'session_id' in result
    assert result['session_id'] == session_id
    assert 10.5 <= result['average_speed'] <= 11.2
    assert 270.0 <= result['average_direction'] <= 275.0
