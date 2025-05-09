#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
詳細なデバッグ情報を出力するテストスクリプト
"""

import unittest
import sys
import time
from sailing_data_processor.data_model.cache_manager import cached, clear_cache, get_cache_stats, CacheManager

def print_debug(msg):
    """デバッグメッセージを出力"""
    print(f"DEBUG: {msg}")

class TestCacheDebug(unittest.TestCase):
    """キャッシュ機能の詳細デバッグテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        print_debug("setUp: キャッシュをクリア")
        clear_cache('test_cache')
        
        # 内部キャッシュ状態を確認
        manager = CacheManager()
        print_debug(f"キャッシュマネージャー状態: _caches={manager._caches}, _stats={manager._stats}")
        
        # 呼び出し回数を記録する変数
        self.call_count = 0
    
    def test_cached_decorator(self):
        """@cached デコレータのテスト"""
        print_debug("\n--- test_cached_decorator 開始 ---")
        
        # デコレータ関数を定義
        @cached('test_cache')
        def expensive_func(x):
            self.call_count += 1
            print_debug(f"expensive_func 実行: x={x}, call_count={self.call_count}")
            return x * 2
        
        # 一度目の呼び出し - キャッシュミス
        print_debug("\n--- 一度目の呼び出し (x=5) ---")
        result1 = expensive_func(5)
        print_debug(f"結果: {result1}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print_debug(f"キャッシュ統計: {stats}")
        
        # 内部キャッシュ状態を確認
        manager = CacheManager()
        cache = manager._caches.get('test_cache', {})
        print_debug(f"test_cache内容: {cache}")
        
        # 同じ引数での二度目の呼び出し - キャッシュヒット
        print_debug("\n--- 二度目の呼び出し (x=5) ---")
        result2 = expensive_func(5)
        print_debug(f"結果: {result2}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print_debug(f"キャッシュ統計: {stats}")
        
        # 異なる引数での呼び出し - キャッシュミス
        print_debug("\n--- 三度目の呼び出し (x=10) ---")
        result3 = expensive_func(10)
        print_debug(f"結果: {result3}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print_debug(f"キャッシュ統計: {stats}")
        
        # 検証
        print_debug("\n--- 検証 ---")
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 10)
        self.assertEqual(result3, 20)
        
        print_debug(f"call_count = {self.call_count}, expecting 2")
        self.assertEqual(self.call_count, 2, f"呼び出し回数が2回になるはずが{self.call_count}回になっています")
        
        stats = get_cache_stats('test_cache')
        print_debug(f"最終キャッシュ統計: {stats}")
        print_debug(f"期待値: hits=1, misses=2")
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 2)
        
        print_debug("--- test_cached_decorator 終了 ---\n")
    
    def test_cache_ttl(self):
        """キャッシュのTTL（有効期限）テスト"""
        print_debug("\n--- test_cache_ttl 開始 ---")
        
        @cached('test_cache', ttl=0.1)  # 100ミリ秒のTTL
        def short_lived(x):
            self.call_count += 1
            print_debug(f"short_lived 実行: x={x}, call_count={self.call_count}")
            return x * 2
        
        # 一度目の呼び出し
        print_debug("\n--- 一度目の呼び出し (x=5) ---")
        result1 = short_lived(5)
        print_debug(f"結果: {result1}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print_debug(f"キャッシュ統計: {stats}")
        
        # すぐに二度目の呼び出し - キャッシュヒット
        print_debug("\n--- 二度目の呼び出し (x=5) ---")
        result2 = short_lived(5)
        print_debug(f"結果: {result2}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print_debug(f"キャッシュ統計: {stats}")
        
        # TTL経過後の呼び出し - キャッシュミス
        print_debug("\n--- TTL待機中... ---")
        time.sleep(0.2)
        print_debug("\n--- 三度目の呼び出し (TTL経過後, x=5) ---")
        result3 = short_lived(5)
        print_debug(f"結果: {result3}, 呼び出し回数: {self.call_count}")
        stats = get_cache_stats('test_cache')
        print_debug(f"キャッシュ統計: {stats}")
        
        # 検証
        print_debug("\n--- 検証 ---")
        self.assertEqual(result1, 10)
        self.assertEqual(result2, 10)
        self.assertEqual(result3, 10)
        
        print_debug(f"call_count = {self.call_count}, expecting 2")
        # 1回目の呼び出しと、TTL経過後の呼び出しの2回のみ関数が実行されるべき
        self.assertEqual(self.call_count, 2, f"呼び出し回数が2回になるはずが{self.call_count}回になっています")
        
        print_debug("--- test_cache_ttl 終了 ---\n")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
