# バッジコンポーネント

バッジコンポーネントは、ステータス、カテゴリ、ラベルなどの情報を簡潔に視覚的に表示するための小さな要素です。様々なスタイル、サイズ、アイコンを使用してカスタマイズできます。

## インポート方法

```python
from ui.components.common.badge import create_badge
```

## 基本的な使い方

```python
create_badge(
    text="新機能",  # バッジに表示するテキスト
    badge_type="primary",  # "primary", "secondary", "success", "warning", "error", "info"
    size="medium",  # "small", "medium", "large"
    icon=None  # Font Awesomeアイコンクラス（オプション）
)
```

## バッジタイプ

バッジには、用途に応じて選択できる複数のスタイルがあります：

### プライマリバッジ

青色のバッジで、主要な情報やカテゴリを表示するのに適しています。

```python
create_badge("プライマリ", badge_type="primary")
```

### セカンダリバッジ

ターコイズ色のバッジで、補助的な情報を表示するのに適しています。

```python
create_badge("セカンダリ", badge_type="secondary")
```

### 成功バッジ

緑色のバッジで、成功や完了済みの状態を示すのに適しています。

```python
create_badge("完了", badge_type="success")
```

### 警告バッジ

オレンジ色のバッジで、注意が必要な状態や項目を示すのに適しています。

```python
create_badge("注意", badge_type="warning")
```

### エラーバッジ

赤色のバッジで、エラーや問題のある状態を示すのに適しています。

```python
create_badge("エラー", badge_type="error")
```

### 情報バッジ

水色のバッジで、便宜的な情報や注記を示すのに適しています。

```python
create_badge("情報", badge_type="info")
```

## サイズバリエーション

バッジには3つのサイズがあります：

### 小サイズ

```python
create_badge("小サイズ", size="small")
```

### 中サイズ（デフォルト）

```python
create_badge("中サイズ", size="medium")
```

### 大サイズ

```python
create_badge("大サイズ", size="large")
```

## アイコン付きバッジ

バッジにはFont Awesomeアイコンを追加することもできます：

```python
# アイコン付きバッジの例
create_badge("新機能", badge_type="primary", icon="fas fa-star")
create_badge("ベータ版", badge_type="secondary", icon="fas fa-flask")
create_badge("完了", badge_type="success", icon="fas fa-check")
create_badge("注意", badge_type="warning", icon="fas fa-exclamation")
create_badge("エラー", badge_type="error", icon="fas fa-times")
create_badge("ヒント", badge_type="info", icon="fas fa-lightbulb")
```

## 実装例

バッジは様々な場面で使用できます：

### ステータス表示

```python
st.write("タスクステータス:")
col1, col2, col3 = st.columns(3)
with col1:
    create_badge("完了", badge_type="success", icon="fas fa-check")
    st.write("データ読み込み")
with col2:
    create_badge("処理中", badge_type="warning", icon="fas fa-spinner")
    st.write("分析処理")
with col3:
    create_badge("未開始", badge_type="error", icon="fas fa-clock")
    st.write("レポート生成")
```

### バージョン表示

```python
st.title("セーリング戦略分析システム")
create_badge("v1.0", badge_type="primary", size="small")
```

### 機能ラベル

```python
st.subheader("風向分析")
create_badge("AI搭載", badge_type="info", icon="fas fa-robot", size="small")
```

### 項目リスト

```python
st.write("利用可能な機能:")
features = [
    {"name": "風向分析", "status": "available", "icon": "fas fa-wind"},
    {"name": "タック検出", "status": "available", "icon": "fas fa-exchange-alt"},
    {"name": "レース比較", "status": "beta", "icon": "fas fa-chart-line"},
    {"name": "予測モデル", "status": "coming_soon", "icon": "fas fa-crystal-ball"}
]

for feature in features:
    col1, col2 = st.columns([1, 4])
    with col1:
        if feature["status"] == "available":
            create_badge("利用可", badge_type="success", icon="fas fa-check")
        elif feature["status"] == "beta":
            create_badge("ベータ版", badge_type="warning", icon="fas fa-flask")
        else:
            create_badge("近日公開", badge_type="secondary", icon="fas fa-clock")
    with col2:
        st.write(f"{feature['name']}")
```

## ベストプラクティス

1. **目的に合ったバッジタイプを選択する**
   - プライマリバッジ: 主要な情報、カテゴリ
   - 成功バッジ: 完了、利用可能な状態
   - 警告バッジ: 注意が必要な項目、ベータ版
   - エラーバッジ: 問題、利用不可の状態
   - 情報バッジ: 中立的な情報、補足

2. **簡潔なテキストを使用する**
   - バッジは小さなスペースのため、短いテキスト（1〜2語）が最適
   - 長いテキストはバッジの視覚的効果を損なう

3. **アイコンを効果的に使用する**
   - テキストを補完するアイコンを選択
   - 一般的に認知されるアイコンを使用
   - アイコンとテキストの両方で情報を伝える（アクセシビリティ向上）

4. **適切なサイズを選択する**
   - 表示コンテキストに合わせてサイズを調整
   - ヘッダーの横には小さいバッジ
   - リストアイテムには中サイズのバッジ
   - 強調したい場合は大きいバッジ

5. **過剰使用を避ける**
   - バッジは視覚的注目を集めるため、重要な情報にのみ使用
   - 1つの画面に多すぎるバッジを配置しない

## 技術仕様

### create_badge

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`text`|str|必須|バッジに表示するテキスト|
|`badge_type`|str|"primary"|バッジのタイプ ("primary", "secondary", "success", "warning", "error", "info")|
|`size`|str|"medium"|バッジのサイズ ("small", "medium", "large")|
|`icon`|str|None|バッジの前に表示するアイコン（Font Awesomeクラス）|

### バッジタイプ別の色設定

|バッジタイプ|背景色|テキスト色|
|---|---|---|
|primary|#1565C0 (濃い青)|白|
|secondary|#00ACC1 (ターコイズ)|白|
|success|#26A69A (緑)|白|
|warning|#FFA726 (オレンジ)|黒|
|error|#EF5350 (赤)|白|
|info|#2196F3 (水色)|白|

### サイズ別の設定

|サイズ|フォントサイズ|パディング|アイコンサイズ|
|---|---|---|---|
|small|10px|2px 6px|8px|
|medium|12px|3px 8px|12px|
|large|14px|4px 12px|14px|