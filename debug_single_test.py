#!/usr/bin/env python3
"""
個別テストのデバッグスクリプト
"""

import sys
import unittest
import os
import traceback

# カレントディレクトリを追加
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('sailing_data_processor'))
sys.path.insert(0, os.path.abspath('tests'))

print("=== 個別テストデバッグ開始 ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from tests.test_decision_points_analyzer import TestDecisionPointsAnalyzer
    
    suite = unittest.TestSuite()
    suite.addTest(TestDecisionPointsAnalyzer('test_initialization'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    print("詳細なトレースバック:")
    traceback.print_exc()
