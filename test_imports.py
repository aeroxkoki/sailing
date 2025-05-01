#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポートテスト用スクリプト
"""

import sys
import os
import traceback

# パスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# インポートを試みる
try:
    print("1. モジュールのインポート開始")
    import sailing_data_processor
    print("2. モジュールのインポート成功")
    
    print("3. WindFieldInterpolator インスタンス化")
    from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator
    interpolator = WindFieldInterpolator()
    print("4. WindFieldInterpolator インスタンス化成功")
    
    print("5. WindFieldFusionSystem インスタンス化")
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    fusion_system = WindFieldFusionSystem()
    print("6. WindFieldFusionSystem インスタンス化成功")
    print("7. 関連付けられたInterpolator:", fusion_system.field_interpolator)
    
    # メソッドのシグネチャを確認
    import inspect
    
    # フィールドインターポレーターのメソッドシグネチャを確認
    print("8. field_interpolator.interpolate_wind_field シグネチャ:", 
          inspect.signature(fusion_system.field_interpolator.interpolate_wind_field))
    print("9. field_interpolator._resample_wind_field シグネチャ:", 
          inspect.signature(fusion_system.field_interpolator._resample_wind_field))
    
    # データポイントを追加
    print("10. 単一データポイント追加")
    from datetime import datetime
    fusion_system.add_wind_data_point({
        'timestamp': datetime.now(),
        'latitude': 35.45,
        'longitude': 139.65,
        'wind_direction': 90.0,
        'wind_speed': 10.0,
        'confidence': 0.8
    })
    print("11. データポイント追加成功")
    
    # 複数のデータポイントを追加
    print("12. 複数データポイント追加開始")
    for i in range(4):
        lat = 35.45 + i * 0.01
        lon = 139.65 + i * 0.01
        print(f"13.{i} データポイント追加: lat={lat}, lon={lon}")
        fusion_system.add_wind_data_point({
            'timestamp': datetime.now(),
            'latitude': lat,
            'longitude': lon,
            'wind_direction': 90.0 + i,
            'wind_speed': 10.0 + i * 0.5,
            'confidence': 0.8 - i * 0.05
        })
        print(f"13.{i} データポイント追加成功")
    print("14. 複数データポイント追加完了")
    
    # 現在のデータポイント数を確認
    print("15. 現在のデータポイント数:", len(fusion_system.wind_data_points))
    
    # 風の場生成
    print("16. 風の場生成メソッド直接呼び出し")
    from datetime import datetime, timedelta
    wind_field = fusion_system.fuse_wind_data()
    print("17. 風の場生成メソッド呼び出し成功")
    
    if wind_field:
        print("18. 風の場生成成功")
        print(f"  - グリッドサイズ: {wind_field['wind_direction'].shape}")
    else:
        print("18. 風の場生成失敗")
    
    # データスケーリングテスト
    print("19. データスケーリングテスト開始")
    import numpy as np
    test_data = {
        'latitude': np.array([35.45, 35.46]),
        'longitude': np.array([139.65, 139.66]),
        'wind_speed': np.array([10.0, 11.0]),
        'wind_direction': np.array([90.0, 91.0])
    }
    
    try:
        # スケーリング関数を直接呼び出し
        scaled_data = fusion_system._scale_data_points([
            {
                'latitude': 35.45,
                'longitude': 139.65,
                'wind_speed': 10.0,
                'wind_direction': 90.0
            },
            {
                'latitude': 35.46,
                'longitude': 139.66,
                'wind_speed': 11.0,
                'wind_direction': 91.0
            }
        ])
        print("20. データスケーリング成功")
        print(f"  - スケーリング後データ: {len(scaled_data)}件")
        print(f"  - スケーリング結果キー: {list(scaled_data[0].keys()) if scaled_data else []}")
    except Exception as e:
        print(f"20. データスケーリング失敗: {e}")
    
    # 直接interpolatorでテスト
    print("21. 直接interpolatorでテスト")
    try:
        resampled = interpolator._resample_wind_field(
            wind_field=test_data, 
            resolution=10,
            qhull_options=None
        )
        print("22. interpolator._resample_wind_field 呼び出し成功")
        print(f"  - 結果グリッドサイズ: {resampled['wind_direction'].shape}")
    except Exception as e:
        print(f"22. interpolator._resample_wind_field 呼び出し失敗: {e}")
    
    print("23. 全テスト完了")
    
except Exception as e:
    print(f"エラー: {e}")
    traceback.print_exc()
