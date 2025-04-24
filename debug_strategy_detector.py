#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StrategyDetector のデバッグテスト

このスクリプトは unhashable type: 'dict' エラーを再現するためのテストスクリプトです。
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import traceback

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_strategy_detector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.debug(f"Added project root to sys.path: {project_root}")

def main():
    """メイン関数"""
    try:
        # sailing_data_processor のモジュールをインポート
        from sailing_data_processor.strategy.detector import StrategyDetector
        
        logger.info("StrategyDetector のインスタンス化を試みます...")
        strategy_detector = StrategyDetector()
        
        logger.info("StrategyDetector のインスタンス化に成功しました")
        
        # テスト用のサンプルデータを作成
        logger.info("テスト用のサンプルデータを作成しています...")
        sample_course_data = create_sample_course_data()
        sample_wind_field = create_sample_wind_field()
        
        # 風向シフト検出を実行
        logger.info("風向シフト検出を実行します...")
        wind_shifts = strategy_detector.detect_wind_shifts(
            sample_course_data, sample_wind_field
        )
        
        logger.info(f"風向シフト検出に成功しました: {wind_shifts}")
        
        # unhashable type: 'dict' エラーを起こす可能性のある操作
        logger.info("dictをキーにした操作を試みます...")
        try:
            test_dict = {}
            test_dict[sample_course_data] = "Test"  # これでエラーになるはず
            logger.error("dictをキーにする操作が成功しました（通常はエラーになります）")
        except TypeError as e:
            logger.info(f"予想通りエラーが発生しました: {e}")
        
        # その他のメソッドも試す
        logger.info("detect_optimal_tacks メソッドを試みます...")
        tacks = strategy_detector.detect_optimal_tacks(
            sample_course_data, sample_wind_field
        )
        logger.info(f"detect_optimal_tacks の結果: {tacks}")
        
        logger.info("detect_laylines メソッドを試みます...")
        laylines = strategy_detector.detect_laylines(
            sample_course_data, sample_wind_field
        )
        logger.info(f"detect_laylines の結果: {laylines}")
        
    except ImportError as e:
        logger.error(f"インポートエラー: {e}")
        logger.error(f"現在のシステムパス: {sys.path}")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        logger.error(traceback.format_exc())

def create_sample_course_data():
    """テスト用のコースデータを作成"""
    start_time = datetime.now()
    
    course_data = {
        'start_time': start_time,
        'legs': [
            {
                'leg_number': 1,
                'is_upwind': True,
                'start_waypoint': {
                    'lat': 35.45,
                    'lon': 139.65,
                    'name': 'Start'
                },
                'end_waypoint': {
                    'lat': 35.46,
                    'lon': 139.66,
                    'name': 'Mark 1'
                },
                'path': {
                    'path_points': [
                        {
                            'lat': 35.45 + i * 0.001,
                            'lon': 139.65 + i * 0.001,
                            'time': start_time + timedelta(minutes=i*2),
                            'course': 45,
                            'timestamp': (start_time + timedelta(minutes=i*2)).timestamp()
                        } for i in range(10)
                    ]
                }
            }
        ]
    }
    
    return course_data

def create_sample_wind_field():
    """テスト用の風の場データを作成"""
    import numpy as np
    
    # グリッドの生成
    grid_size = 5
    lat_grid = np.linspace(35.45, 35.47, grid_size)
    lon_grid = np.linspace(139.65, 139.67, grid_size)
    grid_lats, grid_lons = np.meshgrid(lat_grid, lon_grid)
    
    # 風向・風速・信頼度のマトリックス生成
    wind_direction = np.ones_like(grid_lats) * 90  # 一定の風向
    wind_speed = np.ones_like(grid_lats) * 12      # 一定の風速
    confidence = np.ones_like(grid_lats) * 0.8     # 一定の信頼度
    
    # 風の場データ
    wind_field = {
        'lat_grid': grid_lats,
        'lon_grid': grid_lons,
        'wind_direction': wind_direction,
        'wind_speed': wind_speed,
        'confidence': confidence,
        'time': datetime.now()
    }
    
    return wind_field

if __name__ == "__main__":
    logger.info("StrategyDetector デバッグテストを開始します...")
    main()
    logger.info("テスト完了")
