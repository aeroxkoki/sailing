#!/usr/bin/env python3

import sys
import os
import traceback

# カレントディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Python path:")
for path in sys.path:
    print(f"  {path}")

# テスト対象のモジュール
modules_to_test = [
    "sailing_data_processor.reporting.elements.map.base_map_element",
    "sailing_data_processor.reporting.elements.map.map_utils",
    "sailing_data_processor.validation.quality_metrics_improvements",
    "sailing_data_processor.validation.quality_metrics_integration_backup"
]

# 各モジュールをインポートして結果を表示
for module_name in modules_to_test:
    print(f"\nTesting import for: {module_name}")
    try:
        module = __import__(module_name, fromlist=["*"])
        print(f"✓ Successfully imported {module_name}")
    except Exception as e:
        print(f"✗ Failed to import {module_name}")
        print(f"Error: {e}")
        traceback.print_exc()
