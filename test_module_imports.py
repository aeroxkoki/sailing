# -*- coding: utf-8 -*-
import sys
import os
import importlib
import traceback

# テスト対象のパッケージ
packages = [
    'sailing_data_processor',
    'sailing_data_processor.wind_field_fusion_system',
    'sailing_data_processor.wind_field_interpolator',
    'sailing_data_processor.wind_propagation_model',
    'sailing_data_processor.prediction_evaluator',
    'tests.test_wind_field_fusion_system',
]

print("モジュールインポートテスト開始")

# カレントディレクトリをパスに追加
sys.path.insert(0, os.getcwd())

# 各パッケージのインポートテスト
for package in packages:
    print(f"インポート試行: {package}")
    try:
        module = importlib.import_module(package)
        print(f"インポート成功: {package}")
        
        # モジュールの内容を確認
        if hasattr(module, '__file__'):
            print(f"  ファイルパス: {module.__file__}")
        
        # クラスやメソッドの存在確認
        if package == 'sailing_data_processor.wind_field_fusion_system':
            if hasattr(module, 'WindFieldFusionSystem'):
                print("  WindFieldFusionSystemクラスが存在します")
                wffs = module.WindFieldFusionSystem()
                print("  WindFieldFusionSystemのインスタンス化成功")
            else:
                print("  WindFieldFusionSystemクラスが見つかりません")
        
        elif package == 'sailing_data_processor.wind_field_interpolator':
            if hasattr(module, 'WindFieldInterpolator'):
                print("  WindFieldInterpolatorクラスが存在します")
                wfi = module.WindFieldInterpolator()
                print("  WindFieldInterpolatorのインスタンス化成功")
            else:
                print("  WindFieldInterpolatorクラスが見つかりません")
    
    except Exception as e:
        print(f"インポートエラー: {package}")
        print(f"  エラー: {str(e)}")
        traceback.print_exc()

print("モジュールインポートテスト終了")
