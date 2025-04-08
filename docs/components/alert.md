# アラートコンポーネント

アラートコンポーネントは、ユーザーに重要な情報、成功メッセージ、警告、またはエラーを通知するために使用されます。さまざまなスタイルがあり、閉じることもできます。

## インポート方法

```python
from ui.components.common.alert import create_alert, create_info_alert, create_success_alert, create_warning_alert, create_error_alert
```

## 基本的な使い方

### 汎用アラート

```python
create_alert(
    message="これはアラートメッセージです。",
    alert_type="info",  # "info", "success", "warning", "error"
    dismissible=False,  # 閉じるボタンを表示するかどうか
    icon=None  # Font Awesomeアイコンクラス（オプション）
)
```

### 情報アラート

情報アラートは、一般的な情報や注意点をユーザーに伝えるために使用されます。

```python
create_info_alert(
    message="ここに情報メッセージを表示します。",
    dismissible=False,  # 閉じるボタンを表示するかどうか
    icon="fas fa-info-circle"  # アイコン（オプション）
)
```

### 成功アラート

成功アラートは、操作が正常に完了したことをユーザーに通知するために使用されます。

```python
create_success_alert(
    message="操作が正常に完了しました。",
    dismissible=False,  # 閉じるボタンを表示するかどうか
    icon="fas fa-check-circle"  # アイコン（オプション）
)
```

### 警告アラート

警告アラートは、注意が必要な情報をユーザーに伝えるために使用されます。

```python
create_warning_alert(
    message="この操作は元に戻せません。続行する前に確認してください。",
    dismissible=False,  # 閉じるボタンを表示するかどうか
    icon="fas fa-exclamation-triangle"  # アイコン（オプション）
)
```

### エラーアラート

エラーアラートは、エラーや問題が発生したことをユーザーに通知するために使用されます。

```python
create_error_alert(
    message="エラーが発生しました。もう一度お試しください。",
    dismissible=False,  # 閉じるボタンを表示するかどうか
    icon="fas fa-times-circle"  # アイコン（オプション）
)
```

## 閉じることができるアラート

アラートを閉じることができるようにするには、`dismissible`パラメータを`True`に設定します。

```python
# 閉じることができる警告アラート
closed = create_warning_alert(
    message="この警告アラートは閉じることができます。右上の✕ボタンをクリックしてください。",
    dismissible=True
)

# アラートが閉じられたときの処理
if closed:
    st.write("アラートが閉じられました")
```

## カスタムアイコンの使用

アラートにはカスタムアイコンを設定できます。アイコンはFont Awesomeクラスを使用して指定します。

```python
# カスタムアイコン付き情報アラート
create_info_alert(
    message="カスタムアイコン付き情報アラート",
    icon="fas fa-lightbulb"
)

# カスタムアイコン付き成功アラート
create_success_alert(
    message="カスタムアイコン付き成功アラート",
    icon="fas fa-thumbs-up"
)
```

## セッション状態の管理

閉じることができるアラートは、Streamlitのセッション状態を使用して閉じた状態を維持します。これにより、ページの再読み込み後も閉じた状態が保持されます。

```python
# セッション状態の管理
if 'alert_closed' not in st.session_state:
    st.session_state.alert_closed = False

if not st.session_state.alert_closed:
    closed = create_warning_alert(
        message="このアラートは一度閉じると再読み込みしても表示されません。",
        dismissible=True
    )
    if closed:
        st.session_state.alert_closed = True
else:
    if st.button("アラートを再表示"):
        st.session_state.alert_closed = False
        st.experimental_rerun()
```

## アラートの組み合わせ

複数のアラートを組み合わせて使用することもできます。

```python
# 複数のアラートを表示
create_info_alert("情報: データ処理が開始されました。")
create_success_alert("成功: ファイルのアップロードが完了しました。")
create_warning_alert("警告: ディスク容量が残り少なくなっています。")
create_error_alert("エラー: データベース接続に失敗しました。")
```

## ベストプラクティス

1. **適切なアラートタイプを選択する**
   - 情報アラート: 一般的な情報や注意点
   - 成功アラート: 操作が正常に完了したことを伝える
   - 警告アラート: 注意が必要な情報や潜在的な問題
   - エラーアラート: エラーや失敗した操作

2. **明確で簡潔なメッセージを作成する**
   - ユーザーが理解しやすい言葉を使用する
   - 必要な情報のみを含め、簡潔にする
   - 必要に応じてアクションを提案する

3. **アイコンを効果的に使用する**
   - アラートの種類に適したアイコンを選択する
   - アイコンはメッセージの内容を補完するものにする

4. **閉じることができるアラートを適切に使用する**
   - 一時的な通知には閉じることができるアラートを使用する
   - 重要な情報や警告には閉じることができないアラートを使用する

5. **アクセシビリティを考慮する**
   - アラートの色だけでなく、アイコンや形状でも情報を伝える
   - 十分なコントラスト比を確保する

## 技術仕様

### create_alert

|プロパティ|タイプ|デフォルト値|説明|
|---|---|---|---|
|`message`|str|必須|アラートに表示するメッセージ|
|`alert_type`|str|"info"|アラートのタイプ ("info", "success", "warning", "error")|
|`dismissible`|bool|False|閉じるボタンを表示するかどうか|
|`icon`|str|None|アラートの前に表示するアイコン（Font Awesomeクラス）|

### 戻り値

- `dismissible=False`の場合: なし
- `dismissible=True`の場合: `bool` - アラートが閉じられたらTrue、そうでなければFalse

### アラートタイプ別のデフォルトアイコン

|アラートタイプ|デフォルトアイコン|
|---|---|
|info|fas fa-info-circle|
|success|fas fa-check-circle|
|warning|fas fa-exclamation-triangle|
|error|fas fa-times-circle|