#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システムのSailingDataAnalyzerテスト
"""

import os
import sys
import traceback

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")

# テスト対象のモジュールを個別にインポート
try:
    print("Importing core_analysis.py ...")
    from sailing_data_processor.core_analysis import SailingDataAnalyzer
    print("Successfully imported SailingDataAnalyzer")
    
    print("\nTesting SailingDataAnalyzer instantiation...")
    analyzer = SailingDataAnalyzer()
    print("Successfully created SailingDataAnalyzer instance")
    print(f"Attributes: {dir(analyzer)[:10]}...")
    
    print("\nImporting core.py ...")
    from sailing_data_processor.core import SailingDataProcessor
    print("Successfully imported SailingDataProcessor")
    
    print("\nTesting SailingDataProcessor instantiation...")
    processor = SailingDataProcessor()
    print("Successfully created SailingDataProcessor instance")
    print(f"Attributes: {dir(processor)[:10]}...")
    
    print("\nAll imports and instantiations successful!")
    
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")
    traceback.print_exc()
