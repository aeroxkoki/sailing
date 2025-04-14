@echo off
REM セーリング戦略分析システム MVPバージョン実行バッチファイル

REM カレントディレクトリをバッチファイルのあるディレクトリに変更
cd /d "%~dp0"

REM 環境変数の設定
set PYTHONPATH=%cd%;%PYTHONPATH%

REM アプリケーションの起動
echo セーリング戦略分析システム MVPを起動しています...
streamlit run ui/app_mvp.py %*
