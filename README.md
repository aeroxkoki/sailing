# セーリング戦略分析システム (Sailing Strategy Analyzer)

GPSデータとAI技術を活用して風向風速を推定し、セーリング競技者の意思決定を支援するシステムです。

## 主な機能

- **GPSデータの読み込みと前処理**：GPXやCSVファイルからGPSデータを読み込み、クリーニングおよび前処理
- **風向風速の推定**：艇の動きから風向風速を推定、複数艇のデータを統合した信頼性の高い風推定
- **戦略的判断ポイントの検出**：風向シフト、最適タック位置、レイラインなどの重要な判断ポイントを自動検出
- **パフォーマンス分析**：速度、タック、VMG、風に対する挙動などの分析
- **可視化による分析サポート**：マップ表示、速度分析グラフ、ポーラーチャートなど多角的な可視化機能

## システム要件

- Python 3.8以上
- 必要なパッケージ（requirements.txtに記載）

## インストール方法

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/sailing-strategy-analyzer.git
cd sailing-strategy-analyzer

# 必要なパッケージのインストール
pip install -r requirements.txt

# 開発環境でのインストール
pip install -r requirements-dev.txt
pip install -e .
```

## テスト実行方法

テスト環境の設定を適切に行うため、以下の方法でテストを実行してください。

### 自動テスト実行スクリプトを使用

プロジェクトルートディレクトリで以下のコマンドを実行します：

```bash
# Linux/macOS
./run_tests.sh

# Windows
run_tests.bat
```

このスクリプトは以下のテストを順次実行します：
1. 基本インポートテスト
2. スタンドアロンテスト（`standalone_tests/`ディレクトリ内のテスト）
3. PyTestテスト（利用可能な場合）

### 手動でのテスト実行

環境変数を設定してテストを実行する場合：

```bash
# プロジェクトルートディレクトリをPythonパスに追加
export PYTHONPATH=/path/to/sailing-strategy-analyzer:$PYTHONPATH

# インポートテスト
python test_import.py

# スタンドアロンテスト
python standalone_tests/test_wind_propagation_model.py

# PyTestの実行
pytest -v
```

### テスト環境のトラブルシューティング

テスト実行時に問題が発生した場合は、以下を確認してください：

1. PYTHONPATHにプロジェクトルートディレクトリが含まれていること
2. 必要な開発用パッケージがインストールされていること
3. `.env`ファイルが正しく設定されていること
```

## 使用方法

### Webインターフェースの起動

```bash
# Streamlitアプリケーションの起動
cd ui
streamlit run app.py
```

ブラウザで自動的に http://localhost:8501 が開き、Webインターフェースにアクセスできます。

### 主な操作方法

1. **データアップロード**：「データ管理」タブからGPXまたはCSVファイルをアップロード
2. **マップ表示**：「マップビュー」タブでGPS軌跡を表示、複数艇の同時表示も可能
3. **パフォーマンス分析**：「パフォーマンス分析」タブで速度分析、風向応答、タック分析などを実行
4. **戦略分析**：風向シフトや最適タックポイントなどの戦略的判断ポイントを検出・表示

### プログラムからの利用

```python
from sailing_data_processor.core import SailingDataProcessor
from visualization.sailing_visualizer import SailingVisualizer

# データプロセッサの初期化
processor = SailingDataProcessor()

# GPXまたはCSVデータの読み込み
boat_data = processor.load_multiple_files([
    ('boat1.gpx', open('path/to/boat1.gpx', 'rb').read(), 'gpx'),
    ('boat2.csv', open('path/to/boat2.csv', 'rb').read(), 'csv')
])

# データ前処理
processed_data = processor.process_multiple_boats()

# 風向風速の推定
wind_estimates = processor.estimate_wind_from_all_boats()

# 可視化
visualizer = SailingVisualizer()
visualizer.boats_data = processed_data['data']
map_object = visualizer.create_track_map()
```

## ファイル構成

```
sailing-strategy-analyzer/
├── sailing_data_processor/   # コアデータ処理モジュール
│   ├── core.py              # メインデータプロセッサクラス
│   ├── wind_estimator.py    # 風向風速推定機能
│   ├── strategy/            # 戦略ポイント検出アルゴリズム
│   ├── utilities/           # ユーティリティ関数
│   └── data/                # 極座標データなど
├── visualization/           # 可視化モジュール
│   ├── map_display.py       # マップ表示機能
│   ├── performance_plots.py # パフォーマンス分析グラフ
│   └── sailing_visualizer.py # 可視化統合インターフェース
├── ui/                      # ユーザーインターフェース
│   └── app.py               # Streamlitアプリケーション
├── tests/                   # テストコード
├── docs/                    # ドキュメント
└── setup.py                 # インストールスクリプト
```

## コントリビューション

バグ報告や機能改善のプルリクエストを歓迎します。コントリビューションする際は以下の点にご注意ください：

1. テストを追加・更新し、すべてのテストが正常に通ることを確認
2. ドキュメントを更新（必要に応じて）
3. コーディング規約を遵守（PEP 8推奨）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルをご覧ください。

## 謝辞

このプロジェクトは、セーリング競技におけるデータ分析技術の向上を目指す取り組みの一環として開発されました。ご協力いただいた皆様に感謝いたします。
