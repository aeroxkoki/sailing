# -*- coding: utf-8 -*-
import unittest
import numpy as np
from datetime import datetime, timedelta
from sailing_data_processor.wind_propagation_model import WindPropagationModel

class TestWindPropagationModel(unittest.TestCase):
    
    def setUp(self):
        self.model = WindPropagationModel()
        self.base_time = datetime.now()
        self.standard_wind_data = self._create_standard_wind_data()
        self.complex_wind_data = self._create_complex_wind_data()
        self.varying_speed_data = self._create_varying_speed_data()
        
    def _create_standard_wind_data(self):
        """標準的な風の移動パターン（風速の60%で風向方向に移動）"""
        data = []
        base_lat, base_lon = 35.4, 139.7
        wind_dir, wind_speed = 90, 10  # 東風、10ノット
        
        for i in range(10):
            time = self.base_time + timedelta(seconds=i*5)
            lon_offset = 0.000139 * i  # 5秒間の東方向移動量
            
            data.append({
                'timestamp': time,
                'latitude': base_lat,
                'longitude': base_lon + lon_offset,
                'wind_direction': wind_dir,
                'wind_speed': wind_speed
            })
        return data
    
    def _create_complex_wind_data(self):
        """コリオリ効果を含む複雑な風パターン（風向から15度ずれた方向へ移動）"""
        data = []
        base_lat, base_lon = 35.5, 139.6
        wind_dir, wind_speed = 90, 12
        propagation_angle = 105  # 15度ずれ
        
        for i in range(10):
            time = self.base_time + timedelta(seconds=i*5)
            propagation_rad = np.radians(propagation_angle)
            lon_offset = 0.000150 * i * np.cos(propagation_rad)
            lat_offset = 0.000150 * i * np.sin(propagation_rad)
            
            data.append({
                'timestamp': time,
                'latitude': base_lat + lat_offset,
                'longitude': base_lon + lon_offset,
                'wind_direction': wind_dir,
                'wind_speed': wind_speed
            })
        return data
        
    def _create_varying_speed_data(self):
        """風速が変化するデータ（5～14ノット）"""
        data = []
        base_lat, base_lon = 35.6, 139.5
        wind_dir = 45
        
        for i in range(10):
            time = self.base_time + timedelta(seconds=i*5)
            wind_speed = 5 + i
            propagation_rad = np.radians(wind_dir)
            speed_factor = 0.6 * wind_speed / 10
            lon_offset = 0.000150 * i * speed_factor * np.cos(propagation_rad)
            lat_offset = 0.000150 * i * speed_factor * np.sin(propagation_rad)
            
            data.append({
                'timestamp': time,
                'latitude': base_lat + lat_offset,
                'longitude': base_lon + lon_offset,
                'wind_direction': wind_dir,
                'wind_speed': wind_speed
            })
        return data
    
    def test_estimate_propagation_vector_standard(self):
        """標準的な風データでの移動ベクトル推定をテスト"""
        result = self.model.estimate_propagation_vector(self.standard_wind_data)
        
        # 結果構造の確認
        self.assertIn('speed', result)
        self.assertIn('direction', result)
        self.assertIn('confidence', result)
        
        # 風向(90°)に近い方向で、風速の約60%の速度を期待
        expected_direction = 90
        expected_speed = 10 * 0.6 * 0.51444  # ノットからm/sへ変換
        
        self.assertAlmostEqual(result['direction'], expected_direction, delta=20)
        self.assertAlmostEqual(result['speed'], expected_speed, delta=1.0)
    
    def test_estimate_propagation_vector_complex(self):
        """コリオリ効果を含む風データでのテスト"""
        result = self.model.estimate_propagation_vector(self.complex_wind_data)
        
        # コリオリ効果により風向から約15度ずれた方向(105°)を期待
        expected_direction = 105
        expected_speed = 12 * 0.6 * 0.51444
        
        self.assertAlmostEqual(result['direction'], expected_direction, delta=25)
    
    def test_wind_speed_factor_adjustment(self):
        """風速に基づく係数調整のテスト"""
        # 低風速データ（5ノット）
        low_wind_data = [{'wind_speed': 5} for _ in range(5)]
        low_factor = self.model._adjust_wind_speed_factor(low_wind_data)
        self.assertLessEqual(low_factor, self.model.wind_speed_factor)
        
        # 高風速データ（16ノット）
        high_wind_data = [{'wind_speed': 16} for _ in range(5)]
        high_factor = self.model._adjust_wind_speed_factor(high_wind_data)
        self.assertGreaterEqual(high_factor, self.model.wind_speed_factor)
    
    def test_propagation_uncertainty(self):
        """距離・時間による不確実性の増加をテスト"""
        base_uncertainty = 0.5
        
        # 近距離・短時間の予測
        near_uncertainty = self.model._calculate_propagation_uncertainty(100, 60, base_uncertainty)
        
        # 遠距離・長時間の予測
        far_uncertainty = self.model._calculate_propagation_uncertainty(1000, 600, base_uncertainty)
        
        # 遠距離・長時間の方が不確実性は高くなるはず
        self.assertGreater(far_uncertainty, near_uncertainty)
        
    def test_predict_future_wind(self):
        """将来の風状況予測をテスト"""
        # 過去データ
        historical_data = self.standard_wind_data
        
        # 将来位置と時間
        future_pos = (35.41, 139.72)
        future_time = self.base_time + timedelta(minutes=5)
        
        # 予測実行
        prediction = self.model.predict_future_wind(future_pos, future_time, historical_data)
        
        # 結果構造の確認
        self.assertIn('wind_direction', prediction)
        self.assertIn('wind_speed', prediction)
        self.assertIn('confidence', prediction)
        
        # 信頼度は0-1の間
        self.assertGreaterEqual(prediction['confidence'], 0)
        self.assertLessEqual(prediction['confidence'], 1)

if __name__ == '__main__':
    unittest.main()
