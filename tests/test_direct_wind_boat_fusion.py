#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風向風速推定モジュールとボートデータ融合モジュールの直接テスト
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# パスの追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 必要なモジュールを直接インポート
import sailing_data_processor.wind
import sailing_data_processor.boat_fusion
from sailing_data_processor.wind import WindEstimator
from sailing_data_processor.boat_fusion import BoatDataFusionModel

def test_direct_wind_estimation():
    """風向風速推定の基本機能テスト"""
    # WindEstimator インスタンスの作成
    estimator = WindEstimator()
    
    # テスト用データの作成
    # (時間, 緯度, 経度, 速度, 方向) の形式
    gps_data = [
        (datetime.now(), 35.0, 139.0, 5.0, 90),  # 東向き
        (datetime.now() + timedelta(minutes=1), 35.0, 139.001, 5.0, 90),
        (datetime.now() + timedelta(minutes=2), 35.0, 139.002, 5.0, 90),
        # タックして北向きに変更
        (datetime.now() + timedelta(minutes=3), 35.001, 139.002, 4.0, 0),
        (datetime.now() + timedelta(minutes=4), 35.002, 139.002, 4.5, 0),
        (datetime.now() + timedelta(minutes=5), 35.003, 139.002, 5.0, 0),
    ]
    
    # データフレームに変換
    df = pd.DataFrame(gps_data, columns=['timestamp', 'latitude', 'longitude', 'speed', 'heading'])
    
    # 風向風速を推定
    wind_data = estimator.estimate_wind_from_data(df)
    
    # 結果の検証
    assert wind_data is not None
    assert 'wind_direction' in wind_data
    assert 'wind_speed' in wind_data
    
    # 方向が範囲内であることを確認
    assert 0 <= wind_data['wind_direction'] < 360
    
    # 速度が正の値であることを確認
    assert wind_data['wind_speed'] > 0

def test_direct_boat_fusion():
    """ボートデータ融合の基本機能テスト"""
    # BoatDataFusionModel インスタンスの作成
    model = BoatDataFusionModel()
    
    # スキルレベルと艇種の設定
    skill_levels = {'boat1': 0.8, 'boat2': 0.6}
    boat_types = {'boat1': 'laser', 'boat2': '470'}
    
    model.set_boat_skill_levels(skill_levels)
    model.set_boat_types(boat_types)
    
    # テストデータの生成
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
    
    # 風向風速の統合テスト
    result = model.fuse_wind_estimates(data)
    
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
