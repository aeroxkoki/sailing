#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
from sailing_data_processor.data_model.cache_manager import cached, clear_cache, get_cache_stats

class TestCacheDirectly(unittest.TestCase):
    """キャッシュ機能の直接テスト"""
    
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
            print(f"関数実行: x={x}, call_count={self.call_count}")
            return x * 2
        
        # 一度目の呼び出し - キャッシュミス
        print("\n--- 一度目の呼び出し (x=5) ---")
        result1 = expensive_func(5)
        print(f"結果: {result1}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print(f"キャッシュ統計: {stats}")
        
        # 同じ引数での二度目の呼び出し - キャッシュヒット
        print("\n--- 二度目の呼び出し (x=5) ---")
        result2 = expensive_func(5)
        print(f"結果: {result2}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print(f"キャッシュ統計: {stats}")
        
        # 異なる引数での呼び出し - キャッシュミス
        print("\n--- 三度目の呼び出し (x=10) ---")
        result3 = expensive_func(10)
        print(f"結果: {result3}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print(f"キャッシュ統計: {stats}")
        
        # テスト検証
        print("\n--- テスト検証 ---")
        try:
            self.assertEqual(self.call_count, 2)
            print("テスト成功: 呼び出し回数は2回")
        except AssertionError as e:
            print(f"テスト失敗: {e}")
        
        try:
            stats = get_cache_stats('test_cache')
            self.assertEqual(stats['hits'], 1)
            self.assertEqual(stats['misses'], 2)
            print("テスト成功: hits=1, misses=2")
        except AssertionError as e:
            print(f"テスト失敗: {e}")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
