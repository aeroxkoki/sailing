#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拡張テストコード

この拡張テストでは、主要なモジュールの機能と性能をテストします。
特に、改善された機能についてのテストを含みます。
"""

import sys
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time

try:
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

class WindDataGenerator:
    """テスト用の風データ生成クラス"""
    
    @staticmethod
    def create_test_boat_data(num_boats=3, points_per_boat=20):
        """複数艇のテストデータを生成"""
        boats_data = {}
        base_time = datetime.now()
        
        for boat_idx in range(num_boats):
            boat_id = f"boat_{boat_idx}"
            data = []
            
            # 各艇に異なる基準位置を設定
            base_lat = 35.4 + boat_idx * 0.1
            base_lon = 139.7 + boat_idx * 0.1
            
            # 各艇に若干異なる風向・風速を設定
            wind_dir = 90 + boat_idx * 10
            wind_speed = 10 + boat_idx * 1.0
            
            # 各艇の航跡を生成（8の字に近い動きを模擬）
            for i in range(points_per_boat):
                angle = i * 0.31
                time = base_time + timedelta(seconds=i*10)
                
                # 8の字を描くような位置の変化
                lat_offset = 0.005 * np.sin(angle)
                lon_offset = 0.005 * np.sin(angle * 2)
                
                # 風向・風速にも変動を追加
                dir_oscillation = np.sin(angle) * 5
                speed_oscillation = np.cos(angle) * 1.0
                
                data.append({
                    'timestamp': time,
                    'latitude': base_lat + lat_offset,
                    'longitude': base_lon + lon_offset,
                    'wind_direction': (wind_dir + dir_oscillation) % 360,
                    'wind_speed_knots': max(0.5, wind_speed + speed_oscillation),
                    'confidence': 0.8 - 0.1 * (boat_idx % 2)
                })
            
            boats_data[boat_id] = pd.DataFrame(data)
        
        return boats_data
    
    @staticmethod
    def create_wind_propagation_data(base_lat=35.45, base_lon=139.65, 
                                    wind_dir=90, wind_speed=10, 
                                    num_points=20, time_step=5):
        """風の移動パターンを含むデータセットを作成"""
        base_time = datetime.now()
        data = []
        
        # コリオリ効果を考慮した移動方向（北半球では右に偏向）
        propagation_dir = (wind_dir + 10) % 360
        propagation_rad = np.radians(propagation_dir)
        
        # 風速の60%で風が移動すると仮定
        speed_factor = 0.6
        
        for i in range(num_points):
            time = base_time + timedelta(seconds=i*time_step)
            
            # 風の移動に応じた位置変化
            distance = i * wind_speed * speed_factor * 0.51444 * time_step / 100  # 調整係数
            lat_offset = distance * np.sin(propagation_rad) / 111111  # 緯度1度は約111.1km
            lon_offset = distance * np.cos(propagation_rad) / (111111 * np.cos(np.radians(base_lat)))
            
            # 時間とともに少し変化する風向風速
            wind_dir_variation = np.sin(i * 0.2) * 3
            wind_speed_variation = np.cos(i * 0.3) * 0.5
            
            data.append({
                'timestamp': time,
                'latitude': base_lat + lat_offset,
                'longitude': base_lon + lon_offset,
                'wind_direction': (wind_dir + wind_dir_variation) % 360,
                'wind_speed': max(0.5, wind_speed + wind_speed_variation)
            })
        
        return data

class WindFieldFusionSystemTest(unittest.TestCase):
    """WindFieldFusionSystemのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        self.fusion_system = WindFieldFusionSystem()
        self.boat_data = WindDataGenerator.create_test_boat_data()
    
    def test_update_with_boat_data(self):
        """艇データによる風の場更新機能のテスト"""
        result = self.fusion_system.update_with_boat_data(self.boat_data)
        
        self.assertIsNotNone(result)
        self.assertIn('lat_grid', result)
        self.assertIn('lon_grid', result)
        self.assertIn('wind_direction', result)
        self.assertIn('wind_speed', result)
        self.assertIn('confidence', result)
    
    def test_scale_data_points(self):
        """データポイントのスケーリング機能のテスト"""
        # 単一のポイント集合のテスト
        points = [
            {'latitude': 35.45, 'longitude': 139.65, 'wind_speed': 10, 'wind_direction': 90},
            {'latitude': 35.46, 'longitude': 139.66, 'wind_speed': 12, 'wind_direction': 95}
        ]
        
        scaled_points = self.fusion_system._scale_data_points(points)
        
        self.assertEqual(len(scaled_points), len(points))
        self.assertIn('scaled_latitude', scaled_points[0])
        self.assertIn('scaled_longitude', scaled_points[0])
        self.assertIn('scaled_height', scaled_points[0])
    
    def test_qhull_precision_handling(self):
        """Qhull精度エラー対策のテスト"""
        # 非常に近い位置のデータポイントを作成
        close_points = []
        base_lat, base_lon = 35.45, 139.65
        for i in range(10):
            point = {
                'timestamp': datetime.now() + timedelta(seconds=i),
                'latitude': base_lat + i * 0.00001,  # 非常に小さな差
                'longitude': base_lon,
                'wind_direction': 90,
                'wind_speed': 10
            }
            close_points.append(point)
        
        # 風の場生成をテスト
        for point in close_points:
            self.fusion_system.add_wind_data_point(point)
        
        # エラーが発生せずに風の場が生成されればテスト成功
        self.assertIsNotNone(self.fusion_system.current_wind_field)
    
    def test_performance_with_large_dataset(self):
        """大規模データセットでのパフォーマンステスト"""
        # 大量のボートデータを生成
        large_boat_data = WindDataGenerator.create_test_boat_data(num_boats=5, points_per_boat=50)
        
        # 処理時間を計測
        start_time = time.time()
        self.fusion_system.update_with_boat_data(large_boat_data)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        print(f"大規模データセット処理時間: {elapsed_time:.3f}秒")
        
        # 処理時間が許容範囲内かチェック
        self.assertLess(elapsed_time, 5.0)  # 5秒以内

class WindPropagationModelTest(unittest.TestCase):
    """WindPropagationModelのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        self.model = WindPropagationModel()
        self.sample_data = WindDataGenerator.create_wind_propagation_data()
    
    def test_coriolis_factor(self):
        """コリオリ係数の検証"""
        # コリオリ係数が期待値の10.0に設定されていることを確認
        self.assertEqual(self.model.coriolis_factor, 10.0)
    
    def test_wind_speed_factor_adjustment(self):
        """風速係数調整機能のテスト"""
        # 低風速テスト用データ
        low_wind_data = self.sample_data.copy()
        for point in low_wind_data:
            point['wind_speed'] = 3.0
        
        # 高風速テスト用データ
        high_wind_data = self.sample_data.copy()
        for point in high_wind_data:
            point['wind_speed'] = 18.0
        
        # 風速係数調整をテスト
        low_factor = self.model._adjust_wind_speed_factor(low_wind_data)
        high_factor = self.model._adjust_wind_speed_factor(high_wind_data)
        
        # 風速に応じて適切に調整されることを確認
        self.assertLess(low_factor, self.model.wind_speed_factor)  # 低風速では係数が小さく
        self.assertGreater(high_factor, self.model.wind_speed_factor)  # 高風速では係数が大きく
    
    def test_estimate_propagation_vector(self):
        """風の移動ベクトル推定機能のテスト"""
        result = self.model.estimate_propagation_vector(self.sample_data)
        
        # 結果の構造を確認
        self.assertIn('speed', result)
        self.assertIn('direction', result)
        self.assertIn('confidence', result)
        
        # 値が妥当な範囲内にあることを確認
        self.assertGreaterEqual(result['speed'], 0)
        self.assertLessEqual(result['speed'], 20)  # 最大想定風速の上限
        self.assertGreaterEqual(result['direction'], 0)
        self.assertLessEqual(result['direction'], 360)
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)

class StrategyDetectorWithPropagationTest(unittest.TestCase):
    """StrategyDetectorWithPropagationのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        # WindFieldFusionSystemをモックで初期化
        self.wind_fusion_system = WindFieldFusionSystem()
        
        # StrategyDetectorWithPropagationのインスタンス化
        self.strategy_detector = StrategyDetectorWithPropagation(
            vmg_calculator=None,  # 実際のテストでは適切なモックが必要
            wind_fusion_system=self.wind_fusion_system
        )
    
    def test_normalize_to_timestamp(self):
        """タイムスタンプ正規化機能のテスト"""
        # 様々な時間表現をテスト
        now = datetime.now()
        one_hour = timedelta(hours=1)
        timestamp = now.timestamp()
        
        # 正規化結果を確認
        self.assertAlmostEqual(self.strategy_detector._normalize_to_timestamp(now), timestamp, places=0)
        self.assertEqual(self.strategy_detector._normalize_to_timestamp(one_hour), 3600.0)
        self.assertEqual(self.strategy_detector._normalize_to_timestamp(3600), 3600.0)
        self.assertEqual(self.strategy_detector._normalize_to_timestamp(3600.5), 3600.5)
    
    def test_filter_duplicate_shift_points(self):
        """重複する風向シフトポイントのフィルタリング機能のテスト"""
        from sailing_data_processor.strategy.points import WindShiftPoint
        
        # テスト用の風向シフトポイントを作成
        shift_point1 = WindShiftPoint((35.45, 139.65), datetime.now())
        shift_point1.shift_angle = 10
        shift_point1.shift_probability = 0.7
        
        shift_point2 = WindShiftPoint((35.4501, 139.6501), datetime.now() + timedelta(seconds=10))
        shift_point2.shift_angle = 12
        shift_point2.shift_probability = 0.8
        
        shift_point3 = WindShiftPoint((35.46, 139.66), datetime.now() + timedelta(minutes=5))
        shift_point3.shift_angle = 45
        shift_point3.shift_probability = 0.9
        
        # 重複フィルタリングをテスト
        filtered_points = self.strategy_detector._filter_duplicate_shift_points(
            [shift_point1, shift_point2, shift_point3]
        )
        
        # フィルタリング結果を確認
        self.assertEqual(len(filtered_points), 2)  # 重複する2つのポイントが1つにマージされる

def run_tests():
    """テストを実行"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 各テストクラスを追加
    suite.addTest(loader.loadTestsFromTestCase(WindFieldFusionSystemTest))
    suite.addTest(loader.loadTestsFromTestCase(WindPropagationModelTest))
    suite.addTest(loader.loadTestsFromTestCase(StrategyDetectorWithPropagationTest))
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("拡張テストを実行します...")
    success = run_tests()
    print(f"テスト結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)
