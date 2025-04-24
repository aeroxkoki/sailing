# -*- coding: utf-8 -*-
"""
風の移動モデル（WindPropagationModel）の基本機能検証スクリプト

このスクリプトは通常のテストフレームワークを使わず、直接WindPropagationModelの
基本機能を検証するために使用します。
"""

import sys
import os
import math
from datetime import datetime, timedelta
import numpy as np

# プロジェクトルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # WindPropagationModelをインポート
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    print("WindPropagationModelのインポートに成功しました")
except ImportError as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)

# テスト用の風データを生成
def create_standard_wind_data():
    """標準的な風の移動パターン（風速の60%で風向方向に移動）"""
    data = []
    base_time = datetime.now()
    base_lat, base_lon = 35.4, 139.7
    wind_dir, wind_speed = 90, 10  # 東風、10ノット
    
    for i in range(10):
        time = base_time + timedelta(seconds=i*5)
        lon_offset = 0.000139 * i  # 5秒間の東方向移動量
        
        data.append({
            'timestamp': time,
            'latitude': base_lat,
            'longitude': base_lon + lon_offset,
            'wind_direction': wind_dir,
            'wind_speed': wind_speed
        })
    return data, base_time

def create_complex_wind_data():
    """コリオリ効果を含む複雑な風パターン（風向から15度ずれた方向へ移動）"""
    data = []
    base_time = datetime.now()
    base_lat, base_lon = 35.5, 139.6
    wind_dir, wind_speed = 90, 12
    propagation_angle = 105  # 15度ずれ
    
    for i in range(10):
        time = base_time + timedelta(seconds=i*5)
        propagation_rad = np.radians(propagation_angle)
        lon_offset = 0.000150 * i * np.cos(propagation_rad)
        lat_offset = 0.000150 * i * np.sin(propagation_rad)
        
        data.append({
            'timestamp': time,
            'latitude': base_lat + lat_offset,
            'longitude': base_lon + lon_offset,
            'wind_direction': wind_dir,
            'wind_speed': wind_speed
        })
    return data, base_time

def create_varying_speed_data():
    """風速が変化するデータ（5～14ノット）"""
    data = []
    base_time = datetime.now()
    base_lat, base_lon = 35.6, 139.5
    wind_dir = 45
    
    for i in range(10):
        time = base_time + timedelta(seconds=i*5)
        wind_speed = 5 + i
        propagation_rad = np.radians(wind_dir)
        speed_factor = 0.6 * wind_speed / 10
        lon_offset = 0.000150 * i * speed_factor * np.cos(propagation_rad)
        lat_offset = 0.000150 * i * speed_factor * np.sin(propagation_rad)
        
        data.append({
            'timestamp': time,
            'latitude': base_lat + lat_offset,
            'longitude': base_lon + lon_offset,
            'wind_direction': wind_dir,
            'wind_speed': wind_speed
        })
    return data, base_time

# 基本的なテスト関数
def test_estimate_propagation_vector():
    print("\n=== 風の移動ベクトル推定テスト ===")
    
    # WindPropagationModelインスタンス作成
    model = WindPropagationModel()
    
    # 標準データでのテスト
    standard_data, _ = create_standard_wind_data()
    result = model.estimate_propagation_vector(standard_data)
    
    print("- 標準データでの推定結果:")
    print(f"  速度: {result['speed']:.2f} m/s")
    print(f"  方向: {result['direction']:.2f}°")
    print(f"  信頼度: {result['confidence']:.2f}")
    
    # 期待値
    expected_direction = 90
    expected_speed = 10 * 0.6 * 0.51444  # ノットからm/sへ変換
    
    # 許容誤差内かチェック
    direction_diff = abs(result['direction'] - expected_direction)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    if direction_diff <= 20:
        print("  方向: OK（許容誤差内）")
    else:
        print(f"  方向: NG（期待値: {expected_direction}°, 誤差: {direction_diff:.2f}°）")
    
    speed_diff = abs(result['speed'] - expected_speed)
    if speed_diff <= 1.0:
        print("  速度: OK（許容誤差内）")
    else:
        print(f"  速度: NG（期待値: {expected_speed:.2f}m/s, 誤差: {speed_diff:.2f}m/s）")

    # 複雑なデータでのテスト
    complex_data, _ = create_complex_wind_data()
    result = model.estimate_propagation_vector(complex_data)
    
    print("\n- 複雑なデータでの推定結果:")
    print(f"  速度: {result['speed']:.2f} m/s")
    print(f"  方向: {result['direction']:.2f}°")
    print(f"  信頼度: {result['confidence']:.2f}")
    
    # コリオリ効果を考慮した期待値
    expected_direction = 105
    
    direction_diff = abs(result['direction'] - expected_direction)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
    
    if direction_diff <= 25:
        print("  方向: OK（コリオリ効果考慮内）")
    else:
        print(f"  方向: NG（期待値: {expected_direction}°, 誤差: {direction_diff:.2f}°）")

def test_wind_speed_factor_adjustment():
    print("\n=== 風速に基づく係数調整テスト ===")
    
    # WindPropagationModelインスタンス作成
    model = WindPropagationModel()
    
    # 低風速データ（5ノット）
    low_wind_data = [{'wind_speed': 5} for _ in range(5)]
    low_factor = model._adjust_wind_speed_factor(low_wind_data)
    print(f"- 低風速（5ノット）での係数: {low_factor:.3f}")
    if low_factor <= model.wind_speed_factor:
        print("  結果: OK（基本係数より低い）")
    else:
        print("  結果: NG（基本係数より高い）")
    
    # 高風速データ（16ノット）
    high_wind_data = [{'wind_speed': 16} for _ in range(5)]
    high_factor = model._adjust_wind_speed_factor(high_wind_data)
    print(f"- 高風速（16ノット）での係数: {high_factor:.3f}")
    if high_factor >= model.wind_speed_factor:
        print("  結果: OK（基本係数より高い）")
    else:
        print("  結果: NG（基本係数より低い）")

def test_predict_future_wind():
    print("\n=== 将来の風状況予測テスト ===")
    
    # WindPropagationModelインスタンス作成
    model = WindPropagationModel()
    
    # 過去データ
    historical_data, base_time = create_standard_wind_data()
    
    # 将来位置と時間
    future_pos = (35.41, 139.72)
    future_time = base_time + timedelta(minutes=5)
    
    # 予測実行
    prediction = model.predict_future_wind(future_pos, future_time, historical_data)
    
    print("- 予測結果:")
    print(f"  風向: {prediction['wind_direction']:.2f}°")
    print(f"  風速: {prediction['wind_speed']:.2f} ノット")
    print(f"  信頼度: {prediction['confidence']:.2f}")
    
    # 結果構造の確認
    if 'wind_direction' in prediction and 'wind_speed' in prediction and 'confidence' in prediction:
        print("  結果構造: OK")
    else:
        print("  結果構造: NG（必要なキーが不足）")
    
    # 信頼度は0-1の間
    if 0 <= prediction['confidence'] <= 1:
        print("  信頼度範囲: OK")
    else:
        print("  信頼度範囲: NG")

def test_propagation_uncertainty():
    print("\n=== 距離・時間による不確実性増加テスト ===")
    
    # WindPropagationModelインスタンス作成
    model = WindPropagationModel()
    
    base_uncertainty = 0.5
    
    # 近距離・短時間の予測
    near_uncertainty = model._calculate_propagation_uncertainty(100, 60, base_uncertainty)
    
    # 遠距離・長時間の予測
    far_uncertainty = model._calculate_propagation_uncertainty(1000, 600, base_uncertainty)
    
    print(f"- 基本不確実性: {base_uncertainty:.2f}")
    print(f"- 近距離・短時間（100m, 60秒）での不確実性: {near_uncertainty:.2f}")
    print(f"- 遠距離・長時間（1000m, 600秒）での不確実性: {far_uncertainty:.2f}")
    
    # 遠距離・長時間の方が不確実性は高くなるはず
    if far_uncertainty > near_uncertainty:
        print("  結果: OK（距離・時間増加で不確実性増加）")
    else:
        print("  結果: NG（距離・時間増加で不確実性が増加していない）")

def main():
    print("風の移動モデル（WindPropagationModel）機能検証\n")
    
    # 各テスト実行
    test_estimate_propagation_vector()
    test_wind_speed_factor_adjustment()
    test_predict_future_wind()
    test_propagation_uncertainty()
    
    print("\n全テスト完了")

if __name__ == "__main__":
    main()
