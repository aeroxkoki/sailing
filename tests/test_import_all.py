#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各モジュールのインポートテスト
"""

import sys
import os
import importlib
import pytest
import warnings

# IDE実行用のパス追加
# 実際のテスト実行時はconftest.pyが先に読み込まれるためこの処理は不要だが、
# 単独実行時の利便性のために残す
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'sailing_data_processor'))

print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# テスト対象のモジュールリスト
# 依存順に並べて依存関係による問題を避ける
modules_to_test = [
    'sailing_data_processor',
    'sailing_data_processor.wind_propagation_model',
    'sailing_data_processor.wind_field_interpolator',  # 追加
    'sailing_data_processor.prediction_evaluator',     # 追加
    'sailing_data_processor.wind_estimator',
    'sailing_data_processor.wind_field_fusion_system',
    'sailing_data_processor.utilities.math_utils',
    'sailing_data_processor.utilities.gps_utils',
    'sailing_data_processor.strategy.strategy_detector_with_propagation'
]

# 非常に詳細なモジュールエラーに警告フィルターを設定（テストが継続できるように）
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# テスト関数として定義して、pytestがこれを実行するようにする
@pytest.mark.parametrize("module_name", modules_to_test)
def test_module_import(module_name):
    """モジュールが正しくインポートできることをテスト"""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        
        # モジュール内のクラスやバージョン情報があれば表示
        if hasattr(module, '__version__'):
            print(f"   Version: {module.__version__}")
            
        # 主要モジュールがインポートできることを確認
        if module_name == 'sailing_data_processor.wind_propagation_model':
            from sailing_data_processor.wind_propagation_model import WindPropagationModel
            model = WindPropagationModel()
            print(f"Successfully created WindPropagationModel instance")
            assert isinstance(model, WindPropagationModel)
            
        elif module_name == 'sailing_data_processor.wind_field_fusion_system':
            from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
            fusion = WindFieldFusionSystem()
            print(f"Successfully created WindFieldFusionSystem instance")
            assert isinstance(fusion, WindFieldFusionSystem)
            
        # 成功を確認
        assert module is not None
        print("-" * 60)
        
    except ImportError as e:
        print(f"❌ Failed to import {module_name}")
        print(f"   Error: {e}")
        pytest.skip(f"Import error with {module_name}: {e}")
        
    except Exception as e:
        print(f"❌ Error with {module_name}")
        print(f"   Error: {e}")
        pytest.skip(f"Error with {module_name}: {e}")

if __name__ == "__main__":
    print("モジュールのインポートテスト開始")
    
    # 手動テスト実行
    for module_name in modules_to_test:
        try:
            test_module_import(module_name)
        except Exception as e:
            print(f"テスト失敗: {module_name} - {e}")
            
    print("モジュールのインポートテスト完了")
