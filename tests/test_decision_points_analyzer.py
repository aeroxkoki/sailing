# -*- coding: utf-8 -*-
"""
DecisionPointsAnalyzerのテスト

重要ポイント特定アルゴリズムのテスト
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging

# ロギングの無効化
logging.disable(logging.CRITICAL)

# モジュールのインポートパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sailing_data_processor.analysis.decision_points_analyzer import DecisionPointsAnalyzer

class TestDecisionPointsAnalyzer(unittest.TestCase):
    """
    DecisionPointsAnalyzerクラスのテスト
    """
    
    def setUp(self):
        """テスト環境のセットアップ"""
        # テスト用のアナライザの作成
        self.analyzer = DecisionPointsAnalyzer(sensitivity=0.7, analysis_level="advanced")
        
        # テスト用のトラックデータの作成
        self.track_data = self._create_test_track_data()
        
        # テスト用の風データの作成
        self.wind_data = self._create_test_wind_data()
    
    def test_initialization(self):
        """初期化のテスト"""
        # 基本設定でのインスタンス化
        analyzer = DecisionPointsAnalyzer()
        self.assertEqual(analyzer.sensitivity, 0.7)
        self.assertEqual(analyzer.analysis_level, "advanced")
        
        # カスタム設定でのインスタンス化
        analyzer = DecisionPointsAnalyzer(sensitivity=0.5, analysis_level="professional")
        self.assertEqual(analyzer.sensitivity, 0.5)
        self.assertEqual(analyzer.analysis_level, "professional")
        
        # 検出パラメータが適切に設定されていることの確認
        self.assertIn("vmg_change_threshold", analyzer.detection_params)
        self.assertIn("speed_change_threshold", analyzer.detection_params)
        self.assertIn("wind_shift_threshold", analyzer.detection_params)
    
    def test_identify_key_points(self):
        """重要ポイント特定のテスト"""
        # 基本的な動作テスト
        result = self.analyzer.identify_key_points(self.track_data, self.wind_data)
        
        # 結果の構造をチェック
        self.assertIsInstance(result, dict)
        self.assertIn("high_impact_points", result)
        self.assertIn("strategic_points", result)
        self.assertIn("performance_points", result)
        self.assertIn("summary", result)
        
        # 空のデータフレームに対する動作テスト
        empty_result = self.analyzer.identify_key_points(pd.DataFrame(), self.wind_data)
        self.assertEqual(len(empty_result["high_impact_points"]), 0)
    
    def test_detect_strategic_decisions(self):
        """戦略的決断の検出テスト"""
        strategic_points = self.analyzer.detect_strategic_decisions(self.track_data, self.wind_data)
        
        # 戦略的ポイントが検出されていることをチェック
        self.assertIsInstance(strategic_points, list)
        
        # ポイントの各フィールドをチェック
        if strategic_points:
            point = strategic_points[0]
            self.assertIn("type", point)
            self.assertIn("time", point)
            self.assertIn("position", point)
            self.assertIn("description", point)
    
    def test_detect_performance_changes(self):
        """パフォーマンス変化の検出テスト"""
        performance_metrics = self.analyzer._extract_performance_metrics(self.track_data, self.wind_data)
        performance_points = self.analyzer.detect_performance_changes(self.track_data, performance_metrics)
        
        # パフォーマンスポイントが検出されていることをチェック
        self.assertIsInstance(performance_points, list)
        
        # ポイントの各フィールドをチェック
        if performance_points:
            point = performance_points[0]
            self.assertIn("type", point)
            self.assertIn("time", point)
            self.assertIn("position", point)
            self.assertIn("description", point)
    
    def test_calculate_impact_scores(self):
        """影響度スコア計算のテスト"""
        # テスト用のポイントリスト
        test_points = [
            {
                "type": "tack",
                "time": datetime.now(),
                "position": (35.0, 139.0),
                "description": "テストタック",
                "execution_quality": 0.8
            },
            {
                "type": "vmg_improvement",
                "time": datetime.now() + timedelta(minutes=5),
                "position": (35.01, 139.01),
                "description": "VMG向上",
                "change_magnitude": 0.2
            }
        ]
        
        scored_points = self.analyzer.calculate_impact_scores(test_points, self.track_data, self.wind_data)
        
        # スコアリングされたポイントをチェック
        self.assertEqual(len(scored_points), 2)
        for point in scored_points:
            self.assertIn("impact_score", point)
            self.assertGreaterEqual(point["impact_score"], 0)
            self.assertLessEqual(point["impact_score"], 10)
    
    def test_generate_what_if_scenarios(self):
        """What-ifシナリオ生成のテスト"""
        # テスト用のポイント
        test_point = {
            "type": "tack",
            "time": datetime.now(),
            "position": (35.0, 139.0),
            "description": "テストタック",
            "execution_quality": 0.8,
            "old_heading": 45.0,
            "new_heading": 315.0
        }
        
        scenarios = self.analyzer.generate_what_if_scenarios(test_point, self.track_data, self.wind_data)
        
        # シナリオが生成されていることをチェック
        self.assertIsInstance(scenarios, list)
        self.assertGreater(len(scenarios), 0)
        
        # シナリオの各フィールドをチェック
        if scenarios:
            scenario = scenarios[0]
            self.assertIn("scenario", scenario)
            self.assertIn("outcome", scenario)
            self.assertIn("impact", scenario)
    
    def test_analyze_cross_points(self):
        """クロスポイント分析のテスト"""
        # テスト用の競合艇データ
        competitor_data = self._create_test_competitor_data()
        
        cross_points = self.analyzer.analyze_cross_points(self.track_data, competitor_data)
        
        # クロスポイントリストが返されることをチェック
        self.assertIsInstance(cross_points, list)
    
    def test_analyze_mark_roundings(self):
        """マーク回航分析のテスト"""
        # テスト用のマークデータ
        marks = [
            {"latitude": 35.01, "longitude": 139.01, "type": "windward"},
            {"latitude": 34.99, "longitude": 139.01, "type": "leeward"}
        ]
        
        mark_points = self.analyzer.analyze_mark_roundings(self.track_data, marks)
        
        # マーク回航ポイントリストが返されることをチェック
        self.assertIsInstance(mark_points, list)
    
    def test_detect_missed_opportunities(self):
        """機会損失ポイント検出のテスト"""
        missed_points = self.analyzer.detect_missed_opportunities(self.track_data, self.wind_data, None)
        
        # 機会損失ポイントリストが返されることをチェック
        self.assertIsInstance(missed_points, list)
    
    def test_remove_duplicate_points(self):
        """重複ポイント除外のテスト"""
        # 重複するポイントを含むリスト
        test_points = [
            {
                "type": "tack",
                "time": datetime.now(),
                "position": (35.0, 139.0),
                "description": "テストタック1"
            },
            {
                "type": "tack",
                "time": datetime.now(),
                "position": (35.0, 139.0),
                "description": "テストタック2"
            },
            {
                "type": "gybe",
                "time": datetime.now() + timedelta(minutes=5),
                "position": (35.01, 139.01),
                "description": "テストジャイブ"
            }
        ]
        
        unique_points = self.analyzer._remove_duplicate_points(test_points)
        
        # 重複が除去されていることをチェック
        self.assertEqual(len(unique_points), 2)
    
    def test_generate_analysis_summary(self):
        """分析サマリー生成のテスト"""
        # テストデータ
        high_impact_points = [
            {
                "type": "tack",
                "time": datetime.now(),
                "position": (35.0, 139.0),
                "description": "テストタック",
                "impact_score": 8.5
            }
        ]
        strategic_points = [high_impact_points[0]]
        performance_points = []
        cross_points = []
        missed_points = []
        
        summary = self.analyzer._generate_analysis_summary(
            high_impact_points, strategic_points, performance_points, cross_points, missed_points
        )
        
        # サマリーが文字列であることをチェック
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
    
    def test_calculate_distance(self):
        """距離計算のテスト"""
        # テスト座標
        lat1, lon1 = 35.0, 139.0
        lat2, lon2 = 35.01, 139.01
        
        # 距離計算
        distance = self.analyzer._calculate_distance(lat1, lon1, lat2, lon2)
        
        # 距離が正の値であることをチェック
        self.assertGreater(distance, 0)
    
    def test_calculate_bearing(self):
        """方位角計算のテスト"""
        # テスト座標
        lat1, lon1 = 35.0, 139.0
        lat2, lon2 = 35.01, 139.0  # 北方向
        
        # 方位角計算
        bearing = self.analyzer._calculate_bearing(lat1, lon1, lat2, lon2)
        
        # 方位角が0-360度の範囲であることをチェック
        self.assertGreaterEqual(bearing, 0)
        self.assertLess(bearing, 360)
        
        # 北方向なので、方位角は0度付近であるべき
        self.assertLess(bearing, 45)
    
    def _create_test_track_data(self):
        """テスト用のトラックデータを作成"""
        # 現在時刻
        now = datetime.now()
        
        # 円形コースのシミュレーション
        n_points = 100
        timestamps = [now + timedelta(seconds=i*10) for i in range(n_points)]
        
        # 中心点と半径
        center_lat, center_lon = 35.0, 139.0
        radius = 0.01  # 約1km
        
        # 円周上の点を生成
        angles = np.linspace(0, 2 * np.pi, n_points)
        latitudes = center_lat + radius * np.sin(angles)
        longitudes = center_lon + radius * np.cos(angles)
        
        # ヘディングの計算（接線方向）
        headings = (np.degrees(angles) + 90) % 360
        
        # 速度（5〜8ノット）
        speeds = 6.0 + np.sin(angles * 2) * 1.5
        
        # VMG（速度の70〜90%）
        vmg = speeds * (0.7 + 0.2 * np.abs(np.sin(angles)))
        
        # データフレームの作成
        data = {
            'timestamp': timestamps,
            'latitude': latitudes,
            'longitude': longitudes,
            'heading': headings,
            'speed': speeds,
            'vmg': vmg
        }
        
        return pd.DataFrame(data)
    
    def _create_test_wind_data(self):
        """テスト用の風データを作成"""
        # 現在時刻
        now = datetime.now()
        
        # データポイント数
        n_points = 100
        timestamps = [now + timedelta(seconds=i*10) for i in range(n_points)]
        
        # 風向（平均225度、±20度の変動）
        wind_directions = 225 + np.sin(np.linspace(0, 4 * np.pi, n_points)) * 20
        
        # 風速（平均10ノット、±2ノットの変動）
        wind_speeds = 10 + np.sin(np.linspace(0, 8 * np.pi, n_points)) * 2
        
        # データフレームの作成
        data = {
            'timestamp': timestamps,
            'wind_direction': wind_directions,
            'wind_speed': wind_speeds
        }
        
        return pd.DataFrame(data)
    
    def _create_test_competitor_data(self):
        """テスト用の競合艇データを作成"""
        # トラックデータをベースに少し位置をずらす
        competitor_data = self.track_data.copy()
        
        # 位置をランダムにずらす
        np.random.seed(42)  # 再現性のため
        lat_noise = np.random.normal(0, 0.0002, len(competitor_data))
        lon_noise = np.random.normal(0, 0.0002, len(competitor_data))
        
        competitor_data['latitude'] += lat_noise
        competitor_data['longitude'] += lon_noise
        
        # 艇IDを追加
        competitor_data['boat_id'] = 2
        
        return competitor_data

if __name__ == "__main__":
    unittest.main()
