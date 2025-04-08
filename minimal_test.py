#!/usr/bin/env python3
"""
最小限のテストコード
"""

import sys
import unittest
from datetime import datetime, timedelta

# テスト対象のモジュールをインポート
try:
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

class MinimalTest(unittest.TestCase):
    """最小限のテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        self.fusion_system = WindFieldFusionSystem()
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.fusion_system)
        self.assertEqual(self.fusion_system.wind_data_points, [])
        self.assertIsNone(self.fusion_system.current_wind_field)
    
    def test_haversine_distance(self):
        """Haversine距離計算のテスト"""
        distance = self.fusion_system._haversine_distance(35.45, 139.65, 35.46, 139.66)
        self.assertGreater(distance, 1400)
        self.assertLess(distance, 1500)

def run_tests():
    """テストを実行"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(MinimalTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    print("最小限のテストを実行します...")
    success = run_tests()
    print(f"テスト結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)
