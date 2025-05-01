# -*- coding: utf-8 -*-
# sailing_data_processor/__init__.py
"""
セーリング戦略分析システム - データ処理モジュール

GPSデータから風向風速を推定し、セーリングレースの戦略分析を支援するモジュール

モジュール依存関係:
core -> data_model
      -> wind_estimator
      -> performance_optimizer
      -> boat_data_fusion
      -> wind_field_interpolator
      -> wind_propagation_model -> wind_field_fusion_system
                                -> strategy
"""

# バージョン情報
__version__ = '2.0.0'

# ロギング設定
import logging
import os
import sys
import warnings

# 最初にパス情報をログに記録
logger = logging.getLogger(__name__)
logger.debug(f"sailing_data_processor path: {__file__}")
logger.debug(f"sailing_data_processor version: {__version__}")

# 後方互換性のために元のクラスをインポート可能にする
from .core import SailingDataProcessor

# 新しいクラスもインポート可能にする
from .wind_estimator import WindEstimator
from .performance_optimizer import PerformanceOptimizer
from .boat_data_fusion import BoatDataFusionModel
from .wind_field_interpolator import WindFieldInterpolator
try:
    from .wind_propagation_model import WindPropagationModel
    logger.debug("Successfully imported WindPropagationModel")
    # モジュールがインポートされたことを確認するためのインスタンス作成
    wind_prop_model = WindPropagationModel()
    logger.debug("Successfully created WindPropagationModel instance")
except ImportError as e:
    logger.error(f"Error importing WindPropagationModel: {e}")
    WindPropagationModel = None

try:
    from .wind_field_fusion_system import WindFieldFusionSystem
    logger.debug("Successfully imported WindFieldFusionSystem")
except ImportError as e:
    logger.error(f"Error importing WindFieldFusionSystem: {e}")
    WindFieldFusionSystem = None

from .prediction_evaluator import PredictionEvaluator

# 戦略検出器をグローバル変数として初期化
StrategyDetectorWithPropagation = None

def load_strategy_detector():
    """戦略検出器を遅延ロード
    
    Returns:
        StrategyDetectorWithPropagation: 戦略検出器クラス
    """
    global StrategyDetectorWithPropagation
    if StrategyDetectorWithPropagation is None:
        # デバッグ情報を出力
        print("===== 戦略検出器ロード開始 =====")
        print(f"現在のディレクトリ: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        print(f"sailing_data_processor path: {__file__}")
        
        try:
            # strategy サブパッケージのインポート
            from .strategy import StrategyDetectorWithPropagation as SDwP
            if SDwP is not None:
                StrategyDetectorWithPropagation = SDwP
                print(f"Successfully loaded strategy detector: {SDwP.__name__}")
            else:
                # SDwPがNoneの場合の処理
                print("SDwP was None from direct import, trying loader function")
                raise ImportError("SDwP was None")
        except ImportError as e:
            # strategy サブパッケージから直接インポートが失敗した場合
            try:
                # strategy パッケージの遅延ロード関数を使用
                print("Imported load_strategy_detector from root module")
                from .strategy import load_strategy_detector_with_propagation
                
                # 遅延ロード関数を呼び出す
                detector = load_strategy_detector_with_propagation()
                
                if detector is not None:
                    StrategyDetectorWithPropagation = detector
                    print(f"Successfully loaded StrategyDetectorWithPropagation via root loader: {detector.__name__}")
                else:
                    print("Strategy package loader returned None, creating fallback detector")
                    # フォールバックとして最小限の代替クラスを定義
                    from .strategy.detector import StrategyDetector
                    
                    class FallbackStrategyDetectorWithPropagation(StrategyDetector):
                        """フォールバック用の最小限実装"""
                        def __init__(self, vmg_calculator=None, wind_fusion_system=None):
                            super().__init__(vmg_calculator)
                            self.wind_fusion_system = wind_fusion_system
                            self.propagation_config = {
                                'wind_shift_prediction_horizon': 1800,
                                'prediction_time_step': 300,
                                'wind_shift_confidence_threshold': 0.7,
                                'min_propagation_distance': 1000,
                                'prediction_confidence_decay': 0.1,
                                'use_historical_data': True
                            }
                        
                        def detect_wind_shifts_with_propagation(self, course_data, wind_field):
                            """非常にシンプルな実装"""
                            print("FallbackStrategyDetectorWithPropagation.detect_wind_shifts_with_propagation called")
                            return []
                        
                        def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
                            """空実装"""
                            return []
                        
                        def _get_wind_at_position(self, lat, lon, time, wind_field):
                            """空実装"""
                            return None
                    
                    # クラス名を適切に設定
                    FallbackStrategyDetectorWithPropagation.__name__ = "StrategyDetectorWithPropagation"
                    StrategyDetectorWithPropagation = FallbackStrategyDetectorWithPropagation
                    print("Created fallback StrategyDetectorWithPropagation implementation")
            except ImportError as e2:
                warnings.warn(f"StrategyDetectorWithPropagation could not be imported: {e2}")
                print("Error creating fallback implementation, no strategy detector will be available")
                StrategyDetectorWithPropagation = None
        
        print("===== 戦略検出器ロード完了 =====")
    
    return StrategyDetectorWithPropagation

# データモデルのインポート
from .data_model import (
    DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer,
    cached, memoize, clear_cache, get_cache_stats
)

# デフォルトでエクスポートするシンボル
__all__ = [
    # 従来のクラス
    'SailingDataProcessor',
    'WindEstimator',
    'PerformanceOptimizer',
    'BoatDataFusionModel',
    'WindFieldInterpolator', 
    'WindPropagationModel',
    'WindFieldFusionSystem',
    'PredictionEvaluator',
    
    # 戦略検出
    'load_strategy_detector',
    
    # データモデル
    'DataContainer',
    'GPSDataContainer', 
    'WindDataContainer',
    'StrategyPointContainer',
    
    # キャッシュ機能
    'cached',
    'memoize',
    'clear_cache',
    'get_cache_stats'
]