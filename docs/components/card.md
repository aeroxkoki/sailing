# カードコンポーネント

カードコンポーネントは、関連するコンテンツをグループ化して表示するためのコンテナ要素です。タイトル、サブタイトル、コンテンツ、フッターといった構造化された形式で情報を提示します。

## インポート方法

```python
from ui.components.common.card import create_card, create_info_card, create_action_card
```

## 基本的な使い方

### 標準カード

```python
create_card(
    title="カードタイトル",
    subtitle="サブタイトル（オプション）",
    content="カードの本文内容。<br>HTMLタグも使用できます。",
    footer="フッターテキスト（オプション）",
    padding="normal",  # "small", "normal", "large"
    shadow=True,  # 影をつけるかどうか
    border=False  # 枠線をつけるかどうか
)
```

### 情報カード

情報カードは、特定の種類の情報を視覚的に区別して表示するためのカードです。

```python
create_info_card(
    title="お知らせ",
    content="これは重要な情報です。",
    color=Colors.INFO,  # Colors.INFO, Colors.SUCCESS, Colors.WARNING, Colors.ERROR など
    icon="fas fa-info-circle"  # Font Awesomeアイコンクラス（オプション）
)
```

### アクション付きカード

アクション付きカードは、ユーザーがアクションを実行できるボタンを含むカードです。

```python
actions = [
    {"label": "詳細", "key": "view", "type": "secondary"},
    {"label": "編集", "key": "edit", "type": "primary"},
    {"label": "削除", "key": "delete", "type": "warning"}
]

result = create_action_card(
    title="アクション付きカード",
    content="このカードには複数のアクションボタンがあります。",
    actions=actions,
    padding="normal",
    shadow=True
)

# クリックされたアクションの処理
for key, clicked in result.items():
    if clicked:
        if key == "view":
            # 詳細表示の処理
            st.write("詳細ボタンがクリックされました")
        elif key == "edit":
            # 編集処理
            st.write("編集ボタンがクリックされました")
        elif key == "delete":
            # 削除処理
            st.write("削除ボタンがクリックされました")
```

## スタイルカスタマイズ

### パディングのサイズ

カードのパディング（内側の余白）は3つのサイズから選択できます：

```python
# 小さいパディング
create_card(title="小パディングカード", content="コンテンツ", padding="small")

# 標準パディング（デフォルト）
create_card(title="標準パディングカード", content="コンテンツ", padding="normal")

# 大きいパディング
create_card(title="大パディングカード", content="コンテンツ", padding="large")
```

### 影と枠線

カードには影や枠線を追加してスタイルをカスタマイズできます：

```python
# 影付きカード（デフォルト）
create_card(title="影付きカード", content="コンテンツ", shadow=True)

# 枠線付きカード
create_card(title="枠線付きカード", content="コンテンツ", border=True, shadow=False)

# 影と枠線の両方があるカード
create_card(title="影と枠線付きカード", content="コンテンツ", shadow=True, border=True)
```

## 情報カードのバリエーション

情報カードには、さまざまなタイプの情報を表す色とアイコンを設定できます：

```python
# 情報（青）
create_info_card(
    title="情報",
    content="これは一般的な情報です。",
    color=Colors.INFO,
    icon="fas fa-info-circle"
)

# 成功（緑）
create_info_card(
    title="成功",
    content="操作が成功しました。",
    color=Colors.SUCCESS,
    icon="fas fa-check-circle"
)

# 警告（オレンジ）
create_info_card(
    title="警告",
    content="注意が必要です。",
    color=Colors.WARNING,
    icon="fas fa-exclamation-triangle"
)

# エラー（赤）
create_info_card(
    title="エラー",
    content="問題が発生しました。",
    color=Colors.ERROR,
    icon="fas fa-times-circle"
)
```

## アクション付きカードの設定

アクション付きカードでは、各アクションに以下のプロパティを設定できます：

```python
actions = [
    {
        "label": "表示",  # ボタンのラベル（必須）
        "key": "view",    # 一意のキー（オプション、デフォルトは自動生成）
        "type": "secondary"  # ボタンタイプ（オプション、デフォルトは"secondary"）
                            # "primary", "secondary", "text", "warning"から選択
    }
]
```

## HTMLコンテンツのサポート

カードのコンテンツとフッターにはHTMLタグを使用できます：

```python
create_card(
    title="HTMLサポート",
    content="""
        <h4>HTMLフォーマット</h4>
        <p>このカードには<strong>HTML</strong>コンテンツが含まれています。</p>
        <ul>
            <li>リスト項目1</li>
            <li>リスト項目2</li>
        </ul>
    """,
    footer="<em>フッターテキスト</em>"
)
```

## カード内のレイアウト

カード内で複数の要素を配置する例：

```python
content = f"""
    <div style="display: flex; align-items: center; gap: 16px;">
        <div style="flex: 0 0 64px;">
            <img src="https://via.placeholder.com/64" alt="アイコン" style="border-radius: 8px;">
        </div>
        <div style="flex: 1;">
            <h4 style="margin: 0 0 8px 0;">項目名</h4>
            <p style="margin: 0;">説明テキストが入ります。</p>
        </div>
    </div>
"""

create_card(content=content)
```

## ベストプラクティス

1. **適切な目的に使用する**
   - 関連する情報をグループ化する
   - 視覚的に区切りたいコンテンツに使用する
   - 複数のカードを使用する場合は一貫した構造を保つ

2. **適切な情報量**
   - カードには適切な量の情報を含める
   - 情報過多を避け、必要に応じて「詳細を見る」などのアクションを提供

3. **視覚的階層**
   - 重要な情報はタイトルやサブタイトルに配置
   - 視覚的な優先順位を考慮（タイトル→サブタイトル→コンテンツ→フッター）

4. **アクセシビリティ**
   - 適切なコントラスト比を確保
   - HTMLコンテンツを使用する場合は適切なセマンティックタグを使用

5. **レスポンシブデザイン**
   - 画面サイズに応じてカードがどのように表示されるか考慮
   - モバイル表示では特に余白と情報量に注意

## 技術仕様

### create_card

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`title`|str|None|カードのタイトル|
|`subtitle`|str|None|カードのサブタイトル|
|`content`|str|None|カードの本文内容（HTML対応）|
|`footer`|str|None|カードのフッター内容（HTML対応）|
|`padding`|str|"normal"|内側の余白サイズ ("small", "normal", "large")|
|`shadow`|bool|True|影をつけるかどうか|
|`border`|bool|False|枠線をつけるかどうか|

### create_info_card

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`title`|str|None|カードのタイトル|
|`content`|str|None|カードの本文内容（HTML対応）|
|`color`|str|Colors.INFO|カードのアクセントカラー|
|`icon`|str|None|表示するアイコン（Font Awesomeクラス）|

### create_action_card

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`title`|str|必須|カードのタイトル|
|`content`|str|None|カードの本文内容（HTML対応）|
|`actions`|list|None|アクションボタンの設定リスト|
|`padding`|str|"normal"|内側の余白サイズ ("small", "normal", "large")|
|`shadow`|bool|True|影をつけるかどうか|

### actionsリストの各項目

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|ボタンのラベル|
|`key`|str|自動生成|ボタンの一意のキー|
|`type`|str|"secondary"|ボタンのタイプ ("primary", "secondary", "text", "warning")|