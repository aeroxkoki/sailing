#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WindPropagationModel モジュールのスタンドアロンテスト

このスクリプトはPyTest環境に依存せず単独で実行可能なテストを提供します。
風の移動モデルの主要機能をテストします。
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# テスト対象のモジュールをインポート
try:
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

class TestWindPropagationModel(unittest.TestCase):
    """WindPropagationModelのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        # WindPropagationModelのインスタンス化
        self.model = WindPropagationModel()
        
        # テスト用のサンプルデータを準備
        self.sample_data = self._create_sample_wind_data()
    
    def _create_sample_wind_data(self):
        """テスト用の風データを作成"""
        base_time = datetime.now()
        
        # 10ポイントの風データを生成
        wind_data = []
        for i in range(10):
            point = {
                'timestamp': base_time + timedelta(minutes=i*5),
                'latitude': 35.45 + i * 0.001,
                'longitude': 139.65 + i * 0.001,
                'wind_direction': 90 + i * 2,  # 少しずつ変化する風向
                'wind_speed': 12 + i * 0.2,    # 少しずつ変化する風速
            }
            wind_data.append(point)
        
        return wind_data
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.model)
        self.assertEqual(self.model.wind_speed_factor, 0.6)
        self.assertEqual(self.model.min_data_points, 5)
        self.assertEqual(self.model.coriolis_factor, 10.0)
    
    def test_estimate_propagation_vector(self):
        """風の移動ベクトル推定機能のテスト"""
        result = self.model.estimate_propagation_vector(self.sample_data)
        
        # 結果が辞書形式で返されることを確認
        self.assertIsInstance(result, dict)
        
        # 期待されるキーが存在することを確認
        self.assertIn('speed', result)
        self.assertIn('direction', result)
        self.assertIn('confidence', result)
        
        # 値が妥当な範囲内にあることを確認
        self.assertGreaterEqual(result['speed'], 0)
        self.assertGreaterEqual(result['direction'], 0)
        self.assertLessEqual(result['direction'], 360)
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)
        
        # 推定ベクトルがインスタンス変数に保存されることを確認
        self.assertEqual(self.model.propagation_vector, result)
    
    def test_predict_future_wind(self):
        """将来の風状況予測機能のテスト"""
        # 予測対象の位置
        position = (35.46, 139.66)
        
        # 現在時刻から30分後の風を予測
        future_time = datetime.now() + timedelta(minutes=30)
        
        # 予測実行
        prediction = self.model.predict_future_wind(position, future_time, self.sample_data)
        
        # 結果が辞書形式で返されることを確認
        self.assertIsInstance(prediction, dict)
        
        # 期待されるキーが存在することを確認
        self.assertIn('wind_direction', prediction)
        self.assertIn('wind_speed', prediction)
        self.assertIn('confidence', prediction)
        
        # 値が妥当な範囲内にあることを確認
        self.assertGreaterEqual(prediction['wind_direction'], 0)
        self.assertLessEqual(prediction['wind_direction'], 360)
        self.assertGreaterEqual(prediction['wind_speed'], 0)
        self.assertGreaterEqual(prediction['confidence'], 0)
        self.assertLessEqual(prediction['confidence'], 1)
    
    def test_adjust_wind_speed_factor(self):
        """風速係数調整機能のテスト"""
        # 低風速のテスト（5ノット未満）
        low_wind_data = self.sample_data.copy()
        for point in low_wind_data:
            point['wind_speed'] = 3.0
        
        low_result = self.model._adjust_wind_speed_factor(low_wind_data)
        
        # 高風速のテスト（15ノット超）
        high_wind_data = self.sample_data.copy()
        for point in high_wind_data:
            point['wind_speed'] = 18.0
        
        high_result = self.model._adjust_wind_speed_factor(high_wind_data)
        
        # 風速に応じた適切な調整が行われること
        self.assertLess(low_result, self.model.wind_speed_factor)  # 低風速では係数が小さくなる
        self.assertGreater(high_result, self.model.wind_speed_factor)  # 高風速では係数が大きくなる
    
    def test_haversine_distance(self):
        """Haversine距離計算のテスト"""
        # 既知の2点間の距離をテスト
        # 東京タワー (35.6586, 139.7454) と国会議事堂 (35.6758, 139.7458)
        tower_lat, tower_lon = 35.6586, 139.7454
        diet_lat, diet_lon = 35.6758, 139.7458
        
        # 距離計算
        distance = self.model._haversine_distance(tower_lat, tower_lon, diet_lat, diet_lon)
        
        # 実際の距離は約1.9kmなので、その付近の値になっていることを確認
        self.assertGreater(distance, 1800)  # 1.8km以上
        self.assertLess(distance, 2000)     # 2.0km以下
    
    def test_calculate_bearing(self):
        """方位角計算のテスト"""
        # 東から西へ：270度の方位になるはず
        east_lat, east_lon = 35.65, 139.75
        west_lat, west_lon = 35.65, 139.74
        
        bearing = self.model._calculate_bearing(east_lat, east_lon, west_lat, west_lon)
        
        # 西方向（270度付近）になっていることを確認
        self.assertGreater(bearing, 265)
        self.assertLess(bearing, 275)
        
        # 南から北へ：0度の方位になるはず
        south_lat, south_lon = 35.64, 139.75
        north_lat, north_lon = 35.65, 139.75
        
        bearing = self.model._calculate_bearing(south_lat, south_lon, north_lat, north_lon)
        
        # 北方向（0度付近）になっていることを確認
        self.assertLess(bearing, 5)
        # またはほぼ360度
        if bearing > 350:
            self.assertGreater(bearing, 355)

def run_tests():
    """テストを実行"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWindPropagationModel)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("WindPropagationModel モジュールのスタンドアロンテストを実行します...")
    success = run_tests()
    sys.exit(0 if success else 1)
