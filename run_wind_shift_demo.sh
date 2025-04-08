#!/bin/bash
# 風向シフト分析デモの実行スクリプト

# 現在のディレクトリを取得
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Streamlitでアプリを起動
streamlit run "$DIR/ui/demo_wind_shift.py" "$@"
