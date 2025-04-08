@echo off
REM セーリング戦略分析システム テスト実行スクリプト (Windows版)
REM このスクリプトはプロジェクトのテストを一括で実行します

echo =====================================================
echo   セーリング戦略分析システム テスト実行スクリプト  
echo =====================================================
echo.

REM 現在のディレクトリを保存
set ORIGINAL_DIR=%CD%

REM スクリプトのあるディレクトリに移動
cd /d "%~dp0"
set PROJECT_ROOT=%CD%

REM PYTHONPATHの設定
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%

echo テスト環境情報:
echo Project Root: %PROJECT_ROOT%
echo Python Path: %PYTHONPATH%
python --version

REM テスト結果のカウンター
set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

REM 基本インポートテスト
echo.
echo ====================================================
echo 基本インポートテスト
echo ====================================================
python test_import.py
if %ERRORLEVEL% EQU 0 (
    set /a TOTAL_TESTS+=1
    set /a PASSED_TESTS+=1
    echo [OK] 基本インポートテスト ... 成功
) else (
    set /a TOTAL_TESTS+=1
    set /a FAILED_TESTS+=1
    echo [NG] 基本インポートテスト ... 失敗
)

REM スタンドアロンテスト
echo.
echo ====================================================
echo スタンドアロンテスト
echo ====================================================

REM スタンドアロンテストディレクトリの確認
if exist standalone_tests (
    REM スタンドアロンテストの実行
    for %%F in (standalone_tests\test_*.py) do (
        echo 実行中: %%~nF
        python "%%F"
        if %ERRORLEVEL% EQU 0 (
            set /a TOTAL_TESTS+=1
            set /a PASSED_TESTS+=1
            echo [OK] %%~nF ... 成功
        ) else (
            set /a TOTAL_TESTS+=1
            set /a FAILED_TESTS+=1
            echo [NG] %%~nF ... 失敗
        )
    )
) else (
    echo スタンドアロンテストディレクトリが見つかりません
)

REM PyTestの実行（インストールされている場合）
echo.
echo ====================================================
echo PyTestテスト
echo ====================================================
python -m pytest -v
echo 注意: PyTest結果は集計に含まれていません

REM 結果のサマリー
echo.
echo ====================================================
echo テスト結果サマリー
echo ====================================================
echo 総テスト数: %TOTAL_TESTS%
echo 成功: %PASSED_TESTS%
echo 失敗: %FAILED_TESTS%

REM 成功率の計算と表示
if %TOTAL_TESTS% GTR 0 (
    set /a SUCCESS_RATE=PASSED_TESTS * 100 / TOTAL_TESTS
    echo 成功率: %SUCCESS_RATE%%%
    
    REM 全テスト成功時のメッセージ
    if %FAILED_TESTS% EQU 0 (
        echo すべてのテストが成功しました！
    )
) else (
    echo テストは実行されませんでした
)

REM 元のディレクトリに戻る
cd /d "%ORIGINAL_DIR%"

REM 一時停止（結果を確認できるように）
pause
