#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風の場の移動予測を考慮した戦略検出器のテスト

このスクリプトは StrategyDetectorWithPropagation クラスをテストし、
エラーがないかを検証します。
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import traceback
import numpy as np

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_propagation.log"),
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
        # 必要なモジュールのインポート
        from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
        from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
        
        logger.info("WindFieldFusionSystem のインスタンス化を試みます...")
        wind_fusion_system = WindFieldFusionSystem()
        logger.info("WindFieldFusionSystem のインスタンス化に成功しました")
        
        logger.info("StrategyDetectorWithPropagation のインスタンス化を試みます...")
        strategy_detector = StrategyDetectorWithPropagation(
            vmg_calculator=None,
            wind_fusion_system=wind_fusion_system
        )
        logger.info("StrategyDetectorWithPropagation のインスタンス化に成功しました")
        
        # テスト用のサンプルデータを作成
        logger.info("テスト用のサンプルデータを作成しています...")
        sample_course_data = create_sample_course_data()
        sample_wind_field = create_sample_wind_field()
        
        # propagation_configを確認
        logger.info(f"propagation_config: {strategy_detector.propagation_config}")
        
        # 風向シフト検出を実行（通常のメソッド）
        logger.info("detect_wind_shifts メソッドを実行します...")
        wind_shifts = strategy_detector.detect_wind_shifts(
            sample_course_data, sample_wind_field
        )
        logger.info(f"風向シフト検出に成功しました: {wind_shifts}")
        
        # 風向シフト検出を実行（移動予測を考慮したメソッド）
        logger.info("detect_wind_shifts_with_propagation メソッドを実行します...")
        wind_shifts_with_prop = strategy_detector.detect_wind_shifts_with_propagation(
            sample_course_data, sample_wind_field
        )
        logger.info(f"移動予測を考慮した風向シフト検出に成功しました: {wind_shifts_with_prop}")
        
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
        
        # _normalize_to_timestamp メソッドのテスト
        logger.info("_normalize_to_timestamp メソッドをテストします...")
        test_normalize_timestamps()
        
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

def test_normalize_timestamps():
    """_normalize_to_timestamp メソッドをテストする関数"""
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    
    detector = StrategyDetectorWithPropagation()
    
    # さまざまな入力をテスト
    test_inputs = [
        datetime.now(),
        datetime.now().timestamp(),
        timedelta(seconds=3600),
        "2025-04-20T12:34:56",
        "invalid_string",
        {"timestamp": 1650000000},
        {"other_key": "value"},
        None
    ]
    
    logger.info("_normalize_to_timestamp のテスト結果:")
    for input_value in test_inputs:
        try:
            result = detector._normalize_to_timestamp(input_value)
            logger.info(f"  入力: {input_value} => 結果: {result}")
        except Exception as e:
            logger.error(f"  入力: {input_value} => エラー: {e}")

if __name__ == "__main__":
    logger.info("StrategyDetectorWithPropagation テストを開始します...")
    main()
    logger.info("テスト完了")
