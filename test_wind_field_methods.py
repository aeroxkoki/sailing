# -*- coding: utf-8 -*-
import sys
import os
import traceback
from datetime import datetime, timedelta
import inspect

# カレントディレクトリをパスに追加
sys.path.insert(0, os.getcwd())

print("風フィールド関連メソッドのテスト開始")

try:
    # 必要なモジュールをインポート
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator
    
    print("1. モジュールのインポート成功")
    
    # WindFieldInterpolatorの動作確認
    interpolator = WindFieldInterpolator()
    print("2. WindFieldInterpolator インスタンス化")
    
    # メソッドの存在確認
    if hasattr(interpolator, 'interpolate_wind_field'):
        print("3. WindFieldInterpolator インスタンス化成功")
    else:
        print("3. interpolate_wind_fieldメソッドが見つかりません")
    
    # WindFieldFusionSystemの動作確認
    fusion_system = WindFieldFusionSystem()
    print("4. WindFieldFusionSystem インスタンス化")
    
    # メソッドの存在確認
    if hasattr(fusion_system, 'add_wind_data_point'):
        print("5. WindFieldFusionSystem インスタンス化成功")
    else:
        print("5. add_wind_data_pointメソッドが見つかりません")
    
    # フィールドの確認
    print(f"6. 関連付けられたInterpolator: {fusion_system.field_interpolator}")
    
    # メソッドのシグネチャ確認
    interpolate_sig = inspect.signature(interpolator.interpolate_wind_field)
    print(f"7. interpolate_wind_field シグネチャ: {interpolate_sig}")
    
    resample_sig = inspect.signature(interpolator._resample_wind_field)
    print(f"8. *resample*wind_field シグネチャ: {resample_sig}")
    
    # 単一データポイントの追加テスト
    print("9. 単一データポイント追加")
    current_time = datetime.now()
    test_point = {
        'timestamp': current_time,
        'latitude': 35.45,
        'longitude': 139.65,
        'wind_direction': 180.0,
        'wind_speed': 5.0
    }
    
    fusion_system.add_wind_data_point(test_point)
    print("10. データポイント追加成功")
    
    # 複数データポイントの追加テスト
    print("11. 複数データポイント追加開始")
    for i in range(4):
        time_point = current_time + timedelta(minutes=i*5)
        test_point = {
            'timestamp': time_point,
            'latitude': 35.45 + i * 0.01,
            'longitude': 139.65 + i * 0.01,
            'wind_direction': 180.0 + i * 2,
            'wind_speed': 5.0 + i * 0.5
        }
        
        print(f"12.{i} データポイント追加: lat={test_point['latitude']}, lon={test_point['longitude']}")
        fusion_system.add_wind_data_point(test_point)
        print(f"12.{i} データポイント追加成功")
    
    print("13. 複数データポイント追加完了")
    
    # データポイント数の確認
    print(f"14. 現在のデータポイント数: {len(fusion_system.wind_data_points)}")
    
    # 風の場生成メソッド直接呼び出し
    print("15. 風の場生成メソッド直接呼び出し")
    
    # フォールバックとなる単純な風の場を生成
    simple_field = fusion_system._create_simple_wind_field(
        fusion_system.wind_data_points, 20, current_time
    )
    
    print("16. 風の場生成メソッド呼び出し成功")
    
    # 風の場の確認
    if simple_field:
        print("17. 風の場生成成功")
        print(f" - グリッドサイズ: {simple_field['lat_grid'].shape}")
    else:
        print("17. 風の場生成失敗")
    
    # データスケーリングのテスト
    print("18. データスケーリングテスト開始")
    
    scaled_data = fusion_system._scale_data_points(fusion_system.wind_data_points[:2])
    
    if scaled_data:
        print("19. データスケーリング成功")
        print(f" - スケーリング後データ: {len(scaled_data)}件")
        print(f" - スケーリング結果キー: {list(scaled_data[0].keys())}")
    else:
        print("19. データスケーリング失敗")
    
    # 直接interpolatorを使ったテスト
    print("20. 直接interpolatorでテスト")
    
    resampled_field = interpolator._resample_wind_field(simple_field, 10)
    
    if resampled_field:
        print("21. interpolator._resample_wind_field 呼び出し成功")
        print(f" - 結果グリッドサイズ: {resampled_field['lat_grid'].shape}")
    else:
        print("21. interpolator._resample_wind_field 呼び出し失敗")
    
    print("22. 全テスト完了")
    
except Exception as e:
    print(f"エラー発生: {str(e)}")
    traceback.print_exc()

print("風フィールド関連メソッドのテスト終了")
