#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポート構造テスト：リファクタリングされたboat_fusionモジュールのインポート構造を確認
"""

import sys
import os
import traceback

try:
    # テスト対象のモジュールをインポート
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import sailing_data_processor.boat_fusion
    from sailing_data_processor.boat_fusion import BoatDataFusionModel
    
    print("モジュール情報:")
    print(f"sailing_data_processor.boat_fusion: {sailing_data_processor.boat_fusion}")
    print(f"BoatDataFusionModel: {BoatDataFusionModel}")
    
    # メソッドを表示
    methods = [method for method in dir(BoatDataFusionModel) if not method.startswith('_')]
    print(f"\nメソッド一覧: {methods}")
    
    # モジュールパス
    print(f"\nモジュールパス:")
    print(f"sailing_data_processor.boat_fusion.__file__: {sailing_data_processor.boat_fusion.__file__}")
    
    # インポート階層を表示
    print("\nインポート階層:")
    boat_fusion_dir = os.path.dirname(sailing_data_processor.boat_fusion.__file__)
    print(f"ディレクトリ内容: {os.listdir(boat_fusion_dir)}")
    
except Exception as e:
    print(f"エラー発生: {e}")
    traceback.print_exc()
