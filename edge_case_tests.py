#!/usr/bin/env python3
"""
エッジケーステスト - セーリング戦略分析システム (モジュールインポートテスト)

このスクリプトは、セーリング戦略分析システムのモジュールインポートをテストします。
"""

import os
import sys
import traceback

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"現在のPythonパス: {sys.path}")
print(f"カレントディレクトリ: {os.getcwd()}")

# モジュールのインポートテスト
try:
    print("sailing_data_processor.utilities.gps_anomaly_detector モジュールのインポートを試みます...")
    from sailing_data_processor.utilities.gps_anomaly_detector import AnomalyDetector
    print("AnomalyDetectorのインポートに成功しました")
    
    # モジュールの内容確認
    print(f"AnomalyDetectorクラスの定義: {AnomalyDetector.__module__}")
    print(f"_detect_by_speedメソッドの存在: {'_detect_by_speed' in dir(AnomalyDetector)}")
    
    # ファイルの存在確認
    module_path = os.path.abspath(sys.modules[AnomalyDetector.__module__].__file__)
    print(f"モジュールのファイルパス: {module_path}")
    print(f"ファイルの存在: {os.path.exists(module_path)}")
    
except ImportError as e:
    print(f"インポートエラー: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"その他のエラー: {e}")
    traceback.print_exc()

# ディレクトリ構造の確認
print("\nディレクトリ構造:")
sailing_dir = os.path.join(project_root, "sailing_data_processor")
if os.path.exists(sailing_dir):
    print(f"sailing_data_processor ディレクトリが存在します")
    
    utils_dir = os.path.join(sailing_dir, "utilities")
    if os.path.exists(utils_dir):
        print(f"utilities ディレクトリが存在します")
        
        gps_file = os.path.join(utils_dir, "gps_anomaly_detector.py")
        if os.path.exists(gps_file):
            print(f"gps_anomaly_detector.py ファイルが存在します")
            # ファイルの先頭数行を表示
            try:
                with open(gps_file, 'r') as f:
                    print("\ngps_anomaly_detector.py の先頭10行:")
                    for i, line in enumerate(f.readlines()[:10]):
                        print(f"{i+1}: {line.rstrip()}")
            except Exception as e:
                print(f"ファイル読み込みエラー: {e}")
        else:
            print(f"gps_anomaly_detector.py ファイルが見つかりません")
    else:
        print(f"utilities ディレクトリが見つかりません")
else:
    print(f"sailing_data_processor ディレクトリが見つかりません")

# ストラテジーディテクタのインポートテスト
try:
    print("\nextended_test からのインポートを試みます...")
    from extended_test import StrategyDetectorWithPropagationTest
    print("StrategyDetectorWithPropagationTestのインポートに成功しました")
except ImportError as e:
    print(f"インポートエラー: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"その他のエラー: {e}")
    traceback.print_exc()

print("\nモジュールインポートテスト完了")
