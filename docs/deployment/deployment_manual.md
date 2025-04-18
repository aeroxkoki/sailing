# セーリング戦略分析システム - デプロイマニュアル

## 概要

このドキュメントでは、セーリング戦略分析システムを本番環境にデプロイするための手順を詳細に説明します。システムはVercel（フロントエンド）、Render（バックエンド）、Supabase（データベース）を使用して構成されています。

## 前提条件

- Vercelアカウント
- Renderアカウント
- Supabaseアカウント
- GitHubリポジトリへのアクセス権限

## デプロイ手順

### 1. Supabaseセットアップ

#### 1.1 新規プロジェクト作成

1. Supabase管理コンソールにログイン
2. 「New Project」をクリック
3. プロジェクト名「sailing-strategy-analyzer-prod」を設定
4. リージョンを「Asia Northeast（Tokyo）」を選択
5. パスワードを設定（安全な方法で保存しておく）
6. 「Create Project」をクリック
7. プロジェクト作成完了まで待機（約1分）

#### 1.2 データベーススキーマのセットアップ

1. プロジェクトダッシュボードから「SQL Editor」を選択
2. 「New Query」をクリック
3. 以下のスキーマ定義SQLを実行

```sql
-- プロジェクトテーブル
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  user_id UUID NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  metadata JSONB
);

-- セッションテーブル
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  metadata JSONB,
  CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- GPSデータテーブル
CREATE TABLE gps_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  speed DOUBLE PRECISION,
  course DOUBLE PRECISION,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  metadata JSONB,
  CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 風データテーブル
CREATE TABLE wind_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  direction DOUBLE PRECISION NOT NULL,
  speed DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  metadata JSONB,
  CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 戦略ポイントテーブル
CREATE TABLE strategy_points (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  point_type TEXT NOT NULL,
  description TEXT,
  importance INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  metadata JSONB,
  CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- タグテーブル
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- セッションとタグの中間テーブル
CREATE TABLE session_tags (
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (session_id, tag_id),
  CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- インデックス作成
CREATE INDEX idx_gps_data_session_id ON gps_data(session_id);
CREATE INDEX idx_gps_data_timestamp ON gps_data(timestamp);
CREATE INDEX idx_wind_data_session_id ON wind_data(session_id);
CREATE INDEX idx_wind_data_timestamp ON wind_data(timestamp);
CREATE INDEX idx_strategy_points_session_id ON strategy_points(session_id);
CREATE INDEX idx_strategy_points_timestamp ON strategy_points(timestamp);
CREATE INDEX idx_sessions_project_id ON sessions(project_id);
```

#### 1.3 RLSポリシーの設定

1. 「Authentication」→「Policies」を選択
2. 各テーブルに適切なRow Level Securityポリシーを設定

#### 1.4 APIキーとURLの取得

1. 「Settings」→「API」を選択
2. 以下の情報をメモ
   - API URL
   - anon key
   - service_role key（本番環境用）

### 2. バックエンドデプロイ（Render）

#### 2.1 新規Webサービス作成

1. Render管理コンソールにログイン
2. 「New +」→「Web Service」をクリック
3. GitHubリポジトリに接続
4. 「sailing-strategy-analyzer」リポジトリを選択
5. サービス名「sailing-strategy-analyzer-backend」を設定
6. Root Directory「backend」を指定
7. Environment「Python」を選択
8. Build Command「pip install -r requirements.txt」を入力
9. Start Command「uvicorn main:app --host 0.0.0.0 --port $PORT」を入力
10. インスタンスタイプを選択（初期段階では「Starter」で十分）
11. 「Advanced」をクリックし環境変数を設定

#### 2.2 環境変数の設定

以下の環境変数を設定します：

```
SUPABASE_URL=<Supabaseから取得したAPI URL>
SUPABASE_KEY=<Supabaseから取得したservice_role key>
SUPABASE_JWT_SECRET=<Supabaseから取得したJWT Secret>
DATABASE_URL=<Supabaseから取得したPostgreSQL接続文字列>
CORS_ORIGINS=https://sailing-strategy-analyzer.vercel.app
SECRET_KEY=<ランダムな文字列を生成>
APP_ENV=production
DEBUG=false
```

#### 2.3 デプロイ実行

1. 「Create Web Service」をクリックしてデプロイを開始
2. デプロイが完了するまで待機（約5分）
3. 自動生成されたURLをメモ（例：https://sailing-strategy-analyzer-backend.onrender.com）

### 3. フロントエンドデプロイ（Vercel）

#### 3.1 新規プロジェクト作成

1. Vercel管理コンソールにログイン
2. 「New Project」をクリック
3. GitHubリポジトリに接続
4. 「sailing-strategy-analyzer」リポジトリを選択
5. 「Framework Preset」で「Next.js」を選択
6. Root Directory「frontend」を指定

#### 3.2 環境変数の設定

以下の環境変数を設定します：

```
NEXT_PUBLIC_API_URL=<RenderのバックエンドサービスのデプロイされたベースURL>
NEXT_PUBLIC_SUPABASE_URL=<SupabaseのAPI URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<Supabaseのanon key>
```

#### 3.3 デプロイ実行

1. 「Deploy」をクリックしてデプロイを開始
2. デプロイが完了するまで待機（約3分）
3. 自動生成されたURLをメモ（例：https://sailing-strategy-analyzer.vercel.app）

### 4. 動作確認

#### 4.1 ヘルスチェック

1. バックエンドのヘルスチェックエンドポイントにアクセス
   ```
   https://sailing-strategy-analyzer-backend.onrender.com/health
   ```
   
   以下のようなレスポンスが表示されることを確認
   ```json
   {"status": "healthy"}
   ```

2. フロントエンドにアクセスして正常に表示されることを確認
   ```
   https://sailing-strategy-analyzer.vercel.app
   ```

#### 4.2 API接続テスト

1. フロントエンドから新規ユーザーを登録
2. ログインが正常にできることを確認
3. プロジェクト作成などの基本機能が動作することを確認

#### 4.3 日本語対応確認

1. 日本語を含むプロジェクト名やセッション名を作成
2. 保存と表示が正常に行われることを確認

### 5. カスタムドメイン設定（オプション）

#### 5.1 Vercelのカスタムドメイン設定

1. Vercelプロジェクト設定から「Domains」を選択
2. カスタムドメインを追加（例：app.sailing-analyzer.com）
3. DNSプロバイダーの指示に従って必要なDNSレコードを設定

#### 5.2 Renderのカスタムドメイン設定

1. Renderサービス設定から「Custom Domain」を選択
2. カスタムドメインを追加（例：api.sailing-analyzer.com）
3. DNSプロバイダーの指示に従って必要なDNSレコードを設定

#### 5.3 CORS設定の更新

カスタムドメインを使用する場合、バックエンドのCORS設定を更新：

1. Renderダッシュボードから環境変数を編集
2. CORS_ORIGINSを更新:
   ```
   CORS_ORIGINS=https://app.sailing-analyzer.com
   ```

## 運用管理

### 1. モニタリング

#### 1.1 ログ確認

- Renderダッシュボードの「Logs」タブでバックエンドログを確認
- Vercelダッシュボードの「Logs」タブでフロントエンドログを確認

#### 1.2 パフォーマンスモニタリング

- Renderダッシュボードの「Metrics」タブでリソース使用状況を確認
- Vercelダッシュボードの「Analytics」タブでパフォーマンスメトリクスを確認

### 2. バックアップ

#### 2.1 定期バックアップ

Supabaseのデータベースを定期的にバックアップします：

1. Supabaseダッシュボードの「Database」→「Backups」を選択
2. 「Create Backup」をクリックして手動バックアップを作成
3. 自動バックアップスケジュールを確認（デフォルトで毎日実行）

### 3. アップデート

#### 3.1 継続的デプロイ

GitHubリポジトリの特定ブランチへのプッシュが行われた際に自動デプロイが実行されます：

1. バックエンド（Render）：`main` ブランチへのプッシュで自動デプロイ
2. フロントエンド（Vercel）：`main` ブランチへのプッシュで自動デプロイ

#### 3.2 手動デプロイ

必要に応じて手動デプロイも実行可能：

1. Renderダッシュボードから「Manual Deploy」→「Deploy latest commit」を選択
2. Vercelダッシュボードから「Deployments」→「Redeploy」を選択

### 4. トラブルシューティング

#### 4.1 デプロイ失敗時の対応

1. ビルドログを確認して失敗の原因を特定
2. ローカル環境で同様の問題が再現できるか確認
3. 問題を修正してから再デプロイを実行

#### 4.2 パフォーマンス問題の対応

1. リソース使用状況を確認
2. 必要に応じてプランをアップグレード
3. データベースインデックスやクエリの最適化を検討

#### 4.3 通信エラーの対応

1. CORS設定が正しいか確認
2. エンドポイントURLが正しいか確認
3. ネットワークタブでAPIリクエストを調査

## セキュリティ対策

### 1. 環境変数の管理

- シークレットキーやAPIキーは必ず環境変数として設定
- 本番環境のキーはテスト環境と異なるものを使用
- キーの定期的なローテーションを実施

### 2. アクセス制御

- Supabaseの認証機能とRLSポリシーを活用
- 適切なユーザー権限管理を実施
- デプロイ権限は必要なメンバーのみに付与

### 3. 定期的なセキュリティチェック

- 依存パッケージの脆弱性スキャンを定期的に実施
- コードレビューでセキュリティ問題がないか確認
- セキュリティアップデートを迅速に適用

## 参考情報

- [Vercel公式ドキュメント](https://vercel.com/docs)
- [Render公式ドキュメント](https://render.com/docs)
- [Supabase公式ドキュメント](https://supabase.io/docs)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)

---

**作成日**: 2025年4月18日  
**作成者**: セーリング戦略分析システム開発チーム  
**最終更新日**: 2025年4月18日
