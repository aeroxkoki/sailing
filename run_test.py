#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from tests.test_data_model import TestCacheFunctions

if __name__ == "__main__":
    # 特定のテストメソッドだけ実行
    suite = unittest.TestSuite()
    suite.addTest(TestCacheFunctions("test_cached_decorator"))
    suite.addTest(TestCacheFunctions("test_memoize_decorator"))
    suite.addTest(TestCacheFunctions("test_cache_ttl"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"テスト結果: 成功={result.testsRun - len(result.errors) - len(result.failures)}, 失敗={len(result.failures)}, エラー={len(result.errors)}")
    
    # 失敗とエラーの詳細を表示
    if result.failures:
        print("\n失敗したテスト:")
        for failure in result.failures:
            print(f"{failure[0]}")
            print(f"{failure[1]}")
    
    if result.errors:
        print("\nエラーが発生したテスト:")
        for error in result.errors:
            print(f"{error[0]}")
            print(f"{error[1]}")
