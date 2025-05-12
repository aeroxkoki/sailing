#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡単なテスト：リファクタリングされたboat_fusionモジュールの基本機能テスト
"""

import sys
import os
import traceback

try:
    # テスト対象のモジュールをインポート
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from sailing_data_processor.boat_fusion import BoatDataFusionModel
    
    # インスタンス化テスト
    fusion_model = BoatDataFusionModel()
    print("インスタンス化成功")
    
    # スキルレベル設定テスト
    fusion_model.set_boat_skill_levels({'boat1': 0.8, 'boat2': 0.6})
    print(f"スキルレベル設定成功: {fusion_model.boat_skill_levels}")
    
    # 艇種設定テスト
    fusion_model.set_boat_types({'boat1': 'laser', 'boat2': '470'})
    print(f"艇種設定成功: {fusion_model.boat_types}")
    
    print("すべてのテスト成功!")
    
except Exception as e:
    print(f"エラー発生: {e}")
    traceback.print_exc()
