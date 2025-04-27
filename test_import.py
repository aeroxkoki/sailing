#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本インポートテスト
このスクリプトはセーリング戦略分析システムの基本ライブラリが
正しくインポートできることを確認するためのものです。
"""

import sys
import os

print("--- セーリング戦略分析システム 基本インポートテスト ---")
print(f"Python バージョン: {sys.version}")
print(f"実行パス: {sys.executable}")
print(f"カレントディレクトリ: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")
print("---")

# 基本インポートテスト
try:
    print("sailing_data_processor モジュールのインポートを試みます...")
    import sailing_data_processor
    print(f"sailing_data_processor バージョン: {sailing_data_processor.__version__ if hasattr(sailing_data_processor, '__version__') else '不明'}")
    print("インポート成功!")

    # サブモジュールのインポートテスト
    print("\nサブモジュールのインポートテスト:")
    
    # 存在するサブモジュール名のリストを取得して表示
    submodules = [
        "sailing_data_processor.importers",
        "sailing_data_processor.strategy",
        "sailing_data_processor.analysis",
        "sailing_data_processor.visualization",
        "sailing_data_processor.utilities"
    ]
    
    for module in submodules:
        try:
            exec(f"import {module}")
            print(f"✓ {module} インポート成功")
        except ImportError as e:
            print(f"✗ {module} インポート失敗: {str(e)}")
    
    print("\nすべての基本インポートテストが完了しました。")
    sys.exit(0)  # 成功
except Exception as e:
    print(f"エラー: {str(e)}")
    print(f"エラータイプ: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)  # 失敗
