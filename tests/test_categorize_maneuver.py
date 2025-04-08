"""
WindEstimatorクラスのタック検出・分類機能のテスト
"""
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# モジュールのインポートパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.append(project_dir)

try:
    from sailing_data_processor.wind_estimator import WindEstimator
except ImportError:
    print("WindEstimatorのインポートに失敗しました。パスを確認してください。")
    sys.exit(1)

class TestWindEstimatorManeuvers(unittest.TestCase):
    """WindEstimatorの方向転換検出・分類機能のテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.estimator = WindEstimator()
    
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

    def test_wind_direction_calculation(self):
        """風向計算メソッドのテスト"""
        # 風上走行の場合
        boat_bearing = 45
        vmg_angle = 40
        wind_dir_upwind = self.estimator._calculate_wind_direction(boat_bearing, 'upwind', vmg_angle)
        
        # 理論上の風向（方位+180-VMG角度）
        theoretical_wind_dir = (boat_bearing + 180 - vmg_angle) % 360
        
        # 検証
        self.assertEqual(wind_dir_upwind, theoretical_wind_dir, 
                   f"風上走行での風向計算が不正確です: {wind_dir_upwind} \!= {theoretical_wind_dir}")
        
        # 風下走行の場合
        boat_bearing = 180
        wind_dir_downwind = self.estimator._calculate_wind_direction(boat_bearing, 'downwind')
        
        # 修正後の風下走行では、艇の方位＋VMG角度が風向
        # デフォルトのVMG角度は150度
        expected_downwind_dir = (boat_bearing + 150) % 360
        self.assertEqual(wind_dir_downwind, expected_downwind_dir, 
                   f"風下走行での風向計算が不正確です: {wind_dir_downwind} \!= {expected_downwind_dir}")

if __name__ == '__main__':
    unittest.main()
