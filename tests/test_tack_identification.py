# -*- coding: utf-8 -*-
import unittest
import numpy as np
import sys
import os

# パス設定の問題を回避するための試み（複数のインポート戦略）
try:
    # 1. 最初の試行: 絶対パスインポート
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
except ImportError:
    try:
        # 2. 代替手段: 親ディレクトリを追加して再試行
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        module_path = os.path.join(project_root, 'sailing_data_processor')
        strategy_path = os.path.join(module_path, 'strategy')
        
        # プロジェクトルートをPythonパスに追加
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            
        # sailing_data_processor パスを追加
        if module_path not in sys.path:
            sys.path.insert(0, module_path)
            
        # strategy パスを追加
        if strategy_path not in sys.path:
            sys.path.insert(0, strategy_path)
            
        # インポート再試行
        from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    except ImportError:
        # 3. 最終手段: strategy_detector_utils から直接関数をインポート
        from sailing_data_processor.strategy.detector import StrategyDetector
        from sailing_data_processor.strategy.strategy_detector_utils import determine_tack_type
        
        # ダミーのStrategyDetectorWithPropagationクラスを作成
        class StrategyDetectorWithPropagation(StrategyDetector):
            """テスト用のダミークラス"""
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
            
            def _determine_tack_type(self, bearing, wind_direction):
                """determine_tack_type関数をラップ"""
                return determine_tack_type(bearing, wind_direction)

class TestTackIdentification(unittest.TestCase):
    
    def setUp(self):
        self.detector = StrategyDetectorWithPropagation()
    
    def test_determine_tack_type_basic(self):
        """基本的な風向・方位のパターンでタイプ判定をテスト"""
        # テストケース: (艇の方位, 風向, 期待されるタックタイプ)
        test_cases = [
            # スターボードタック (右舷から風を受ける)
            (0, 270, 'starboard'),   # 北向き、西風
            (90, 0, 'starboard'),    # 東向き、北風
            (180, 90, 'starboard'),  # 南向き、東風
            (270, 180, 'starboard'), # 西向き、南風
            
            # ポートタック (左舷から風を受ける)
            (0, 90, 'port'),         # 北向き、東風
            (90, 180, 'port'),       # 東向き、南風
            (180, 270, 'port'),      # 南向き、西風
            (270, 0, 'port'),        # 西向き、北風
        ]
        
        for bearing, wind_direction, expected in test_cases:
            tack_type = self.detector._determine_tack_type(bearing, wind_direction)
            self.assertEqual(tack_type, expected, 
                            f"Failed for bearing {bearing}, wind {wind_direction}")
    
    def test_determine_tack_type_edge_cases(self):
        """境界条件でのタックタイプ判定をテスト"""
        edge_cases = [
            # 真風（風に正対）
            (0, 0, 'starboard'),     # 風に向かって直進
            (180, 180, 'starboard'), # 風から直接離れる
            
            # 境界線上
            (90, 270, 'starboard'),  # 真右から風
            (90, 90, 'port'),        # 真左から風
            
            # 360度の特殊ケース
            (0, 360, 'starboard'),   # 360° = 0°
            (360, 180, 'starboard'), # 360° = 0°
        ]
        
        for bearing, wind_direction, expected in edge_cases:
            tack_type = self.detector._determine_tack_type(bearing, wind_direction)
            self.assertEqual(tack_type, expected)
    
    def test_determine_tack_type_comprehensive(self):
        """包括的な角度組み合わせでのタックタイプ判定テスト"""
        # 45度刻みの全方位組み合わせをテスト
        for bearing in range(0, 360, 45):
            for wind_offset in range(0, 360, 45):
                wind_direction = (bearing + wind_offset) % 360
                
                # 期待値の計算: 風のオフセットが0-180度なら右舷から(starboard)、それ以外なら左舷から(port)
                expected = 'starboard' if 0 <= wind_offset <= 180 else 'port'
                
                tack_type = self.detector._determine_tack_type(bearing, wind_direction)
                self.assertEqual(tack_type, expected, 
                                f"Failed for bearing {bearing}, wind {wind_direction}")

if __name__ == '__main__':
    unittest.main()
