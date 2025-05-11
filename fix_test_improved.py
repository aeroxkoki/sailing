#!/usr/bin/env python3

# test_wind_estimator_improved.pyのインポートエラーを修正

file_path = "tests/test_wind_estimator_improved.py"

# ファイルを読み込む
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# unittestモジュールのインポートを追加
if 'import unittest' not in content:
    # pytestの後にunittestを追加
    content = content.replace('import pytest', 'import pytest\nimport unittest')

# スキップデコレータを修正
content = content.replace('@unittest.skip("Method implementation not required for core functionality")',
                         '@pytest.mark.skip(reason="Method implementation not required for core functionality")')

# 修正した内容を書き戻す
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("test_wind_estimator_improved.py を修正しました！")
