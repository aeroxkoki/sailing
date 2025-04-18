# セーリング戦略分析システム - モジュール分割レポート

## 概要

本ドキュメントでは、既存のStreamlitベースのセーリング戦略分析システムから、Next.js + FastAPI + Supabaseの新アーキテクチャへの移行にあたり、既存のコードベースを分析した結果を報告します。各機能カテゴリごとにモジュール分割の方針、既存コードの再利用可能性、およびAPI化のための変更点について説明します。

## 機能カテゴリとモジュール分割

既存のコードベースを分析した結果、以下の主要な機能カテゴリが特定されました。

### 1. データインポート/変換

#### 主要機能
- GPX, CSV, TCX, FITなどの各種フォーマットのインポート
- データ形式の正規化と変換
- メタデータの抽出と設定

#### 主要ファイル
- sailing_data_processor/importers/base_importer.py
- sailing_data_processor/importers/gpx_importer.py
- sailing_data_processor/importers/csv_importer.py
- sailing_data_processor/importers/tcx_importer.py
- sailing_data_processor/importers/fit_importer.py
- sailing_data_processor/importers/batch_importer.py

#### API設計方針
- 各ファイル形式ごとにエンドポイントを作成
- ファイルアップロード処理とバリデーション
- バッチインポート処理の非同期化

```python
# backend/app/api/routes/import.py
from fastapi import APIRouter, UploadFile, File, Form, Depends
from ...services.importers import gpx_service, csv_service
from ...models.import_models import ImportOptions

router = APIRouter()

@router.post("/gpx")
async def import_gpx(
    file: UploadFile = File(...),
    options: ImportOptions = Depends(),
    current_user = Depends(get_current_user)
):
    """GPXファイルをインポート"""
    return await gpx_service.import_file(file, options, current_user)
```

#### 依存関係
- GPXpy, Pandas, NumPy
- Pydantic（バリデーション）
- ファイルアップロード処理

### 2. 風向風速推定

#### 主要機能
- GPS軌跡からの風向風速推定
- マニューバー検出と解析
- VMG分析
- 複数データの統合（ベイズ推定）

#### 主要ファイル
- sailing_data_processor/wind_estimator.py
- sailing_data_processor/wind_estimator_optimized.py
- sailing_data_processor/wind_field_fusion_system.py
- sailing_data_processor/wind_field_interpolator.py

#### API設計方針
- 風向風速推定のエンドポイント
- 非同期タスク処理
- キャッシュ戦略

```python
# backend/app/api/routes/wind.py
from fastapi import APIRouter, Depends, BackgroundTasks
from ...services.wind import wind_estimation_service
from ...models.wind_models import WindEstimationRequest

router = APIRouter()

@router.post("/estimate")
async def estimate_wind(
    request: WindEstimationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """GPSデータから風向風速を推定（非同期）"""
    task_id = await wind_estimation_service.create_estimation_task(
        request, current_user, background_tasks
    )
    return {"task_id": task_id}
```

#### 依存関係
- NumPy, Pandas
- 地理空間計算ライブラリ
- 数学/統計関数

### 3. 戦略ポイント検出

#### 主要機能
- タック/ジャイブポイントの検出
- 風向シフトの検出
- レイラインの検出と評価
- 戦略的判断の最適化提案

#### 主要ファイル
- sailing_data_processor/strategy/detector.py
- sailing_data_processor/strategy/points.py
- sailing_data_processor/strategy/evaluator.py
- sailing_data_processor/strategy_point_detector.py

#### API設計方針
- 戦略ポイント検出のエンドポイント
- 検出済みポイントの取得と評価
- 複数セッションの比較分析

```python
# backend/app/api/routes/strategy.py
from fastapi import APIRouter, Depends
from ...services.strategy import strategy_detector_service
from ...models.strategy_models import StrategyDetectionRequest

router = APIRouter()

@router.post("/detect")
async def detect_strategy_points(
    request: StrategyDetectionRequest,
    current_user = Depends(get_current_user)
):
    """セッションデータから戦略ポイントを検出"""
    return await strategy_detector_service.detect_points(request, current_user)
```

#### 依存関係
- 風向風速推定モジュール
- GPS操作ライブラリ
- 数学/統計関数

### 4. 可視化/UI

#### 主要機能
- マップ表示
- タイムラインコントロール
- 風向風速の視覚化
- チャートとグラフ

#### 主要ファイル
- ui/components/visualizations/
- visualization/map_components.py
- visualization/strategy_visualization.py
- visualization/shift_visualization.py

#### API設計方針
- データフォーマットの標準化
- 軽量なレスポンス設計
- インタラクティブ要素のフロントエンドへの移行

```python
# backend/app/api/routes/visualization.py
from fastapi import APIRouter, Depends, Query
from ...services.visualization import map_service
from ...models.visualization_models import MapDataRequest

router = APIRouter()

@router.get("/map/{session_id}")
async def get_map_data(
    session_id: str,
    zoom_level: int = Query(13),
    current_user = Depends(get_current_user)
):
    """セッションのマップ表示用データを取得"""
    return await map_service.get_map_data(session_id, zoom_level, current_user)
```

#### 依存関係
- フロントエンド（React, Mapbox, Recharts）
- JSON形式のデータ交換
- GeoJSONデータ形式

### 5. レポート生成

#### 主要機能
- 分析結果のレポート作成
- 各種フォーマットでのエクスポート
- テンプレートベースの生成

#### 主要ファイル
- sailing_data_processor/reporting/
- sailing_data_processor/exporters/

#### API設計方針
- レポート生成の非同期化
- ストレージとのインテグレーション
- カスタムテンプレート管理

```python
# backend/app/api/routes/reports.py
from fastapi import APIRouter, Depends, BackgroundTasks
from ...services.reports import report_service
from ...models.report_models import ReportGenerationRequest

router = APIRouter()

@router.post("/generate")
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """分析レポートを生成（非同期）"""
    task_id = await report_service.create_report_task(
        request, current_user, background_tasks
    )
    return {"task_id": task_id}
```

#### 依存関係
- テンプレートエンジン
- PDF生成ライブラリ
- データエクスポートモジュール

## コア機能の再設計

### コアモジュールのリファクタリング

`sailing_data_processor/core.py`はシステムのコア機能を提供していますが、多くの責務が混在しています。これを以下のように分割します：

#### 1. データサービス層

```python
# backend/app/services/data/gps_service.py
class GPSDataService:
    """GPSデータの処理とアクセスを行うサービス"""
    
    async def get_track_points(self, track_id, start_time=None, end_time=None, limit=1000):
        """トラックのGPSポイントを取得"""
        pass
    
    async def calculate_statistics(self, track_id):
        """トラックの基本統計を計算"""
        pass
```

#### 2. ドメインロジック層

```python
# backend/app/core/analysis/track_analyzer.py
class TrackAnalyzer:
    """トラックデータの分析ロジック"""
    
    def detect_maneuvers(self, points_df):
        """マニューバー（タック/ジャイブ）を検出"""
        pass
    
    def calculate_performance_metrics(self, points_df, wind_data=None):
        """パフォーマンス指標を計算"""
        pass
```

### 風向風速推定の最適化

風向風速推定モジュールは計算負荷が高いため、以下の最適化を行います：

- 非同期処理によるAPI負荷分散
- 結果のキャッシュ戦略
- バッチ処理のスケジューリング

```python
# backend/app/core/wind/estimator.py
class OptimizedWindEstimator:
    """最適化された風向風速推定ロジック"""
    
    async def estimate_from_track(self, track_data, options=None):
        """トラックデータから風向風速を推定"""
        pass
```

## API設計詳細

### APIレイヤーの責務

- **ルーティングとパラメータ検証**: FastAPIのPathパラメータ、クエリパラメータ、リクエストボディの検証
- **認証・認可**: JWTベースの認証とロールベースのアクセス制御
- **レスポンス整形**: 一貫性のあるレスポンス形式の提供
- **エラーハンドリング**: 適切なHTTPステータスコードとエラーメッセージの提供

### サービスレイヤーの責務

- **ビジネスロジックの実装**: コア機能の実装とオーケストレーション
- **データアクセス**: リポジトリパターンを使用したデータの取得と保存
- **トランザクション管理**: 必要に応じたトランザクション境界の定義
- **ドメインイベントの発行**: 非同期処理のトリガー

### リポジトリレイヤーの責務

- **データアクセスの抽象化**: データベースへのアクセスをカプセル化
- **クエリの最適化**: 効率的なクエリの構築と実行
- **データマッピング**: データベースモデルとドメインモデルの変換

## 課題と対応策

### 1. UIの分離

**課題**: 現在のStreamlitアプリはバックエンドとUIが密結合しています。

**対応策**:
- UIロジックとデータ処理を完全に分離
- REST APIによるデータ交換
- JSONスキーマによるデータ構造の定義

### 2. 大規模データ処理

**課題**: GPSトラックなどの大量データの効率的な処理と保存

**対応策**:
- ページング処理の徹底
- ストリーミングレスポンスの活用
- データのダウンサンプリングオプションの提供

```python
# backend/app/api/routes/tracks.py
@router.get("/{id}/points")
async def get_track_points(
    id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, le=5000),
    downsample: Optional[int] = None,
    current_user = Depends(get_current_user)
):
    """トラックポイントのページング取得"""
    return await track_service.get_points(
        id, start_time, end_time, limit, downsample, current_user
    )
```

### 3. 非同期処理

**課題**: 計算負荷の高い処理（風向推定など）のレスポンス時間

**対応策**:
- バックグラウンドタスク処理
- タスクキューの導入
- WebSocketによる進捗通知

```python
# backend/app/core/tasks/task_manager.py
class TaskManager:
    """非同期タスク管理"""
    
    async def create_task(self, task_type, params, user_id):
        """タスクを作成してキューに追加"""
        task_id = await self.db.create_task(task_type, params, user_id)
        await self.queue.add_task(task_id, task_type, params)
        return task_id
    
    async def get_task_status(self, task_id, user_id):
        """タスクのステータスを取得"""
        return await self.db.get_task(task_id, user_id)
```

## 既存コードの再利用方針

### 即時再利用可能なコード

以下のモジュールは最小限の変更で再利用可能です：

1. **データインポーターモジュール**: 主にI/O処理の修正
2. **風向風速推定アルゴリズム**: 独立した関数として再利用
3. **GPS座標計算ユーティリティ**: そのまま再利用可能

### 大幅な変更が必要なコード

以下のモジュールは大幅な再設計が必要です：

1. **UI関連コード**: React/Next.jsでの完全な書き換え
2. **データストレージ**: IndexedDBからSupabaseへの変更
3. **セッション管理**: マルチユーザー対応への拡張

### マイグレーション優先順位

1. **コアアルゴリズム**: 風向風速推定、戦略検出エンジン
2. **データインポート/エクスポート**: データ交換の基盤
3. **可視化コンポーネント**: UI/UXの基本機能
4. **レポート生成**: 拡張機能

## 次のステップ

### バックエンド開発

1. **FastAPIプロジェクト構造の設定**
   - ルーター、ミドルウェア、依存関係の設定
   - 認証システムの実装

2. **データモデルの設計と実装**
   - Pydanticモデルの作成
   - データベーススキーマの定義

3. **コアモジュールの移植**
   - 風向風速推定ロジックの移植
   - 戦略検出アルゴリズムの移植

### フロントエンド開発

1. **Next.jsのプロジェクト構造設定**
   - ページ構造の設計
   - コンポーネント階層の設計

2. **APIクライアントの実装**
   - APIエンドポイントへの接続
   - データフェッチングと状態管理

3. **UIコンポーネントの開発**
   - マップ表示コンポーネント
   - チャートとグラフコンポーネント
   - タイムラインコントロール

## 結論

既存のコードベースは、新アーキテクチャへの移行において多くの価値あるアルゴリズムとロジックを含んでいます。特に、風向風速推定や戦略検出のコアロジックは、FastAPIのバックエンドサービスとして再設計することで、パフォーマンスと拡張性が向上します。

フロントエンド部分は、ReactとNext.jsを使用して完全に再実装することで、より柔軟でインタラクティブなユーザー体験を提供できます。これにより、モバイル対応やオフラインサポートなどの新機能も実現可能になります。

段階的なアプローチで移行を進めることで、途中でもテスト可能な状態を維持しながら、最終的には拡張性と操作性に優れた新システムを構築できます。

## 更新履歴

- 2025-04-18: 初版作成
