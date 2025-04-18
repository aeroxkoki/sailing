# Supabase データベーススキーマ設計

本ドキュメントでは、セーリング戦略分析システムの新アーキテクチャで使用するSupabase（PostgreSQL）データベースのスキーマ設計について説明します。

## 1. テーブル構造

### 1.1 users テーブル

ユーザー情報を管理するテーブルです。Supabaseの認証機能と連携します。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | ユーザーID | PRIMARY KEY, NOT NULL |
| email | text | メールアドレス | UNIQUE, NOT NULL |
| full_name | text | 氏名 | NULL許容 |
| avatar_url | text | アバター画像URL | NULL許容 |
| created_at | timestamptz | 作成日時 | DEFAULT now() |
| updated_at | timestamptz | 更新日時 | NULL許容 |
| preferences | jsonb | ユーザー設定（JSONフォーマット） | DEFAULT '{}' |
| last_login | timestamptz | 最終ログイン日時 | NULL許容 |

### 1.2 sessions テーブル

セーリングセッション（練習・レース等）のメタデータを管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | セッションID | PRIMARY KEY, NOT NULL |
| user_id | uuid | 所有者ID | REFERENCES users(id) |
| name | text | セッション名 | NOT NULL |
| location | text | 場所名 | NULL許容 |
| start_time | timestamptz | 開始時間 | NULL許容 |
| end_time | timestamptz | 終了時間 | NULL許容 |
| notes | text | メモ | NULL許容 |
| metadata | jsonb | メタデータ（JSONフォーマット） | DEFAULT '{}' |
| visibility | text | 公開範囲（'private', 'team', 'public'） | DEFAULT 'private' |
| created_at | timestamptz | 作成日時 | DEFAULT now() |
| updated_at | timestamptz | 更新日時 | DEFAULT now() |

### 1.3 tracks テーブル

セッション内の各艇のトラック情報を管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | トラックID | PRIMARY KEY, NOT NULL |
| session_id | uuid | セッションID | REFERENCES sessions(id) |
| boat_id | text | 艇ID（データ内の識別子） | NOT NULL |
| boat_name | text | 艇名 | NULL許容 |
| color | text | 表示色（HEX形式） | DEFAULT '#3B82F6' |
| vessel_type | text | 艇種 | NULL許容 |
| created_at | timestamptz | 作成日時 | DEFAULT now() |
| updated_at | timestamptz | 更新日時 | DEFAULT now() |
| metadata | jsonb | メタデータ（JSONフォーマット） | DEFAULT '{}' |

### 1.4 track_points テーブル

GPSポイントデータを管理するテーブルです。PostGISの地理空間データ型を使用します。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | ポイントID | PRIMARY KEY, NOT NULL |
| track_id | uuid | トラックID | REFERENCES tracks(id) |
| timestamp | timestamptz | タイムスタンプ | NOT NULL |
| position | geography(POINT) | 位置（PostGIS Point型） | NOT NULL |
| speed | float | 速度（m/s） | NULL許容 |
| course | float | 進行方向（度） | NULL許容 |
| raw_data | jsonb | 元データ（JSONフォーマット） | DEFAULT '{}' |

**インデックス**:
- (track_id, timestamp) - ポイントの時系列検索を高速化
- position - 地理空間インデックス

### 1.5 wind_estimates テーブル

風向風速の推定結果を管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | 推定ID | PRIMARY KEY, NOT NULL |
| session_id | uuid | セッションID | REFERENCES sessions(id) |
| timestamp | timestamptz | タイムスタンプ | NOT NULL |
| position | geography(POINT) | 位置（PostGIS Point型） | NULL許容 |
| wind_direction | float | 風向（度） | NOT NULL |
| wind_speed | float | 風速（ノット） | NOT NULL |
| confidence | float | 信頼度（0-1） | DEFAULT 0.5 |
| method | text | 推定方法 | NULL許容 |
| source_track_ids | uuid[] | 推定に使用したトラックID配列 | NULL許容 |
| metadata | jsonb | メタデータ（JSONフォーマット） | DEFAULT '{}' |

**インデックス**:
- (session_id, timestamp) - 時系列検索を高速化
- position - 地理空間インデックス

### 1.6 wind_fields テーブル

風の場（空間的に分布した風向風速）を管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | フィールドID | PRIMARY KEY, NOT NULL |
| session_id | uuid | セッションID | REFERENCES sessions(id) |
| timestamp | timestamptz | タイムスタンプ | NOT NULL |
| resolution | integer | 解像度（グリッドサイズ） | DEFAULT 20 |
| field_data | jsonb | 風の場データ（JSONフォーマット） | NOT NULL |
| bbox | geography(POLYGON) | バウンディングボックス | NULL許容 |
| created_at | timestamptz | 作成日時 | DEFAULT now() |

**インデックス**:
- (session_id, timestamp) - 時系列検索を高速化

### 1.7 strategy_points テーブル

戦略的判断ポイント（タック/ジャイブ、レイライン、風向変化など）を管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | ポイントID | PRIMARY KEY, NOT NULL |
| session_id | uuid | セッションID | REFERENCES sessions(id) |
| track_id | uuid | トラックID | REFERENCES tracks(id) |
| timestamp | timestamptz | タイムスタンプ | NOT NULL |
| position | geography(POINT) | 位置（PostGIS Point型） | NOT NULL |
| type | text | タイプ（'tack', 'jibe', 'layline', 'wind_shift' 等） | NOT NULL |
| importance | float | 重要度（0-1） | DEFAULT 0.5 |
| metadata | jsonb | メタデータ（JSONフォーマット） | DEFAULT '{}' |
| created_at | timestamptz | 作成日時 | DEFAULT now() |

**インデックス**:
- (session_id, type) - タイプ別検索を高速化
- (track_id, timestamp) - トラック内の時系列検索
- position - 地理空間インデックス

### 1.8 statistics テーブル

分析統計情報を管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | 統計ID | PRIMARY KEY, NOT NULL |
| session_id | uuid | セッションID | REFERENCES sessions(id) |
| track_id | uuid | トラックID | REFERENCES tracks(id), NULL許容 |
| category | text | カテゴリー | NOT NULL |
| stats_data | jsonb | 統計データ（JSONフォーマット） | NOT NULL |
| created_at | timestamptz | 作成日時 | DEFAULT now() |
| updated_at | timestamptz | 更新日時 | DEFAULT now() |

**インデックス**:
- (session_id, category) - カテゴリー別検索を高速化

### 1.9 teams テーブル

チーム情報を管理するテーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | チームID | PRIMARY KEY, NOT NULL |
| name | text | チーム名 | NOT NULL |
| description | text | 説明 | NULL許容 |
| owner_id | uuid | オーナーID | REFERENCES users(id) |
| created_at | timestamptz | 作成日時 | DEFAULT now() |
| updated_at | timestamptz | 更新日時 | DEFAULT now() |

### 1.10 team_members テーブル

チームメンバーシップを管理する中間テーブルです。

| カラム名 | データ型 | 説明 | その他 |
|---------|---------|------|--------|
| id | uuid | メンバーシップID | PRIMARY KEY, NOT NULL |
| team_id | uuid | チームID | REFERENCES teams(id) |
| user_id | uuid | ユーザーID | REFERENCES users(id) |
| role | text | 役割（'admin', 'member', 'viewer'） | DEFAULT 'member' |
| joined_at | timestamptz | 参加日時 | DEFAULT now() |

**インデックス**:
- (team_id, user_id) - ユニーク制約（一人のユーザーが同じチームに複数回所属することはできない）

## 2. RLS（Row Level Security）ポリシー

Supabaseのセキュリティ機能であるRLS（Row Level Security）を使用して、データアクセス制御を実装します。

### 2.1 sessions テーブル

```sql
-- 所有者またはチームメンバーのみ読み取り可能
CREATE POLICY "所有者またはチームメンバーのみ読み取り可能" ON sessions
FOR SELECT
USING (
  auth.uid() = user_id
  OR
  EXISTS (
    SELECT 1 FROM team_members tm
    JOIN teams t ON tm.team_id = t.id
    JOIN sessions s ON s.user_id = t.owner_id
    WHERE tm.user_id = auth.uid() AND s.id = sessions.id
  )
  OR
  visibility = 'public'
);

-- 所有者のみ更新可能
CREATE POLICY "所有者のみ更新可能" ON sessions
FOR UPDATE
USING (auth.uid() = user_id);

-- 所有者のみ削除可能
CREATE POLICY "所有者のみ削除可能" ON sessions
FOR DELETE
USING (auth.uid() = user_id);
```

### 2.2 tracks テーブル

```sql
-- セッションの所有者またはチームメンバーのみ読み取り可能
CREATE POLICY "セッションの所有者またはチームメンバーのみ読み取り可能" ON tracks
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM sessions s
    WHERE s.id = tracks.session_id
    AND (
      s.user_id = auth.uid()
      OR
      EXISTS (
        SELECT 1 FROM team_members tm
        JOIN teams t ON tm.team_id = t.id
        WHERE tm.user_id = auth.uid() AND s.user_id = t.owner_id
      )
      OR
      s.visibility = 'public'
    )
  )
);

-- セッションの所有者のみ更新可能
CREATE POLICY "セッションの所有者のみ更新可能" ON tracks
FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM sessions s
    WHERE s.id = tracks.session_id
    AND s.user_id = auth.uid()
  )
);
```

その他のテーブルについても同様のポリシーを設定します。

## 3. 機能別SQLサンプル

### 3.1 セッション一覧の取得

```sql
-- ユーザーのセッション一覧
SELECT s.*, 
  COUNT(DISTINCT t.id) AS track_count,
  MIN(s.start_time) AS session_start,
  MAX(s.end_time) AS session_end,
  COALESCE(
    (SELECT jsonb_agg(json_build_object('type', sp.type, 'count', COUNT(*)))
     FROM strategy_points sp
     WHERE sp.session_id = s.id
     GROUP BY sp.type), 
    '[]'::jsonb
  ) AS strategy_points_summary
FROM sessions s
LEFT JOIN tracks t ON s.id = t.session_id
WHERE s.user_id = auth.uid()
GROUP BY s.id
ORDER BY s.created_at DESC;
```

### 3.2 風向風速の推定結果取得

```sql
-- セッションの風向風速時系列データ
SELECT
  timestamp,
  wind_direction,
  wind_speed,
  confidence,
  method,
  ST_X(position::geometry) AS longitude,
  ST_Y(position::geometry) AS latitude
FROM wind_estimates
WHERE session_id = '00000000-0000-0000-0000-000000000000'
ORDER BY timestamp;
```

### 3.3 戦略ポイントの取得

```sql
-- トラックごとの戦略ポイント
SELECT
  sp.id,
  sp.timestamp,
  sp.type,
  sp.importance,
  sp.metadata,
  ST_X(sp.position::geometry) AS longitude,
  ST_Y(sp.position::geometry) AS latitude,
  t.boat_name,
  t.color
FROM strategy_points sp
JOIN tracks t ON sp.track_id = t.id
WHERE sp.session_id = '00000000-0000-0000-0000-000000000000'
ORDER BY sp.timestamp;
```

### 3.4 地理空間データの操作

```sql
-- 特定の地理的範囲内のトラックポイント取得
SELECT
  tp.id,
  tp.timestamp,
  tp.speed,
  tp.course,
  ST_X(tp.position::geometry) AS longitude,
  ST_Y(tp.position::geometry) AS latitude,
  t.boat_name,
  t.color
FROM track_points tp
JOIN tracks t ON tp.track_id = t.id
WHERE t.session_id = '00000000-0000-0000-0000-000000000000'
AND ST_DWithin(
  tp.position,
  ST_MakePoint(139.65, 35.45)::geography,
  1000  -- 1000メートル以内
)
ORDER BY tp.timestamp;
```

## 4. データマイグレーション戦略

既存のStreamlitアプリケーションからSupabaseへのデータ移行は、以下の手順で行います。

1. **スキーマ作成**:
   - Supabaseダッシュボードでテーブルの作成
   - RLSポリシーの設定

2. **移行スクリプトの作成**:
   - 既存のデータ（GPX, CSVファイル）をインポートするPythonスクリプト
   - データを適切なテーブルに変換・挿入するロジック

3. **段階的なデータ移行**:
   - セッション、トラック、ポイントデータの基本情報を先に移行
   - 分析結果（風向風速推定、戦略ポイント）を後から計算・追加

4. **データ検証**:
   - 移行後のデータの整合性チェック
   - パフォーマンス検証（クエリ速度など）

## 5. 性能に関する考慮事項

### 5.1 インデックス戦略

- 頻繁に使用される検索条件（セッションID、タイムスタンプ、位置など）にはインデックスを設定
- 複合インデックスの活用（例: session_id + timestamp）
- 地理空間データには専用のGiSTインデックスを使用

### 5.2 大規模データへの対応

- track_pointsテーブルはセッションごとに数千〜数万行のデータになる可能性がある
- 長時間のセッションやポイント数が多いデータの場合:
  - 時間範囲でのパーティショニングを検討
  - 表示前のダウンサンプリング機能の実装
  - 大量データ処理用のバッチ処理の導入

### 5.3 キャッシュ戦略

- 頻繁にアクセスされるが更新頻度の低いデータ（風向風速の推定結果など）はキャッシュを検討
- Supabaseの組み込みキャッシュ機能の活用

## 6. 拡張性の考慮

将来的な機能拡張に備えて、以下の項目を考慮したスキーマ設計を行っています。

- **メタデータカラムの追加**: 各テーブルにjsonbタイプの`metadata`カラムを追加し、スキーマ変更なしで追加情報を格納できるようにしています。
- **チーム・グループ機能**: 将来的なコラボレーション機能に備えて、チームとメンバーシップのテーブルを用意しています。
- **統計情報の柔軟な格納**: 様々な統計情報を格納できるように、汎用的な統計テーブルを設計しています。

## 7. まとめ

この設計ドキュメントでは、セーリング戦略分析システムの新アーキテクチャで使用するSupabaseデータベースのスキーマ設計について説明しました。PostgreSQLの機能とSupabaseのセキュリティ機能を活用することで、スケーラブルで安全なデータ管理が可能になります。

地理空間データの処理や時系列データの管理など、セーリングデータの特性に合わせた最適化が行われており、将来の機能拡張にも対応できる柔軟な設計となっています。
