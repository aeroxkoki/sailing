#!/usr/bin/env python3
"""
テストエラーのデバッグスクリプト
"""

import sys
import traceback
import os
import pytest

# カレントディレクトリを追加
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('sailing_data_processor'))

print("=== テストデバッグ開始 ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    # デバッグモードでテストを実行
    import subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '-v', '--tb=long', '-p', 'no:warnings', 'tests/test_decision_points_analyzer.py::TestDecisionPointsAnalyzer::test_initialization'],
        capture_output=True,
        text=True,
        cwd='/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer'
    )
    
    print("=== STDOUT ===")
    print(result.stdout)
    print("=== STDERR ===")
    print(result.stderr)
    print(f"Exit code: {result.returncode}")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    print("詳細なトレースバック:")
    traceback.print_exc()
