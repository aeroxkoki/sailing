#!/bin/bash

# セッションリスト表示のデモ実行スクリプト
echo "セッションリスト表示デモを起動しています..."

# カレントディレクトリをスクリプトのディレクトリに変更
cd "$(dirname "$0")"

# Streamlitでデモスクリプトを実行
python3 -m streamlit run ui/demo_session_list.py
