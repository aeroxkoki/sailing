# -*- coding: utf-8 -*-
#\!/usr/bin/env python3
"""
WindEstimatorクラスの改良部分をテストするスクリプト
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト対象のクラスをインポート
from sailing_data_processor.wind_estimator import WindEstimator

def test_categorize_maneuver():
    """マニューバー分類機能のテスト"""
    estimator = WindEstimator()
    
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
    ]
    
    for i, (before, after, wind_dir, boat, expected) in enumerate(test_cases):
        result = estimator._categorize_maneuver(before, after, wind_dir, boat)
        if result['maneuver_type'] \!= expected:
            print(f"❌ テスト{i+1}失敗: 期待されるマニューバタイプ（{expected}）と実際の結果（{result['maneuver_type']}）が一致しません")
        else:
            print(f"✅ テスト{i+1}成功: マニューバタイプ {result['maneuver_type']}")
        
        # 信頼度が0-1の範囲内にあることを確認
        if not (0 <= result['confidence'] <= 1):
            print(f"❌ テスト{i+1}失敗: 信頼度（{result['confidence']}）が範囲外です")
        
        # 状態情報も出力
        print(f"   状態: {result['before_state']} → {result['after_state']}, 信頼度: {result['confidence']:.2f}")
        print(f"   角度変化: {result['angle_change']:.1f}°")
        print()

def test_determine_point_state():
    """風に対する状態判定のテスト"""
    estimator = WindEstimator()
    
    # テストケース
    test_cases = [
        # (相対角度, upwind_range, downwind_range, 期待される状態)
        (0, 80, 100, 'upwind'),
        (80, 80, 100, 'upwind'),
        (359, 80, 100, 'upwind'),
        (100, 80, 100, 'downwind'),
        (180, 80, 100, 'downwind'),
        (260, 80, 100, 'downwind'),
        (85, 80, 100, 'reaching'),
        (95, 80, 100, 'reaching'),
        (275, 80, 100, 'reaching'),
    ]
    
    for i, (rel_angle, upwind, downwind, expected) in enumerate(test_cases):
        result = estimator._determine_point_state(rel_angle, upwind, downwind)
        if result \!= expected:
            print(f"❌ テスト{i+1}失敗: 相対角度{rel_angle}°の期待される状態（{expected}）と実際の結果（{result}）が一致しません")
        else:
            print(f"✅ テスト{i+1}成功: 相対角度{rel_angle}°が正しく {result} と判定されました")

def _create_simple_tack_data():
    """明確なタックを含むシンプルなGPSデータを作成"""
    # 基準時刻
    base_time = datetime(2024, 3, 1, 10, 0, 0)
    
    # 100ポイントのデータ生成
    points = 100
    timestamps = [base_time + timedelta(seconds=i*5) for i in range(points)]
    
    # 方位データ - より明確なタックパターン（急激な変化）を作成
    bearings = [30] * 45  # 最初の45ポイントは30度
    bearings += [i for i in range(30, 150, 12)]  # 10ポイントで30度→150度へ変化
    bearings += [150] * (points - len(bearings))  # 残りのポイントは150度
    
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

def test_detect_maneuvers():
    """マニューバー検出機能のテスト"""
    estimator = WindEstimator()
    
    # テストデータ作成
    test_data = _create_simple_tack_data()
    
    # 風向を設定（テストデータでは風向0度を想定）
    wind_direction = 0.0
    
    # マニューバー検出
    maneuvers = estimator.detect_maneuvers(test_data, wind_direction)
    
    # 検出結果の表示
    if len(maneuvers) == 0:
        print("❌ テスト失敗: マニューバが検出されていません")
    else:
        print(f"✅ テスト成功: {len(maneuvers)}個のマニューバが検出されました")
        for i, maneuver in maneuvers.iterrows():
            print(f"マニューバ{i+1}: {maneuver['maneuver_type']}, 信頼度: {maneuver['maneuver_confidence']:.2f}")
            print(f"  角度変化: {maneuver['angle_change']:.1f}°, 方位: {maneuver['before_bearing']:.1f}° → {maneuver['after_bearing']:.1f}°")
            print(f"  状態変化: {maneuver['before_state']} → {maneuver['after_state']}")

if __name__ == "__main__":
    print("=== マニューバー分類テスト ===")
    test_categorize_maneuver()
    print("\n=== 状態判定テスト ===")
    test_determine_point_state()
    print("\n=== マニューバー検出テスト ===")
    test_detect_maneuvers()
