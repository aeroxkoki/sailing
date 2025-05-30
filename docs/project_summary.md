# セーリング戦略分析システム - プロジェクトサマリー

## プロジェクト概要

セーリング戦略分析システムは、セーリング競技者とコーチのためのデータ分析ツールです。GPSデータを基に風向風速を推定し、セーリング競技における戦略的判断ポイントを検出・評価するための統合プラットフォームを提供します。

### 目的と背景

セーリング競技において、風向や風速は最も重要な環境要因であり、競技パフォーマンスに直接影響します。従来、セーラーは経験と感覚に頼った判断を行っていましたが、これらの判断を客観的に分析し、改善することは困難でした。

本プロジェクトは以下の課題を解決するために開発されました：

1. レース中の風向風速の正確な把握と記録の難しさ
2. 戦略的判断ポイントの特定と評価の困難さ
3. トレーニングとレース分析における客観的指標の不足
4. チーム内での知見共有と効率的なコミュニケーション手段の欠如

## 開発フェーズの概要

本プロジェクトは以下のフェーズで開発されました：

### フェーズ1: 技術的基盤の安定化（完了）
- コアデータ処理モジュールの開発
- 基本的なGPSデータ処理機能の実装
- データモデルの設計

### フェーズ2: ユーザーエクスペリエンスの向上（完了）
- Streamlitを用いたUIの開発
- 基本的なデータ可視化機能の実装
- プロジェクト/セッション管理機能の実装

### フェーズ3: 差別化機能の強化（完了）
- 風向シフト分析の精度向上
- レース後戦略分析エンジンの拡充
- データバリデーション機能の強化

### フェーズ4: 統合アプリケーションの公開（現在）
- 既存機能の統合
- ユーザーインターフェースの改善
- 基本ドキュメントの整備
- Streamlit Cloudへのデプロイ準備

## 実装された機能

### コアモジュール

- **データ処理**
  - GPXファイルインポート
  - CSVファイルインポート
  - FITファイルインポート
  - データクリーニングと前処理

- **分析エンジン**
  - 風向風速推定アルゴリズム
  - 戦略検出エンジン
  - パフォーマンス評価指標計算

- **エクスポート**
  - CSVエクスポート
  - JSONエクスポート
  - レポート生成（基本）

### ユーザーインターフェース

- **プロジェクト管理**
  - プロジェクト作成/編集/削除
  - セッション管理
  - タグ付けとメタデータ管理

- **データインポート**
  - ファイルアップロード
  - 列マッピング（CSVの場合）
  - データプレビュー

- **データ検証**
  - 問題検出
  - 対話的修正
  - バリデーションレポート

- **分析と可視化**
  - マップビュー
  - 風向風速可視化
  - 戦略ポイント表示
  - パフォーマンスチャート

## 技術スタック

### バックエンド

- **言語**: Python 3.9+
- **データ処理**: Pandas, NumPy, GeoPy
- **ファイル処理**: gpxpy, fitparse
- **分析**: SciPy, scikit-learn
- **テスト**: PyTest

### フロントエンド

- **フレームワーク**: Streamlit
- **データ可視化**: Folium, Plotly, Matplotlib
- **地図表示**: Folium, streamlit-folium
- **インタラクティブUI**: Streamlit widgets

### ストレージ

- **ローカル**: ファイルベースのストレージ
- **ブラウザ**: SessionState, streamlit-js-eval

### デプロイ

- **ローカル実行**: Streamlit
- **クラウドデプロイ**: Streamlit Cloud

## プロジェクト構造

```
sailing-strategy-analyzer/
├── .streamlit/                # Streamlit設定
├── docs/                     # ドキュメント
├── sailing_data_processor/   # コアデータ処理モジュール
│   ├── analysis/             # 分析アルゴリズム
│   ├── exporters/            # エクスポート機能
│   ├── importers/            # インポート機能
│   ├── project/              # プロジェクト管理
│   ├── storage/              # ストレージ管理
│   └── validation/           # データ検証
├── tests/                    # テストコード
├── ui/                       # ユーザーインターフェース
│   ├── components/           # UIコンポーネント
│   ├── integrated/           # 統合UI
│   ├── pages/                # ページ定義
│   └── app_v5.py             # メインアプリ
├── visualization/            # 可視化ライブラリ
├── requirements.txt          # 依存パッケージ
└── streamlit_app.py          # エントリーポイント
```

## 開発と貢献

### 開発環境のセットアップ

1. リポジトリのクローン
   ```
   git clone https://github.com/your-username/sailing-strategy-analyzer.git
   ```

2. 依存パッケージのインストール
   ```
   cd sailing-strategy-analyzer
   pip install -r requirements.txt
   pip install -e .  # 開発モードでインストール
   ```

3. テストの実行
   ```
   pytest tests/
   ```

### 貢献ガイドライン

- **コードスタイル**: PEP 8に準拠
- **ドキュメント**: すべての新機能にはドキュメントを追加
- **テスト**: 新機能には対応するテストを追加
- **コミットメッセージ**: 明確で簡潔なメッセージを使用

## ライセンスと謝辞

### ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は`LICENSE`ファイルを参照してください。

### 謝辞

- Streamlitチームが提供する素晴らしいデータアプリケーションフレームワーク
- オープンソースの地理空間データ処理ライブラリ
- テストデータを提供してくれたセーリング競技者の皆様
