#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リファクタリングされたBoatDataFusionモデルのテスト
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# パスの追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# リファクタリング後のモデルのインポート
from sailing_data_processor.boat_fusion import BoatDataFusionModel

def create_test_data():
    """テスト用のデータを作成"""
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

def test_model_initialization():
    """モデルの初期化テスト"""
    model = BoatDataFusionModel()
    assert hasattr(model, 'boat_skill_levels')
    assert hasattr(model, 'boat_types')
    assert hasattr(model, 'estimation_history')

def test_wind_fusion():
    """風向風速の統合テスト"""
    model = BoatDataFusionModel()
    
    # スキルレベルと艇種の設定
    skill_levels = {'boat1': 0.8, 'boat2': 0.6}
    boat_types = {'boat1': 'laser', 'boat2': '470'}
    
    model.set_boat_skill_levels(skill_levels)
    model.set_boat_types(boat_types)
    
    # テストデータの生成
    test_data = create_test_data()
    
    # 風向風速の統合テスト
    result = model.fuse_wind_estimates(test_data)
    
    # 結果の検証
    assert result is not None
    assert 'wind_direction' in result
    assert 'wind_speed' in result
    assert 'confidence' in result
    assert 'boat_count' in result
    
    # 値の範囲チェック
    assert 0 <= result['wind_direction'] < 360
    assert result['wind_speed'] >= 0
    assert 0 <= result['confidence'] <= 1
    assert result['boat_count'] == 2

def test_spatiotemporal_wind_field():
    """時空間風場のテスト"""
    model = BoatDataFusionModel()
    
    # スキルレベルと艇種の設定
    skill_levels = {'boat1': 0.8, 'boat2': 0.6}
    boat_types = {'boat1': 'laser', 'boat2': '470'}
    
    model.set_boat_skill_levels(skill_levels)
    model.set_boat_types(boat_types)
    
    # テストデータの生成
    test_data = create_test_data()
    
    # 十分な履歴データを作成
    for _ in range(4):  # 4回の履歴データ
        result = model.fuse_wind_estimates(test_data)
        assert result is not None
    
    # 時間点の設定
    time_points = [datetime.now() + timedelta(minutes=i*5) for i in range(3)]
    
    # 時空間風場の作成
    wind_fields = model.create_spatiotemporal_wind_field(time_points, grid_resolution=10)
    
    # 結果の検証
    assert wind_fields is not None
    assert isinstance(wind_fields, dict)  # ここを修正：dictを期待
    assert len(wind_fields) > 0
    
    # 各時間点のデータをチェック
    for time_point, field in wind_fields.items():  # ここを修正：dictをループ
        assert isinstance(time_point, datetime)  # 時間点のチェック
        assert 'wind_direction' in field  # キー名の修正
        assert 'wind_speed' in field      # キー名の修正
        assert 'lat_grid' in field
        assert 'lon_grid' in field
