#\!/usr/bin/env python3
"""
WindEstimatorのマニューバー検出機能の改良版テスト
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import os
import sys
import warnings

# テスト対象のモジュールをインポート
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sailing_data_processor.wind_estimator import WindEstimator


class TestManeuverDetection(unittest.TestCase):
    """改良したマニューバー検出機能のテストケース"""
    
    def setUp(self):
        """テストの準備"""
        # 警告を無視
        warnings.filterwarnings("ignore")
        
        # テスト用のオブジェクト作成
        self.estimator = WindEstimator()
        
        # テスト用のデータを作成
        self.simple_tack_data = self._create_simple_tack_data()
        self.simple_jibe_data = self._create_simple_jibe_data()
    
    def _create_simple_tack_data(self):
        """明確なタックを含むシンプルなGPSデータを作成"""
        # 基準時刻
        base_time = datetime(2023, 3, 1, 10, 0, 0)
        
        # 100ポイントのデータ生成
        points = 100
        timestamps = [base_time + timedelta(seconds=i*5) for i in range(points)]
        
        # 方位データ - 明確なタックパターン（30度→330度）
        bearings = [30] * 45  # 最初の45ポイントは30度
        bearings += [i for i in range(30, 330, 30)]  # 10ポイントで30度→330度へ変化
        bearings += [330] * (100 - len(bearings))  # 残りのポイントは330度
        
        # 緯度・経度データ（シンプルな直線）
        base_lat, base_lon = 35.6, 139.7
        lats = [base_lat + i * 0.0001 for i in range(points)]
        lons = [base_lon + i * 0.0001 for i in range(points)]
        
        # 速度データ（タック時に減速）
        speeds = []
        for i in range(points):
            if 45 <= i < 55:  # タック中は減速
                speeds.append(3.0)
            else:
                speeds.append(5.0)
        
        # 配列の長さを確認
        assert len(timestamps) == points
        assert len(bearings) == points
        assert len(lats) == points
        assert len(lons) == points
        assert len(speeds) == points
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'latitude': lats,
            'longitude': lons,
            'speed': np.array(speeds) * 0.514444,  # ノット→m/s変換
            'bearing': bearings,
            'boat_id': ['TestBoat'] * points
        })
        
        return df
    
    def _create_simple_jibe_data(self):
        """明確なジャイブを含むシンプルなGPSデータを作成"""
        # 基準時刻
        base_time = datetime(2023, 3, 1, 10, 0, 0)
        
        # 100ポイントのデータ生成
        points = 100
        timestamps = [base_time + timedelta(seconds=i*5) for i in range(points)]
        
        # 方位データ - 明確なジャイブパターン（150度→210度）
        bearings = [150] * 45  # 最初の45ポイントは150度
        bearings += [i for i in range(150, 210, 6)]  # 10ポイントで150度→210度へ変化
        bearings += [210] * (100 - len(bearings))  # 残りのポイントは210度
        
        # 緯度・経度データ（シンプルな直線）
        base_lat, base_lon = 35.6, 139.7
        lats = [base_lat + i * 0.0001 for i in range(points)]
        lons = [base_lon + i * 0.0001 for i in range(points)]
        
        # 速度データ（ジャイブ時に減速）
        speeds = []
        for i in range(points):
            if 45 <= i < 55:  # ジャイブ中は減速
                speeds.append(4.0)
            else:
                speeds.append(6.0)
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'latitude': lats,
            'longitude': lons,
            'speed': np.array(speeds) * 0.514444,  # ノット→m/s変換
            'bearing': bearings,
            'boat_id': ['TestBoat'] * points
        })
        
        return df

    def test_categorize_maneuver(self):
        """マニューバー分類機能のテスト"""
        # テストシナリオの設定
        test_cases = [
            # (before_bearing, after_bearing, wind_direction, boat_type, expected_type)
            # タックのテスト
            (30, 330, 0, 'laser', 'tack'),
            (330, 30, 0, 'laser', 'tack'),
            # ジャイブのテスト
            (150, 210, 0, 'laser', 'jibe'),
            (210, 150, 0, 'laser', 'jibe'),
            # ベアアウェイのテスト
            (30, 150, 0, 'laser', 'bear_away'),
            # ヘッドアップのテスト
            (150, 30, 0, 'laser', 'head_up'),
            # 異なる風向でのテスト
            (90, 270, 180, 'laser', 'tack'),
            (270, 90, 180, 'laser', 'tack')
        ]
        
        for before, after, wind_dir, boat, expected in test_cases:
            result = self.estimator._categorize_maneuver(before, after, wind_dir, boat)
            self.assertEqual(result['maneuver_type'], expected,
                         f"期待されるマニューバタイプ（{expected}）と実際の結果（{result['maneuver_type']}）が一致しません")
            
            # 信頼度が0-1の範囲内にあることを確認
            self.assertTrue(0 <= result['confidence'] <= 1,
                        f"信頼度（{result['confidence']}）が範囲外です")
            
            # 状態が正しく設定されていることを確認
            self.assertIn(result['before_state'], ['upwind', 'downwind', 'reaching'],
                      f"転換前の状態（{result['before_state']}）が無効です")
            self.assertIn(result['after_state'], ['upwind', 'downwind', 'reaching'],
                      f"転換後の状態（{result['after_state']}）が無効です")

    def test_determine_point_state(self):
        """風に対する状態判定のテスト"""
        # アップウィンド（風上）範囲のテスト
        self.assertEqual(self.estimator._determine_point_state(0, 80, 100), 'upwind')
        self.assertEqual(self.estimator._determine_point_state(80, 80, 100), 'upwind')
        self.assertEqual(self.estimator._determine_point_state(359, 80, 100), 'upwind')
        
        # ダウンウィンド（風下）範囲のテスト
        self.assertEqual(self.estimator._determine_point_state(100, 80, 100), 'downwind')
        self.assertEqual(self.estimator._determine_point_state(180, 80, 100), 'downwind')
        self.assertEqual(self.estimator._determine_point_state(260, 80, 100), 'downwind')
        
        # リーチング範囲のテスト
        self.assertEqual(self.estimator._determine_point_state(85, 80, 100), 'reaching')
        self.assertEqual(self.estimator._determine_point_state(95, 80, 100), 'reaching')
        self.assertEqual(self.estimator._determine_point_state(275, 80, 100), 'reaching')

    def test_detect_maneuvers_tack(self):
        """タック検出のテスト"""
        # 風向を設定（テストデータでは風向0度を想定）
        wind_direction = 0.0
        
        # マニューバー検出
        maneuvers = self.estimator.detect_maneuvers(self.simple_tack_data, wind_direction)
        
        # 検出結果があることを確認
        self.assertIsNotNone(maneuvers, "マニューバー検出結果がNoneです")
        self.assertGreater(len(maneuvers), 0, "マニューバーが検出されていません")
        
        # タックが正しく検出されていることを確認
        if len(maneuvers) > 0:
            # 最初の検出結果がタックであることを確認
            self.assertEqual(maneuvers.iloc[0]['maneuver_type'], 'tack', 
                         "検出されたマニューバーがタックではありません")
            
            # 信頼度スコアが存在することを確認
            self.assertIn('maneuver_confidence', maneuvers.columns, 
                      "信頼度スコアが結果に含まれていません")
            
            # 信頼度スコアが妥当な範囲にあることを確認
            self.assertTrue(0 <= maneuvers.iloc[0]['maneuver_confidence'] <= 1,
                        f"信頼度（{maneuvers.iloc[0]['maneuver_confidence']}）が範囲外です")

    def test_detect_maneuvers_jibe(self):
        """ジャイブ検出のテスト"""
        # 風向を設定（テストデータでは風向0度を想定）
        wind_direction = 0.0
        
        # マニューバー検出
        maneuvers = self.estimator.detect_maneuvers(self.simple_jibe_data, wind_direction)
        
        # 検出結果があることを確認
        self.assertIsNotNone(maneuvers, "マニューバー検出結果がNoneです")
        self.assertGreater(len(maneuvers), 0, "マニューバーが検出されていません")
        
        # ジャイブが正しく検出されていることを確認
        if len(maneuvers) > 0:
            # 最初の検出結果がジャイブであることを確認
            self.assertEqual(maneuvers.iloc[0]['maneuver_type'], 'jibe', 
                         "検出されたマニューバーがジャイブではありません")
            
            # 信頼度スコアが存在することを確認
            self.assertIn('maneuver_confidence', maneuvers.columns, 
                      "信頼度スコアが結果に含まれていません")

    def test_boat_type_adjustment(self):
        """艇種によるパラメータ調整のテスト"""
        # 異なる艇種での比較
        maneuver_info_laser = self.estimator._categorize_maneuver(30, 330, 0, 'laser')
        maneuver_info_49er = self.estimator._categorize_maneuver(30, 330, 0, '49er')
        
        # 風上/風下の範囲が艇種によって異なることを確認
        self.assertNotEqual(maneuver_info_laser['before_state'], maneuver_info_49er['before_state'],
                        "艇種による風上/風下判定の違いが反映されていません")
        
        # 信頼度スコアの違いを確認
        self.assertNotEqual(maneuver_info_laser['confidence'], maneuver_info_49er['confidence'],
                        "艇種による信頼度スコアの違いが反映されていません")

if __name__ == '__main__':
    unittest.main()
