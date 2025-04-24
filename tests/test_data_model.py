# -*- coding: utf-8 -*-
"""
データモデルとキャッシュ機能のテスト
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from sailing_data_processor.data_model import (
    DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer,
    cached, memoize, clear_cache, get_cache_stats
)

class TestDataContainer(unittest.TestCase):
    """DataContainerの基本機能テスト"""
    
    def test_init(self):
        """初期化テスト"""
        data = {"test": "value"}
        container = DataContainer(data)
        
        self.assertEqual(container.data, data)
        self.assertIn('created_at', container.metadata)
        self.assertIn('updated_at', container.metadata)
    
    def test_metadata(self):
        """メタデータテスト"""
        container = DataContainer([1, 2, 3])
        
        # メタデータの追加
        container.add_metadata('test_key', 'test_value')
        self.assertEqual(container.get_metadata('test_key'), 'test_value')
        
        # 存在しないキーのデフォルト値
        self.assertEqual(container.get_metadata('non_existent', 'default'), 'default')
    
    def test_apply(self):
        """apply機能テスト"""
        container = DataContainer([1, 2, 3])
        
        # 関数を適用
        def double(x):
            return [i * 2 for i in x]
        
        result = container.apply(double)
        
        self.assertEqual(result.data, [2, 4, 6])
        self.assertEqual(result, container)  # 同じインスタンスが返される
        self.assertEqual(result.get_metadata('processed_by'), 'double')
    
    def test_to_dict(self):
        """辞書変換テスト"""
        container = DataContainer([1, 2, 3], {'custom': 'metadata'})
        
        result = container.to_dict()
        
        self.assertEqual(result['data'], [1, 2, 3])
        self.assertEqual(result['metadata']['custom'], 'metadata')
        self.assertEqual(result['type'], 'DataContainer')
    
    def test_to_json(self):
        """JSON変換テスト"""
        container = DataContainer([1, 2, 3])
        
        json_str = container.to_json()
        
        self.assertIn('"data": [1, 2, 3]', json_str)
        self.assertIn('"type": "DataContainer"', json_str)


class TestGPSDataContainer(unittest.TestCase):
    """GPSDataContainerのテスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        # テスト用GPSデータ
        self.df = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-01-01', periods=5, freq='1min'),
            'latitude': [35.6, 35.601, 35.602, 35.603, 35.604],
            'longitude': [139.7, 139.701, 139.702, 139.703, 139.704],
            'speed': [5.0, 5.2, 5.1, 5.3, 5.4],
            'course': [90.0, 91.0, 92.0, 93.0, 94.0]
        })
    
    def test_init(self):
        """初期化テスト"""
        container = GPSDataContainer(self.df)
        
        self.assertEqual(len(container.data), 5)
        self.assertIn('time_range', container.metadata)
    
    def test_validation(self):
        """データ検証テスト"""
        container = GPSDataContainer(self.df)
        self.assertTrue(container.validate())
        
        # 必須カラムのないデータフレーム
        with self.assertRaises(ValueError):
            invalid_df = pd.DataFrame({'a': [1, 2, 3]})
            GPSDataContainer(invalid_df)
    
    def test_filter_time_range(self):
        """時間範囲フィルタリングテスト"""
        container = GPSDataContainer(self.df)
        
        start_time = self.df['timestamp'][1]
        end_time = self.df['timestamp'][3]
        
        filtered = container.filter_time_range(start_time, end_time)
        
        self.assertEqual(len(filtered.data), 3)
        self.assertEqual(filtered.data.iloc[0]['timestamp'], start_time)
        self.assertEqual(filtered.data.iloc[-1]['timestamp'], end_time)
    
    def test_to_numpy(self):
        """NumPy変換テスト"""
        container = GPSDataContainer(self.df)
        
        result = container.to_numpy()
        
        self.assertIn('timestamps', result)
        self.assertIn('latitudes', result)
        self.assertIn('longitudes', result)
        self.assertIn('speed', result)
        self.assertIn('course', result)
        
        self.assertEqual(len(result['latitudes']), 5)
        

class TestWindDataContainer(unittest.TestCase):
    """WindDataContainerのテスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        self.wind_data = {
            'direction': 45.0,
            'speed': 10.0,
            'timestamp': datetime.now(),
            'confidence': 0.8
        }
    
    def test_init(self):
        """初期化テスト"""
        container = WindDataContainer(self.wind_data)
        
        self.assertEqual(container.direction, 45.0)
        self.assertEqual(container.speed, 10.0)
        self.assertEqual(container.confidence, 0.8)
    
    def test_validation(self):
        """データ検証テスト"""
        container = WindDataContainer(self.wind_data)
        self.assertTrue(container.validate())
        
        # 必須キーのないデータ
        with self.assertRaises(ValueError):
            invalid_data = {'speed': 10.0}
            WindDataContainer(invalid_data)
    
    def test_to_vector(self):
        """ベクトル変換テスト"""
        container = WindDataContainer(self.wind_data)
        
        vector = container.to_vector()
        
        # 方位45度、風速10ノットの場合のベクトル
        self.assertAlmostEqual(vector[0], 10.0 * np.cos(np.radians(45)), places=5)
        self.assertAlmostEqual(vector[1], 10.0 * np.sin(np.radians(45)), places=5)
    
    def test_from_vector(self):
        """ベクトルからの生成テスト"""
        vector = np.array([7.07, 7.07])  # 約45度、風速10ノットに相当
        timestamp = datetime.now()
        
        container = WindDataContainer.from_vector(vector, timestamp, 0.9)
        
        self.assertAlmostEqual(container.direction, 45.0, places=0)
        self.assertAlmostEqual(container.speed, 10.0, places=1)
        self.assertEqual(container.confidence, 0.9)


class TestStrategyPointContainer(unittest.TestCase):
    """StrategyPointContainerのテスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        self.point_data = {
            'type': 'tack',
            'position': {
                'latitude': 35.6,
                'longitude': 139.7
            },
            'timestamp': datetime.now(),
            'importance': 0.7,
            'details': {
                'wind_direction': 45.0,
                'bearing_change': 90.0
            }
        }
    
    def test_init(self):
        """初期化テスト"""
        container = StrategyPointContainer(self.point_data)
        
        self.assertEqual(container.point_type, 'tack')
        self.assertEqual(container.latitude, 35.6)
        self.assertEqual(container.longitude, 139.7)
        self.assertEqual(container.importance, 0.7)
    
    def test_validation(self):
        """データ検証テスト"""
        container = StrategyPointContainer(self.point_data)
        self.assertTrue(container.validate())
        
        # 必須キーのないデータ
        with self.assertRaises(ValueError):
            invalid_data = {'type': 'tack'}
            StrategyPointContainer(invalid_data)
    
    def test_from_coordinates(self):
        """座標からの生成テスト"""
        timestamp = datetime.now()
        
        container = StrategyPointContainer.from_coordinates(
            'layline', 35.6, 139.7, timestamp, 0.8,
            details={'angle': 30.0}
        )
        
        self.assertEqual(container.point_type, 'layline')
        self.assertEqual(container.latitude, 35.6)
        self.assertEqual(container.longitude, 139.7)
        self.assertEqual(container.importance, 0.8)
        self.assertEqual(container.data['details']['angle'], 30.0)


class TestCacheFunctions(unittest.TestCase):
    """キャッシュ機能のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用のキャッシュをクリア
        clear_cache('test_cache')
        
        # 呼び出し回数を記録する変数
        self.call_count = 0
    
    def test_cached_decorator(self):
        """@cached デコレータのテスト"""
        
        @cached('test_cache')
        def expensive_func(x):
            self.call_count += 1
            return x * 2
        
        # 一度目の呼び出し - キャッシュミス
        result1 = expensive_func(5)
        self.assertEqual(result1, 10)
        self.assertEqual(self.call_count, 1)
        
        # 同じ引数での二度目の呼び出し - キャッシュヒット
        result2 = expensive_func(5)
        self.assertEqual(result2, 10)
        self.assertEqual(self.call_count, 1)  # 関数は実行されていない
        
        # 異なる引数での呼び出し - キャッシュミス
        result3 = expensive_func(10)
        self.assertEqual(result3, 20)
        self.assertEqual(self.call_count, 2)
        
        # 統計情報の確認
        stats = get_cache_stats('test_cache')
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 2)
    
    def test_memoize_decorator(self):
        """@memoize デコレータのテスト"""
        
        @memoize
        def fib(n):
            self.call_count += 1
            if n <= 1:
                return n
            return fib(n-1) + fib(n-2)
        
        # フィボナッチ数列の計算 - メモ化により効率的に計算される
        result = fib(10)
        self.assertEqual(result, 55)
        
        # 実際の関数呼び出し回数の確認 (メモ化なしだと177回になるはず)
        self.assertLess(self.call_count, 20)
    
    def test_cache_ttl(self):
        """キャッシュのTTL（有効期限）テスト"""
        
        @cached('test_cache', ttl=0.1)  # 100ミリ秒のTTL
        def short_lived(x):
            self.call_count += 1
            return x * 2
        
        # 一度目の呼び出し
        result1 = short_lived(5)
        self.assertEqual(result1, 10)
        self.assertEqual(self.call_count, 1)
        
        # すぐに二度目の呼び出し - キャッシュヒット
        result2 = short_lived(5)
        self.assertEqual(result2, 10)
        self.assertEqual(self.call_count, 1)
        
        # TTL経過後の呼び出し - キャッシュミス
        time.sleep(0.2)
        result3 = short_lived(5)
        self.assertEqual(result3, 10)
        self.assertEqual(self.call_count, 2)


if __name__ == '__main__':
    unittest.main()
