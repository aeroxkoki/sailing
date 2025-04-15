#!/bin/bash

# セーリング戦略分析システム - 風向風速表示デモ実行スクリプト

# プロジェクトのルートディレクトリへ移動
cd "$(dirname "$0")"

# 必要な環境変数を設定
export PYTHONPATH="$(pwd)"

# Streamlitを使用してデモを実行
echo "風向風速表示デモを起動します..."
python3 -m streamlit run ui/demo/wind_flow_demo.py --server.port=8501
