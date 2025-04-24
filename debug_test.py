#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デバッグテストコード

テスト実行時の詳細なエラー情報を出力するためのスクリプト
"""

import sys
import os
import traceback
from datetime import datetime

def print_system_info():
    """システム情報の出力"""
    print("===== システム情報 =====")
    print(f"Python バージョン: {sys.version}")
    print(f"実行パス: {os.getcwd()}")
    print(f"システムパス: {sys.path}")
    print(f"環境変数 PYTHONPATH: {os.environ.get('PYTHONPATH', 'なし')}")
    print("========================\n")

def check_module_imports():
    """モジュールのインポートチェック"""
    print("===== モジュールインポートチェック =====")
    
    modules_to_check = [
        "sailing_data_processor",
        "sailing_data_processor.wind_field_fusion_system",
        "sailing_data_processor.wind_propagation_model",
        "sailing_data_processor.strategy.strategy_detector_with_propagation",
        "sailing_data_processor.strategy.points"
    ]
    
    all_success = True
    
    for module_name in modules_to_check:
        try:
            module = __import__(module_name, fromlist=["*"])
            print(f"✓ {module_name} - インポート成功")
            
            # 各モジュールの主要クラスも確認
            if module_name == "sailing_data_processor.wind_field_fusion_system":
                from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
                wffs = WindFieldFusionSystem()
                print(f"  ✓ WindFieldFusionSystem クラスを初期化できました")
                
            elif module_name == "sailing_data_processor.wind_propagation_model":
                from sailing_data_processor.wind_propagation_model import WindPropagationModel
                wpm = WindPropagationModel()
                print(f"  ✓ WindPropagationModel クラスを初期化できました")
                
            elif module_name == "sailing_data_processor.strategy.strategy_detector_with_propagation":
                from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
                # このクラスはVMG計算機が必要なので初期化はスキップ
                print(f"  ✓ StrategyDetectorWithPropagation クラスを確認しました")
                
            elif module_name == "sailing_data_processor.strategy.points":
                from sailing_data_processor.strategy.points import WindShiftPoint
                wsp = WindShiftPoint((35.45, 139.65), datetime.now())
                print(f"  ✓ WindShiftPoint クラスを初期化できました")
                
        except ImportError as e:
            print(f"✗ {module_name} - インポートエラー: {e}")
            all_success = False
        except Exception as e:
            print(f"✗ {module_name} - その他のエラー: {e}")
            traceback.print_exc()
            all_success = False
    
    print("====================================\n")
    return all_success

def check_basic_operations():
    """基本的な操作の確認"""
    print("===== 基本操作チェック =====")
    
    try:
        from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
        
        # WindFieldFusionSystemの基本機能確認
        wffs = WindFieldFusionSystem()
        distance = wffs._haversine_distance(35.45, 139.65, 35.46, 139.66)
        print(f"✓ Haversine距離計算: {distance:.2f}m")
        
        # データポイント追加
        point = {
            'timestamp': datetime.now(),
            'latitude': 35.45,
            'longitude': 139.65,
            'wind_direction': 90,
            'wind_speed': 10
        }
        wffs.add_wind_data_point(point)
        print(f"✓ 風データポイント追加: 成功")
        
        # 風の場予測
        from sailing_data_processor.wind_propagation_model import WindPropagationModel
        
        wpm = WindPropagationModel()
        print(f"✓ WindPropagationModel コリオリ係数: {wpm.coriolis_factor}")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本操作チェック失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("\n===== セーリング戦略分析システム デバッグテスト =====\n")
    
    # システム情報の出力
    print_system_info()
    
    # モジュールインポートチェック
    imports_ok = check_module_imports()
    
    # 基本操作チェック
    operations_ok = check_basic_operations()
    
    # 結果出力
    print("\n===== テスト結果サマリー =====")
    print(f"モジュールインポート: {'成功' if imports_ok else '失敗'}")
    print(f"基本操作: {'成功' if operations_ok else '失敗'}")
    
    overall_result = imports_ok and operations_ok
    print(f"\n総合結果: {'成功' if overall_result else '失敗'}")
    
    return 0 if overall_result else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
