#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト：新旧実装の比較テスト
"""

import sys
import os
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    # パスの追加
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # 新実装のインポート（リファクタリング後）
    from sailing_data_processor.boat_fusion import BoatDataFusionModel as NewBoatDataFusionModel
    
    # 旧実装のインポート（互換性のためのエイリアス）
    from sailing_data_processor.boat_data_fusion import BoatDataFusion as OldBoatDataFusionModel
    
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
    
    def print_result_summary(title, result):
        """結果のサマリを表示"""
        if result:
            print(f"{title}:")
            print(f"  風向: {result['wind_direction']:.2f}")
            print(f"  風速: {result['wind_speed']:.2f}")
            print(f"  信頼度: {result['confidence']:.2f}")
            if 'boat_count' in result:
                print(f"  艇数: {result['boat_count']}")
        else:
            print(f"{title}: None")
    
    # モデルの初期化
    print("== モデルの初期化 ==")
    new_model = NewBoatDataFusionModel()
    old_model = OldBoatDataFusionModel()
    print("初期化完了\n")
    
    # スキルレベルと艇種の設定
    print("== スキルレベルと艇種の設定 ==")
    skill_levels = {'boat1': 0.8, 'boat2': 0.6}
    boat_types = {'boat1': 'laser', 'boat2': '470'}
    
    new_model.set_boat_skill_levels(skill_levels)
    new_model.set_boat_types(boat_types)
    
    old_model.set_boat_skill_levels(skill_levels)
    old_model.set_boat_types(boat_types)
    print("設定完了\n")
    
    # テストデータの生成
    print("== テストデータの生成 ==")
    test_data = create_test_data()
    print(f"生成完了: {len(test_data)} 艇分のデータ\n")
    
    # 風向風速の統合テスト
    print("== 風向風速の統合テスト ==")
    try:
        print("新実装で風向風速統合...")
        new_result = new_model.fuse_wind_estimates(test_data)
        print_result_summary("新実装の結果", new_result)
        
        print("\n旧実装で風向風速統合...")
        old_result = old_model.fuse_wind_estimates(test_data)
        print_result_summary("旧実装の結果", old_result)
        
        # 結果の比較
        if new_result and old_result:
            print("\n結果の比較:")
            dir_diff = abs((new_result['wind_direction'] - old_result['wind_direction'] + 180) % 360 - 180)
            speed_diff = abs(new_result['wind_speed'] - old_result['wind_speed'])
            confidence_diff = abs(new_result['confidence'] - old_result['confidence'])
            
            print(f"  風向の差: {dir_diff:.2f}度")
            print(f"  風速の差: {speed_diff:.2f}ノット")
            print(f"  信頼度の差: {confidence_diff:.2f}")
            
            if dir_diff < 5 and speed_diff < 1 and confidence_diff < 0.2:
                print("  -> 結果は十分に近いです (OK)")
            else:
                print("  -> 結果に差異があります (注意)")
        
    except Exception as e:
        print(f"風向風速の統合でエラー発生: {e}")
        traceback.print_exc()
    
    # 時空間風場のテスト
    print("\n== 時空間風場のテスト ==")
    try:
        # 十分な履歴データを作成
        print("履歴データ作成中...")
        for _ in range(4):  # 4回の履歴データ
            new_model.fuse_wind_estimates(test_data)
            old_model.fuse_wind_estimates(test_data)
        
        # 時間点の設定
        time_points = [datetime.now() + timedelta(minutes=i*5) for i in range(3)]
        
        # 新実装の時空間風場
        print("新実装で時空間風場作成...")
        new_fields = new_model.create_spatiotemporal_wind_field(time_points, grid_resolution=10)
        print(f"新実装の結果: {len(new_fields)} 時間点のデータ")
        
        # 旧実装の時空間風場
        print("旧実装で時空間風場作成...")
        old_fields = old_model.create_spatiotemporal_wind_field(time_points, grid_resolution=10)
        print(f"旧実装の結果: {len(old_fields)} 時間点のデータ")
        
        # 結果の比較
        print("\n結果の比較:")
        if len(new_fields) == len(old_fields):
            print(f"  同じ数の時間点データ: {len(new_fields)} 件")
        else:
            print(f"  時間点データ数が異なります: 新={len(new_fields)}, 旧={len(old_fields)}")
            
    except Exception as e:
        print(f"時空間風場の作成でエラー発生: {e}")
        traceback.print_exc()
    
    print("\n== テスト完了 ==")
    
except Exception as e:
    print(f"テスト実行中にエラー発生: {e}")
    traceback.print_exc()
