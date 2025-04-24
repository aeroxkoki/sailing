#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WindFieldFusionSystem モジュールの単純なテスト

このスクリプトはバグを特定するための簡略化されたテストを提供します。
"""

import os
import sys
import numpy as np
from datetime import datetime, timedelta

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# テスト対象のモジュールをインポート
try:
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

def test_wind_field_fusion_system():
    """WindFieldFusionSystemの基本機能テスト"""
    print("WindFieldFusionSystemテスト開始...")
    
    # インスタンス化
    print("WindFieldFusionSystemのインスタンス化中...")
    fusion_system = WindFieldFusionSystem()
    print("インスタンス化成功")
    
    # サンプルデータの作成
    print("サンプルデータの作成中...")
    base_time = datetime.now()
    data_points = []
    
    for i in range(10):
        point = {
            'timestamp': base_time + timedelta(minutes=i*5),
            'latitude': 35.45 + i * 0.001,
            'longitude': 139.65 + i * 0.001,
            'wind_direction': 90 + i * 2,
            'wind_speed': 12 + i * 0.2,
        }
        data_points.append(point)
    
    print(f"サンプルデータを{len(data_points)}ポイント作成")
    
    # データ追加テスト
    print("風データポイントの追加をテスト中...")
    for point in data_points[:4]:
        fusion_system.add_wind_data_point(point)
    
    print(f"現在のデータポイント数: {len(fusion_system.wind_data_points)}")
    
    # データが融合されたかどうかを確認
    if fusion_system.current_wind_field is None:
        print("データポイント数が少ないため、まだ風の場は生成されていません")
    
    # 残りのデータを追加して融合処理を実行
    print("残りのデータポイントを追加し、風の場の融合を実行...")
    for point in data_points[4:]:
        fusion_system.add_wind_data_point(point)
    
    # 風の場が生成されたかどうかを確認
    if fusion_system.current_wind_field is not None:
        print("風の場生成成功:")
        print(f"- グリッドサイズ: {fusion_system.current_wind_field['lat_grid'].shape}")
        print(f"- 時間: {fusion_system.current_wind_field['time']}")
    else:
        print("風の場生成失敗")
    
    # 風の場の予測をテスト
    print("風の場の予測をテスト中...")
    future_time = base_time + timedelta(minutes=30)
    
    try:
        predicted_field = fusion_system.predict_wind_field(future_time)
        if predicted_field is not None:
            print("予測成功:")
            print(f"- グリッドサイズ: {predicted_field['lat_grid'].shape}")
            print(f"- 時間: {predicted_field['time']}")
        else:
            print("予測失敗: 結果がNone")
    except Exception as e:
        print(f"予測中にエラー発生: {e}")
    
    # 予測品質レポートのテスト
    print("予測品質レポートのテスト...")
    try:
        report = fusion_system.get_prediction_quality_report()
        if report:
            print("レポート取得成功:")
            print(f"- ステータス: {report.get('status')}")
            print(f"- サンプルサイズ: {report.get('sample_size')}")
        else:
            print("レポート取得失敗")
    except Exception as e:
        print(f"レポート取得中にエラー発生: {e}")
    
    print("WindFieldFusionSystemテスト完了")
    return True

if __name__ == "__main__":
    print("風統合システムの単純なテストを実行します...")
    success = test_wind_field_fusion_system()
    sys.exit(0 if success else 1)
