@echo off
REM セーリング戦略分析システムのインストールスクリプト（Windows用）

echo セーリング戦略分析システムのインストールを開始します...

REM Pythonバージョンチェック
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo エラー: Python 3.8以上が必要です。
    exit /b 1
)

echo Pythonバージョンを確認しました。インストールを続行します...

REM 仮想環境の作成と有効化（オプション）
if not exist venv (
    echo 仮想環境を作成しています...
    python -m venv venv
    echo 仮想環境を作成しました。
)

echo 必要なパッケージをインストールしています...

REM パッケージのインストール
call venv\Scripts\activate.bat
pip install -e .

echo セーリング戦略分析システムのインストールが完了しました。
echo 使用方法: python -m sailing_data_processor

pause
