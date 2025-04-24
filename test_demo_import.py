# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - デモインポートテスト
"""

import sys
import os

# カレントディレクトリの確認
print("Current working directory:", os.getcwd())
print("Script location:", __file__)

# パスを追加
sys.path.insert(0, os.getcwd())
print("Python path:", sys.path)

# インポートを試行
try:
    import ui.demo.wind_flow_demo
    print("デモモジュールのインポートに成功しました")
except Exception as e:
    print("デモモジュールのインポートに失敗しました:", e)
    import traceback
    traceback.print_exc()

print("テスト完了")
