# -*- coding: utf-8 -*-
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem

class TestWindFieldFusionSystem(unittest.TestCase):
    
    def setUp(self):
        self.fusion_system = WindFieldFusionSystem()
        self.base_time = datetime.now()
        self.boat_data = self._create_test_boat_data()
    
    def _create_test_boat_data(self):
        """複数艇のテストデータを生成"""
        boats_data = {}
        
        # 3隻分のデータを作成
        for boat_idx in range(3):
            boat_id = f"boat_{boat_idx}"
            data = []
            
            # 各艇に異なる基準位置を設定（より広い範囲に分散）
            base_lat = 35.4 + boat_idx * 0.1  # より大きな差
            base_lon = 139.7 + boat_idx * 0.1  # より大きな差
            
            # 各艇に若干異なる風向・風速を設定
            wind_dir = 90 + boat_idx * 10  # より大きな差
            wind_speed = 10 + boat_idx * 1.0  # より大きな差
            
            # 各艇の航跡を生成（8の字に近い動きを模擬）
            for i in range(20):  # ポイント数を増やす
                angle = i * 0.31  # 徐々に変化する角度
                time = self.base_time + timedelta(seconds=i*10)
                
                # 8の字を描くような位置の変化
                lat_offset = 0.005 * np.sin(angle)  # より大きなオフセット
                lon_offset = 0.005 * np.sin(angle * 2)  # より大きなオフセット
                
                # 風向・風速にも変動を追加
                dir_oscillation = np.sin(angle) * 5
                speed_oscillation = np.cos(angle) * 1.0
                
                data.append({
                    'timestamp': time,
                    'latitude': base_lat + lat_offset,
                    'longitude': base_lon + lon_offset,
                    'wind_direction': (wind_dir + dir_oscillation) % 360,  # 0-360の範囲に保証
                    'wind_speed_knots': max(0.5, wind_speed + speed_oscillation),  # 最小0.5ノット
                    'confidence': 0.8 - 0.1 * (boat_idx % 2)
                })
            
            boats_data[boat_id] = pd.DataFrame(data)
        
        return boats_data
    
    def test_update_with_boat_data(self):
        """艇データによる風の場更新機能のテスト"""
        result = self.fusion_system.update_with_boat_data(self.boat_data)
        
        # 風の場が生成されていることを確認
        self.assertIsNotNone(result)
        
        # 結果構造の確認
        self.assertIn('lat_grid', result)
        self.assertIn('lon_grid', result)
        self.assertIn('wind_direction', result)
        self.assertIn('wind_speed', result)
        self.assertIn('confidence', result)
        
        # 現在の風の場と最終更新時刻が更新されていることを確認
        self.assertIsNotNone(self.fusion_system.current_wind_field)
        self.assertIsNotNone(self.fusion_system.last_fusion_time)
        
        # 風の場履歴が更新されていることを確認
        self.assertEqual(len(self.fusion_system.wind_field_history), 1)
    
    def test_predict_wind_field(self):
        """将来の風の場予測機能のテスト"""
        # まず現在データで更新
        self.fusion_system.update_with_boat_data(self.boat_data)
        
        # 5分後の風の場を予測
        future_time = self.base_time + timedelta(minutes=5)
        prediction = self.fusion_system.predict_wind_field(future_time)
        
        # 予測結果の構造確認
        self.assertIsNotNone(prediction)
        self.assertIn('lat_grid', prediction)
        self.assertIn('wind_direction', prediction)
        self.assertIn('time', prediction)
        
        # 予測時間が要求時間と一致することを確認
        self.assertEqual(prediction['time'], future_time)
    
    def test_spatial_consistency(self):
        """風の場の空間的一貫性のテスト"""
        # 艇データで更新
        self.fusion_system.update_with_boat_data(self.boat_data)
        wind_field = self.fusion_system.current_wind_field
        
        # 風の場が合理的な空間的連続性を持つことを確認
        grid_shape = wind_field['wind_direction'].shape
        
        for i in range(1, grid_shape[0]-1):
            for j in range(1, grid_shape[1]-1):
                # 隣接格子点の風向を取得
                center_dir = wind_field['wind_direction'][i, j]
                adjacent_dirs = [
                    wind_field['wind_direction'][i-1, j],
                    wind_field['wind_direction'][i+1, j],
                    wind_field['wind_direction'][i, j-1],
                    wind_field['wind_direction'][i, j+1]
                ]
                
                # 最大風向差を計算
                max_diff = max(abs(self._angle_difference(center_dir, adj_dir)) 
                               for adj_dir in adjacent_dirs)
                
                # 隣接点での風向変化は急激であるべきではない
                self.assertLess(max_diff, 15)
    
    def _angle_difference(self, a, b):
        """2つの角度間の最小差分を計算（度）"""
        return ((a - b + 180) % 360) - 180

if __name__ == '__main__':
    try:
        # まずテストオブジェクトを作成してみる
        test = TestWindFieldFusionSystem()
        test.setUp()
        print("SetUp successful")
        
        # 最初のテストを実行してみる
        print("Running first test...")
        test.test_update_with_boat_data()
        print("First test passed!")
        
        # 二番目のテストを実行してみる
        print("Running second test...")
        test.test_predict_wind_field()
        print("Second test passed!")
        
        # 三番目のテストを実行してみる
        print("Running third test...")
        test.test_spatial_consistency()
        print("All individual tests passed!")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
    
    # 通常のテスト実行
    # unittest.main()
