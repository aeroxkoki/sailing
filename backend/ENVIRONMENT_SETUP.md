# セーリング戦略分析システム 環境設定ガイド

このドキュメントでは、セーリング戦略分析システムのバックエンドを異なる環境で設定・デプロイする方法について説明します。

## 目次

1. [環境の種類](#環境の種類)
2. [環境変数の設定](#環境変数の設定)
3. [各環境別の設定方法](#各環境別の設定方法)
   - [開発環境](#開発環境)
   - [テスト環境](#テスト環境)
   - [本番環境](#本番環境)
4. [Supabase 設定](#supabase-設定)
5. [依存関係の管理](#依存関係の管理)
6. [トラブルシューティング](#トラブルシューティング)

## 環境の種類

システムは以下の3つの環境で運用されることを想定しています：

1. **開発環境（Development）**：
   - 開発者のローカル環境
   - 機能開発やバグ修正のための環境
   - データは開発用で、実際のユーザーデータは使用しない

2. **テスト環境（Staging）**：
   - 開発環境から本番環境へのステップとして利用
   - テスト・品質保証のための環境
   - 本番に近い設定だが、テスト用データを使用

3. **本番環境（Production）**：
   - エンドユーザーが利用する環境
   - 実際のユーザーデータを扱う
   - 高可用性とセキュリティが重視される

## 環境変数の設定

環境変数は `.env` ファイルで管理され、各環境ごとに異なる値を設定します。
リポジトリには `.env.example` ファイルが含まれており、これをコピーして `.env` ファイルを作成します。

### 主要な環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `APP_ENV` | 現在の環境 | `development`, `staging`, `production` |
| `DEBUG` | デバッグモードの有効/無効 | `true`, `false` |
| `DATABASE_URL` | データベース接続文字列 | `postgresql://user:pass@localhost:5432/db` |
| `SUPABASE_URL` | Supabase プロジェクトURL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase API キー | `eyJxxxxx` |
| `SECRET_KEY` | JWT 署名用の秘密鍵 | ランダムな文字列 |
| `CORS_ORIGINS` | CORSで許可するオリジン | `http://localhost:3000,https://example.com` |

## 各環境別の設定方法

### 開発環境

開発環境では、ローカルでの開発を容易にするために、より緩やかな設定を使用します。

```dotenv
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sailing_analyzer_dev
SUPABASE_URL=https://your-dev-project.supabase.co
SUPABASE_KEY=your-dev-key
SECRET_KEY=your-dev-secret-key
CORS_ORIGINS=http://localhost:3000
```

開発環境の起動方法：

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### テスト環境

テスト環境は本番に近い設定ですが、テスト用のデータベースとサービスを使用します。

```dotenv
APP_ENV=staging
DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/sailing_analyzer_staging
SUPABASE_URL=https://your-staging-project.supabase.co
SUPABASE_KEY=your-staging-key
SECRET_KEY=your-staging-secret-key
CORS_ORIGINS=https://staging.sailing-analyzer.example.com
```

テスト環境のデプロイには Render を使用します：

1. Render ダッシュボードにログイン
2. 「New Web Service」を選択
3. リポジトリを連携
4. 環境変数を設定
5. `backend` をルートディレクトリとして指定
6. `pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port $PORT` を起動コマンドとして指定

### 本番環境

本番環境では、セキュリティとパフォーマンスを最優先する設定を使用します。

```dotenv
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@production-db:5432/sailing_analyzer_prod
SUPABASE_URL=https://your-production-project.supabase.co
SUPABASE_KEY=your-production-key
SECRET_KEY=your-production-secret-key
CORS_ORIGINS=https://sailing-analyzer.example.com
```

本番環境でのデプロイもRenderを使用しますが、以下の点に注意します：

1. 自動デプロイではなく、手動承認後のデプロイを設定
2. より多くのリソース（CPU/メモリ）の割り当て
3. 無料プランではなく有料プランを使用して高可用性を確保

## Supabase 設定

Supabaseは各環境ごとに別のプロジェクトを作成することを推奨します。

### Supabase プロジェクト設定手順

1. [Supabase ダッシュボード](https://app.supabase.io/)にアクセス
2. 「New Project」を選択
3. プロジェクト名を設定（例：`sailing-analyzer-dev`）
4. リージョンを選択（ユーザーの多い地域に近いもの）
5. データベースパスワードを設定
6. プロジェクト作成後、設定画面から以下を取得：
   - Project URL: `SUPABASE_URL` として使用
   - API Key (service_role key): `SUPABASE_KEY` として使用

### RLS (Row Level Security) ポリシー

各環境で一貫した RLS ポリシーを確保するために、マイグレーションスクリプトに RLS ポリシーを含めることをお勧めします。

## 依存関係の管理

依存関係は `requirements.txt` で管理され、各ライブラリのバージョンを明示的に固定して、環境間での一貫性を確保しています。
特に Supabase とその依存ライブラリは、バージョンの不一致によるエラーを防ぐために、正確なバージョンを指定しています。

```
supabase==2.15.0
gotrue==2.12.0
postgrest==1.0.1
realtime==2.4.2
storage3==0.11.3
```

## トラブルシューティング

### Supabase 接続エラー

**症状**: `TypeError: Client.__init__() got an unexpected keyword argument 'proxy'`

**解決策**:
```python
# 代替的な初期化方法を試す
from supabase.lib.client_options import SyncClientOptions
options = SyncClientOptions()
supabase = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY,
    options=options
)
```

### データベース接続エラー

**症状**: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server`

**解決策**:
1. データベースサーバーが起動していることを確認
2. 接続文字列の正確性を確認（ホスト名、ポート、ユーザー名、パスワード）
3. ネットワーク設定（ファイアウォール等）を確認

### CORS エラー

**症状**: ブラウザコンソールに `Access-Control-Allow-Origin` 関連のエラー

**解決策**:
1. `CORS_ORIGINS` 環境変数にフロントエンドのURLが正しく含まれていることを確認
2. 開発中は `CORS_ORIGINS=*` を一時的に設定することで全てのオリジンを許可可能（本番では使用しないこと）

---

このガイドは随時更新されます。ご質問や提案がある場合は、リポジトリのイシューを通じてお知らせください。
