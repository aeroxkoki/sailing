# フォーム要素コンポーネント

フォーム要素コンポーネントは、ユーザーからの入力を収集するためのインタラクティブな要素を提供します。テキスト入力、選択ボックス、チェックボックスなど、様々な入力タイプをサポートしています。

## インポート方法

```python
# テキスト入力、数値入力、パスワード入力
from ui.components.forms.input import create_text_input, create_number_input, create_password_input

# セレクトボックス、マルチセレクト
from ui.components.forms.select import create_select, create_multi_select

# チェックボックス
from ui.components.forms.checkbox import create_checkbox, create_checkbox_group

# ラジオボタン
from ui.components.forms.radio import create_radio_group

# テキストエリア
from ui.components.forms.text_area import create_text_area

# スライダー
from ui.components.forms.slider import create_slider, create_range_slider

# 日付ピッカー
from ui.components.forms.date_picker import create_date_picker, create_date_range_picker

# ファイルアップローダー
from ui.components.forms.file_uploader import create_file_uploader
```

## テキスト入力コンポーネント

### テキスト入力

```python
name = create_text_input(
    label="名前",
    value="",  # 初期値（オプション）
    placeholder="名前を入力してください",  # プレースホルダーテキスト（オプション）
    help="氏名をフルネームで入力してください",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    max_chars=None,  # 最大文字数（オプション）
    key=None,  # 一意のキー（オプション）
    label_visibility="visible"  # ラベルの表示設定（オプション）
)

if name:
    st.write(f"こんにちは、{name}さん！")
```

### 数値入力

```python
age = create_number_input(
    label="年齢",
    value=0,  # 初期値（オプション）
    min_value=0,  # 最小値（オプション）
    max_value=120,  # 最大値（オプション）
    step=1,  # 増減量（オプション）
    format=None,  # フォーマット（オプション）
    help="あなたの年齢を入力してください",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    key=None,  # 一意のキー（オプション）
    label_visibility="visible"  # ラベルの表示設定（オプション）
)

if age:
    st.write(f"あなたは{age}歳です。")
```

### パスワード入力

```python
password = create_password_input(
    label="パスワード",
    value="",  # 初期値（オプション）
    placeholder="パスワードを入力してください",  # プレースホルダーテキスト（オプション）
    help="8文字以上の英数字を含むパスワードを設定してください",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    max_chars=None,  # 最大文字数（オプション）
    key=None,  # 一意のキー（オプション）
    label_visibility="visible"  # ラベルの表示設定（オプション）
)

if password:
    st.write("パスワードが入力されました")
```

## 選択コンポーネント

### セレクトボックス（単一選択）

```python
option = create_select(
    label="お好みのセーリングクラス",
    options=["レーザー", "470", "49er", "ナクラ17", "フィン"],
    index=0,  # デフォルトで選択される選択肢のインデックス（オプション）
    format_func=None,  # 選択肢の表示方法をカスタマイズする関数（オプション）
    help="セーリングクラスを選択してください",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    key=None,  # 一意のキー（オプション）
    label_visibility="visible"  # ラベルの表示設定（オプション）
)

st.write(f"選択されたクラス: {option}")
```

### マルチセレクト（複数選択）

```python
options = create_multi_select(
    label="参加したレース",
    options=["ワールドカップ", "全日本選手権", "インターハイ", "アジア選手権", "オリンピック"],
    default=["全日本選手権"],  # デフォルトで選択される選択肢のリスト（オプション）
    format_func=None,  # 選択肢の表示方法をカスタマイズする関数（オプション）
    help="参加したレースを全て選択してください",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    key=None,  # 一意のキー（オプション）
    label_visibility="visible"  # ラベルの表示設定（オプション）
)

if options:
    st.write(f"選択されたレース: {', '.join(options)}")
```

## チェックボックスコンポーネント

### 単一チェックボックス

```python
agree = create_checkbox(
    label="利用規約に同意する",
    value=False,  # 初期値（オプション）
    help="続行するには利用規約に同意する必要があります",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    key=None,  # 一意のキー（オプション）
    label_visibility="visible"  # ラベルの表示設定（オプション）
)

if agree:
    st.write("ありがとうございます。利用規約に同意いただきました。")
else:
    st.write("続行するには利用規約に同意してください。")
```

### チェックボックスグループ

```python
skills = create_checkbox_group(
    label="あなたのスキル",
    options=["セーリング", "ナビゲーション", "気象学", "戦術", "レース規則"],
    default=["セーリング"],  # デフォルトで選択される選択肢のリスト（オプション）
    help="あなたが持っているスキルを選択してください",  # ヘルプテキスト（オプション）
    disabled=False,  # 無効状態（オプション）
    key_prefix=None  # キー生成の際のプレフィックス（オプション）
)

if skills:
    st.write(f"選択されたスキル: {', '.join(skills)}")
```

## オブジェクトと辞書を使用する例

```python
# 辞書のリストを使用した選択肢
boat_options = [
    {"label": "レーザー", "value": "laser"},
    {"label": "470級", "value": "470"},
    {"label": "49er", "value": "49er"},
    {"label": "ナクラ17", "value": "nacra17"},
    {"label": "フィン級", "value": "finn"}
]

# 辞書を値として表示するカスタム関数
def format_boat(boat_dict):
    return f"{boat_dict['label']}"

# 選択コンポーネント
selected_boat = create_select(
    label="ボートクラス",
    options=boat_options,
    format_func=format_boat
)

st.write(f"選択されたボート: {selected_boat['label']} (値: {selected_boat['value']})")
```

## アクセシビリティの考慮事項

フォーム要素コンポーネントは、アクセシビリティを向上させるために以下の機能を備えています：

1. **明確なラベル**:
   - 各フォーム要素には明確なラベルが付いており、スクリーンリーダーで認識できます。

2. **ヘルプテキスト**:
   - 入力要素の目的や入力形式を説明するヘルプテキストを提供できます。

3. **キーボードアクセシビリティ**:
   - すべてのフォーム要素はキーボードでナビゲートおよび操作できます。

4. **フォーカス表示**:
   - キーボードフォーカスは視覚的に明確に表示されます。

5. **入力検証**:
   - 数値入力では範囲制限を設定でき、誤った入力を防ぐことができます。

## ベストプラクティス

1. **明確なラベルとヘルプテキスト**:
   - ユーザーが何を入力すべきかを明確に理解できるよう、具体的なラベルを使用する
   - 必要に応じて、フォーマットや制約を説明するヘルプテキストを追加する

2. **適切な入力タイプの選択**:
   - 用途に最適な入力タイプを選択する（例：数値には `create_number_input` を使用）
   - 複数選択が必要な場合は `create_multi_select` または `create_checkbox_group` を使用

3. **デフォルト値の提供**:
   - 可能な場合は、ユーザーの入力負担を軽減するためにデフォルト値を提供する
   - デフォルト値は最も一般的な選択肢にする

4. **バリデーションとフィードバック**:
   - 入力制約（`min_value`/`max_value`/`max_chars` など）を設定し、無効な入力を防ぐ
   - 入力エラーがあった場合は明確なフィードバックを提供する

5. **レスポンシブ対応**:
   - フォームレイアウトはさまざまな画面サイズに対応する必要がある
   - モバイルでは特にタップターゲットのサイズに注意する

6. **一貫性の維持**:
   - アプリケーション全体で一貫したスタイルとレイアウトを使用する
   - 同様の目的には同様のコンポーネントを使用する

## 技術仕様

### create_text_input

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|入力フィールドのラベル|
|`value`|str|""|初期値|
|`placeholder`|str|None|プレースホルダーテキスト|
|`help`|str|None|ヘルプテキスト|
|`disabled`|bool|False|無効状態にするかどうか|
|`max_chars`|int|None|最大文字数|
|`key`|str|None|コンポーネントの一意のキー|
|`label_visibility`|str|"visible"|ラベルの表示設定 ("visible", "hidden", "collapsed")|

### create_number_input

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|入力フィールドのラベル|
|`value`|int/float|0|初期値|
|`min_value`|int/float|None|最小値|
|`max_value`|int/float|None|最大値|
|`step`|int/float|None|増減量|
|`format`|str|None|表示フォーマット|
|`help`|str|None|ヘルプテキスト|
|`disabled`|bool|False|無効状態にするかどうか|
|`key`|str|None|コンポーネントの一意のキー|
|`label_visibility`|str|"visible"|ラベルの表示設定 ("visible", "hidden", "collapsed")|

### create_select

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|選択コンポーネントのラベル|
|`options`|list|必須|選択肢のリスト|
|`index`|int|0|デフォルトで選択される選択肢のインデックス|
|`format_func`|callable|None|選択肢の表示方法をカスタマイズする関数|
|`help`|str|None|ヘルプテキスト|
|`disabled`|bool|False|無効状態にするかどうか|
|`key`|str|None|コンポーネントの一意のキー|
|`label_visibility`|str|"visible"|ラベルの表示設定 ("visible", "hidden", "collapsed")|

### create_multi_select

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|選択コンポーネントのラベル|
|`options`|list|必須|選択肢のリスト|
|`default`|list|None|デフォルトで選択される選択肢のリスト|
|`format_func`|callable|None|選択肢の表示方法をカスタマイズする関数|
|`help`|str|None|ヘルプテキスト|
|`disabled`|bool|False|無効状態にするかどうか|
|`key`|str|None|コンポーネントの一意のキー|
|`label_visibility`|str|"visible"|ラベルの表示設定 ("visible", "hidden", "collapsed")|

### create_checkbox

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|チェックボックスのラベル|
|`value`|bool|False|初期値|
|`help`|str|None|ヘルプテキスト|
|`disabled`|bool|False|無効状態にするかどうか|
|`key`|str|None|コンポーネントの一意のキー|
|`label_visibility`|str|"visible"|ラベルの表示設定 ("visible", "hidden", "collapsed")|

### create_checkbox_group

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`label`|str|必須|グループのラベル|
|`options`|list|必須|選択肢のリスト|
|`default`|list|[]|デフォルトで選択される選択肢のリスト|
|`help`|str|None|ヘルプテキスト|
|`disabled`|bool|False|全てのチェックボックスを無効状態にするかどうか|
|`key_prefix`|str|自動生成|キー生成の際のプレフィックス|