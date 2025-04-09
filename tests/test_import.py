#!/usr/bin/env python3
"""
インポートテスト用の簡単なスクリプト
"""

import sys
import os

# 現在のパスを表示
print("Current directory:", os.getcwd())
print("Python path:", sys.path)

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # sailing_data_processorパッケージのインポートを試みる
    import sailing_data_processor
    print("Successfully imported sailing_data_processor")
    
    # 詳細情報
    print("sailing_data_processor path:", sailing_data_processor.__file__)
    print("sailing_data_processor version:", sailing_data_processor.__version__)
    
    # 特定のモジュールのインポートを試みる
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    print("Successfully imported WindPropagationModel")
    
    # WindPropagationModelのインスタンス化
    model = WindPropagationModel()
    print("Successfully created WindPropagationModel instance")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
