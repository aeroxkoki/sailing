# -*- coding: utf-8 -*-
"""
WindEstimatorの新しいAPIに対応したテスト
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# モジュールのインポートパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.append(project_dir)

from sailing_data_processor.wind_estimator import WindEstimator

class TestWindEstimatorNewAPI(unittest.TestCase):
    """WindEstimatorの新しいAPIに対応したテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.estimator = WindEstimator()
    
    def test_detect_maneuvers(self):
        """detect_maneuversメソッドのテスト"""
        # テスト用データの作成
        data = []
        base_time = datetime.now()
        
        # タックを含むデータを作成
        for i in range(20):
            timestamp = base_time + timedelta(seconds=i * 5)
            latitude = 35.0 + i * 0.0001
            longitude = 139.0 + i * 0.0001
            
            # 10番目のポイントでタック（大きな方位変化）
            if i < 10:
                course = 45.0  # 北東方向
                heading = 45.0  # 北東方向
                speed = 5.0
            else:
                course = 315.0  # 北西方向
                heading = 315.0  # 北西方向
                speed = 4.0  # タック後の速度低下
            
            data.append({
                'timestamp': timestamp,
                'latitude': latitude,
                'longitude': longitude,
                'course': course,
                'heading': heading,
                'speed': speed
            })
        
        test_df = pd.DataFrame(data)
        
        # マニューバー検出
        maneuvers = self.estimator.detect_maneuvers(test_df)
        
        # 検出結果があることを確認
        self.assertIsNotNone(maneuvers)
        # DataFrameであることを確認
        self.assertIsInstance(maneuvers, pd.DataFrame)
        self.assertFalse(maneuvers.empty)
        
        # マニューバーの内容を確認
        self.assertIn('maneuver_type', maneuvers.columns)
        self.assertIn('timestamp', maneuvers.columns)
        self.assertEqual(maneuvers.iloc[0]['maneuver_type'], 'tack')
    
    def test_estimate_wind(self):
        """estimate_windメソッドのテスト"""
        # テスト用データの作成
        data = []
        base_time = datetime.now()
        
        for i in range(50):
            timestamp = base_time + timedelta(seconds=i * 5)
            latitude = 35.0 + i * 0.0001
            longitude = 139.0 + i * 0.0001
            
            # 風向を仮定して、風上走行と風下走行のパターンを作成
            if i % 20 < 10:
                course = 45.0  # 風上
                heading = 45.0  # 風上
                speed = 4.0
            else:
                course = 225.0  # 風下
                heading = 225.0  # 風下
                speed = 6.0
            
            data.append({
                'timestamp': timestamp,
                'latitude': latitude,
                'longitude': longitude,
                'course': course,
                'heading': heading,
                'speed': speed
            })
        
        test_df = pd.DataFrame(data)
        
        # 風速推定
        wind_estimate = self.estimator.estimate_wind(test_df)
        
        # 結果の検証
        self.assertIsNotNone(wind_estimate)
        self.assertIsInstance(wind_estimate, dict)
        self.assertIn('boat', wind_estimate)
        self.assertIn('wind', wind_estimate)
        self.assertIn('direction', wind_estimate['wind'])
        self.assertIn('speed', wind_estimate['wind'])
        self.assertIn('confidence', wind_estimate['wind'])

if __name__ == '__main__':
    unittest.main()
