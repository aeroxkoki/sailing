#!/bin/bash

# セーリング戦略分析システム MVPバージョン実行スクリプト

# カレントディレクトリをスクリプトのあるディレクトリに変更
cd "$(dirname "$0")"

# 環境変数の設定
export PYTHONPATH="$(pwd):$PYTHONPATH"

# アプリケーションの起動
echo "セーリング戦略分析システム MVPを起動しています..."
streamlit run ui/app_mvp.py "$@"
