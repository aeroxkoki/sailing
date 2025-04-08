# UIコンポーネント実装ガイド

このドキュメントは、セーリング戦略分析システム向けの新しいUIコンポーネントを実装する際のガイドラインとベストプラクティスを提供します。

## 目次

1. [基本原則](#1-基本原則)
2. [コンポーネント構造](#2-コンポーネント構造)
3. [設計パターン](#3-設計パターン)
4. [スタイリング](#4-スタイリング)
5. [テスト](#5-テスト)
6. [ドキュメント](#6-ドキュメント)
7. [実装例](#7-実装例)

## 1. 基本原則

新しいコンポーネントを実装する際は、以下の基本原則に従ってください：

### 1.1 単一責任の原則

各コンポーネントは単一の責任を持つべきです：

- 1つのコンポーネントは1つの明確な目的を持つ
- 複雑な機能は小さなコンポーネントに分割する
- 関連する機能のみを含める

### 1.2 再利用性

コンポーネントは再利用可能なように設計します：

- 特定のページやコンテキストに依存しない
- カスタマイズ可能なプロパティを提供する
- 不必要な依存関係を避ける

### 1.3 一貫性

UIガイドラインに沿った一貫性のあるインターフェースを維持します：

- デザインガイドラインに従う
- 既存のコンポーネントと同様のAPIを提供する
- 命名規則とコーディング標準を遵守する

### 1.4 アクセシビリティ

すべてのコンポーネントはアクセシビリティに配慮して実装します：

- 適切なARIA属性を使用する
- キーボードナビゲーションをサポートする
- 十分なコントラスト比を確保する
- スクリーンリーダーでの使用をテストする

## 2. コンポーネント構造

### 2.1 ディレクトリ構造

新しいコンポーネントは以下のディレクトリ構造に従って実装します：

```
ui/
  components/
    common/           # 共通の基本コンポーネント
      button.py       # ボタンコンポーネント
      card.py         # カードコンポーネント
      ...
    forms/            # フォーム関連コンポーネント
      input.py        # 入力コンポーネント
      select.py       # 選択コンポーネント
      ...
    navigation/       # ナビゲーション関連コンポーネント
      sidebar.py      # サイドバーコンポーネント
      tabs.py         # タブコンポーネント
      ...
    layout/           # レイアウト関連コンポーネント
      container.py    # コンテナコンポーネント
      grid.py         # グリッドコンポーネント
      ...
    visualizations/   # データ可視化コンポーネント
      chart.py        # チャートコンポーネント
      map.py          # マップコンポーネント
      ...
```

### 2.2 コンポーネントファイル構造

各コンポーネントファイルは以下の構造に従って実装します：

```python
"""
セーリング戦略分析システム - [コンポーネント名]

[コンポーネントの簡単な説明]
"""

import streamlit as st
from ..styles import Colors, FontSizes, BorderRadius, ...  # 必要なスタイル定数をインポート

def create_[component_name](
    # 必要なパラメータ
):
    """
    [コンポーネントの詳細な説明]
    
    Parameters:
    -----------
    [パラメータ名] : [型]
        [パラメータの説明]
    ...
    
    Returns:
    --------
    [戻り値の型]
        [戻り値の説明]
    """
    # コンポーネントのスタイル定義
    component_style = f"""
    <style>
    /* CSSスタイル */
    </style>
    """
    
    st.markdown(component_style, unsafe_allow_html=True)
    
    # コンポーネントのHTMLまたはStreamlit要素の生成
    ...
    
    # 結果の返却
    return result
```

## 3. 設計パターン

### 3.1 ファクトリーパターン

コンポーネントの作成には、`create_[component_name]`というパターンを使用します：

```python
def create_button(label, button_type="primary", size="medium", ...):
    # 内部で適切な具体的ボタン関数を呼び出す
    if button_type == "primary":
        return create_primary_button(label, size, ...)
    elif button_type == "secondary":
        return create_secondary_button(label, size, ...)
    # ...
```

### 3.2 バリエーションパターン

バリエーションが必要なコンポーネントでは、基本実装と具体的な実装を分けます：

```python
def _create_alert_by_type(message, alert_type, color, bg_color, ...):
    # 共通の実装
    ...

def create_info_alert(message, ...):
    return _create_alert_by_type(message, "info", Colors.INFO, ...)

def create_success_alert(message, ...):
    return _create_alert_by_type(message, "success", Colors.SUCCESS, ...)
```

### 3.3 プロパティオブジェクトパターン

複雑なコンポーネントでは、関連するプロパティをグループ化します：

```python
def create_data_table(data, columns, 
                      style={
                          "striped": True,
                          "bordered": False,
                          "hover": True
                      },
                      pagination={
                          "enabled": True,
                          "page_size": 10,
                          "sizes": [5, 10, 25, 50]
                      },
                      ...):
    # ...
```

## 4. スタイリング

### 4.1 スタイルの適用方法

コンポーネントのスタイルは、次の方法で適用します：

1. スタイル定数の使用（Colors, FontSizes, BorderRadius等）
2. インラインCSSの生成とHTMLマークダウンによる適用
3. 共通スタイルの再利用

```python
def create_component():
    component_style = f"""
    <style>
    .my-component {{
        background-color: {Colors.WHITE};
        border-radius: {BorderRadius.MEDIUM};
        padding: {Spacing.M};
        /* ... */
    }}
    </style>
    """
    
    st.markdown(component_style, unsafe_allow_html=True)
    
    # コンポーネントの内容...
```

### 4.2 レスポンシブ対応

コンポーネントはレスポンシブデザインを考慮して実装します：

- 固定サイズを避け、相対的なサイズ（%, em, rem）を使用する
- メディアクエリを活用する
- フレックスボックスやグリッドレイアウトを活用する

```css
@media (max-width: 768px) {
    .my-component {
        flex-direction: column;
    }
}
```

### 4.3 テーマカラー

コンポーネントのカラースキームは、スタイル定数から取得します：

```python
from ..styles import Colors

# 正しい使用法
background_color = Colors.PRIMARY
text_color = Colors.WHITE

# 避けるべき方法
background_color = "#1565C0"  # ハードコードされた色
```

## 5. テスト

### 5.1 動作確認

新しいコンポーネントを実装したら、以下の動作を確認します：

1. 基本機能が期待通りに動作するか
2. すべてのプロパティが正しく反映されるか
3. エッジケース（空の値、極端な値）での動作
4. レスポンシブ対応（様々な画面サイズでのテスト）
5. キーボード操作とスクリーンリーダーでの使用

### 5.2 デモページへの追加

実装したコンポーネントは、`ui/component_demo.py`に追加してテストします：

```python
# ボタンコンポーネントのデモ追加例
if category == "新しいコンポーネント":
    st.header("新しいコンポーネント")
    
    st.subheader("基本的な使用方法")
    new_component = create_new_component("基本設定")
    
    st.subheader("バリエーション")
    create_new_component("カスタム設定", option1="value1", option2="value2")
```

## 6. ドキュメント

### 6.1 コンポーネントのドキュメント

新しいコンポーネントには、以下の情報を含むドキュメントを提供します：

1. 目的と使用場面
2. パラメータの詳細説明
3. 戻り値の説明
4. 使用例

```python
def create_new_component(label, option="default"):
    """
    新しいコンポーネントを作成します。
    
    このコンポーネントは、[目的]のために使用され、[特徴]を提供します。
    
    Parameters:
    -----------
    label : str
        コンポーネントのラベル
    option : str, optional
        オプション設定。"default", "custom1", "custom2"のいずれか。
        デフォルトは"default"。
    
    Returns:
    --------
    any
        コンポーネントの状態や入力値
    
    Examples:
    ---------
    >>> result = create_new_component("ラベル", option="custom1")
    >>> if result:
    ...     # 結果の処理
    """
    # 実装...
```

### 6.2 更新履歴

コンポーネントに変更を加えた場合は、ドキュメントの更新履歴を記録します：

```python
"""
セーリング戦略分析システム - 新コンポーネント

変更履歴：
- 2025-03-30: 初期実装
- 2025-04-05: パラメータXを追加
- 2025-04-10: バグ修正: エッジケースYでの挙動を修正
"""
```

## 7. 実装例

### 7.1 基本的なボタンコンポーネント

以下は、ボタンコンポーネントの実装例です：

```python
"""
セーリング戦略分析システム - ボタンコンポーネント

様々なスタイルのボタンコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, Transitions, FontSizes, FontWeights

def create_button(label, button_type="primary", size="medium", icon=None, key=None):
    """
    ボタンコンポーネントを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    button_type : str, optional
        ボタンのタイプ ("primary", "secondary", "text", "warning")
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンに表示するアイコン（Font Awesomeクラス名）
    key : str, optional
        Streamlitコンポーネントの一意のキー
        
    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    if button_type == "primary":
        return create_primary_button(label, size, icon, key)
    elif button_type == "secondary":
        return create_secondary_button(label, size, icon, key)
    # 他のケースも同様...
    else:
        return create_primary_button(label, size, icon, key)

def create_primary_button(label, size="medium", icon=None, key=None):
    """
    プライマリボタンを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンに表示するアイコン（Font Awesomeクラス名）
    key : str, optional
        Streamlitコンポーネントの一意のキー
        
    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    # サイズに応じたスタイル設定
    height, padding, font_size = _get_button_size_properties(size)
    
    # CSSスタイルの定義
    button_style = f"""
    <style>
    div[data-testid="stButton"] button.primary-btn {{
        background-color: {Colors.PRIMARY};
        color: {Colors.WHITE};
        border: none;
        border-radius: {BorderRadius.SMALL};
        padding: {padding};
        height: {height};
        font-size: {font_size};
        font-weight: {FontWeights.MEDIUM};
        transition: all {Transitions.FAST} ease-out;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }}
    
    div[data-testid="stButton"] button.primary-btn:hover {{
        background-color: #0D47A1; /* 濃いめの青 */
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    </style>
    """
    
    st.markdown(button_style, unsafe_allow_html=True)
    
    # アイコンの追加
    button_content = label
    if icon:
        button_content = f'<i class="{icon}"></i> {label}'
    
    # ボタンの生成
    button_key = key if key else f"primary_button_{label}"
    clicked = st.button(button_content, key=button_key, type="primary")
    
    return clicked

def _get_button_size_properties(size):
    """
    ボタンサイズに応じたプロパティを取得します。
    
    Parameters:
    -----------
    size : str
        ボタンのサイズ ("small", "medium", "large")
        
    Returns:
    --------
    tuple
        (高さ, パディング, フォントサイズ)
    """
    if size == "small":
        return "32px", "4px 12px", "12px"
    elif size == "large":
        return "44px", "8px 24px", "16px"
    else:  # medium (default)
        return "38px", "6px 16px", "14px"
```

### 7.2 カードコンポーネント例

以下は、カードコンポーネントの実装例です：

```python
"""
セーリング戦略分析システム - カードコンポーネント

様々なスタイルのカードコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, Shadows, Spacing, FontSizes, FontWeights

def create_card(title=None, subtitle=None, content=None, footer=None, 
                padding="normal", shadow=True, border=False):
    """
    カードコンポーネントを作成します。
    
    Parameters:
    -----------
    title : str, optional
        カードのタイトル
    subtitle : str, optional
        カードのサブタイトル
    content : str, optional
        カードの内容（HTMLをサポート）
    footer : str, optional
        カードのフッター内容（HTMLをサポート）
    padding : str, optional
        内部余白のサイズ ("small", "normal", "large")
    shadow : bool, optional
        影を表示するかどうか
    border : bool, optional
        枠線を表示するかどうか
        
    Returns:
    --------
    None
    """
    # パディングサイズの設定
    if padding == "small":
        padding_size = Spacing.S
    elif padding == "large":
        padding_size = Spacing.L
    else:  # normal
        padding_size = Spacing.M
    
    # 影と枠線のスタイル
    shadow_style = f"box-shadow: {Shadows.SHADOW_1};" if shadow else ""
    border_style = f"border: 1px solid {Colors.GRAY_2};" if border else ""
    
    # カードのHTML生成
    card_html = f"""
    <div style="
        background-color: {Colors.WHITE};
        border-radius: {BorderRadius.MEDIUM};
        padding: {padding_size};
        margin-bottom: {Spacing.M};
        {shadow_style}
        {border_style}
    ">
        {f'<div style="font-size: {FontSizes.TITLE}; font-weight: {FontWeights.SEMIBOLD}; margin-bottom: {Spacing.S};">{title}</div>' if title else ''}
        {f'<div style="font-size: {FontSizes.SUBTITLE}; color: {Colors.DARK_1}; margin-bottom: {Spacing.S};">{subtitle}</div>' if subtitle else ''}
        {f'<div style="font-size: {FontSizes.BODY}; line-height: 1.5;">{content}</div>' if content else ''}
        {f'<div style="margin-top: {Spacing.M}; padding-top: {Spacing.S}; border-top: 1px solid {Colors.GRAY_2};">{footer}</div>' if footer else ''}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
```

これらの例を参考に、新しいコンポーネントを実装してください。コンポーネントの設計と実装は、ユーザーエクスペリエンスと開発者エクスペリエンスの両方を考慮することが重要です。
