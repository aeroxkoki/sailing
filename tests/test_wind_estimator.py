# -*- coding: utf-8 -*-
"""
WindEstimatorクラスの包括的なテスト
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sailing_data_processor.wind_estimator import WindEstimator


class TestWindEstimator(unittest.TestCase):
    """WindEstimatorのテストケース"""
    
    def setUp(self):
        """テストの初期設定"""
        self.estimator = WindEstimator()
    
    def _create_simple_tack_data(self):
        """シンプルなタックパターンのテストデータを作成"""
        times = pd.date_range(start='2023-01-01 12:00:00', periods=20, freq='5s')
        latitudes = [35.45] * 20  # 緯度は一定
        longitudes = [139.65] * 20  # 経度も一定
        
        # ヘディングのパターン（明確なタック）
        # 045度→急激に135度へ変化→維持
        headings = [45] * 8 + [90] + [135] * 11
        speeds = [6.0] * 20  # 速度は一定
        
        data = pd.DataFrame({
            'timestamp': times,
            'latitude': latitudes,
            'longitude': longitudes,
            'sog': speeds,
            'heading': headings
        })
        
        return data
    
    def _create_gybe_data(self):
        """ジャイブのテストデータを作成"""
        times = pd.date_range(start='2023-01-01 12:00:00', periods=20, freq='5s')
        latitudes = [35.45] * 20
        longitudes = [139.65] * 20
        
        # ヘディングのパターン（明確なジャイブ）
        # 225度→急激に315度へ変化
        headings = [225] * 8 + [270] + [315] * 11
        speeds = [8.0] * 20
        
        data = pd.DataFrame({
            'timestamp': times,
            'latitude': latitudes,
            'longitude': longitudes,
            'sog': speeds,
            'heading': headings
        })
        
        return data
    
    def _create_continuous_data(self):
        """連続的なヘディング変化のデータを作成"""
        times = pd.date_range(start='2023-01-01 12:00:00', periods=100, freq='5s')
        latitudes = [35.45] * 100
        longitudes = [139.65] * 100
        
        # ゆっくりと継続的にヘディングが変化
        headings = np.linspace(0, 180, 100)
        speeds = [6.0] * 100
        
        data = pd.DataFrame({
            'timestamp': times,
            'latitude': latitudes,
            'longitude': longitudes,
            'sog': speeds,
            'heading': headings
        })
        
        return data
    
    def test_detect_tacks(self):
        """タック検出のテスト"""
        data = self._create_simple_tack_data()
        tacks = self.estimator.detect_tacks(data)
        
        # タックが1つ検出されることを確認
        self.assertEqual(len(tacks), 1)
        
        if len(tacks) > 0:
            tack = tacks.iloc[0]
            # タックの角度変化が適切か確認
            self.assertGreater(tack['angle_change'], 80)
    
    def test_detect_gybes(self):
        """ジャイブ検出のテスト"""
        data = self._create_gybe_data()
        gybes = self.estimator.detect_gybes(data)
        
        # ジャイブが1つ検出されることを確認
        self.assertEqual(len(gybes), 1)
        
        if len(gybes) > 0:
            gybe = gybes.iloc[0]
            # ジャイブの角度変化が適切か確認
            self.assertGreater(gybe['angle_change'], 80)
    
    def test_no_false_detection(self):
        """誤検出がないことのテスト"""
        data = self._create_continuous_data()
        
        tacks = self.estimator.detect_tacks(data)
        gybes = self.estimator.detect_gybes(data)
        
        # 連続的な変化ではタックやジャイブを検出しない
        self.assertEqual(len(tacks), 0)
        self.assertEqual(len(gybes), 0)
    
    def test_estimate_wind_from_empty_data(self):
        """空のデータでの風推定テスト"""
        data = pd.DataFrame(columns=['timestamp', 'latitude', 'longitude', 'sog', 'heading'])
        
        result = self.estimator.estimate_wind(data)
        
        # 空のデータでもエラーにならず、空の結果を返すことを確認
        self.assertIsNotNone(result)
        self.assertIn('boat', result)
        self.assertIn('wind', result)
    
    def test_estimate_wind_from_data(self):
        """データからの風推定テスト"""
        data = self._create_simple_tack_data()
        
        result = self.estimator.estimate_wind(data)
        
        # 結果の構造を確認
        self.assertIsNotNone(result)
        self.assertIn('boat', result)
        self.assertIn('wind', result)
        
        # 風データが推定されていることを確認
        if 'wind' in result and result['wind'] is not None:
            wind_data = result['wind']['wind_data']
            self.assertGreater(len(wind_data), 0)
    
    def test_calculate_laylines(self):
        """レイライン計算のテスト"""
        wind_direction = 270  # 西からの風
        wind_speed = 12
        mark_position = {'latitude': 35.5, 'longitude': 139.7}
        current_position = {'latitude': 35.45, 'longitude': 139.65}
        
        laylines = self.estimator.calculate_laylines(
            wind_direction, wind_speed,
            mark_position, current_position
        )
        
        # レイラインの結果を確認
        self.assertIsNotNone(laylines)
        self.assertIn('starboard', laylines)
        self.assertIn('port', laylines)
        self.assertIn('direct_bearing', laylines)
        self.assertIn('tacking_required', laylines)
    
    def test_calculate_vmg(self):
        """VMG計算のテスト"""
        boat_speed = 6.0
        boat_heading = 45
        wind_direction = 0  # 北からの風
        
        vmg = self.estimator._calculate_vmg(boat_speed, boat_heading, wind_direction)
        
        # VMGが適切な範囲内であることを確認
        self.assertGreater(vmg, 0)
        self.assertLessEqual(vmg, boat_speed)
    
    def test_normalize_angle(self):
        """角度正規化のテスト"""
        # 様々な角度をテスト
        self.assertEqual(self.estimator._normalize_angle(0), 0)
        self.assertEqual(self.estimator._normalize_angle(360), 0)
        self.assertEqual(self.estimator._normalize_angle(-90), 270)
        self.assertEqual(self.estimator._normalize_angle(450), 90)
    
    def test_convert_wind_vector_to_angle(self):
        """風ベクトルから角度への変換テスト"""
        # 北からの風
        angle = self.estimator._convert_wind_vector_to_angle((0, 1))
        self.assertAlmostEqual(angle, 180, places=1)
        
        # 東からの風
        angle = self.estimator._convert_wind_vector_to_angle((1, 0))
        self.assertAlmostEqual(angle, 270, places=1)
    
    def test_convert_angle_to_wind_vector(self):
        """風向角度からベクトルへの変換テスト"""
        # 北からの風（風向180度）
        u, v = self.estimator._convert_angle_to_wind_vector(180, 10)
        self.assertAlmostEqual(u, 0, places=1)
        self.assertAlmostEqual(v, -10, places=1)
        
        # 東からの風（風向270度）
        u, v = self.estimator._convert_angle_to_wind_vector(270, 10)
        self.assertAlmostEqual(u, -10, places=1)
        self.assertAlmostEqual(v, 0, places=1)

    def test_get_conversion_functions(self):
        """単位変換関数のテスト"""
        lat_func, lon_func = self.estimator._get_conversion_functions(35.5)
        
        # 変換関数が妥当な値を返すことを確認
        meters_per_degree_lat = lat_func(1)
        meters_per_degree_lon = lon_func(1)
        
        self.assertGreater(meters_per_degree_lat, 100000)  # 大体111km
        self.assertGreater(meters_per_degree_lon, 80000)   # 緯度35度で大体91km

if __name__ == '__main__':
    unittest.main()
