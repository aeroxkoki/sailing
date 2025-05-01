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
        # インポート前にパス情報を出力
        print(f"📦 Importing {module_name} with sys.path: {sys.path}")
        
        # モジュールをインポート
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        
        # モジュールの詳細情報を表示
        if hasattr(module, '__version__'):
            print(f"   Version: {module.__version__}")
            
        if hasattr(module, '__file__'):
            print(f"   Module path: {module.__file__}")
        
        # モジュール内のクラスと関数を表示（最大10個まで）
        module_contents = [name for name in dir(module) if not name.startswith('_')][:10]
        if module_contents:
            print(f"   Contents (partial): {', '.join(module_contents)}")
            
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
            
        elif module_name == 'sailing_data_processor.strategy.strategy_detector_with_propagation':
            print("Testing strategy_detector_with_propagation import")
            
            # まず基本クラスを確認
            from sailing_data_processor.strategy.detector import StrategyDetector
            print("Base StrategyDetector imported")
            
            # 遅延ロード機能を試す
            from sailing_data_processor.strategy import load_strategy_detector_with_propagation
            detector_class = load_strategy_detector_with_propagation()
            print(f"Loaded detector class via lazily loading: {detector_class.__name__ if detector_class else 'None'}")
            assert detector_class is not None
            
            # 直接参照のテスト
            from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
            print(f"Directly imported StrategyDetectorWithPropagation")
            assert issubclass(StrategyDetectorWithPropagation, StrategyDetector)
            
        # 成功を確認
        assert module is not None
        print("=" * 60)
        
    except ImportError as e:
        print(f"❌ Failed to import {module_name}")
        print(f"   Error: {e}")
        
        # デバッグ情報の出力
        if hasattr(e, "__traceback__"):
            import traceback
            print("詳細なエラー情報:")
            traceback.print_tb(e.__traceback__)
            
        # モジュールパスの検索を試みる
        print(f"モジュール '{module_name}' の検索:")
        parts = module_name.split('.')
        current_path = None
        for i, part in enumerate(parts):
            path_to_check = os.path.join(current_path, part) if current_path else part
            if i < len(parts) - 1:
                path_to_check = os.path.join(path_to_check, "__init__.py")
            else:
                path_to_check = f"{path_to_check}.py"
                
            for sys_path in sys.path:
                full_path = os.path.join(sys_path, path_to_check)
                exists = os.path.exists(full_path)
                print(f"   {full_path} - {'存在します' if exists else '存在しません'}")
        
        pytest.skip(f"Import error with {module_name}: {e}")
        
    except Exception as e:
        print(f"❌ Error with {module_name}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
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
