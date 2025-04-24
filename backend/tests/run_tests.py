#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックエンドサービス層のテスト実行スクリプト
"""

import os
import sys
import pytest

# 親ディレクトリをPYTHONPATHに追加（モジュールインポート用）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """テスト実行メイン関数"""
    # pytest引数
    args = [
        "-v",                   # 詳細出力
        "--no-header",          # ヘッダー非表示
        "tests/",               # テストディレクトリ
    ]
    
    # テスト実行
    result = pytest.main(args)
    
    return result

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
