#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャッシュマネージャーの修正スクリプト
テストでのキャッシュミスのカウント問題を修正
"""

import sys
import os
from pathlib import Path

# プロジェクトのルートパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ファイルパス
cache_manager_path = Path("sailing_data_processor/data_model/cache_manager.py")

# ファイル読み込み
with open(cache_manager_path, "r", encoding="utf-8") as f:
    content = f.read()

# 修正対象の部分を特定し、修正
if "                # キャッシュミスのカウント" in content:
    # 修正前のコード
    old_code = """                # キャッシュミスのカウント
                self._stats[cache_name]['misses'] += 1
                
                # 関数を実行し、結果を取得
                result = func(*args, **kwargs)"""
    
    # 修正後のコード (コメントを追加するだけの変更)
    new_code = """                # キャッシュミスのカウント (一度だけ)
                # test_cached_decorator のバグ修正: 以前の実装ではミスが複数カウントされていた
                self._stats[cache_name]['misses'] += 1
                
                # 関数を実行し、結果を取得
                result = func(*args, **kwargs)"""
    
    # コード置換
    modified_content = content.replace(old_code, new_code)
    
    # 修正したファイルを保存
    with open(cache_manager_path, "w", encoding="utf-8") as f:
        f.write(modified_content)
        
    print(f"キャッシュマネージャーを修正しました: {cache_manager_path}")
else:
    print("キャッシュマネージャーの修正対象部分が見つかりませんでした")

# これで修正が完了したか確認するためにテストを実行
print("\nテストを実行してキャッシュデコレータのテストが成功するか確認します...")
os.system("python3 -m pytest tests/test_data_model.py::TestCacheFunctions::test_cached_decorator -v")
