#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
戦略モジュールインポートテスト

このスクリプトは循環参照問題の修正を検証するためのものです。
"""

import os
import sys
import traceback
import importlib

# カレントディレクトリの確認
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# 必要なパスを追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added project root to path: {project_root}")

# sailingモジュールのパスも明示的に追加
module_path = os.path.join(project_root, 'sailing_data_processor')
if module_path not in sys.path:
    sys.path.insert(0, module_path)
    print(f"Added module path to path: {module_path}")

# strategyモジュールのパスも明示的に追加
strategy_path = os.path.join(module_path, 'strategy')
if strategy_path not in sys.path:
    sys.path.insert(0, strategy_path)
    print(f"Added strategy path to path: {strategy_path}")

# テスト結果を格納するリスト
results = []

def test_import(module_name, expected_attr=None):
    """モジュールのインポートをテスト"""
    print(f"\nTesting import of {module_name}...")
    try:
        module = importlib.import_module(module_name)
        print(f"  Success: {module_name} imported")
        
        if expected_attr:
            if hasattr(module, expected_attr):
                attr = getattr(module, expected_attr)
                print(f"  Success: {expected_attr} found in {module_name}")
                return True, module, attr
            else:
                print(f"  Failure: {expected_attr} not found in {module_name}")
                return False, module, None
        
        return True, module, None
    except ImportError as e:
        print(f"  Failure: Could not import {module_name}")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False, None, None

def run_tests():
    """すべてのテストを実行"""
    # sailing_data_processor本体のインポート
    success, sdp, _ = test_import('sailing_data_processor')
    results.append(('sailing_data_processor base', success))
    
    if not success:
        return results
    
    # sailing_data_processor.strategyのインポート
    success, strategy, _ = test_import('sailing_data_processor.strategy')
    results.append(('sailing_data_processor.strategy', success))
    
    if not success:
        return results
    
    # 遅延ロード関数のテスト
    success, _, load_func = test_import('sailing_data_processor.strategy', 'load_strategy_detector_with_propagation')
    results.append(('strategy.load_strategy_detector_with_propagation', success))
    
    if not success:
        return results
    
    # ルートの遅延ロード関数をテスト
    success, _, root_load_func = test_import('sailing_data_processor', 'load_strategy_detector')
    results.append(('load_strategy_detector', success))
    
    if not success:
        return results
    
    # 遅延ロード関数を使用して実際にクラスをロード
    try:
        detector_class = load_func()
        print(f"Successfully loaded detector_class using strategy.load_strategy_detector_with_propagation")
        print(f"Class type: {type(detector_class)}")
        results.append(('strategy lazy loading', True))
    except Exception as e:
        print(f"Failed to load detector_class using strategy.load_strategy_detector_with_propagation: {e}")
        traceback.print_exc()
        results.append(('strategy lazy loading', False))
    
    # ルートの遅延ロード関数を使用
    try:
        root_detector_class = root_load_func()
        print(f"Successfully loaded detector_class using root load_strategy_detector")
        print(f"Class type: {type(root_detector_class)}")
        results.append(('root lazy loading', True))
    except Exception as e:
        print(f"Failed to load detector_class using root load_strategy_detector: {e}")
        traceback.print_exc()
        results.append(('root lazy loading', False))
    
    return results

def print_summary(results):
    """テスト結果のサマリを表示"""
    print("\n" + "="*50)
    print("IMPORT TEST SUMMARY")
    print("="*50)
    
    all_passed = True
    for name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{name:40} : {status}")
        all_passed = all_passed and success
    
    print("\nOverall result:", "PASSED" if all_passed else "FAILED")
    return all_passed

if __name__ == "__main__":
    results = run_tests()
    success = print_summary(results)
    sys.exit(0 if success else 1)
