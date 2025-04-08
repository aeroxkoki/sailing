#!/bin/bash

# セーリング戦略分析 - 共有機能デモ実行スクリプト

echo "セーリング戦略分析 - 共有機能デモ起動中..."

# Pythonコマンドの確認
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# 現在のディレクトリをリポジトリルートに変更
cd "$(dirname "$0")"

# Streamlitが存在するか確認
$PYTHON_CMD -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Streamlit がインストールされていません。インストールします..."
    $PYTHON_CMD -m pip install streamlit
fi

# デモ起動
$PYTHON_CMD -m streamlit run ui/demo_sharing.py
