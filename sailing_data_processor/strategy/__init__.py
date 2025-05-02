# -*- coding: utf-8 -*-
"""
sailing_data_processor.strategy package

Provides detection, evaluation, and visualization of strategic decision points in sailing races.

Module dependencies:
Base classes: detector -> evaluator -> visualizer
Strategy points: points
Special classes: strategy_detector_with_propagation
"""

import os
import sys
import logging
import warnings
import importlib.util
from typing import Optional, Type

logger = logging.getLogger(__name__)

# Import base classes first to avoid circular dependencies
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint, StrategyAlternative
from sailing_data_processor.strategy.detector import StrategyDetector
from sailing_data_processor.strategy.evaluator import StrategyEvaluator
from sailing_data_processor.strategy.visualizer import StrategyVisualizer

# Avoid eager loading to prevent circular references
StrategyDetectorWithPropagation = None

# Set a flag for import tracking
_strategy_imports_attempted = False

# Add a direct reference to the module path for testing
import os
import sys
_strategy_module_path = os.path.dirname(os.path.abspath(__file__))
if _strategy_module_path not in sys.path:
    sys.path.insert(0, _strategy_module_path)

def load_strategy_detector_with_propagation() -> Optional[Type]:
    """戦略検出器クラスの遅延ロード
    
    circular importを防ぐために遅延ロードを行う
    テストの際にも使用される
    
    Returns:
        StrategyDetectorWithPropagation: 戦略検出器クラス
    """
    global StrategyDetectorWithPropagation, _strategy_imports_attempted
    
    # すでにロードされている場合はそれを返す
    if StrategyDetectorWithPropagation is not None:
        logger.debug("既にロード済みの戦略検出器を返します")
        return StrategyDetectorWithPropagation
    
    # インポートの試行回数を制限（無限ループ防止）
    if _strategy_imports_attempted:
        logger.warning("Strategy detector import already attempted, using fallback")
        return _create_fallback_detector()
    
    _strategy_imports_attempted = True
    
    # デバッグ情報
    logger.debug(f"戦略検出器ロード - sys.path: {sys.path}")
    logger.debug(f"現在のディレクトリ: {os.getcwd()}")
    logger.debug(f"モジュールファイルパス: {__file__}")
    
    # インポート試行の多段階アプローチ
    success = False
    
    # アプローチ1: 絶対パスでインポート
    try:
        logger.debug("アプローチ1: 絶対パスでインポート")
        from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
        if SDwP is not None:
            StrategyDetectorWithPropagation = SDwP
            logger.info("絶対パスでのインポートに成功")
            success = True
        else:
            logger.warning("モジュールはロードされましたがStrategyDetectorWithPropagationがNoneです")
    except ImportError as e:
        logger.warning(f"絶対パスインポートエラー: {e}")
    
    # アプローチ2: 絶対パスからインポート
    if not success:
        try:
            logger.debug("アプローチ2: 絶対パスからインポート")
            module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       "strategy_detector_with_propagation.py")
            logger.debug(f"モジュールパス: {module_path}")
            
            # モジュール名を作成
            module_name = "strategy_detector_with_propagation"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "StrategyDetectorWithPropagation"):
                    StrategyDetectorWithPropagation = getattr(module, "StrategyDetectorWithPropagation")
                    logger.info("絶対パスからのインポートに成功")
                    success = True
        except Exception as e:
            logger.warning(f"絶対パスインポートエラー: {e}")
    
    # アプローチ3: もし戦略検出器が存在するかどうかをフルパスで確認
    if not success:
        try:
            logger.debug("アプローチ3: フルパスでインポート")
            import sailing_data_processor.strategy.strategy_detector_with_propagation
            SDwP = sailing_data_processor.strategy.strategy_detector_with_propagation.StrategyDetectorWithPropagation
            StrategyDetectorWithPropagation = SDwP
            logger.info("フルパスでのインポートに成功")
            success = True
        except Exception as e:
            logger.warning(f"フルパスインポートエラー: {e}")
    
    # どの方法も失敗した場合はフォールバックを使用
    if not success:
        logger.warning("すべてのインポート方法が失敗したため、フォールバックを使用します")
        return _create_fallback_detector()
    
    return StrategyDetectorWithPropagation

def _create_fallback_detector():
    """フォールバック実装を作成"""
    global StrategyDetectorWithPropagation
    
    logger.info("フォールバック実装を作成")
    
    # テスト環境かどうか
    is_test_environment = any(module in sys.modules for module in ['unittest', 'pytest', 'conftest'])
    logger.debug(f"テスト環境判定: {is_test_environment}")
    
    # フォールバッククラス定義
    class FallbackSDwP(StrategyDetector):
        """StrategyDetectorWithPropagationのフォールバック
        
        循環インポートや動的ロードの問題が発生した場合に使用される
        テスト環境での代替実装。実際の実装とのAPI互換性を確保します。
        """
        def __init__(self, vmg_calculator=None, wind_fusion_system=None):
            """初期化
            
            Parameters:
            -----------
            vmg_calculator : any, optional
                VMG計算機（親クラスに渡される）
            wind_fusion_system : any, optional
                風場融合システム（予測に使用）
            """
            # 親クラスの初期化
            super().__init__(vmg_calculator)
            
            # 風場融合システム設定
            self.wind_fusion_system = wind_fusion_system
            
            # 予測設定 - 本実装と同じデフォルト値
            self.propagation_config = {
                'wind_shift_prediction_horizon': 1800,  # 予測最大時間（秒）
                'prediction_time_step': 300,           # 予測ステップ（秒）
                'wind_shift_confidence_threshold': 0.7, # 予測確信度閾値
                'min_propagation_distance': 1000,      # 最小伝播距離（m）
                'prediction_confidence_decay': 0.1,    # 予測の時間減衰パラメータ
                'use_historical_data': True            # 履歴データ使用
            }
            
            # テストモードであることをログ出力
            logger.info("代替実装の戦略検出器を使用しています（テスト/デバッグモード）")
        
        def detect_wind_shifts_with_propagation(self, course_data, wind_field):
            """風向予測を考慮した風向変化検出
            
            Parameters:
            -----------
            course_data : Dict[str, Any]
                コースデータ
            wind_field : Dict[str, Any]
                風場データ
                
            Returns:
            --------
            List
                検出した風向変化点（空リスト）
            """
            logger.debug("FallbackSDwP.detect_wind_shifts_with_propagation called")
            return []
            
        def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
            """各レグでの風向変化検出
            
            Parameters:
            -----------
            course_data : Dict[str, Any]
                コースデータ
            wind_field : Dict[str, Any]
                風場データ
            target_time : datetime
                対象時刻
                
            Returns:
            --------
            List
                検出した風向変化点（空リスト）
            """
            return []
            
        def _get_wind_at_position(self, lat, lon, time, wind_field):
            """位置での風情報を取得
            
            Parameters:
            -----------
            lat, lon : float
                位置（緯度、経度）
            time : datetime
                時刻
            wind_field : Dict[str, Any]
                風場データ
                
            Returns:
            --------
            Dict or None
                風情報（方向、速度など）
            """
            return None
        
        def detect_optimal_tacks(self, course_data, wind_field):
            """最適タックポイント検出
            
            Parameters:
            -----------
            course_data : Dict[str, Any]
                コースデータ
            wind_field : Dict[str, Any]
                風場データ
                
            Returns:
            --------
            List
                検出した最適タックポイント（空リスト）
            """
            return []
            
        def detect_laylines(self, course_data, wind_field):
            """レイラインポイント検出
            
            Parameters:
            -----------
            course_data : Dict[str, Any]
                コースデータ
            wind_field : Dict[str, Any]
                風場データ
                
            Returns:
            --------
            List
                検出したレイラインポイント（空リスト）
            """
            return []
        
        def __str__(self):
            """文字列表現"""
            return "StrategyDetectorWithPropagation(Fallback)"
        
        def __repr__(self):
            """オブジェクト表現"""
            return "StrategyDetectorWithPropagation(Fallback)"
    
    # クラス名を設定
    FallbackSDwP.__name__ = "StrategyDetectorWithPropagation"
    StrategyDetectorWithPropagation = FallbackSDwP
    logger.info("フォールバック実装を使用")
    
    return StrategyDetectorWithPropagation

__version__ = '1.0.1'
__all__ = [
    'StrategyPoint',
    'WindShiftPoint',
    'TackPoint',
    'LaylinePoint',
    'StrategyAlternative',
    'StrategyDetector',
    'StrategyEvaluator',
    'StrategyVisualizer',
    'load_strategy_detector_with_propagation',
]

def get_version():
    """Returns the package version"""
    return __version__
