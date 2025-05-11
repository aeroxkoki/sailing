# -*- coding: utf-8 -*-
"""
sailing_data_processorパッケージの初期化テスト
"""

import unittest
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestPackageImport(unittest.TestCase):
    """パッケージインポートのテスト"""
    
    def test_import_sailing_data_processor(self):
        """sailing_data_processorパッケージのインポートテスト"""
        import sailing_data_processor
        self.assertIsNotNone(sailing_data_processor)
    
    def test_package_version(self):
        """パッケージバージョンのテスト"""
        import sailing_data_processor
        self.assertEqual(sailing_data_processor.__version__, '2.0.0')
    
    def test_import_core_modules(self):
        """コアモジュールのインポートテスト"""
        from sailing_data_processor import SailingDataProcessor
        from sailing_data_processor import WindEstimator
        
        self.assertIsNotNone(SailingDataProcessor)
        self.assertIsNotNone(WindEstimator)
    
    def test_import_optimizer_modules(self):
        """最適化モジュールのインポートテスト"""
        from sailing_data_processor import PerformanceOptimizer
        from sailing_data_processor import BoatDataFusionModel
        
        self.assertIsNotNone(PerformanceOptimizer)
        self.assertIsNotNone(BoatDataFusionModel)
    
    def test_import_wind_modules(self):
        """風関連モジュールのインポートテスト"""
        from sailing_data_processor import WindFieldInterpolator
        from sailing_data_processor import PredictionEvaluator
        
        self.assertIsNotNone(WindFieldInterpolator)
        self.assertIsNotNone(PredictionEvaluator)
    
    def test_import_data_models(self):
        """データモデルのインポートテスト"""
        from sailing_data_processor import (
            DataContainer, GPSDataContainer, 
            WindDataContainer, StrategyPointContainer
        )
        
        self.assertIsNotNone(DataContainer)
        self.assertIsNotNone(GPSDataContainer)
        self.assertIsNotNone(WindDataContainer)
        self.assertIsNotNone(StrategyPointContainer)
    
    def test_import_cache_functions(self):
        """キャッシュ機能のインポートテスト"""
        from sailing_data_processor import (
            cached, memoize, clear_cache, get_cache_stats
        )
        
        self.assertIsNotNone(cached)
        self.assertIsNotNone(memoize)
        self.assertIsNotNone(clear_cache)
        self.assertIsNotNone(get_cache_stats)
    
    def test_load_strategy_detector(self):
        """戦略検出器の遅延ロードテスト"""
        from sailing_data_processor import load_strategy_detector
        
        self.assertIsNotNone(load_strategy_detector)
        
        # 戦略検出器をロード
        detector = load_strategy_detector()
        # 戦略検出器またはNoneが返されることを確認
        self.assertTrue(detector is None or callable(detector))
    
    def test_all_exports(self):
        """__all__に定義されたエクスポートのテスト"""
        import sailing_data_processor
        
        for name in sailing_data_processor.__all__:
            self.assertTrue(hasattr(sailing_data_processor, name),
                          f"'{name}' is not available in sailing_data_processor")


if __name__ == '__main__':
    unittest.main()
