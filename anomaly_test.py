#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnomalyDetector テスト - セーリング戦略分析システム

このスクリプトは、AnomalyDetectorの境界ケーステストを行います。
"""

import os
import sys
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"現在のPythonパス: {sys.path}")
print(f"カレントディレクトリ: {os.getcwd()}")

# AnomalyDetectorクラスが定義されているファイル一覧
anomaly_detector_files = [
    "sailing_data_processor/gps_anomaly_detector.py",
    "sailing_data_processor/utilities/gps_anomaly_detector.py",
    "sailing_data_processor/utilities/anomaly_detector.py",
    "sailing_data_processor/anomaly_detector.py"
]

# 各ファイルの存在確認
print("\nAnomalyDetectorクラスが定義されているファイル一覧:")
for file_path in anomaly_detector_files:
    full_path = os.path.join(project_root, file_path)
    exists = os.path.exists(full_path)
    print(f"{file_path}: {'存在します' if exists else '存在しません'}")
    if exists:
        # ファイルの先頭数行を表示
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()[:10]
                print(f"  先頭10行:")
                for i, line in enumerate(lines):
                    print(f"  {i+1}: {line.rstrip()}")
        except Exception as e:
            print(f"  ファイル読み込みエラー: {e}")

# インポートテスト
print("\nインポートテスト:")
try:
    print("1. sailing_data_processor.anomaly_detector からのインポートを試みます...")
    from sailing_data_processor.anomaly_detector import AnomalyDetector as AnomalyDetector1
    print("  成功しました")
except ImportError as e:
    print(f"  インポートエラー: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"  その他のエラー: {e}")
    traceback.print_exc()

try:
    print("2. sailing_data_processor.utilities.anomaly_detector からのインポートを試みます...")
    from sailing_data_processor.utilities.anomaly_detector import AnomalyDetector as AnomalyDetector2
    print("  成功しました")
except ImportError as e:
    print(f"  インポートエラー: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"  その他のエラー: {e}")
    traceback.print_exc()

try:
    print("3. sailing_data_processor.utilities.gps_anomaly_detector からのインポートを試みます...")
    from sailing_data_processor.utilities.gps_anomaly_detector import AnomalyDetector as AnomalyDetector3
    print("  成功しました")
except ImportError as e:
    print(f"  インポートエラー: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"  その他のエラー: {e}")
    traceback.print_exc()

try:
    print("4. sailing_data_processor.gps_anomaly_detector からのインポートを試みます...")
    from sailing_data_processor.gps_anomaly_detector import AnomalyDetector as AnomalyDetector4
    print("  成功しました")
except ImportError as e:
    print(f"  インポートエラー: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"  その他のエラー: {e}")
    traceback.print_exc()

# テスト用のシンプルなデータを作成
def create_test_data(size=100):
    """テスト用のシンプルなデータを作成"""
    start_time = datetime.now()
    latitudes = np.linspace(35.45, 35.50, num=size)
    longitudes = np.linspace(139.65, 139.70, num=size)
    timestamps = [start_time + timedelta(seconds=i*10) for i in range(size)]
    
    # DataFrameを作成
    return pd.DataFrame({
        'latitude': latitudes,
        'longitude': longitudes,
        'timestamp': timestamps
    })

# ボリュームごとのテスト (10, 100, 1000, 10000)
print("\nデータ量に応じたテスト:")
data_sizes = [10, 100, 1000, 10000]

# うまくインポートできたAnomalyDetectorを使用
AnomalyDetector = None
if 'AnomalyDetector3' in locals():
    print("sailing_data_processor.utilities.gps_anomaly_detector の AnomalyDetector を使用します")
    AnomalyDetector = AnomalyDetector3
elif 'AnomalyDetector1' in locals():
    print("sailing_data_processor.anomaly_detector の AnomalyDetector を使用します")
    AnomalyDetector = AnomalyDetector1
elif 'AnomalyDetector2' in locals():
    print("sailing_data_processor.utilities.anomaly_detector の AnomalyDetector を使用します")
    AnomalyDetector = AnomalyDetector2
elif 'AnomalyDetector4' in locals():
    print("sailing_data_processor.gps_anomaly_detector の AnomalyDetector を使用します")
    AnomalyDetector = AnomalyDetector4
else:
    print("有効なAnomalyDetectorがインポートできませんでした。テストを終了します。")
    sys.exit(1)

# インスタンスの作成
detector = AnomalyDetector()

# メソッド一覧を表示
print(f"\nAnomalyDetectorのメソッド一覧:")
for method in dir(AnomalyDetector):
    if not method.startswith('_') or method == '_detect_by_speed':
        print(f"  {method}")

# 各データサイズでテスト
for size in data_sizes:
    print(f"\nデータサイズ {size} でテスト:")
    
    # テストデータを作成
    test_df = create_test_data(size)
    
    # z_scoreメソッドのテスト
    try:
        print(f"  z_scoreメソッドをテスト中...")
        start_time = time.time()
        result_df = detector.detect_anomalies(test_df, ['z_score'])
        duration = time.time() - start_time
        anomaly_count = result_df['is_anomaly'].sum() if 'is_anomaly' in result_df.columns else 0
        print(f"  成功: {anomaly_count}個の異常値を検出, 実行時間: {duration:.3f}秒")
    except Exception as e:
        print(f"  失敗: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
    
    # speedメソッドのテスト
    try:
        print(f"  speedメソッドをテスト中...")
        start_time = time.time()
        result_df = detector.detect_anomalies(test_df, ['speed'])
        duration = time.time() - start_time
        anomaly_count = result_df['is_anomaly'].sum() if 'is_anomaly' in result_df.columns else 0
        print(f"  成功: {anomaly_count}個の異常値を検出, 実行時間: {duration:.3f}秒")
    except Exception as e:
        print(f"  失敗: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

print("\nテスト完了")
