#!/usr/bin/env python3
"""
WindFieldFusionSystem エラーデバッグテスト - 拡張版

このスクリプトは、風の場生成のエラーをより詳細に追跡します。
風の場生成中の内部メソッド呼び出しを監視し、問題点を特定します。
"""

import sys
import traceback
from datetime import datetime

try:
    # モジュールとクラスのインポート
    print("1. モジュールのインポート開始")
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator
    print("2. モジュールのインポート成功")
    
    # WindFieldInterpolatorの初期化
    print("3. WindFieldInterpolator インスタンス化")
    interpolator = WindFieldInterpolator()
    print("4. WindFieldInterpolator インスタンス化成功")
    
    # WindFieldFusionSystemの初期化
    print("5. WindFieldFusionSystem インスタンス化")
    fusion_system = WindFieldFusionSystem()
    print("6. WindFieldFusionSystem インスタンス化成功")
    
    # field_interpolatorの確認
    print(f"7. 関連付けられたInterpolator: {fusion_system.field_interpolator}")
    
    # シグネチャ確認
    from inspect import signature
    interp_signature = signature(interpolator.interpolate_wind_field)
    print(f"8. interpolate_wind_field シグネチャ: {interp_signature}")
    
    resample_signature = signature(interpolator._resample_wind_field)
    print(f"9. _resample_wind_field シグネチャ: {resample_signature}")
    
    # 単純なデータポイントでテスト
    test_point = {
        'timestamp': datetime.now(),
        'latitude': 35.45,
        'longitude': 139.65,
        'wind_direction': 90,
        'wind_speed': 10
    }
    
    print("10. 単一データポイント追加")
    fusion_system.add_wind_data_point(test_point)
    print("11. データポイント追加成功")
    
    # 5つのデータポイントを追加（風の場生成をトリガー）
    print("12. 複数データポイント追加開始")
    for i in range(4):  # すでに1つ追加しているので、あと4つ
        point = {
            'timestamp': datetime.now(),
            'latitude': 35.45 + i * 0.01,
            'longitude': 139.65 + i * 0.01,
            'wind_direction': 90 + i * 5,
            'wind_speed': 10 + i * 0.5
        }
        try:
            print(f"13.{i} データポイント追加: lat={point['latitude']}, lon={point['longitude']}")
            fusion_system.add_wind_data_point(point)
            print(f"13.{i} データポイント追加成功")
        except Exception as e:
            print(f"13.{i} データポイント追加失敗: {e}")
            traceback.print_exc()
    
    print("14. 複数データポイント追加完了")
    
    # 現在のデータポイント数の確認
    print(f"15. 現在のデータポイント数: {len(fusion_system.wind_data_points)}")
    
    # 風の場生成メソッド呼び出しを直接デバッグ
    print("16. 風の場生成メソッド直接呼び出し")
    try:
        fusion_system.fuse_wind_data()
        print("17. 風の場生成メソッド呼び出し成功")
    except Exception as e:
        print(f"17. 風の場生成メソッド呼び出し失敗: {e}")
        traceback.print_exc()
    
    # 風の場生成の確認
    if fusion_system.current_wind_field is not None:
        print("18. 風の場生成成功")
        print(f"  - グリッドサイズ: {fusion_system.current_wind_field['lat_grid'].shape}")
    else:
        print("18. 風の場生成失敗")
    
    # スケーリング機能テスト
    print("19. データスケーリングテスト開始")
    test_points = [
        {'latitude': 35.45, 'longitude': 139.65, 'wind_speed': 10, 'wind_direction': 90},
        {'latitude': 35.46, 'longitude': 139.66, 'wind_speed': 12, 'wind_direction': 95}
    ]
    
    try:
        scaled_points = fusion_system._scale_data_points(test_points)
        print("20. データスケーリング成功")
        print(f"  - スケーリング後データ: {len(scaled_points)}件")
        if scaled_points:
            print(f"  - スケーリング結果キー: {list(scaled_points[0].keys())}")
    except Exception as e:
        print(f"20. データスケーリングエラー: {e}")
        traceback.print_exc()
    
    # 直接interpolatorを使用してみる
    try:
        print("21. 直接interpolatorでテスト")
        # テスト用のサンプルデータ
        test_lats = [35.45, 35.46, 35.47, 35.48, 35.49]
        test_lons = [139.65, 139.66, 139.67, 139.68, 139.69]
        test_dirs = [90, 92, 94, 96, 98]
        test_speeds = [10, 11, 12, 13, 14]
        
        import numpy as np
        test_grid_lats, test_grid_lons = np.meshgrid(test_lats, test_lons)
        
        test_field = {
            'lat_grid': test_grid_lats,
            'lon_grid': test_grid_lons,
            'wind_direction': np.array(test_dirs).reshape((1, 5)) * np.ones_like(test_grid_lats),
            'wind_speed': np.array(test_speeds).reshape((1, 5)) * np.ones_like(test_grid_lats),
            'confidence': 0.8 * np.ones_like(test_grid_lats),
            'time': datetime.now()
        }
        
        # interpolatorのメソッド直接呼び出し
        interp_result = interpolator._resample_wind_field(test_field, 10, qhull_options='QJ')
        print("22. interpolator._resample_wind_field 呼び出し成功")
        if interp_result:
            print(f"  - 結果グリッドサイズ: {interp_result['lat_grid'].shape}")
    except Exception as e:
        print(f"22. interpolator._resample_wind_field 呼び出し失敗: {e}")
        traceback.print_exc()
    
    print("23. 全テスト完了")
    sys.exit(0)
    
except Exception as e:
    print(f"エラー発生: {e}")
    traceback.print_exc()
    sys.exit(1)
