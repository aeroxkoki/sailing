#!/bin/bash

# データ処理デモアプリの実行スクリプト

echo "セーリングデータ処理デモアプリケーションを起動します..."
echo "Streamlitを使用して、データ処理機能の表示テストを行います。"

# 現在のディレクトリを保存
CURR_DIR=$(pwd)

# スクリプトのあるディレクトリに移動
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

# 環境変数設定
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Streamlitアプリを実行
python3 -m streamlit run ui/demo_data_processing.py "$@"

# 元のディレクトリに戻る
cd "$CURR_DIR"

echo "デモアプリケーションを終了しました。"
