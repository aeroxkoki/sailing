# -*- coding: utf-8 -*-
"""
WindEstimatorクラスのマニューバー検出機能のテスト
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

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
        
        # タックパターンの方位変化（45度→315度）
        bearings = [45] * 9 + [0] + [315] * 10
        
        # 速度データ（タック中に減速）
        speeds = [5.5] * 9 + [3.0] + [5.5] * 10
        
        return pd.DataFrame({
            'timestamp': times,
            'latitude': latitudes,
            'longitude': longitudes,
            'speed': speeds,
            'course': bearings
        })
    
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

    def test_detect_maneuvers_integration(self):
        """マニューバー検出の統合テスト"""
        # シンプルなタックパターンのデータを作成
        test_data = self._create_simple_tack_data()
        
        # 風向を設定（テストデータでは風向0度を想定）
        wind_direction = 0.0
        
        # マニューバー検出
        maneuvers = self.estimator.detect_maneuvers(test_data, wind_direction)
        
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


if __name__ == '__main__':
    unittest.main()
