#!/bin/bash

# デモアプリケーションを実行するスクリプト
# マップレイヤー管理とデータ連携機能のデモを起動します

# プロジェクトのルートディレクトリに移動
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Streamlitでデモアプリケーションを起動
echo "マップレイヤー管理とデータ連携機能のデモを起動しています..."
streamlit run ui/demo_map_layers.py
