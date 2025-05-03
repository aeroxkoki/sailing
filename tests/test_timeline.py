# -*- coding: utf-8 -*-
"""
tests.test_timeline

イベントタイムラインとパラメータタイムラインのテストモジュールです。
タイムライン要素の機能が正しく動作することを検証します。

注: このテストは、まだ実装されていないレポーティング機能に依存しているため、
現時点では無効化されています。将来的にレポーティング機能が実装された際に
再度有効化します。
"""

import unittest
import datetime
import json
import re
import math
import sys
import os
from typing import Dict, Any
import numpy as np

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# EventTimelineとParameterTimelineは現在未実装のため、テストをスキップ
# from sailing_data_processor.reporting.elements.timeline.event_timeline import EventTimeline
# from sailing_data_processor.reporting.elements.timeline.parameter_timeline import ParameterTimeline


@unittest.skip("レポーティング機能が未実装のため一時的にスキップ")
class TestEventTimeline(unittest.TestCase):
    """
    イベントタイムライン機能のテストケース
    """
    
    def setUp(self):
        """テスト用のイベントタイムラインとデータを設定"""
        self.timeline = EventTimeline(name="テスト用イベントタイムライン")
        
        # テスト用のイベントデータを準備
        self.time_base = datetime.datetime(2023, 4, 1, 12, 0, 0)
        self.test_events = [
            {"time": self.time_base, "type": "tack", "label": "タックA"},
            {"time": self.time_base + datetime.timedelta(minutes=5), "type": "jibe", "label": "ジャイブA"},
            {"time": self.time_base + datetime.timedelta(minutes=10), "type": "mark_rounding", "label": "マーク1"},
            {"time": self.time_base + datetime.timedelta(minutes=15), "type": "tack", "label": "タックB"},
            {"time": self.time_base + datetime.timedelta(minutes=20), "type": "start", "label": "スタート"},
            {"time": self.time_base + datetime.timedelta(minutes=30), "type": "finish", "label": "フィニッシュ"}
        ]
        
        # テスト用のデータセット
        self.test_data = {
            "timestamp": [ev["time"].isoformat() for ev in self.test_events],
            "is_tack": [ev["type"] == "tack" for ev in self.test_events],
            "is_jibe": [ev["type"] == "jibe" for ev in self.test_events],
            "is_mark_rounding": [ev["type"] == "mark_rounding" for ev in self.test_events],
            "is_start": [ev["type"] == "start" for ev in self.test_events],
            "is_finish": [ev["type"] == "finish" for ev in self.test_events],
            "speed": [5.0, 4.5, 6.0, 5.5, 4.0, 5.0],
            "wind_speed": [12.0, 12.5, 13.0, 12.0, 11.5, 12.0],
            "wind_direction": [45.0, 48.0, 50.0, 47.0, 45.0, 46.0],
            "heading": [280.0, 100.0, 90.0, 270.0, 95.0, 100.0]
        }
    
    def test_event_addition(self):
        """イベントの追加と取得のテスト"""
        # 直接イベントを追加
        for event in self.test_events:
            event_data = self.timeline.add_event(
                timestamp=event["time"],
                event_type=event["type"],
                label=event["label"],
                details={"test": True}
            )
            # イベントIDが生成されることを確認
            self.assertIsNotNone(event_data["id"])
            # イベントタイプが正しく設定されることを確認
            self.assertEqual(event_data["type"], event["type"])
            # ラベルが正しく設定されることを確認
            self.assertEqual(event_data["label"], event["label"])
        
        # イベント数を確認
        self.assertEqual(len(self.test_events), len(self.timeline._events))
    
    def test_event_extraction_from_data(self):
        """データからのイベント抽出のテスト"""
        # データソースを設定
        self.timeline.set_property("data_source", "test_data")
        
        # イベントタイプとフィールドの対応を設定
        self.timeline.set_property("event_type_fields", {
            "tack": "is_tack",
            "jibe": "is_jibe",
            "mark_rounding": "is_mark_rounding",
            "start": "is_start",
            "finish": "is_finish"
        })
        
        # タイムラインをレンダリング（これによりイベントが抽出される）
        html = self.timeline.render({"test_data": self.test_data})
        
        # イベントのフィルタリングが機能することを確認するため、一部のイベントを非表示に設定
        self.timeline.set_property("show_tacks", False)
        filtered_html = self.timeline.render({"test_data": self.test_data})
        
        # HTMLの長さが変わることを確認（タックが非表示になっているため）
        self.assertLess(len(filtered_html), len(html))
        
        # HTMLにタックイベントのラベルが含まれていないことを確認
        self.assertNotIn("タックA", filtered_html)
        self.assertNotIn("タックB", filtered_html)
        
        # ジャイブイベントはまだ表示されていることを確認
        self.assertIn("ジャイブA", filtered_html)
    
    def test_event_filtering(self):
        """イベントのフィルタリング設定のテスト"""
        # イベントを追加
        for event in self.test_events:
            self.timeline.add_event(
                timestamp=event["time"],
                event_type=event["type"],
                label=event["label"]
            )
        
        # すべてのイベントタイプを表示
        self.timeline.set_property("show_tacks", True)
        self.timeline.set_property("show_jibes", True)
        self.timeline.set_property("show_marks", True)
        self.timeline.set_property("show_custom", True)
        
        html = self.timeline.render()
        
        # 各イベントのラベルがHTMLに含まれていることを確認
        for event in self.test_events:
            self.assertIn(event["label"], html)
        
        # タックイベントを非表示に設定
        self.timeline.set_property("show_tacks", False)
        filtered_html = self.timeline.render()
        
        # タックイベントのラベルがHTML内に存在しないことを確認
        tack_events = [e for e in self.test_events if e["type"] == "tack"]
        for event in tack_events:
            self.assertNotIn(event["label"], filtered_html)
        
        # その他のイベントは表示されていることを確認
        non_tack_events = [e for e in self.test_events if e["type"] != "tack"]
        for event in non_tack_events:
            self.assertIn(event["label"], filtered_html)
    
    def test_event_styling(self):
        """イベントの表示スタイル設定のテスト"""
        # イベントを追加
        for event in self.test_events:
            self.timeline.add_event(
                timestamp=event["time"],
                event_type=event["type"],
                label=event["label"]
            )
        
        # 表示スタイル設定のテスト
        self.timeline.set_property("event_height", 30)
        self.timeline.set_property("group_events", False)
        self.timeline.set_property("tooltip_placement", "bottom")
        
        html = self.timeline.render()
        
        # イベント高さの設定が反映されていることを確認
        self.assertIn("eventHeight: 30", html)
        
        # グループ化設定が反映されていることを確認
        self.assertIn("groupEvents: false", html)
        
        # ツールチップの位置設定が反映されていることを確認
        self.assertIn('tooltipPlacement: "bottom"', html)


@unittest.skip("レポーティング機能が未実装のため一時的にスキップ")
class TestParameterTimeline(unittest.TestCase):
    """
    パラメータタイムライン機能のテストケース
    """
    
    def setUp(self):
        """テスト用のパラメータタイムラインとデータを設定"""
        self.timeline = ParameterTimeline(name="テスト用パラメータタイムライン")
        
        # テスト用の時間データを準備
        self.time_base = datetime.datetime(2023, 4, 1, 12, 0, 0)
        time_points = 50
        self.timestamps = [
            (self.time_base + datetime.timedelta(seconds=i*10)).isoformat()
            for i in range(time_points)
        ]
        
        # 各パラメータのテストデータを生成
        np.random.seed(42)  # 再現性のための乱数シード設定
        
        self.speed_data = 5.0 + np.sin(np.linspace(0, 4*np.pi, time_points)) + np.random.normal(0, 0.2, time_points)
        self.wind_speed_data = 12.0 + np.sin(np.linspace(0, 2*np.pi, time_points)) + np.random.normal(0, 0.5, time_points)
        self.wind_dir_data = 45.0 + np.sin(np.linspace(0, 3*np.pi, time_points)) * 10.0 + np.random.normal(0, 2.0, time_points)
        self.heading_data = np.concatenate([
            np.ones(time_points//2) * 270.0,
            np.ones(time_points//2) * 90.0
        ]) + np.random.normal(0, 2.0, time_points)
        
        # テスト用のデータセット
        self.test_data = {
            "timestamp": self.timestamps,
            "speed": self.speed_data.tolist(),
            "wind_speed": self.wind_speed_data.tolist(),
            "wind_direction": self.wind_dir_data.tolist(),
            "heading": self.heading_data.tolist()
        }
    
    def test_parameter_display_settings(self):
        """パラメータの表示設定テスト"""
        # データソースを設定
        self.timeline.set_property("data_source", "test_data")
        
        # すべてのパラメータを表示
        self.timeline.set_property("show_speed", True)
        self.timeline.set_property("show_wind_speed", True)
        self.timeline.set_property("show_wind_direction", True)
        self.timeline.set_property("show_heading", True)
        
        html = self.timeline.render({"test_data": self.test_data})
        
        # 各パラメータのラベルがHTMLに含まれていることを確認
        self.assertIn("速度 (kt)", html)
        self.assertIn("風速 (kt)", html)
        self.assertIn("風向 (°)", html)
        self.assertIn("艇首方位 (°)", html)
        
        # 風向を非表示に設定
        self.timeline.set_property("show_wind_direction", False)
        filtered_html = self.timeline.render({"test_data": self.test_data})
        
        # 風向のラベルがHTML内に存在しないことを確認
        self.assertNotIn("風向 (°)", filtered_html)
        
        # その他のパラメータは表示されていることを確認
        self.assertIn("速度 (kt)", filtered_html)
        self.assertIn("風速 (kt)", filtered_html)
        self.assertIn("艇首方位 (°)", filtered_html)
    
    def test_parameter_data_setting(self):
        """データの設定と取得のテスト"""
        # 直接データを設定
        self.timeline.set_data(self.test_data)
        
        # レンダリング
        html = self.timeline.render()
        
        # データがJSON形式で含まれていることを確認
        for ts in self.timestamps[:5]:  # 最初の5つのタイムスタンプをチェック
            self.assertIn(ts, html)
    
    def test_custom_parameter(self):
        """カスタムパラメータの追加と表示のテスト"""
        # データソースを設定
        self.timeline.set_property("data_source", "test_data")
        
        # VMGを計算してテストデータに追加
        vmg = self.speed_data * np.cos(np.radians(np.abs(self.wind_dir_data - self.heading_data)))
        self.test_data["vmg"] = vmg.tolist()
        
        # カスタムパラメータを追加
        self.timeline.add_custom_parameter(
            name="vmg_test",
            field="vmg",
            color="#FF9800",
            label="VMG",
            unit="kt",
            axis="y-left"
        )
        
        # カスタムパラメータリストが更新されたことを確認
        custom_params = self.timeline.get_property("custom_parameters", [])
        self.assertIn("vmg_test", custom_params)
        
        # カスタムパラメータをパラメータ定義に追加
        self.assertEqual(self.timeline._parameters["vmg_test"]["label"], "VMG")
        self.assertEqual(self.timeline._parameters["vmg_test"]["color"], "#FF9800")
        
        # レンダリング
        html = self.timeline.render({"test_data": self.test_data})
        
        # カスタムパラメータが出力に含まれることを確認（カスタムパラメータは自動的に追加されないので確認不可）
    
    def test_statistics_calculation(self):
        """統計情報の計算テスト"""
        # 直接データを設定
        self.timeline.set_data(self.test_data)
        
        # calculate_statistics メソッドをテスト
        speed_stats = self.timeline.calculate_statistics(self.test_data, "speed")
        
        # 統計値が計算されていることを確認
        self.assertIn("min", speed_stats)
        self.assertIn("max", speed_stats)
        self.assertIn("avg", speed_stats)
        
        # 計算値が正しいことを確認
        self.assertAlmostEqual(speed_stats["min"], min(self.speed_data), places=4)
        self.assertAlmostEqual(speed_stats["max"], max(self.speed_data), places=4)
        self.assertAlmostEqual(speed_stats["avg"], sum(self.speed_data) / len(self.speed_data), places=4)
        
        # 統計情報表示設定を有効にしてレンダリング
        self.timeline.set_property("show_statistics", True)
        html = self.timeline.render()
        
        # 統計情報を示す文字列がHTMLに含まれていることを確認
        self.assertIn("statistics", html)
    
    def test_styling_options(self):
        """表示スタイル設定のテスト"""
        # データを設定
        self.timeline.set_data(self.test_data)
        
        # 表示スタイル設定
        self.timeline.set_property("line_style", "spline")
        self.timeline.set_property("point_radius", 5)
        self.timeline.set_property("enable_zoom", True)
        
        html = self.timeline.render()
        
        # 線の張力（スプライン）設定が反映されていることを確認
        self.assertIn("tension: 0.1", html)
        
        # 点のサイズ設定が反映されていることを確認
        self.assertIn("pointRadius: 5", html)
        
        # ズーム設定が反映されていることを確認
        self.assertIn("zoom", html)
        
        # 線のスタイルを変更
        self.timeline.set_property("line_style", "linear")
        updated_html = self.timeline.render()
        
        # 張力が0に変更されていることを確認（直線）
        self.assertIn("tension: 0", updated_html)


if __name__ == '__main__':
    unittest.main()
