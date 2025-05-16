#!/bin/bash

# スクリプトが存在するディレクトリをプロジェクトルートとして使用
cd "$(dirname "$0")"

echo "Sailing Strategy Analyzer - 直接フロントエンドデプロイスクリプト"
echo "=========================================================="
echo ""

# フロントエンドディレクトリに移動
cd frontend

# Vercel CLI がインストールされているか確認
if ! command -v vercel &> /dev/null; then
    echo "Vercel CLI がインストールされていません。インストールします..."
    npm install -g vercel
fi

# Vercel にログイン (トークンがあればそれを使用)
echo "Vercel へのログインを確認しています..."
if [ -z "$VERCEL_TOKEN" ]; then
    vercel login
else
    echo "環境変数の VERCEL_TOKEN を使用します"
fi

# プロジェクトリンクを確認
echo "プロジェクトリンクを確認しています..."
if [ ! -f ".vercel/project.json" ]; then
    echo "プロジェクトリンクを作成します..."
    vercel link
fi

# デプロイを実行
echo "フロントエンドを直接 Vercel にデプロイします..."
vercel --prod --yes

echo ""
echo "デプロイプロセスが完了しました。"
