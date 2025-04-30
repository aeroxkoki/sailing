#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システムのモジュールインポートテスト
"""

import os
import sys
import traceback

# 現在のファイルのディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# モジュールパスの表示
print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")

# テスト対象モジュールをインポート
try:
    print("Importing sailing_data_processor module...")
    import sailing_data_processor
    print(f"Successfully imported sailing_data_processor")
    print(f"sailing_data_processor path: {sailing_data_processor.__file__}")
    print(f"sailing_data_processor version: {sailing_data_processor.__version__}")
    
    print("\nImporting specific modules...")
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    print("Successfully imported WindPropagationModel")
    
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    print("Successfully imported WindFieldFusionSystem")
    
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    print("Successfully imported StrategyDetectorWithPropagation")
    
    # インスタンス化テスト
    print("\nTesting instantiation...")
    wpm = WindPropagationModel()
    print("Successfully created WindPropagationModel instance")
    
    wfs = WindFieldFusionSystem()
    print("Successfully created WindFieldFusionSystem instance")
    
    # インスタンス化せず、モジュールのプロパティのみ確認
    print("\nTesting module properties...")
    sdp_module = sys.modules['sailing_data_processor.strategy.strategy_detector_with_propagation']
    print(f"StrategyDetectorWithPropagation module: {sdp_module}")
    
    print("\nAll imports successful\!")
    
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")
    traceback.print_exc()
