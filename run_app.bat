@echo off
REM セーリング戦略分析システム起動スクリプト（Windows用）
REM 使用方法: run_app.bat [環境]
REM 環境: dev (開発環境) または prod (本番環境)、デフォルトは dev

REM 実行環境の設定
SET ENV=%1
IF "%ENV%"=="" SET ENV=dev
echo セーリング戦略分析システムを %ENV% モードで起動します...

REM 環境変数の設定
IF /I "%ENV%"=="dev" (
    SET STREAMLIT_DEBUG=true
    SET STREAMLIT_SERVER_PORT=8501
    SET STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    SET STREAMLIT_THEME_BASE=light
    SET STREAMLIT_THEME_PRIMARY_COLOR=#1E88E5
    SET STREAMLIT_SERVER_HEADLESS=false
    SET STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
    echo 開発モード: デバッグ有効、ポート 8501、統計無効
) ELSE IF /I "%ENV%"=="prod" (
    SET STREAMLIT_DEBUG=false
    SET STREAMLIT_SERVER_PORT=8501
    SET STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    SET STREAMLIT_THEME_BASE=light
    SET STREAMLIT_THEME_PRIMARY_COLOR=#1E88E5
    SET STREAMLIT_SERVER_HEADLESS=true
    SET STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
    echo 本番モード: デバッグ無効、ポート 8501、ヘッドレスモード有効
) ELSE (
    echo エラー: 環境パラメータは 'dev' または 'prod' を指定してください
    exit /b 1
)

REM アプリケーションの起動
echo アプリケーションを起動しています...
REM Streamlit Cloudと互換性を持たせるためにstreamlit_app.pyを使用
python -m streamlit run streamlit_app.py

REM エラーハンドリング
IF %ERRORLEVEL% NEQ 0 (
    echo エラー: アプリケーションの起動に失敗しました（コード: %ERRORLEVEL%）
    echo 依存関係が正しくインストールされていることを確認してください:
    echo pip install -r requirements.txt
    exit /b %ERRORLEVEL%
)

exit /b 0
