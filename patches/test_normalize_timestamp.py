#!/usr/bin/env python3
"""
_normalize_to_timestamp修正の検証テスト
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # 修正対象のクラスをインポート
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    from sailing_data_processor.strategy.points import WindShiftPoint
    
    # インスタンス化
    detector = StrategyDetectorWithPropagation()
    
    # テスト用のデータを作成
    test_data = [
        datetime.now(),                      # datetimeオブジェクト
        timedelta(hours=1),                  # timedeltaオブジェクト
        123.45,                              # 数値
        {'timestamp': 1234567890},           # timestampキーを持つ辞書
        {'other': 'value'},                  # timestampキーを持たない辞書
        '2025-03-28',                        # 日付文字列
        '123.45',                            # 数値文字列
        None,                                # None
    ]
    
    # 各テストデータでの動作を検証
    for i, data in enumerate(test_data):
        try:
            result = detector._normalize_to_timestamp(data)
            logger.info(f"テスト{i+1}: 入力 {type(data).__name__}({data}) -> 結果 {result}")
        except Exception as e:
            logger.error(f"テスト{i+1}: 入力 {type(data).__name__}({data}) -> エラー {e}")

    # WindShiftPointを使った実際のユースケースをテスト
    logger.info("実際のユースケーステスト開始")
    
    # 通常のdatetime
    point1 = WindShiftPoint((35.45, 139.65), datetime.now())
    
    # タイムスタンプを含む辞書
    timestamp_dict = {'timestamp': datetime.now().timestamp()}
    point2 = WindShiftPoint((35.46, 139.66), timestamp_dict)
    
    # タイムスタンプを含まない辞書
    invalid_dict = {'some_key': 'some_value'}
    point3 = WindShiftPoint((35.47, 139.67), invalid_dict)
    
    # テスト用のポイントをリスト化
    test_points = [point1, point2, point3]
    
    # フィルタリング関数を呼び出し
    try:
        filtered_points = detector._filter_duplicate_shift_points(test_points)
        logger.info(f"フィルタリングテスト成功: 入力 {len(test_points)}件 -> 出力 {len(filtered_points)}件")
    except Exception as e:
        logger.error(f"フィルタリングテスト失敗: {e}")
    
    logger.info("テスト完了!")
    
except ImportError as e:
    logger.error(f"モジュールインポートエラー: {e}")
except Exception as e:
    logger.error(f"予期せぬエラー: {e}")
