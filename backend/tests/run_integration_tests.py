# -*- coding: utf-8 -*-
"""
統合テスト実行スクリプト
"""

import os
import sys
import pytest

def main():
    """統合テストを実行"""
    print("セーリング戦略分析システム 統合テスト実行")
    print("=" * 50)
    
    # テストディレクトリ
    test_dir = os.path.join(os.path.dirname(__file__), "integration")
    
    # pytest引数
    pytest_args = [
        test_dir,
        "-v",
        "--no-header",
    ]
    
    # テスト実行
    result = pytest.main(pytest_args)
    
    # 結果に応じた終了コード
    sys.exit(result)

if __name__ == "__main__":
    main()