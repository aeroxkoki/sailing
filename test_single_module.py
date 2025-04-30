#!/usr/bin/env python3

import sys
import os
import traceback

# モジュール名をコマンドライン引数から取得
if len(sys.argv) < 2:
    print("Usage: python test_single_module.py module_name")
    sys.exit(1)

module_name = sys.argv[1]

# カレントディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print(f"Testing import for: {module_name}")
try:
    module = __import__(module_name, fromlist=["*"])
    print(f"✓ Successfully imported {module_name}")
except Exception as e:
    print(f"✗ Failed to import {module_name}")
    print(f"Error: {e}")
    traceback.print_exc()
