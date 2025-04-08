#!/usr/bin/env python3
"""
WindFieldFusionSystem モジュールのスタンドアロンテスト

このスクリプトはPyTest環境に依存せず単独で実行可能なテストを提供します。
複数艇からの風データを統合し、風の場を生成するシステムをテストします。
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# テスト対象のモジュールをインポート
try:
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

class TestWindFieldFusionSystem(unittest.TestCase):
    """WindFieldFusionSystemのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        # WindFieldFusionSystemのインスタンス化
        self.fusion_system = WindFieldFusionSystem()
        
        # テスト用のサンプルデータを準備
        self.sample_wind_data_points = self._create_sample_wind_data_points()
        self.sample_boats_data = self._create_sample_boats_data()
    
    def _create_sample_wind_data_points(self):
        """テスト用の風データポイントを作成"""
        base_time = datetime.now()
        
        # 10ポイントの風データを生成
        wind_data_points = []
        for i in range(10):
            point = {
                'timestamp': base_time + timedelta(minutes=i*5),
                'latitude': 35.45 + i * 0.001,
                'longitude': 139.65 + i * 0.001,
                'wind_direction': 90 + i * 2,  # 少しずつ変化する風向
                'wind_speed': 12 + i * 0.2,    # 少しずつ変化する風速
            }
            wind_data_points.append(point)
        
        return wind_data_points
    
    def _create_sample_boats_data(self):
        """テスト用の複数艇データを作成"""
        base_time = datetime.now()
        
        # ボート1のデータ
        boat1_data = pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
            'latitude': [35.45 + i * 0.001 for i in range(5)],
            'longitude': [139.65 + i * 0.001 for i in range(5)],
            'wind_direction': [90 + i * 2 for i in range(5)],
            'wind_speed_knots': [12 + i * 0.2 for i in range(5)]
        })
        
        # ボート2のデータ
        boat2_data = pd.DataFrame({
            'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
            'latitude': [35.46 + i * 0.001 for i in range(5)],
            'longitude': [139.66 + i * 0.001 for i in range(5)],
            'wind_direction': [92 + i * 2 for i in range(5)],
            'wind_speed_knots': [12.5 + i * 0.2 for i in range(5)]
        })
        
        return {
            'boat1': boat1_data,
            'boat2': boat2_data
        }
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.fusion_system)
        self.assertEqual(self.fusion_system.wind_data_points, [])
        self.assertIsNone(self.fusion_system.current_wind_field)
        self.assertEqual(self.fusion_system.wind_field_history, [])
        self.assertEqual(self.fusion_system.max_history_size, 10)
    
    def test_add_wind_data_point(self):
        """風データポイント追加機能のテスト"""
        # ひとつのポイントを追加
        point = self.sample_wind_data_points[0]
        self.fusion_system.add_wind_data_point(point)
        
        # 追加されていることを確認
        self.assertEqual(len(self.fusion_system.wind_data_points), 1)
        self.assertEqual(self.fusion_system.wind_data_points[0], point)
        
        # 必須キーが欠けたポイントは追加されないことを確認
        invalid_point = {'latitude': 35.45, 'longitude': 139.65}  # timestampなどが欠けている
        self.fusion_system.add_wind_data_point(invalid_point)
        
        # 無効なポイントは追加されないので、カウントは変わらないはず
        self.assertEqual(len(self.fusion_system.wind_data_points), 1)
    
    def test_update_with_boat_data(self):
        """複数艇データからの風の場更新機能のテスト"""
        result = self.fusion_system.update_with_boat_data(self.sample_boats_data)
        
        # 結果は風の場（または None）であることを確認
        self.assertIsNotNone(result)
        
        # 風データポイントが正しく追加されていることを確認
        expected_points = len(self.sample_boats_data['boat1']) + len(self.sample_boats_data['boat2'])
        self.assertEqual(len(self.fusion_system.wind_data_points), expected_points)
    
    def test_fuse_wind_data(self):
        """風データ融合機能のテスト"""
        # 風データポイントを追加
        for point in self.sample_wind_data_points:
            self.fusion_system.add_wind_data_point(point)
        
        # 風の場が生成されていることを確認
        self.assertIsNotNone(self.fusion_system.current_wind_field)
        
        # 風の場データの構造を確認
        wind_field = self.fusion_system.current_wind_field
        self.assertIn('lat_grid', wind_field)
        self.assertIn('lon_grid', wind_field)
        self.assertIn('wind_direction', wind_field)
        self.assertIn('wind_speed', wind_field)
        self.assertIn('confidence', wind_field)
        self.assertIn('time', wind_field)
        
        # グリッドの形状が一致していることを確認
        self.assertEqual(wind_field['lat_grid'].shape, wind_field['wind_direction'].shape)
        self.assertEqual(wind_field['lon_grid'].shape, wind_field['wind_speed'].shape)
        self.assertEqual(wind_field['confidence'].shape, wind_field['wind_direction'].shape)
    
    def test_predict_wind_field(self):
        """風の場予測機能のテスト"""
        # 風データを追加して風の場を生成
        for point in self.sample_wind_data_points:
            self.fusion_system.add_wind_data_point(point)
        
        # 将来時点の予測
        future_time = datetime.now() + timedelta(minutes=30)
        predicted_field = self.fusion_system.predict_wind_field(future_time)
        
        # 予測結果が返されることを確認
        self.assertIsNotNone(predicted_field)
        
        # 予測風の場の構造を確認
        self.assertIn('lat_grid', predicted_field)
        self.assertIn('lon_grid', predicted_field)
        self.assertIn('wind_direction', predicted_field)
        self.assertIn('wind_speed', predicted_field)
        self.assertIn('confidence', predicted_field)
        self.assertIn('time', predicted_field)
        
        # 時間が正しく設定されていることを確認
        self.assertEqual(predicted_field['time'], future_time)
    
    def test_get_prediction_quality_report(self):
        """予測品質レポート機能のテスト"""
        report = self.fusion_system.get_prediction_quality_report()
        
        # レポートが辞書形式で返されることを確認
        self.assertIsInstance(report, dict)
        
        # 予測評価機能が有効であることを確認
        self.assertEqual(report.get('enable_evaluation', True), True)
        
        # 保留中の予測数が含まれていることを確認
        self.assertIn('pending_predictions', report)
    
    def test_haversine_distance(self):
        """Haversine距離計算のテスト"""
        # 既知の2点間の距離をテスト
        tower_lat, tower_lon = 35.6586, 139.7454
        diet_lat, diet_lon = 35.6758, 139.7458
        
        # 距離計算
        distance = self.fusion_system._haversine_distance(tower_lat, tower_lon, diet_lat, diet_lon)
        
        # 実際の距離は約1.9kmなので、その付近の値になっていることを確認
        self.assertGreater(distance, 1800)  # 1.8km以上
        self.assertLess(distance, 2000)     # 2.0km以下

def run_tests():
    """テストを実行"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWindFieldFusionSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("WindFieldFusionSystem モジュールのスタンドアロンテストを実行します...")
    success = run_tests()
    sys.exit(0 if success else 1)
