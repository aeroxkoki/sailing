#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各モジュールのインポートテスト
"""

import sys
import os
import importlib

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# テスト対象のモジュールリスト
modules_to_test = [
    'sailing_data_processor',
    'sailing_data_processor.wind_propagation_model',
    'sailing_data_processor.wind_estimator',
    'sailing_data_processor.wind_field_fusion_system',
    'sailing_data_processor.strategy.strategy_detector_with_propagation',
    'sailing_data_processor.utilities.math_utils',
    'sailing_data_processor.utilities.gps_utils'
]

# 各モジュールをインポートしてテスト
for module_name in modules_to_test:
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        
        # モジュール内のクラスやバージョン情報があれば表示
        if hasattr(module, '__version__'):
            print(f"   Version: {module.__version__}")
        
    except ImportError as e:
        print(f"❌ Failed to import {module_name}")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Error with {module_name}")
        print(f"   Error: {e}")
    
    print("-" * 60)
