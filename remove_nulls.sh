#!/bin/bash
# このスクリプトはPythonファイル内のnull文字を削除します

# Pythonファイルを検索
find_cmd="find backend -name \"*.py\" -print0"

# 各ファイルからnull文字を削除
$find_cmd | xargs -0 -I{} sh -c 'cat "{}" | tr -d "\000" > temp_file && mv temp_file "{}"'

echo "Nullバイトを削除しました"

# 確認のためにnull文字を含むファイルを再検索
null_files=$(find backend -name "*.py" -print0 | xargs -0 grep -l "$(printf '\0')" 2>/dev/null || echo "")

if [ -z "$null_files" ]; then
    echo "すべてのファイルからnullバイトが削除されました"
else
    echo "まだnullバイトが含まれているファイル:"
    echo "$null_files"
fi
