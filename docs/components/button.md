# ボタンコンポーネント

ボタンコンポーネントは、ユーザーがアクションを実行するためのインタラクティブな要素を提供します。さまざまなスタイルとサイズのバリエーションがあり、アイコンを追加することもできます。

## インポート方法

```python
from ui.components.common.button import create_button, create_primary_button, create_secondary_button, create_text_button, create_warning_button
```

## 基本的な使い方

### 汎用ボタン

```python
clicked = create_button(
    label="ボタンテキスト",
    button_type="primary",  # "primary", "secondary", "text", "warning"
    size="medium",  # "small", "medium", "large"
    icon=None,  # Font Awesomeクラス（例: "fas fa-save"）
    on_click=None,  # クリック時に実行する関数
    key=None  # ボタンの一意のキー
)

if clicked:
    # ボタンがクリックされたときの処理
    st.write("ボタンがクリックされました！")
```

### プライマリボタン

プライマリボタンは、主要なアクションやページの主な目的のために使用されます。

```python
clicked = create_primary_button(
    label="保存",
    size="medium",
    icon="fas fa-save",
    key="save_button"
)

if clicked:
    # 保存処理
    st.success("保存しました！")
```

### セカンダリボタン

セカンダリボタンは、補助的なアクションや代替オプションのために使用されます。

```python
clicked = create_secondary_button(
    label="キャンセル",
    size="medium",
    key="cancel_button"
)

if clicked:
    # キャンセル処理
    st.info("キャンセルしました")
```

### テキストボタン

テキストボタンは、影響の少ないアクションやナビゲーションリンクに使用されます。

```python
clicked = create_text_button(
    label="詳細を見る",
    size="medium",
    icon="fas fa-external-link-alt",
    key="details_button"
)

if clicked:
    # 詳細表示処理
    st.session_state.show_details = True
```

### 警告ボタン

警告ボタンは、削除やリセットなどの取り消せないアクションに使用されます。

```python
clicked = create_warning_button(
    label="削除",
    size="medium",
    icon="fas fa-trash",
    key="delete_button"
)

if clicked:
    # 削除処理の前に確認
    st.warning("本当に削除しますか？")
    confirmed = st.button("はい、削除します")
    if confirmed:
        # 削除処理
        st.success("削除しました")
```

## サイズバリエーション

ボタンには3つのサイズバリエーションがあります：

### 小サイズ

```python
create_primary_button("小ボタン", size="small")
```

### 中サイズ（デフォルト）

```python
create_primary_button("中ボタン", size="medium")
```

### 大サイズ

```python
create_primary_button("大ボタン", size="large")
```

## アイコンの使用

ボタンにはFont Awesomeアイコンを追加できます。アイコンはボタンテキストの前に表示されます。

```python
create_primary_button("保存", icon="fas fa-save")
create_secondary_button("編集", icon="fas fa-edit")
create_text_button("検索", icon="fas fa-search")
create_warning_button("削除", icon="fas fa-trash")
```

## カスタム関数の実行

`on_click`パラメータを使用して、ボタンクリック時に実行するカスタム関数を指定できます。

```python
def handle_click():
    st.session_state.count = st.session_state.get('count', 0) + 1
    st.success(f"ボタンが {st.session_state.count} 回クリックされました！")

create_primary_button("カウントアップ", on_click=handle_click)
```

## ベストプラクティス

1. **適切なボタンタイプを選択する**
   - プライマリボタン：メインアクション（保存、送信など）
   - セカンダリボタン：代替アクション（キャンセル、戻るなど）
   - テキストボタン：軽微なアクション（詳細表示、ヘルプなど）
   - 警告ボタン：破壊的アクション（削除、リセットなど）

2. **明確なラベルを使用する**
   - 動詞で始めるのが理想的（「保存」「削除」など）
   - 短く具体的に
   - ユーザーが何を期待すべきかを明確に

3. **アイコンを効果的に使用する**
   - アクションを視覚的に強化するアイコンを選択
   - 一般的に認知されるアイコンを使用
   - アイコンのみのボタンは避ける（アクセシビリティの観点から）

4. **レスポンシブな対応**
   - モバイル向けには大きめのボタンサイズを考慮
   - タッチターゲットは最低44×44ピクセルが推奨

5. **フィードバックを提供する**
   - ボタンクリック後は何らかの視覚的フィードバックを提供
   - 処理に時間がかかる場合は進行状況を表示

## 技術仕様

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|ボタンに表示するテキスト|
|`button_type`|str|"primary"|ボタンのタイプ ("primary", "secondary", "text", "warning")|
|`size`|str|"medium"|ボタンのサイズ ("small", "medium", "large")|
|`icon`|str|None|ボタンの前に表示するアイコン（Font Awesomeクラス）|
|`on_click`|callable|None|クリック時に実行する関数|
|`key`|str|None|ボタンの一意のキー|

## アクセシビリティの考慮事項

- ボタンにはキーボードフォーカスの視覚的表示があります
- アイコンのみのボタンは使用を避けるか、適切なARIA属性を提供してください
- 色だけでなく、形や位置でもボタンの種類を識別できるようにしています
- 十分なコントラスト比を確保しています