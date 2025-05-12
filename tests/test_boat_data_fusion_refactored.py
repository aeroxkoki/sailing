#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト：リファクタリングされたboat_fusionモジュールのテスト
"""

import sys
import os
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    # テスト対象のモジュールをインポート
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from sailing_data_processor.boat_fusion import BoatDataFusionModel
    
    def create_test_data():
        """テストデータの作成"""
        base_time = datetime.now()
        data = {
            'boat1': pd.DataFrame({
                'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
                'latitude': [35.45 + i*0.001 for i in range(5)],
                'longitude': [139.65 + i*0.001 for i in range(5)],
                'wind_direction': [90 + i for i in range(5)],
                'wind_speed_knots': [10 + i*0.5 for i in range(5)],
                'confidence': [0.8 for _ in range(5)]
            }),
            'boat2': pd.DataFrame({
                'timestamp': [base_time + timedelta(minutes=i) for i in range(5)],
                'latitude': [35.46 + i*0.001 for i in range(5)],
                'longitude': [139.66 + i*0.001 for i in range(5)],
                'wind_direction': [95 + i for i in range(5)],
                'wind_speed_knots': [11 + i*0.5 for i in range(5)],
                'confidence': [0.7 for _ in range(5)]
            })
        }
        return data
    
    # モデルの初期化
    print("モデルの初期化開始")
    fusion_model = BoatDataFusionModel()
    print("モデルの初期化完了")
    
    # スキルレベルと艇種の設定
    print("スキルレベルと艇種を設定")
    fusion_model.set_boat_skill_levels({'boat1': 0.8, 'boat2': 0.6})
    fusion_model.set_boat_types({'boat1': 'laser', 'boat2': '470'})
    
    # テストデータの生成
    print("テストデータの生成")
    test_data = create_test_data()
    print(f"テストデータ: {len(test_data)} 艇分のデータ")
    
    # 風向風速の統合テスト
    print("風向風速の統合テスト開始")
    try:
        result = fusion_model.fuse_wind_estimates(test_data)
        if result:
            print(f"風向風速の統合結果: 風向={result['wind_direction']}, 風速={result['wind_speed']}, 信頼度={result['confidence']}")
        else:
            print("風向風速の統合結果: None")
    except Exception as e:
        print(f"風向風速の統合でエラー発生: {e}")
        traceback.print_exc()
    
    # 時空間風場のテスト
    print("\n時空間風場のテスト開始")
    try:
        # データを統合して履歴を作成
        print("風向風速の統合（履歴作成）")
        fusion_model.fuse_wind_estimates(test_data)
        
        # 時空間風場の作成
        print("時空間風場の作成")
        time_points = [datetime.now() + timedelta(minutes=i*5) for i in range(3)]
        wind_fields = fusion_model.create_spatiotemporal_wind_field(time_points, grid_resolution=10)
        
        print(f"時空間風場の結果: {len(wind_fields)} 時間点のデータ")
    except Exception as e:
        print(f"時空間風場の作成でエラー発生: {e}")
        traceback.print_exc()
        
    print("\nテスト完了")
    
except Exception as e:
    print(f"テスト実行中にエラー発生: {e}")
    traceback.print_exc()
