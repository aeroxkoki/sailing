#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細なインポートトレースを有効にしてテスト
"""

import sys
import os
import traceback
import warnings
import importlib
from pprint import pprint

# 最大の詳細さでインポートを表示するよう設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONVERBOSE"] = "2"  # 最大詳細度

# モジュールのインポートパスを表示
print("=== Python Path ===")
pprint(sys.path)
print("=" * 40)

# 正しいパスが設定されているか確認
project_root = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(project_root, 'sailing_data_processor')
strategy_path = os.path.join(module_path, 'strategy')

print(f"Current Directory: {os.getcwd()}")
print(f"Project Root: {project_root}")
print(f"Module Path: {module_path}")
print(f"Strategy Path: {strategy_path}")

# すべてのパスが追加されていることを確認
for path in [project_root, module_path, strategy_path]:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"Added missing path: {path}")

print("=" * 40)

try:
    # sailing_data_processorモジュールをインポート
    print("Importing sailing_data_processor...")
    import sailing_data_processor
    print(f"Found version: {sailing_data_processor.__version__}")
    
    # StrategyDetectorWithPropagationクラスをインポート
    print("\nImporting StrategyDetectorWithPropagation...")
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    print("Successfully imported StrategyDetectorWithPropagation")
    
    # WindFieldFusionSystemクラスをインポート
    print("\nImporting WindFieldFusionSystem...")
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    print("Successfully imported WindFieldFusionSystem")
    print(f"Module file: {WindFieldFusionSystem.__module__}")
    
    # 循環参照の可能性があるimportを試す
    print("\nTesting circular imports...")
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator
    print("All imports successful\!")
    
    # 完全なテスト実行
    print("\n=== Creating instances ===")
    interpolator = WindFieldInterpolator()
    print("Created WindFieldInterpolator")
    
    fusion = WindFieldFusionSystem()
    print("Created WindFieldFusionSystem")
    
    model = WindPropagationModel()
    print("Created WindPropagationModel")
    
    # このインスタンス化が成功すれば問題解決
    detector = StrategyDetectorWithPropagation(wind_fusion_system=fusion)
    print("Created StrategyDetectorWithPropagation with WindFieldFusionSystem")
    
    print("\nAll tests passed successfully\!")
    
except ImportError as e:
    print(f"Import Error: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
