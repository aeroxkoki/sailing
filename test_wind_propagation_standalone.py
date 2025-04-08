#!/usr/bin/env python3
"""
WindPropagationModelの独立したテストスクリプト
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ここで必要なモジュールを直接インポート
from sailing_data_processor.wind_propagation_model import WindPropagationModel

class TestWindPropagationModel(unittest.TestCase):
    
    def setUp(self):
        self.model = WindPropagationModel()
        self.base_time = datetime.now()
        self.standard_wind_data = self._create_standard_wind_data()
        
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

if __name__ == '__main__':
    unittest.main()
