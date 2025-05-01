#!/bin/bash
# セーリング戦略分析システムのインストールスクリプト

echo "セーリング戦略分析システムのインストールを開始します..."

# プロジェクトルートへの移動
cd "$(dirname "$0")"

# Pythonバージョンチェック
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "エラー: Python 3.8以上が必要です。現在のバージョン: $python_version"
    exit 1
fi

echo "Python $python_version が検出されました。インストールを続行します..."

# 仮想環境の作成と有効化（オプション）
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
    echo "仮想環境を作成しました。"
fi

echo "必要なパッケージをインストールしています..."

# パッケージのインストール
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    source venv/bin/activate
    pip install -e .
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # Linux
    source venv/bin/activate
    pip install -e .
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    # Windows
    venv/Scripts/activate
    pip install -e .
else
    echo "未対応のOSです。手動でインストールしてください。"
    echo "コマンド: pip install -e ."
    exit 1
fi

echo "セーリング戦略分析システムのインストールが完了しました。"
echo "使用方法: python -m sailing_data_processor"
