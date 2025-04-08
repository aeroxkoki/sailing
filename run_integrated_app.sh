#!/bin/bash

# セーリング戦略分析システム - 統合アプリケーション実行スクリプト

# スクリプトが存在するディレクトリに移動
cd "$(dirname "$0")"

# 環境変数の設定
export PYTHONPATH=$(pwd):$PYTHONPATH
export STREAMLIT_THEME_BASE="light"
export STREAMLIT_THEME_PRIMARY_COLOR="#1E88E5"
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 実行前の確認メッセージ
echo "セーリング戦略分析システム - 統合アプリケーションを起動します..."
echo "アプリケーションURL: http://localhost:8501"
echo ""

# Streamlitアプリケーションの実行
python3 -m streamlit run ui/app_integrated.py "$@"

# エラーハンドリング
if [ $? -ne 0 ]; then
    echo "エラー: アプリケーションの実行に失敗しました。"
    echo "以下を確認してください:"
    echo "- Python環境が正しく設定されているか"
    echo "- 必要なパッケージがインストールされているか"
    echo "- ui/app_integrated.py ファイルが存在するか"
    exit 1
fi
