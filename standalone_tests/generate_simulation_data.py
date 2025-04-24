#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - シミュレーションデータ生成ツール

このスクリプトはテストと検証のために、
異なる風の移動パターンを持つシミュレーションデータを生成します。
実際のGPSデータのような構造を持つデータを作成し、CSVファイルとして保存します。
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import argparse
import json
import math

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def generate_wind_field_data(pattern='standard', duration_minutes=60, interval_seconds=10):
    """
    風の場のシミュレーションデータを生成
    
    Parameters:
    -----------
    pattern : str
        風の移動パターン ('standard', 'complex', 'shifting', 'variable_speed')
    duration_minutes : int
        シミュレーション期間（分）
    interval_seconds : int
        データポイント間の時間間隔（秒）
    
    Returns:
    --------
    pandas.DataFrame
        シミュレーションデータ
    dict
        メタデータ（風の場の真値など）
    """
    # 基本設定
    start_time = datetime.now()
    num_points = int(duration_minutes * 60 / interval_seconds)
    
    # 基本位置情報（東京湾エリア）
    base_lat, base_lon = 35.45, 139.65
    
    # 風の初期設定
    if pattern == 'standard':
        # 標準的な風のパターン - 徐々に右に変化
        initial_wind_direction = 90.0  # 東から
        initial_wind_speed = 12.0     # 12ノット
        direction_change_rate = 10.0 / duration_minutes  # 1分あたり約0.17度右に変化
        speed_change_rate = 0.0      # 風速一定
        
    elif pattern == 'complex':
        # 複雑な風のパターン - サイン波状に変化
        initial_wind_direction = 90.0
        initial_wind_speed = 12.0
        direction_change_rate = 0.0  # サイン波で上書きされる
        speed_change_rate = 0.0      # サイン波で上書きされる
        
    elif pattern == 'shifting':
        # 大きな風向シフトを含むパターン
        initial_wind_direction = 90.0
        initial_wind_speed = 12.0
        direction_change_rate = 0.0  # 後でステップ関数で上書き
        speed_change_rate = 0.0
        
    elif pattern == 'variable_speed':
        # 風速変化を伴うパターン
        initial_wind_direction = 90.0
        initial_wind_speed = 8.0
        direction_change_rate = 5.0 / duration_minutes
        speed_change_rate = 8.0 / duration_minutes  # 徐々に風速が上がる
        
    else:
        raise ValueError(f"不明な風パターン: {pattern}")
    
    # データフレーム用のリストを初期化
    data = []
    
    # 実際の風の場（真値）の保存用
    true_wind_field = {
        'times': [],
        'wind_directions': [],
        'wind_speeds': []
    }
    
    # データポイントを生成
    for i in range(num_points):
        # 時間
        timestamp = start_time + timedelta(seconds=i * interval_seconds)
        
        # 風向風速の計算
        if pattern == 'standard':
            # 標準的なパターン - 線形変化
            wind_direction = (initial_wind_direction + i * interval_seconds * direction_change_rate / 60) % 360
            wind_speed = initial_wind_speed + i * interval_seconds * speed_change_rate / 60
            
        elif pattern == 'complex':
            # 複雑なパターン - サイン波による変化
            time_factor = i * interval_seconds / (duration_minutes * 60)  # 0から1の範囲に正規化
            wind_direction = (initial_wind_direction + 15 * math.sin(time_factor * 2 * math.pi * 3)) % 360  # 3サイクル
            wind_speed = initial_wind_speed + 3 * math.sin(time_factor * 2 * math.pi * 2)  # 2サイクル
            
        elif pattern == 'shifting':
            # 急激な風向シフトを含むパターン
            wind_direction = initial_wind_direction
            wind_speed = initial_wind_speed
            
            # 中間点で30度の風向シフト
            if i >= num_points // 3 and i < num_points * 2 // 3:
                wind_direction = (initial_wind_direction + 30) % 360
            # 2/3以降で別の30度シフト
            elif i >= num_points * 2 // 3:
                wind_direction = (initial_wind_direction + 60) % 360
                
        elif pattern == 'variable_speed':
            # 風速変化を伴うパターン
            wind_direction = (initial_wind_direction + i * interval_seconds * direction_change_rate / 60) % 360
            
            # 風速は増加するが、ランダムな変動を含む
            base_wind_speed = initial_wind_speed + i * interval_seconds * speed_change_rate / 60
            wind_speed = base_wind_speed + np.random.normal(0, 1)  # 平均0、標準偏差1のノイズ
            wind_speed = max(0, wind_speed)  # 負の風速を防止
        
        # 計算された風向風速を記録
        true_wind_field['times'].append(timestamp.isoformat())
        true_wind_field['wind_directions'].append(wind_direction)
        true_wind_field['wind_speeds'].append(wind_speed)
        
        # セーリング艇の動きをシミュレート（基本的なモデル）
        # 実際には、風に対する艇の応答はもっと複雑ですが、ここでは単純化
        
        # 風に対する艇の相対角度（風上へのタック）
        boat_relative_angle = 45.0  # 45度のクローズホールド
        
        # 艇の移動方向（コース）- 風向から計算
        # 風向に対して右45度または左45度
        tack_side = 1 if i % 2 == 0 else -1  # 交互にタックを変更
        course = (wind_direction + boat_relative_angle * tack_side) % 360
        
        # 艇の速度 - 風速と相対角度から計算（単純な近似）
        # 風上では風速の約40%、風下では風速の約60%の速度
        is_upwind = abs(boat_relative_angle) < 90
        speed_factor = 0.4 if is_upwind else 0.6
        speed = wind_speed * speed_factor
        
        # 位置の更新（単純化）
        # 実際にはもっと正確な計算が必要ですが、ここでは概算
        course_rad = math.radians(course)
        
        # 速度をm/sに変換（1ノット = 0.51444 m/s）
        speed_ms = speed * 0.51444
        
        # 1ステップでの緯度経度の変化量
        # 非常に単純化した計算。実際には地球の曲率考慮が必要
        dlat = speed_ms * math.cos(course_rad) * interval_seconds * 9e-6  # 概算係数
        dlon = speed_ms * math.sin(course_rad) * interval_seconds * 9e-6  # 概算係数
        
        latitude = base_lat + dlat * i
        longitude = base_lon + dlon * i
        
        # 計測風向にノイズを追加（実際のセンサーのように）
        measured_wind_direction = wind_direction + np.random.normal(0, 2)  # 2度の標準偏差
        measured_wind_speed = wind_speed + np.random.normal(0, 0.5)        # 0.5ノットの標準偏差
        
        # データポイントを追加
        data.append({
            'timestamp': timestamp,
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed,
            'course': course,
            'wind_direction': measured_wind_direction,
            'wind_speed_knots': measured_wind_speed
        })
    
    # データフレームに変換
    df = pd.DataFrame(data)
    
    # メタデータの作成
    metadata = {
        'pattern': pattern,
        'duration_minutes': duration_minutes,
        'interval_seconds': interval_seconds,
        'initial_wind_direction': initial_wind_direction,
        'initial_wind_speed': initial_wind_speed,
        'true_wind_field': true_wind_field
    }
    
    return df, metadata

def save_simulation_data(df, metadata, output_dir='simulation_data', pattern_name='standard'):
    """
    シミュレーションデータを保存
    
    Parameters:
    -----------
    df : pandas.DataFrame
        シミュレーションデータ
    metadata : dict
        メタデータ
    output_dir : str
        出力ディレクトリ
    pattern_name : str
        パターン名（ファイル名の一部に使用）
    """
    # 出力ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 現在のタイムスタンプ
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # ファイル名
    csv_filename = f"{pattern_name}_simulation_{timestamp}.csv"
    metadata_filename = f"{pattern_name}_metadata_{timestamp}.json"
    
    # ファイルパス
    csv_path = os.path.join(output_dir, csv_filename)
    metadata_path = os.path.join(output_dir, metadata_filename)
    
    # CSV形式で保存
    df.to_csv(csv_path, index=False)
    
    # メタデータをJSON形式で保存
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"シミュレーションデータを保存しました: {csv_path}")
    print(f"メタデータを保存しました: {metadata_path}")

def main():
    """メイン実行関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='セーリング戦略分析システム - シミュレーションデータ生成ツール')
    parser.add_argument('--pattern', type=str, default='standard', 
                       choices=['standard', 'complex', 'shifting', 'variable_speed'],
                       help='風の移動パターン')
    parser.add_argument('--duration', type=int, default=60,
                       help='シミュレーション期間（分）')
    parser.add_argument('--interval', type=int, default=10,
                       help='データポイント間の時間間隔（秒）')
    parser.add_argument('--output', type=str, default='simulation_data',
                       help='出力ディレクトリ')
    
    args = parser.parse_args()
    
    print(f"シミュレーションデータを生成します: パターン={args.pattern}, 期間={args.duration}分")
    
    # シミュレーションデータの生成
    df, metadata = generate_wind_field_data(
        pattern=args.pattern,
        duration_minutes=args.duration,
        interval_seconds=args.interval
    )
    
    # データの保存
    save_simulation_data(df, metadata, args.output, args.pattern)
    
    print("シミュレーションデータの生成が完了しました")

if __name__ == "__main__":
    main()
