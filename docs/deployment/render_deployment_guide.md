# Renderへのバックエンドデプロイガイド

このガイドでは、セーリング戦略分析システムのバックエンドをRenderにデプロイする手順を説明します。

## 前提条件

- Renderアカウント（[Render.com](https://render.com)で作成可能）
- GitHubリポジトリへのアクセス権
- PostgreSQLデータベース（RenderのPostgreSQLサービスまたは外部データベース）
- Supabaseプロジェクト（認証機能用）

## デプロイ手順

### 1. データベースの準備

#### Renderでデータベースを作成する場合

1. Renderダッシュボードにログイン
2. 「New +」→「PostgreSQL」を選択
3. 以下の情報を入力：
   - Name: `sailing-analyzer-db`
   - Database: `sailing_analyzer`
   - User: デフォルト値を使用
   - Region: `Singapore` (または最も近いリージョン)
4. 「Create Database」をクリック
5. データベースが作成されたら、接続情報（接続文字列）をメモしておく

### 2. 環境変数の準備

バックエンドサービスを作成する前に、必要な環境変数を用意します：

- `APP_ENV`: `production`
- `DEBUG`: `false`
- `DATABASE_URL`: PostgreSQLの接続文字列
- `CORS_ORIGINS`: フロントエンドのURL（例: `https://sailing-strategy-analyzer.vercel.app,http://localhost:3000`）
- `FRONTEND_URL`: フロントエンドのメインURL（例: `https://sailing-strategy-analyzer.vercel.app`）
- `SECRET_KEY`: セキュアなランダム文字列（JWT認証用）
- `SUPABASE_URL`: SupabaseプロジェクトのURL
- `SUPABASE_KEY`: Supabaseのanon/service key
- `SUPABASE_JWT_SECRET`: SupabaseのJWT secret

### 3. Renderサービスの作成

#### 自動デプロイ（render.yaml使用）

1. Renderダッシュボードで「Blueprint」→「New Blueprint Instance」を選択
2. GitHubリポジトリを選択し、「Connect」をクリック
3. リポジトリ内の`render.yaml`ファイルが自動的に検出され、サービス定義が表示される
4. 環境変数の値を入力
5. 「Apply」をクリックしてデプロイを開始

#### 手動デプロイ

1. Renderダッシュボードで「New +」→「Web Service」を選択
2. GitHubリポジトリを選択し、「Connect」をクリック
3. 以下の情報を入力：
   - Name: `sailing-analyzer-backend`
   - Region: `Singapore` (または最も近いリージョン)
   - Branch: `main` (または適切なブランチ)
   - Root Directory: `backend`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. 「Advanced」セクションで環境変数を設定
5. 「Create Web Service」をクリックしてデプロイを開始

### 4. デプロイの確認

1. デプロイが完了したら、生成されたURLにアクセスしてヘルスチェックを確認：
   - `https://sailing-analyzer-backend.onrender.com/health`
   - `https://sailing-analyzer-backend.onrender.com/api/v1/health`
2. 正常なレスポンスが返ってくることを確認
3. 付属の接続テストスクリプトを実行：
   ```bash
   node scripts/test_connection.js https://sailing-analyzer-backend.onrender.com
   ```

### 5. フロントエンドの設定

Vercelにデプロイされたフロントエンドが、新しいバックエンドAPIを使用するように設定します：

1. Vercelダッシュボードにログイン
2. プロジェクト設定を開く
3. 「Environment Variables」セクションで以下を追加または更新：
   - `NEXT_PUBLIC_API_URL`: `https://sailing-analyzer-backend.onrender.com`
4. 「Save」をクリックし、「Redeploy」でフロントエンドを再デプロイ

## トラブルシューティング

### 一般的な問題

1. **デプロイに失敗する場合**
   - ビルドログを確認して具体的なエラーを特定
   - `requirements.txt`内のパッケージバージョンの互換性を確認
   - Pythonバージョンの互換性を確認

2. **CORS関連のエラー**
   - `CORS_ORIGINS`環境変数が正しく設定されているか確認
   - バックエンドのCORS設定で、フロントエンドのドメインが許可されているか確認
   - ブラウザの開発者ツールでネットワークタブを見て、具体的なCORSエラーを確認

3. **データベース接続エラー**
   - `DATABASE_URL`が正しいか確認
   - データベースのファイアウォールが適切に設定されているか確認
   - RenderのIPアドレス範囲が許可されているか確認

4. **日本語エンコーディング問題**
   - リクエスト/レスポンスヘッダーに`Content-Type: application/json; charset=utf-8`が含まれているか確認
   - データベースが`UTF-8`エンコーディングを使用しているか確認

### ログの確認

1. Renderダッシュボードでサービスを選択
2. 「Logs」タブをクリック
3. ログを確認してエラーメッセージを特定

## デプロイ後の確認事項チェックリスト

- [ ] ヘルスチェックエンドポイントが正常に応答する
- [ ] データベース接続が正常に機能している
- [ ] CORS設定が正しく機能し、フロントエンドからAPIにアクセスできる
- [ ] 認証（Supabase Auth）が正常に機能する
- [ ] 日本語データが正しく表示される
- [ ] APIエンドポイントがドキュメント通りに機能する
- [ ] エラーハンドリングが適切に機能する
- [ ] パフォーマンスが許容範囲内である

## 参考情報

- [Renderドキュメント](https://render.com/docs)
- [FastAPIデプロイガイド](https://fastapi.tiangolo.com/deployment/)
- [Render PostgreSQLドキュメント](https://render.com/docs/databases)
