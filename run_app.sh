#!/bin/bash

# セーリング戦略分析システム起動スクリプト
# 使用方法: ./run_app.sh [環境]
# 環境: dev (開発環境) または prod (本番環境)、デフォルトは dev

# 実行環境の設定
ENV=${1:-dev}
echo "セーリング戦略分析システムを ${ENV} モードで起動します..."

# 環境変数の設定
if [ "$ENV" = "dev" ]; then
    export STREAMLIT_DEBUG=true
    export STREAMLIT_SERVER_PORT=8501
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    export STREAMLIT_THEME_BASE="light"
    export STREAMLIT_THEME_PRIMARY_COLOR="#1E88E5"
    export STREAMLIT_SERVER_HEADLESS=false
    export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
    echo "開発モード: デバッグ有効、ポート 8501、統計無効"
elif [ "$ENV" = "prod" ]; then
    export STREAMLIT_DEBUG=false
    export STREAMLIT_SERVER_PORT=8501
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    export STREAMLIT_THEME_BASE="light"
    export STREAMLIT_THEME_PRIMARY_COLOR="#1E88E5"
    export STREAMLIT_SERVER_HEADLESS=true
    export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
    echo "本番モード: デバッグ無効、ポート 8501、ヘッドレスモード有効"
else
    echo "エラー: 環境パラメータは 'dev' または 'prod' を指定してください"
    exit 1
fi

# アプリケーションの起動
echo "アプリケーションを起動しています..."
# Streamlit Cloudと互換性を持たせるためにstreamlit_app.pyを使用
python3 -m streamlit run streamlit_app.py

# エラーハンドリング
STATUS=$?
if [ $STATUS -ne 0 ]; then
    echo "エラー: アプリケーションの起動に失敗しました（コード: $STATUS）"
    echo "依存関係が正しくインストールされていることを確認してください:"
    echo "$ pip install -r requirements.txt"
    exit $STATUS
fi

exit 0
