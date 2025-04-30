#!/usr/bin/env python3

import sys
import os

# カレントディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# モジュールのインポートを試みる
try:
    from sailing_data_processor.reporting.elements.map import map_utils
    print("Map utils imported successfully")
except Exception as e:
    print(f"Map utils import error: {e}")

try:
    from sailing_data_processor.validation import quality_metrics_integration_backup
    print("Quality metrics integration imported successfully")
except Exception as e:
    print(f"Quality metrics integration import error: {e}")

# Pythonパスを表示
print("\nPython path:")
for p in sys.path:
    print(f"  {p}")

# ファイルの存在確認
map_utils_path = "sailing_data_processor/reporting/elements/map/map_utils.py"
if os.path.exists(map_utils_path):
    print(f"\n{map_utils_path} exists")
    with open(map_utils_path, "r") as f:
        first_few_lines = "".join(f.readlines()[:10])
    print(f"First few lines:\n{first_few_lines}")
else:
    print(f"\n{map_utils_path} does not exist")
