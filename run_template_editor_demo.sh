#!/bin/bash

# カレントディレクトリをスクリプトの場所に変更
cd "$(dirname "$0")" || exit

# 環境設定
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 必要なディレクトリの作成
mkdir -p data/templates

echo "テンプレートエディタデモを起動します..."
python3 -m streamlit run ui/demo_template_editor.py

# エラーがあれば表示
if [ $? -ne 0 ]; then
    echo "エラーが発生しました。詳細は上記のメッセージを確認してください。"
    exit 1
fi
