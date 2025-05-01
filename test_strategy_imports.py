#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
戦略検出モジュールのインポートテスト
"""

import sys
import os
import traceback
import warnings

# パスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'sailing_data_processor'))
sys.path.insert(0, os.path.join(current_dir, 'sailing_data_processor/strategy'))

# インポートを試みる
try:
    print("1. sailing_data_processor のインポート開始")
    import sailing_data_processor
    print("2. sailing_data_processor のインポート成功")
    print("3. sailing_data_processor.strategy のインポート開始")
    import sailing_data_processor.strategy
    print("4. sailing_data_processor.strategy のインポート成功")
    
    print("5. StrategyDetector のインポート開始")
    from sailing_data_processor.strategy.detector import StrategyDetector
    print("6. StrategyDetector のインポート成功")
    
    print("7. points モジュールのインポート開始")
    from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
    print("8. points モジュールのインポート成功")
    
    print("9. strategy_detector_utils のインポート開始")
    from sailing_data_processor.strategy.strategy_detector_utils import calculate_distance
    print("10. strategy_detector_utils のインポート成功")
    
    print("11. strategy_detector_with_propagation のインポート開始")
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    print("12. strategy_detector_with_propagation のインポート成功")
    
    print("13. StrategyDetectorWithPropagation のインスタンス化")
    detector = StrategyDetectorWithPropagation()
    print("14. StrategyDetectorWithPropagation のインスタンス化成功")
    
    print("15. 全テストが成功しました")
    
except Exception as e:
    print(f"エラー: {e}")
    traceback.print_exc()
