# Streamlit Cloudデプロイ手順

このドキュメントでは、セーリング戦略分析システムをStreamlit Cloudにデプロイする方法について説明します。

## 前提条件

1. GitHub上にリポジトリがプッシュされていること
2. Streamlit Cloudのアカウントを持っていること
3. リポジトリのルートディレクトリに`streamlit_app.py`があること (すでに存在します)
4. `.streamlit/config.toml`が適切に設定されていること (すでに設定済みです)

## デプロイ手順

### 1. Streamlit Cloudにログイン

1. [Streamlit Cloud](https://streamlit.io/cloud) にアクセスします
2. GitHubアカウントを使ってログインします

### 2. 新しいアプリをデプロイ

1. "New app" ボタンをクリックします
2. リポジトリとブランチを選択します:
   - Repository: `your-username/sailing-strategy-analyzer`
   - Branch: `main` (またはデプロイするブランチ)
   - Main file path: `streamlit_app.py`

3. 必要に応じて高度な設定を行います:
   - Python version: `3.9` (推奨)
   - パッケージ依存関係: `requirements.txt`から自動的に読み込まれます

4. "Deploy" ボタンをクリックしてデプロイを開始します

### 3. デプロイ状況の確認

1. デプロイログを確認して、エラーがないことを確認します
2. アプリケーションのURLにアクセスして、正常に動作することを確認します

### 4. よくあるデプロイエラーと解決方法

#### ファイルパスの問題

**症状**: ローカルでは動作するが、クラウドで動作しない

**解決策**: 
- 相対パスではなく、絶対パスまたはプロジェクトルートからの相対パスを使用
- `os.path.join` や `Path` オブジェクトを使用してプラットフォーム間の互換性を確保

```python
# 修正例
import os
from pathlib import Path

# 悪い例
data_file = "./data/sample.csv"

# 良い例
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_dir, "data", "sample.csv")

# または
data_file = Path(__file__).parent / "data" / "sample.csv"
```

#### ファイル書き込み権限の問題

**症状**: ファイル書き込み操作でエラーが発生する

**解決策**:
- Streamlit Cloudでは永続的なファイル書き込みに制限があります
- クラウド環境検出機能を使って、クラウド上ではメモリ内操作に切り替える
- テンポラリディレクトリを使用する

```python
# 修正例
import os
import tempfile

# クラウド環境かどうかを検出
is_cloud = os.environ.get("STREAMLIT_SERVER_HEADLESS") == "true"

if is_cloud:
    # クラウド環境ではテンポラリディレクトリを使用
    data_dir = tempfile.gettempdir()
else:
    # ローカル環境では通常のパスを使用
    data_dir = "./data"
```

#### 依存関係の問題

**症状**: モジュールが見つからないなどのインポートエラー

**解決策**:
- `requirements.txt` に必要なすべての依存関係が記載されていることを確認
- バージョン制約を追加して互換性を確保

```
# requirements.txt の例
streamlit==1.38.0
pandas==2.2.0
numpy==1.26.3
```

### 5. デプロイ後のメンテナンス

- GitHubリポジトリを更新すると、Streamlit Cloudは自動的に再デプロイします
- デプロイログを定期的に確認し、エラーがないか監視します
- 大きな変更を行う場合は、ローカルでテストしてから本番環境にデプロイします

### 6. トラブルシューティング

問題が解決しない場合は、以下の確認ポイントを試してください:

1. Streamlit Cloudのデプロイログを確認します
2. `requirements.txt` に必要なパッケージがすべて含まれているか確認します
3. `streamlit_app.py` でエラーハンドリングを強化し、詳細なエラー情報を表示します
4. ローカル環境とクラウド環境での動作の違いを特定するためにログを追加します

## リソース

- [Streamlit Cloud公式ドキュメント](https://docs.streamlit.io/streamlit-cloud)
- [Streamlit Cloud Community Forum](https://discuss.streamlit.io/)
