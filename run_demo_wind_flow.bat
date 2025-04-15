@echo off
REM セーリング戦略分析システム - 風向風速表示デモ実行スクリプト

REM プロジェクトのルートディレクトリへ移動
cd /d "%~dp0"

REM 必要な環境変数を設定
set PYTHONPATH=%cd%

REM Streamlitを使用してデモを実行
echo 風向風速表示デモを起動します...
python -m streamlit run ui/demo/wind_flow_demo.py --server.port=8501
