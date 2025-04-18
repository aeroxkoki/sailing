# セーリング戦略分析システム - API設計書

## 概要

本ドキュメントでは、セーリング戦略分析システムの新アーキテクチャにおけるAPIの設計について詳述します。
APIはFastAPIを使用して実装され、フロントエンド（Next.js）とデータベース（Supabase）の間の通信を担当します。

## API構造

APIエンドポイントは以下のリソースに分類されます：

- データインポート/エクスポート
- セッション管理
- 風向風速分析
- 戦略ポイント検出
- データ可視化
- レポート生成
- ユーザー管理

## エンドポイント詳細

### 認証

```
POST /api/v1/auth/login         - ユーザーログイン
POST /api/v1/auth/register      - ユーザー登録
POST /api/v1/auth/refresh       - トークンリフレッシュ
POST /api/v1/auth/logout        - ログアウト
```

### データインポート

```
POST /api/v1/import/gpx         - GPXファイルのインポート
POST /api/v1/import/csv         - CSVファイルのインポート
POST /api/v1/import/tcx         - TCXファイルのインポート
POST /api/v1/import/fit         - FITファイルのインポート
POST /api/v1/import/batch       - 複数ファイルの一括インポート
```

#### リクエスト例（GPXインポート）:

```json
{
  "file": [バイナリデータ],
  "options": {
    "timezone": "Asia/Tokyo",
    "interpolate_missing": true,
    "auto_detect_stops": true
  }
}
```

#### レスポンス例:

```json
{
  "status": "success",
  "data": {
    "session_id": "f8a7b6c5-d4e3-2f1g-9h8i-7j6k5l4m3n2o",
    "points_count": 1250,
    "duration": "01:23:45",
    "distance": 12.34,
    "metadata": {
      "boat_type": "470",
      "started_at": "2025-04-17T10:30:00+09:00"
    }
  }
}
```

### セッション管理

```
GET    /api/v1/sessions               - セッション一覧の取得
POST   /api/v1/sessions               - 新規セッションの作成
GET    /api/v1/sessions/{id}          - セッション詳細の取得
PUT    /api/v1/sessions/{id}          - セッション情報の更新
DELETE /api/v1/sessions/{id}          - セッションの削除
GET    /api/v1/sessions/{id}/data     - セッションデータの取得
PUT    /api/v1/sessions/{id}/metadata - セッションメタデータの更新
```

#### レスポンス例（セッション一覧）:

```json
{
  "sessions": [
    {
      "id": "f8a7b6c5-d4e3-2f1g-9h8i-7j6k5l4m3n2o",
      "name": "東京湾トレーニング 2025-04-17",
      "created_at": "2025-04-17T10:30:00+09:00",
      "updated_at": "2025-04-17T15:45:00+09:00",
      "duration": "01:23:45",
      "boat_type": "470",
      "location": "東京湾",
      "summary": {
        "distance_nm": 12.34,
        "avg_speed_kt": 5.6,
        "max_speed_kt": 7.8,
        "estimated_wind": {
          "direction": 225,
          "speed": 15.4
        }
      }
    },
    // ...他のセッション
  ],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

### 風向風速分析

```
POST   /api/v1/wind/estimate          - GPSデータからの風向風速推定
GET    /api/v1/wind/estimate/{id}     - 推定結果の取得
POST   /api/v1/wind/analyze           - 風パターンの詳細分析
GET    /api/v1/wind/field             - 風向風速フィールドの取得
POST   /api/v1/wind/integrate         - 複数データソースからの風データ統合
```

#### リクエスト例（風向風速推定）:

```json
{
  "session_id": "f8a7b6c5-d4e3-2f1g-9h8i-7j6k5l4m3n2o",
  "options": {
    "boat_type": "470",
    "use_bayesian": true,
    "min_tack_angle": 30.0
  }
}
```

#### レスポンス例:

```json
{
  "status": "success",
  "data": {
    "estimation_id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
    "wind": {
      "direction": 225,
      "speed": 15.4,
      "confidence": 0.87,
      "method": "bayesian_fusion"
    },
    "maneuvers_detected": 8,
    "time_series": [
      {
        "timestamp": "2025-04-17T10:30:15+09:00",
        "wind_direction": 226,
        "wind_speed": 15.2
      },
      // ...その他のデータポイント
    ]
  }
}
```

### 戦略ポイント検出

```
POST   /api/v1/strategy/detect        - 戦略ポイントの検出
GET    /api/v1/strategy/detect/{id}   - 検出結果の取得
GET    /api/v1/strategy/points        - 検出された戦略ポイントの取得
POST   /api/v1/strategy/evaluate      - 戦略ポイントの評価
POST   /api/v1/strategy/optimize      - 最適戦略の提案
```

#### リクエスト例（戦略ポイント検出）:

```json
{
  "session_id": "f8a7b6c5-d4e3-2f1g-9h8i-7j6k5l4m3n2o",
  "wind_estimation_id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
  "options": {
    "min_wind_shift_angle": 5.0,
    "tack_search_radius": 500,
    "min_vmg_improvement": 0.05
  }
}
```

#### レスポンス例:

```json
{
  "status": "success",
  "data": {
    "detection_id": "q1w2e3r4-t5y6-u7i8-o9p0-a1s2d3f4g5h6",
    "points_count": 15,
    "points": [
      {
        "id": "point-1",
        "type": "tack",
        "timestamp": "2025-04-17T10:35:45+09:00",
        "position": {
          "lat": 35.45678,
          "lon": 139.78901
        },
        "before_course": 320,
        "after_course": 42,
        "wind_direction": 225,
        "evaluation": {
          "timing": 0.85,
          "execution": 0.78,
          "vmg_improvement": 0.12
        }
      },
      {
        "id": "point-2",
        "type": "wind_shift",
        "timestamp": "2025-04-17T10:42:15+09:00",
        "position": {
          "lat": 35.46789,
          "lon": 139.79012
        },
        "before_direction": 225,
        "after_direction": 235,
        "magnitude": 10,
        "duration": 180
      },
      // ...その他のポイント
    ]
  }
}
```

### データ可視化

```
GET    /api/v1/visualization/map/{session_id}      - セッションのマップデータ取得
GET    /api/v1/visualization/timeline/{session_id} - タイムラインデータ取得
GET    /api/v1/visualization/charts/{session_id}   - チャートデータ取得
GET    /api/v1/visualization/wind-field/{session_id} - 風フィールドデータ取得
```

#### レスポンス例（マップデータ）:

```json
{
  "status": "success",
  "data": {
    "center": {
      "lat": 35.46789,
      "lon": 139.79012
    },
    "track": [
      {
        "timestamp": "2025-04-17T10:30:15+09:00",
        "position": {
          "lat": 35.45678,
          "lon": 139.78901
        },
        "speed": 5.6,
        "course": 320
      },
      // ...その他のトラックポイント
    ],
    "strategy_points": [
      // 戦略ポイントデータ
    ],
    "wind_field": {
      // 風フィールドデータ
    }
  }
}
```

### レポート生成

```
POST   /api/v1/reports/generate       - レポートの生成
GET    /api/v1/reports/templates      - レポートテンプレートの取得
GET    /api/v1/reports/{id}           - 生成済みレポートの取得
POST   /api/v1/reports/export         - 各種形式でのエクスポート
```

#### リクエスト例（レポート生成）:

```json
{
  "session_id": "f8a7b6c5-d4e3-2f1g-9h8i-7j6k5l4m3n2o",
  "template_id": "performance_analysis",
  "options": {
    "include_charts": true,
    "include_map": true,
    "include_recommendations": true
  },
  "format": "pdf"
}
```

#### レスポンス例:

```json
{
  "status": "success",
  "data": {
    "report_id": "r1t2y3u4-i5o6-p7a8-s9d0-f1g2h3j4k5l6",
    "title": "パフォーマンス分析レポート - 東京湾トレーニング 2025-04-17",
    "created_at": "2025-04-18T09:30:00+09:00",
    "format": "pdf",
    "file_size": 1245678,
    "download_url": "https://api.example.com/downloads/reports/r1t2y3u4-i5o6-p7a8-s9d0-f1g2h3j4k5l6.pdf"
  }
}
```

### ユーザー管理

```
GET    /api/v1/users/me               - 現在のユーザー情報取得
PUT    /api/v1/users/me               - ユーザー情報更新
GET    /api/v1/users/preferences      - ユーザー設定取得
PUT    /api/v1/users/preferences      - ユーザー設定更新
```

## ステータスコード

APIは以下の標準HTTPステータスコードを使用します：

- 200 OK: リクエストが成功
- 201 Created: リソースの作成が成功
- 400 Bad Request: リクエストの形式が不正
- 401 Unauthorized: 認証が必要
- 403 Forbidden: アクセス権限がない
- 404 Not Found: リソースが見つからない
- 422 Unprocessable Entity: バリデーションエラー
- 500 Internal Server Error: サーバー内部エラー

## エラーレスポンス形式

エラーの場合は以下の形式でレスポンスが返されます：

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "入力データが不正です",
  "details": {
    "field": "options.min_wind_shift_angle",
    "error": "数値は0より大きい必要があります"
  }
}
```

## バージョニング

APIはバージョン管理されており、現在のバージョンは `v1` です。将来的な変更に備えて、全てのエンドポイントは `/api/v1/` の形式でプレフィックスが付与されています。

## 認証とセキュリティ

APIはJWTトークンベースの認証を使用します。アクセストークンは `/api/v1/auth/login` エンドポイントから取得でき、リクエストの `Authorization` ヘッダーで以下のように提供する必要があります：

```
Authorization: Bearer <access_token>
```

アクセストークンの有効期限が切れた場合は、リフレッシュトークンを使用して `/api/v1/auth/refresh` エンドポイントから新しいトークンを取得できます。

## レート制限

APIにはレート制限があり、一定期間内のリクエスト数を制限しています。制限に達した場合は、429 Too Many Requests レスポンスが返されます。

## 更新履歴

- 2025-04-18: 初版作成
