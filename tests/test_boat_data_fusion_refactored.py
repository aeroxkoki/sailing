#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト：リファクタリングされたboat_fusionモジュールのテスト
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sailing_data_processor.boat_fusion import BoatDataFusionModel

def create_test_data():
    """テストデータの作成"""
    base_time = datetime.now()
    data = {
        'boat1': pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
            'latitude': [35.45 + i*0.001 for i in range(5)],
            'longitude': [139.65 + i*0.001 for i in range(5)],
            'wind_direction': [90 + i for i in range(5)],
            'wind_speed_knots': [10 + i*0.5 for i in range(5)],
            'confidence': [0.8 for _ in range(5)]
        }),
        'boat2': pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
            'latitude': [35.46 + i*0.001 for i in range(5)],
            'longitude': [139.66 + i*0.001 for i in range(5)],
            'wind_direction': [95 + i for i in range(5)],
            'wind_speed_knots': [11 + i*0.5 for i in range(5)],
            'confidence': [0.7 for _ in range(5)]
        })
    }
    return data

@pytest.fixture
def fusion_model():
    model = BoatDataFusionModel()
    model.set_boat_skill_levels({'boat1': 0.8, 'boat2': 0.6})
    model.set_boat_types({'boat1': 'laser', 'boat2': '470'})
    return model

def test_model_initialization(fusion_model):
    """モデルの初期化テスト"""
    assert fusion_model is not None
    assert fusion_model.boat_skill_levels == {'boat1': 0.8, 'boat2': 0.6}
    assert fusion_model.boat_types == {'boat1': 'laser', 'boat2': '470'}

def test_wind_fusion(fusion_model):
    """風向風速の統合テスト"""
    test_data = create_test_data()
    result = fusion_model.fuse_wind_estimates(test_data)
    
    # 結果の検証
    assert result is not None
    assert 'wind_direction' in result
    assert 'wind_speed' in result
    assert 'confidence' in result
    
    # 値の範囲チェック
    assert 0 <= result['wind_direction'] < 360
    assert result['wind_speed'] > 0
    assert 0 <= result['confidence'] <= 1

def test_spatiotemporal_wind_field(fusion_model):
    """時空間風場のテスト"""
    test_data = create_test_data()
    
    # データを統合して履歴を作成
    fusion_model.fuse_wind_estimates(test_data)
    
    # 時空間風場の作成
    time_points = [datetime.now() + timedelta(minutes=i*5) for i in range(3)]
    wind_fields = fusion_model.create_spatiotemporal_wind_field(time_points, grid_resolution=10)
    
    # 結果の検証
    assert wind_fields is not None
    assert len(wind_fields) == len(time_points)
    
    # 各時間点のフィールド検証
    for field in wind_fields:
        assert 'time' in field
        assert 'grid' in field
        assert 'wind_directions' in field
        assert 'wind_speeds' in field
