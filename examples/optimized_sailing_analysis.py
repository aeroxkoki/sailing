# -*- coding: utf-8 -*-
#\!/usr/bin/env python3
"""
セーリング戦略分析システム - 最適化データモデルを使用するサンプル

このサンプルスクリプトは、最適化されたデータモデルとアクセスパターンを使って
GPS位置データから風向風速を推定し、戦略ポイントを検出する方法を示します。
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import logging
import time

# モジュールのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# セーリング戦略分析システムのインポート
from sailing_data_processor.data_model import (
    GPSDataContainer, WindDataContainer, StrategyPointContainer,
    cached, clear_cache, get_cache_stats
)
from sailing_data_processor.data_model.utils import (
    preprocess_gps_data, calculate_course_and_speed, extract_time_window
)
from sailing_data_processor.optimized.wind_estimator import OptimizedWindEstimator
from sailing_data_processor.optimized.strategy_detector import OptimizedStrategyDetector

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_gps_data(file_path):
    """
    GPSデータを読み込み、前処理してGPSDataContainerを返す
    """
    logger.info(f"GPSデータを読み込み中: {file_path}")
    
    try:
        # ファイル拡張子に応じて読み込み方法を変更
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            logger.error(f"サポートされていないファイル形式: {file_ext}")
            return None
        
        # 前処理
        logger.info("GPSデータを前処理中...")
        gps_container = preprocess_gps_data(df, clean_outliers=True)
        
        # コースと速度を計算
        logger.info("コースと速度を計算中...")
        gps_container = calculate_course_and_speed(gps_container, smooth=True)
        
        logger.info(f"GPSデータ読み込み完了: {len(gps_container.data)} ポイント")
        return gps_container
    
    except Exception as e:
        logger.error(f"GPSデータ読み込みエラー: {e}")
        return None

def create_dummy_gps_data(num_points=100):
    """
    テスト用のダミーGPSデータを作成
    """
    logger.info(f"ダミーGPSデータを作成中: {num_points} ポイント")
    
    # ベース位置（東京湾）
    base_lat = 35.6
    base_lon = 139.8
    
    # 時間範囲
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    timestamps = pd.date_range(start=start_time, end=end_time, periods=num_points)
    
    # 8の字を描くパターン
    t = np.linspace(0, 4*np.pi, num_points)
    lats = base_lat + 0.01 * np.sin(t)
    lons = base_lon + 0.005 * np.sin(2*t)
    
    # 風向に対してアップウィンド・ダウンウィンドを模擬（風向は南西、225度と仮定）
    # 艇の方位（北が0度、時計回り）
    courses = np.zeros(num_points)
    for i in range(num_points):
        if i < num_points / 4:
            # 風上への移動（風向の逆、45度）
            courses[i] = 45 + 5 * np.sin(t[i])
        elif i < num_points / 2:
            # リーチング（風向と直角、135度）
            courses[i] = 135 + 5 * np.sin(t[i])
        elif i < 3 * num_points / 4:
            # 風下への移動（風向に近い、225度）
            courses[i] = 225 + 5 * np.sin(t[i])
        else:
            # 再びリーチング（315度）
            courses[i] = 315 + 5 * np.sin(t[i])
    
    # 速度（ノット）- 風上は遅く、風下は速い
    speeds = np.zeros(num_points)
    for i in range(num_points):
        if i < num_points / 4 or i >= 3 * num_points / 4:
            # 風上・リーチングは4〜6ノット
            speeds[i] = 4 + 2 * np.sin(t[i])
        else:
            # 風下は5〜8ノット
            speeds[i] = 5 + 3 * np.sin(t[i])
    
    # DataFrameの作成
    df = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': lats,
        'longitude': lons,
        'course': courses,
        'speed': speeds
    })
    
    # GPSDataContainerに変換
    gps_container = GPSDataContainer(df)
    
    logger.info("ダミーGPSデータ作成完了")
    return gps_container

def analyze_sailing_data(gps_container, boat_type="laser"):
    """
    GPSデータを解析し、風向風速と戦略ポイントを検出
    
    Parameters
    ----------
    gps_container : GPSDataContainer
        解析するGPSデータ
    boat_type : str, optional
        艇種（デフォルト: "laser"）
    
    Returns
    -------
    tuple
        (WindDataContainer, List[StrategyPointContainer])
    """
    logger.info(f"セーリングデータの解析を開始: 艇種={boat_type}")
    
    # 最適化されたWindEstimatorの作成
    wind_estimator = OptimizedWindEstimator(boat_type)
    
    # 風向風速の推定
    start_time = time.time()
    logger.info("風向風速を推定中...")
    wind_data = wind_estimator.estimate_wind_from_gps_data(gps_container)
    logger.info(f"風向風速の推定完了: {wind_data.direction:.1f}度, {wind_data.speed:.1f}ノット, " +
               f"信頼度={wind_data.confidence:.2f}, 方法={wind_data.get_metadata('estimation_method')}")
    logger.info(f"風向風速の推定時間: {time.time() - start_time:.2f}秒")
    
    # 単純な風の場の作成（実際のアプリではより高度な風の場を使用）
    # 今回は推定した風を全域に適用
    wind_field = create_simple_wind_field(wind_data, gps_container)
    
    # 最適化されたStrategyDetectorの作成
    strategy_detector = OptimizedStrategyDetector()
    
    # 戦略ポイントの検出
    start_time = time.time()
    logger.info("戦略ポイントを検出中...")
    strategy_points = strategy_detector.detect_wind_shifts_optimized(gps_container.data, wind_field)
    logger.info(f"風向シフトポイントの検出完了: {len(strategy_points)}個のポイント")
    logger.info(f"戦略ポイント検出時間: {time.time() - start_time:.2f}秒")
    
    # キャッシュ統計の表示
    cache_stats = get_cache_stats()
    logger.info(f"キャッシュ統計: {cache_stats}")
    
    return wind_data, strategy_points

def create_simple_wind_field(wind_data, gps_container):
    """
    単純な風の場を作成
    """
    # GPSデータの範囲を取得
    df = gps_container.data
    min_lat = df['latitude'].min()
    max_lat = df['latitude'].max()
    min_lon = df['longitude'].min()
    max_lon = df['longitude'].max()
    
    # 少し余裕を持たせる
    lat_margin = (max_lat - min_lat) * 0.1
    lon_margin = (max_lon - min_lon) * 0.1
    min_lat -= lat_margin
    max_lat += lat_margin
    min_lon -= lon_margin
    max_lon += lon_margin
    
    # グリッドの作成
    grid_size = 5
    lat_grid, lon_grid = np.meshgrid(
        np.linspace(min_lat, max_lat, grid_size),
        np.linspace(min_lon, max_lon, grid_size),
        indexing='ij'
    )
    
    # 風向風速はどこでも同じと仮定
    wind_direction = np.full_like(lat_grid, wind_data.direction)
    wind_speed = np.full_like(lat_grid, wind_data.speed)
    
    # 風の場辞書の作成
    wind_field = {
        "lat_grid": lat_grid,
        "lon_grid": lon_grid,
        "wind_direction": wind_direction,
        "wind_speed": wind_speed,
        "confidence": np.full_like(lat_grid, wind_data.confidence),
        "timestamp": wind_data.timestamp
    }
    
    return wind_field

def print_results(wind_data, strategy_points):
    """
    解析結果を表示
    """
    print("\n" + "="*50)
    print("セーリング戦略分析結果")
    print("="*50)
    
    print("\n【風向風速推定】")
    print(f"風向: {wind_data.direction:.1f}度 ({get_wind_direction_name(wind_data.direction)})")
    print(f"風速: {wind_data.speed:.1f}ノット")
    print(f"信頼度: {wind_data.confidence:.2f}")
    print(f"推定方法: {wind_data.get_metadata('estimation_method')}")
    print(f"推定時刻: {wind_data.timestamp}")
    
    print("\n【検出された戦略ポイント】")
    if strategy_points:
        for i, point in enumerate(strategy_points, 1):
            details = point.data.get('details', {})
            print(f"\nポイント {i}:")
            print(f"  タイプ: {point.point_type}")
            print(f"  位置: 緯度={point.latitude:.6f}, 経度={point.longitude:.6f}")
            print(f"  時刻: {point.timestamp}")
            print(f"  重要度: {point.importance:.2f}")
            
            if 'shift_angle' in details:
                print(f"  シフト角度: {details['shift_angle']:.1f}度")
                print(f"  シフトタイプ: {details['shift_type']}")
                print(f"  現在風向: {details['current_direction']:.1f}度 → " +
                      f"新風向: {details['new_direction']:.1f}度")
                print(f"  予測時刻: {details['forecast_time']}")
    else:
        print("  検出されたポイントはありません。")
    
    print("\n" + "="*50 + "\n")

def get_wind_direction_name(direction):
    """
    風向を方位名に変換
    """
    # 方位名のリスト（16方位）
    directions = [
        "北", "北北東", "北東", "東北東", 
        "東", "東南東", "南東", "南南東",
        "南", "南南西", "南西", "西南西", 
        "西", "西北西", "北西", "北北西"
    ]
    
    # 度数を16方位に変換
    idx = round(direction / 22.5) % 16
    
    return directions[idx] + "の風"

def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description='セーリング戦略分析システム')
    parser.add_argument('-f', '--file', help='GPSデータファイルのパス')
    parser.add_argument('-b', '--boat', default='laser', 
                        help='艇種（デフォルト: laser）')
    parser.add_argument('-d', '--dummy', action='store_true',
                        help='ダミーデータを使用（ファイルが指定されていない場合）')
    parser.add_argument('-n', '--num_points', type=int, default=100,
                        help='ダミーデータのポイント数（デフォルト: 100）')
    
    args = parser.parse_args()
    
    # GPSデータの読み込み
    if args.file:
        gps_container = load_gps_data(args.file)
        if gps_container is None:
            return
    elif args.dummy:
        gps_container = create_dummy_gps_data(args.num_points)
    else:
        logger.error("GPSデータファイルが指定されていないか、--dummyが指定されていません。")
        parser.print_help()
        return
    
    # GPSデータの解析
    wind_data, strategy_points = analyze_sailing_data(gps_container, args.boat)
    
    # 結果の表示
    print_results(wind_data, strategy_points)

if __name__ == "__main__":
    main()
