#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sailing_data_processorパッケージのインストールテスト

このスクリプトは、sailing_data_processorパッケージが正しくインストールされているかを
テストするためのものです。特にRenderデプロイでのインポートエラーのデバッグに役立ちます。
"""

import sys
import os
import importlib.util
import traceback


def check_module_importable(module_name):
    """モジュールがインポート可能かどうかを確認"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False, None
        module = importlib.import_module(module_name)
        return True, module
    except ImportError as e:
        return False, str(e)


def get_module_path(module):
    """モジュールのファイルパスを取得"""
    try:
        return module.__file__
    except AttributeError:
        return "内部モジュール（パスなし）"


def main():
    """メイン関数"""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # sailing_data_processorのチェック
    print("\n=== sailing_data_processor パッケージのチェック ===")
    importable, module = check_module_importable("sailing_data_processor")
    
    if importable:
        print(f"✅ Successfully imported sailing_data_processor")
        print(f"   Path: {get_module_path(module)}")
        print(f"   Version: {getattr(module, '__version__', 'unknown')}")
        
        # サブモジュールのチェック
        sub_modules = [
            "sailing_data_processor.wind_propagation_model",
            "sailing_data_processor.wind_estimator",
            "sailing_data_processor.wind_field_fusion_system",
            "sailing_data_processor.strategy.strategy_detector_with_propagation",
            "sailing_data_processor.utilities.math_utils",
            "sailing_data_processor.utilities.gps_utils"
        ]
        
        for sub_module_name in sub_modules:
            print(f"------------------------------------------------------------")
            sub_importable, sub_module = check_module_importable(sub_module_name)
            if sub_importable:
                print(f"✅ Successfully imported {sub_module_name}")
            else:
                print(f"❌ Failed to import {sub_module_name}")
                print(f"   Error: {sub_module}")
    else:
        print(f"❌ Failed to import sailing_data_processor")
        print(f"   Error: {module}")
        
        # エラー詳細を表示
        print("\n=== Import Error Details ===")
        try:
            import sailing_data_processor
        except Exception as e:
            traceback.print_exc()
    
    # 実際にインスタンス化してテスト
    if importable:
        print("\n=== モジュールのインスタンス化テスト ===")
        try:
            from sailing_data_processor.wind_propagation_model import WindPropagationModel
            model = WindPropagationModel()
            print("✅ WindPropagationModel successfully initialized")
        except Exception as e:
            print("❌ Failed to initialize WindPropagationModel")
            print(f"   Error: {str(e)}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
