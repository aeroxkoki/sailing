#!/bin/bash

# スクリプトが存在するディレクトリをプロジェクトルートとして使用
cd "$(dirname "$0")"

echo "Sailing Strategy Analyzer - 手動デプロイスクリプト"
echo "=================================================="
echo "このスクリプトはフロントエンドを手動でVercelにデプロイします"
echo ""

# フロントエンドディレクトリに移動
cd frontend

# 依存関係がインストールされていることを確認
if [ ! -d "node_modules" ]; then
  echo "依存関係をインストールしています..."
  npm install
fi

# ビルド
echo "ビルドを実行しています..."
npm run build

# デプロイ
echo "Vercelへデプロイを開始します..."
npx vercel --prod --yes

echo ""
echo "デプロイプロセスが完了しました。"
echo "注意: このコマンドは環境によって認証を求める場合があります。"
echo "認証が必要な場合は、表示される指示に従ってください。"
