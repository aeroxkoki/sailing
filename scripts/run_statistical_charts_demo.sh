#!/bin/bash

# 統計分析チャートデモアプリの実行スクリプト

echo "セーリング分析統計チャートデモアプリケーションを起動します..."
echo "Streamlitを使用して、統計分析チャート要素の表示テストを行います。"

# 現在のディレクトリを保存
CURR_DIR=$(pwd)

# スクリプトのあるディレクトリに移動
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

# 環境変数設定
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Streamlitアプリを実行
python3 -m streamlit run ui/demo_statistical_charts.py "$@"

# 元のディレクトリに戻る
cd "$CURR_DIR"

echo "デモアプリケーションを終了しました。"
