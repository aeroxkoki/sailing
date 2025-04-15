# セーリング戦略分析システム - Streamlit Cloudデプロイ手順

このドキュメントでは、セーリング戦略分析システムをStreamlit Cloudにデプロイする手順を説明します。UI/UX改善版の風向風速可視化デモを公開するための設定方法と注意事項が含まれています。

## 1. 前提条件

- GitHubアカウント
- [Streamlit Cloud](https://streamlit.io/cloud)アカウント（Streamlitアカウントに登録してください）
- 本リポジトリへのアクセス権

## 2. デプロイ前の確認事項

### 2.1 必要なファイル

以下のファイルが正しく設定されていることを確認します：

- `streamlit_app.py` - デプロイのエントリポイント
- `requirements.txt` - 必要なPythonパッケージのリスト
- `.streamlit/config.toml` - Streamlit設定
- `packages.txt` - システム依存パッケージのリスト

### 2.2 モジュール構造

次のモジュールとディレクトリが存在することを確認します：

- `ui/components/navigation/` - トップバーとコンテキストバーコンポーネント
- `ui/components/visualizations/` - 風向風速表示と艇マーカーコンポーネント
- `ui/components/controls/` - タイムラインコントロールコンポーネント
- `ui/demo/` - 風向風速デモアプリケーション
- `sailing_data_processor/utilities/` - 風場生成ユーティリティ

## 3. デプロイ手順

### 3.1 GitHubリポジトリの準備

1. 最新の変更をコミットしてプッシュします：
   ```bash
   git add .
   git commit -m "UI/UX改善版の風向風速可視化デモをStreamlit Cloudデプロイ用に準備"
   git push origin main
   ```

### 3.2 Streamlit Cloudへのデプロイ

1. [Streamlit Cloud](https://streamlit.io/cloud)にログインします。

2. 「New app」ボタンをクリックします。

3. リポジトリ設定を行います：
   - GitHubリポジトリ: `https://github.com/<ユーザー名>/sailing-strategy-analyzer`
   - ブランチ: `main`
   - メインモジュールパス: `streamlit_app.py`
   - Pythonバージョン: `3.9` (推奨)

4. 「Advanced settings」を開いて以下の項目を設定します：
   - シークレット設定: 必要に応じて
   - パッケージエラーを無視: 無効
   - Watcherを有効にする: 有効

5. 「Deploy」ボタンをクリックします。

デプロイが完了すると、アプリのURLが提供されます。デフォルトでは `https://share.streamlit.io/<ユーザー名>/sailing-strategy-analyzer/main` のような形式になります。

## 4. デプロイ後の確認

1. デプロイされたアプリにアクセスして正常に動作することを確認します。

2. 特に以下の機能が正しく動作することを確認します：
   - トップバーナビゲーション
   - 風向風速の可視化
   - 艇位置マーカーの表示
   - タイムラインコントロール

3. エラーが発生した場合は、Streamlit Cloudのログを確認してデバッグします。

## 5. デプロイの更新

コードに変更を加えた場合、以下の手順で更新します：

1. 変更を加えてテストします。
2. 変更をコミットしてプッシュします。
3. Streamlit Cloudは自動的に更新をデプロイします（ウォッチャーが有効になっている場合）。

手動で更新するには、Streamlit Cloudダッシュボードで「Reboot」ボタンをクリックします。

## 6. トラブルシューティング

### 一般的な問題

- **パッケージのインストールエラー**: `requirements.txt`が正しく設定されていることを確認します。
- **モジュールインポートエラー**: パスが正しく解決されるようにstreamlit_app.pyのプロジェクトパス設定を確認します。
- **依存関係の問題**: `packages.txt`に必要なシステム依存パッケージがすべて含まれていることを確認します。

### ログの確認

Streamlit Cloudダッシュボードの「Manage app」セクションから「Logs」を選択すると、アプリケーションのログを確認できます。

## 7. 制限事項と注意点

- Streamlit Cloudの無料プランには一定のリソース制限があります。
- ファイルの書き込みはローカルのテンポラリストレージにのみ可能です（恒久的なデータストレージには適していません）。
- セキュリティ上の理由から、機密データをコードにハードコーディングしないでください。代わりに`.streamlit/secrets.toml`を使用してください。
