# セーリング戦略分析システム - UIコンポーネントライブラリ

このドキュメントでは、セーリング戦略分析システムのUIコンポーネントライブラリの使い方を説明します。

## 目次

1. [はじめに](#1-はじめに)
2. [共通コンポーネント](#2-共通コンポーネント)
   1. [ボタン](#21-ボタン)
   2. [カード](#22-カード)
   3. [アラート](#23-アラート)
   4. [バッジ](#24-バッジ)
   5. [ツールチップ](#25-ツールチップ)
   6. [レイアウトヘルパー](#26-レイアウトヘルパー)
3. [フォーム要素](#3-フォーム要素)
   1. [テキスト入力](#31-テキスト入力)
   2. [選択コンポーネント](#32-選択コンポーネント)
   3. [チェックボックス](#33-チェックボックス)
4. [ナビゲーションコンポーネント](#4-ナビゲーションコンポーネント)
5. [コンポーネント組み合わせの例](#5-コンポーネント組み合わせの例)
6. [ベストプラクティス](#6-ベストプラクティス)

## 1. はじめに

UIコンポーネントライブラリは、セーリング戦略分析システムのUI開発を効率化し、一貫性を確保するために設計されています。このライブラリは、UI/UXデザインガイドラインに基づいて実装されており、Streamlitフレームワーク上で動作します。

### インポート方法

コンポーネントを使用するには、必要なコンポーネントを以下のようにインポートします：

```python
# 共通コンポーネント
from ui.components.common.button import create_primary_button
from ui.components.common.card import create_card
from ui.components.common.alert import create_info_alert

# フォーム要素
from ui.components.forms.input import create_text_input
from ui.components.forms.select import create_select
```

## 2. 共通コンポーネント

### 2.1 ボタン

ボタンコンポーネントは、ユーザーアクションを促すために使用されます。

#### 基本的な使い方

```python
from ui.components.common.button import create_primary_button, create_secondary_button

# プライマリボタン
if create_primary_button("保存"):
    # クリック時の処理
    save_data()

# セカンダリボタン
if create_secondary_button("キャンセル"):
    # クリック時の処理
    cancel_action()
```

#### 利用可能なボタンタイプ

- `create_primary_button` - メインアクション用の強調ボタン
- `create_secondary_button` - 補助的なアクション用のボタン
- `create_text_button` - テキストのみのシンプルなボタン
- `create_warning_button` - 警告アクションのためのボタン

#### サイズとアイコン

すべてのボタンタイプは、サイズとアイコンをカスタマイズできます：

```python
# サイズバリエーション（"small", "medium", "large"）
create_primary_button("小ボタン", size="small")
create_primary_button("中ボタン", size="medium")  # デフォルト
create_primary_button("大ボタン", size="large")

# アイコン付きボタン（Font Awesomeクラス）
create_primary_button("保存", icon="fas fa-save")
```

### 2.2 カード

カードコンポーネントは、関連する情報をグループ化するために使用されます。

#### 基本的な使い方

```python
from ui.components.common.card import create_card, create_info_card, create_action_card

# 基本カード
create_card(
    title="基本カード",
    subtitle="サブタイトル",
    content="カードの内容をここに記述します。",
    footer="カードのフッター"
)

# 情報カード
create_info_card(
    title="情報カード",
    content="重要な情報を表示するための情報カードです。",
    color="#2196F3",  # カスタムカラー
    icon="fas fa-info-circle"  # アイコン
)

# アクションカード
actions = [
    {"label": "詳細", "key": "view", "type": "secondary"},
    {"label": "編集", "key": "edit", "type": "primary"}
]

result = create_action_card(
    title="アクション付きカード",
    content="ユーザーが操作できるアクションを含むカードです。",
    actions=actions
)

# クリックされたアクションの処理
for key, clicked in result.items():
    if clicked:
        if key == "view":
            view_details()
        elif key == "edit":
            edit_item()
```

### 2.3 アラート

アラートコンポーネントは、ユーザーに重要な情報を通知するために使用されます。

#### 基本的な使い方

```python
from ui.components.common.alert import create_info_alert, create_success_alert, create_warning_alert, create_error_alert

# 情報アラート
create_info_alert("これは情報アラートです。一般的な情報を表示します。")

# 成功アラート
create_success_alert("操作が正常に完了しました。")

# 警告アラート
create_warning_alert("この操作は元に戻せません。")

# エラーアラート
create_error_alert("エラーが発生しました。")

# 閉じることができるアラート
closed = create_warning_alert(
    "この警告アラートは閉じることができます。",
    dismissible=True
)
if closed:
    # アラートが閉じられた時の処理
    handle_alert_closed()
```

### 2.4 バッジ

バッジコンポーネントは、ステータスやカテゴリを視覚的に表示するために使用されます。

#### 基本的な使い方

```python
from ui.components.common.badge import create_badge

# 基本バッジ
create_badge("新機能", badge_type="primary")

# バッジのバリエーション
create_badge("ベータ版", badge_type="secondary")
create_badge("完了", badge_type="success")
create_badge("注意", badge_type="warning")
create_badge("エラー", badge_type="error")

# サイズ違いのバッジ
create_badge("小サイズ", size="small")
create_badge("中サイズ", size="medium")  # デフォルト
create_badge("大サイズ", size="large")

# アイコン付きバッジ
create_badge("新機能", badge_type="primary", icon="fas fa-star")
```

### 2.5 ツールチップ

ツールチップコンポーネントは、要素に追加情報を提供するために使用されます。

#### 基本的な使い方

```python
from ui.components.common.tooltip import create_tooltip

# 基本ツールチップ
create_tooltip(
    "ホバーしてください",
    "ツールチップの内容がここに表示されます。",
    position="top"  # "top", "right", "bottom", "left"
)

# 幅のカスタマイズ
create_tooltip(
    "ホバーしてください",
    "カスタム幅のツールチップです。",
    position="top",
    width="300px"
)

# アイコンのみのツールチップ
create_tooltip(
    None,
    "アイコンのツールチップです。",
    icon="fas fa-info-circle"
)
```

### 2.6 レイアウトヘルパー

レイアウトヘルパーコンポーネントは、ページのレイアウトを構築するために使用されます。

#### 基本的な使い方

```python
from ui.components.common.layout_helpers import create_spacer, create_divider, create_container

# スペーサー
st.write("テキスト1")
create_spacer(size="M")  # 中サイズの間隔
st.write("テキスト2")

# 区切り線
st.write("セクション1")
create_divider(margin="M")  # 中サイズのマージン
st.write("セクション2")

# コンテナ
create_container(
    content="<p>これはHTMLコンテンツを含むコンテナです。</p>",
    width="100%",
    padding="M",  # "XS", "S", "M", "L", "XL"
    bg_color="#FFFFFF",
    border=True,
    border_radius="MEDIUM",  # "SMALL", "MEDIUM", "LARGE"
    shadow="SHADOW_1"  # "SHADOW_1", "SHADOW_2", "SHADOW_3"
)
```

## 3. フォーム要素

### 3.1 テキスト入力

テキスト入力コンポーネントは、ユーザーからテキスト入力を受け取るために使用されます。

#### 基本的な使い方

```python
from ui.components.forms.input import create_text_input, create_number_input, create_password_input

# テキスト入力
name = create_text_input(
    label="名前",
    value="",  # デフォルト値
    placeholder="名前を入力してください",
    help="氏名を入力してください"
)

# 数値入力
age = create_number_input(
    label="年齢",
    value=20,
    min_value=0,
    max_value=120,
    step=1,
    help="年齢を入力してください"
)

# パスワード入力
password = create_password_input(
    label="パスワード",
    help="安全なパスワードを入力してください"
)
```

### 3.2 選択コンポーネント

選択コンポーネントは、ユーザーに選択肢から選ばせるために使用されます。

#### 基本的な使い方

```python
from ui.components.forms.select import create_select, create_multi_select

# 単一選択
selected_class = create_select(
    label="セーリングクラス",
    options=["レーザー", "470", "49er", "ナクラ17", "フィン"],
    index=0,  # デフォルト選択インデックス
    help="セーリングクラスを選択してください"
)

# カスタム表示用の関数
def format_race(race_info):
    return f"{race_info['name']} ({race_info['year']})"

# フォーマット関数付き選択
races = [
    {"name": "全日本選手権", "year": 2025},
    {"name": "アジア選手権", "year": 2024},
    {"name": "ワールドカップ", "year": 2023}
]
selected_race = create_select(
    label="レース",
    options=races,
    format_func=format_race
)

# 複数選択
selected_skills = create_multi_select(
    label="スキル",
    options=["セーリング", "ナビゲーション", "気象学", "戦術", "レース規則"],
    default=["セーリング"],  # デフォルト選択
    help="あなたが持っているスキルを選択してください"
)
```

### 3.3 チェックボックス

チェックボックスコンポーネントは、ブール値の選択や複数のオプションからの選択に使用されます。

#### 基本的な使い方

```python
from ui.components.forms.checkbox import create_checkbox, create_checkbox_group

# 単一チェックボックス
agreed = create_checkbox(
    label="利用規約に同意する",
    value=False,  # デフォルト値
    help="続行するには利用規約に同意する必要があります"
)

# チェックボックスグループ
selected_features = create_checkbox_group(
    label="使用する機能",
    options=[
        "風向分析",
        "タック検出",
        "戦略ポイント特定",
        "レース比較",
        "パフォーマンス分析"
    ],
    default=["風向分析", "タック検出"],
    help="使用したい機能を選択してください"
)

# ラベルと値が異なるオプション
option_list = [
    {"label": "風向分析 (標準)", "value": "wind_analysis"},
    {"label": "タック検出 (拡張)", "value": "tack_detection"},
    {"label": "戦略ポイント特定 (ベータ)", "value": "strategy_points"}
]
selected_features_with_values = create_checkbox_group(
    label="使用する機能",
    options=option_list,
    default=["wind_analysis"]
)
```

## 4. ナビゲーションコンポーネント

ナビゲーションコンポーネントは、アプリケーション内の異なるセクション間をナビゲートするために使用されます。（コンポーネントの実装は今後追加される予定です）

## 5. コンポーネント組み合わせの例

異なるコンポーネントを組み合わせて、より複雑なUIを構築できます。以下は、フォームとアクションカードを組み合わせた例です：

```python
import streamlit as st
from ui.components.common.card import create_card, create_action_card
from ui.components.common.alert import create_info_alert, create_success_alert
from ui.components.forms.input import create_text_input, create_number_input
from ui.components.forms.select import create_select

def user_registration_form():
    # 情報アラート
    create_info_alert("以下のフォームに必要な情報を入力してください。")
    
    # ユーザー情報カード
    create_card(
        title="ユーザー情報",
        content="""
        <div>
            <p>ユーザー登録に必要な基本情報を入力してください。</p>
        </div>
        """
    )
    
    # フォーム要素
    name = create_text_input("氏名", placeholder="例：山田 太郎")
    email = create_text_input("メールアドレス", placeholder="例：yamada@example.com")
    age = create_number_input("年齢", value=20, min_value=10, max_value=120)
    
    # 選択要素
    sailing_class = create_select(
        label="セーリングクラス",
        options=["レーザー", "470", "49er", "ナクラ17", "フィン"]
    )
    
    # アクションカード
    actions = [
        {"label": "キャンセル", "key": "cancel", "type": "secondary"},
        {"label": "登録", "key": "submit", "type": "primary"}
    ]
    
    result = create_action_card(
        title="アクション",
        content="フォームの入力が完了したら「登録」ボタンをクリックしてください。",
        actions=actions
    )
    
    # 結果の処理
    if result.get("submit", False):
        # 登録処理
        if name and email:
            create_success_alert(f"{name}さんのユーザー登録が完了しました。")
            return True
        else:
            create_error_alert("氏名とメールアドレスは必須です。")
    
    if result.get("cancel", False):
        # キャンセル処理
        st.warning("登録がキャンセルされました。")
        return False
    
    return None
```

## 6. ベストプラクティス

UIコンポーネントライブラリを使用する際のベストプラクティスを以下に示します：

### 一貫性のあるUIを維持する

- 同じ機能には同じコンポーネントを使用する
- 同じタイプのアクションには一貫したボタンスタイルを使用する
- デザインガイドラインに沿った色とスタイルを使用する

### コードの整理

- 関連するUIコンポーネントをグループ化する
- 複雑なUIセクションは関数に分割する
- コンポーネントのカスタマイズは最小限に抑える

### アクセシビリティの確保

- すべての入力フィールドには適切なラベルを使用する
- ヘルプテキストを提供し、操作のヒントを与える
- エラーメッセージを明確に表示する

### パフォーマンスの最適化

- 大量のUIコンポーネントを一度に描画しない
- スタイルの競合を避けるため、コンポーネントスタイルの上書きは避ける
- 複雑なUIはタブやアコーディオンを使って整理する

### モバイル対応

- レスポンシブなレイアウトを使用する
- タッチターゲットの大きさを適切に設定する（最低44px×44px）
- モバイルデバイスでのテストを忘れない

### サンプルコード集

UIコンポーネントライブラリの使用例は、`ui/component_demo.py`で確認できます。これには、各コンポーネントの基本的な使い方と様々な設定オプションが含まれています。

```python
# コンポーネントデモを実行
python3 -m streamlit run ui/component_demo.py
```
