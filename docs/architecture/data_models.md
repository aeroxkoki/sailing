# セーリング戦略分析システム - データモデル設計書

## 概要

本ドキュメントでは、セーリング戦略分析システムの新アーキテクチャにおけるデータモデルの設計について詳述します。
データモデルはPydanticを使用して定義され、PostgreSQL（Supabase）に保存されます。

## 主要エンティティ

### 1. ユーザー（User）

ユーザー情報と認証データを管理します。

```python
class User(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    hashed_password: str  # APIではフィルタリングされる
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
```

**テーブル名**: `users`

### 2. ユーザー設定（UserPreference）

ユーザー固有の設定情報を保存します。

```python
class UserPreference(BaseModel):
    id: UUID
    user_id: UUID
    theme: str = "light"
    default_boat_type: Optional[str] = None
    default_location: Optional[str] = None
    default_units: str = "metric"
    map_preferences: Dict[str, Any] = Field(default_factory=dict)
    analysis_preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
```

**テーブル名**: `user_preferences`

### 3. セッション（Session）

セーリングセッションのメタデータを管理します。

```python
class Session(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    visibility: str = "private"  # private, team, public
    created_at: datetime
    updated_at: datetime
```

**テーブル名**: `sessions`

### 4. トラック（Track）

GPSトラックデータを管理します。

```python
class Track(BaseModel):
    id: UUID
    session_id: UUID
    boat_id: Optional[str] = None
    boat_name: str
    vessel_type: Optional[str] = None
    color: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    points_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
```

**テーブル名**: `tracks`

### 5. トラックポイント（TrackPoint）

GPSトラックの各ポイントデータを保存します。

```python
class TrackPoint(BaseModel):
    id: UUID
    track_id: UUID
    timestamp: datetime
    latitude: float
    longitude: float
    speed: Optional[float] = None
    course: Optional[float] = None
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**テーブル名**: `track_points`

※サイズが大きくなるため、パーティショニングとインデックス最適化が必要です。

### 6. 風データ（WindData）

風向風速の推定結果を保存します。

```python
class WindData(BaseModel):
    id: UUID
    session_id: UUID
    estimation_method: str
    timestamp: datetime
    wind_direction: float
    wind_speed: float
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
```

**テーブル名**: `wind_data`

### 7. 風フィールド（WindField）

空間的な風向風速分布を保存します。

```python
class WindField(BaseModel):
    id: UUID
    session_id: UUID
    timestamp: datetime
    resolution: int
    bounds: Dict[str, float]  # min_lat, max_lat, min_lon, max_lon
    grid_lats: List[float]
    grid_lons: List[float]
    directions: List[List[float]]
    speeds: List[List[float]]
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**テーブル名**: `wind_fields`

### 8. 戦略ポイント（StrategyPoint）

検出された戦略的判断ポイントを保存します。

```python
class StrategyPoint(BaseModel):
    id: UUID
    session_id: UUID
    track_id: UUID
    point_type: str  # tack, jibe, wind_shift, layline, etc.
    timestamp: datetime
    latitude: float
    longitude: float
    importance: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
```

**テーブル名**: `strategy_points`

### 9. 分析タスク（AnalysisTask）

非同期分析タスクのステータスを管理します。

```python
class AnalysisTask(BaseModel):
    id: UUID
    user_id: UUID
    session_id: Optional[UUID] = None
    task_type: str
    status: str  # pending, processing, completed, failed
    progress: int = 0
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
```

**テーブル名**: `analysis_tasks`

### 10. レポート（Report）

生成されたレポートを管理します。

```python
class Report(BaseModel):
    id: UUID
    user_id: UUID
    session_id: UUID
    title: str
    description: Optional[str] = None
    template_id: str
    format: str  # pdf, html, etc.
    file_path: str
    file_size: int
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**テーブル名**: `reports`

### 11. チーム（Team）

ユーザーグループを管理します。

```python
class Team(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
```

**テーブル名**: `teams`

### 12. チームメンバー（TeamMember）

チームのメンバーシップを管理します。

```python
class TeamMember(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    role: str  # owner, admin, member
    status: str  # active, invited, declined
    invited_at: datetime
    joined_at: Optional[datetime] = None
```

**テーブル名**: `team_members`

## リレーション図

```
User 1--* UserPreference
User 1--* Session
User 1--* AnalysisTask
User 1--* Report
User 1--* TeamMember
Session 1--* Track
Session 1--* WindData
Session 1--* WindField
Session 1--* StrategyPoint
Session 1--* Report
Track 1--* TrackPoint
Track 1--* StrategyPoint
Team 1--* TeamMember
Team 1--* Session (via shared_sessions)
```

## データベース最適化

### インデックス

- `track_points`テーブル
  - `(track_id, timestamp)` - 複合インデックス
  - `(latitude, longitude)` - 地理空間インデックス

- `wind_data`テーブル
  - `(session_id, timestamp)` - 複合インデックス

- `strategy_points`テーブル
  - `(session_id, point_type)` - 複合インデックス
  - `(track_id, timestamp)` - 複合インデックス

### パーティショニング

大量のデータを保存する`track_points`テーブルは、セッションIDまたは時間範囲でパーティショニングすることを推奨します。

```sql
CREATE TABLE track_points (
    id UUID PRIMARY KEY,
    track_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    -- 他のフィールド
) PARTITION BY RANGE (timestamp);

CREATE TABLE track_points_2025_q1 PARTITION OF track_points
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE track_points_2025_q2 PARTITION OF track_points
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

-- 他のパーティション
```

## 非正規化と集計テーブル

パフォーマンス向上のために、以下の集計テーブルを導入します。

### セッションサマリー（SessionSummary）

```python
class SessionSummary(BaseModel):
    session_id: UUID
    total_distance: float
    total_duration: float
    max_speed: float
    avg_speed: float
    wind_summary: Dict[str, Any]
    strategy_points_count: Dict[str, int]
    calculated_at: datetime
```

**テーブル名**: `session_summaries`

## マイグレーション戦略

新しいデータベース構造への移行は段階的に行います：

1. スキーマ定義とマイグレーションスクリプトの作成
2. 既存のStreamlitアプリでエクスポートしたデータの変換ユーティリティの実装
3. Supabase初期化スクリプトの作成
4. データインポートとバリデーション

Alembicを使用したマイグレーション管理を導入します。

## 更新履歴

- 2025-04-18: 初版作成
