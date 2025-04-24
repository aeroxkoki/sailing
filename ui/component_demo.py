# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - コンポーネントデモページ

実装したUIコンポーネントをテストするためのデモページです。
"""

import streamlit as st
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# コンポーネントのインポート
from ui.components.common.button import create_button, create_primary_button, create_secondary_button, create_text_button, create_warning_button
from ui.components.common.card import create_card, create_info_card, create_action_card
from ui.components.common.alert import create_alert, create_info_alert, create_success_alert, create_warning_alert, create_error_alert
from ui.components.common.badge import create_badge
from ui.components.common.tooltip import create_tooltip
from ui.components.common.layout_helpers import create_spacer, create_divider, create_container

from ui.components.forms.input import create_text_input, create_number_input, create_password_input
from ui.components.forms.select import create_select, create_multi_select
from ui.components.forms.checkbox import create_checkbox, create_checkbox_group

# アプリケーション設定
st.set_page_config(
    page_title="UI Components Demo",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ページタイトル
st.title("セーリング戦略分析システム - UIコンポーネントデモ")
st.write("様々なUIコンポーネントのデモページです。実装したコンポーネントをテストできます。")

# サイドバー
st.sidebar.title("コンポーネントカテゴリ")
category = st.sidebar.radio(
    "表示するカテゴリ",
    ["ボタン", "カード", "アラート", "バッジとツールチップ", "レイアウトヘルパー", "フォーム要素"]
)

# 各カテゴリのデモ表示
if category == "ボタン":
    st.header("ボタンコンポーネント")
    
    # ボタンの基本サンプル
    st.subheader("基本的なボタン")
    cols = st.columns(4)
    with cols[0]:
        st.write("プライマリボタン")
        clicked_primary = create_primary_button("プライマリ")
        if clicked_primary:
            st.write("クリックされました!")
    
    with cols[1]:
        st.write("セカンダリボタン")
        clicked_secondary = create_secondary_button("セカンダリ")
        if clicked_secondary:
            st.write("クリックされました!")
    
    with cols[2]:
        st.write("テキストボタン")
        clicked_text = create_text_button("テキスト")
        if clicked_text:
            st.write("クリックされました!")
    
    with cols[3]:
        st.write("警告ボタン")
        clicked_warning = create_warning_button("警告")
        if clicked_warning:
            st.write("クリックされました!")
    
    # ボタンサイズの例
    st.subheader("ボタンサイズ")
    size_cols = st.columns(3)
    with size_cols[0]:
        st.write("小")
        create_primary_button("小ボタン", size="small")
    
    with size_cols[1]:
        st.write("中（デフォルト）")
        create_primary_button("中ボタン", size="medium")
    
    with size_cols[2]:
        st.write("大")
        create_primary_button("大ボタン", size="large")
    
    # アイコン付きボタン
    st.subheader("アイコン付きボタン")
    icon_cols = st.columns(4)
    with icon_cols[0]:
        create_primary_button("保存", icon="fas fa-save")
    
    with icon_cols[1]:
        create_secondary_button("編集", icon="fas fa-edit")
    
    with icon_cols[2]:
        create_text_button("検索", icon="fas fa-search")
    
    with icon_cols[3]:
        create_warning_button("削除", icon="fas fa-trash")

elif category == "カード":
    st.header("カードコンポーネント")
    
    # 基本カード
    st.subheader("基本カード")
    create_card(
        title="基本カード",
        subtitle="シンプルなカードの例",
        content="これはセーリング戦略分析システムの基本カードコンポーネントです。様々な情報を表示するのに使用できます。"
    )
    
    # 情報カード
    st.subheader("情報カード")
    create_info_card(
        title="情報カード",
        content="この情報カードは、重要な情報を視覚的に区別して表示するために使用します。",
        color="#2196F3"  # INFO色
    )
    
    create_info_card(
        title="成功メッセージ",
        content="操作が正常に完了しました。",
        color="#26A69A",  # SUCCESS色
        icon="fas fa-check-circle"
    )
    
    create_info_card(
        title="警告メッセージ",
        content="この操作は元に戻せません。続ける前に確認してください。",
        color="#FFA726",  # WARNING色
        icon="fas fa-exclamation-triangle"
    )
    
    # アクション付きカード
    st.subheader("アクション付きカード")
    actions = [
        {"label": "詳細", "key": "view", "type": "secondary"},
        {"label": "編集", "key": "edit", "type": "primary"},
        {"label": "削除", "key": "delete", "type": "warning"}
    ]
    
    result = create_action_card(
        title="アクション付きカード",
        content="このカードにはアクションボタンが付いています。ユーザーがアクションを実行できます。",
        actions=actions
    )
    
    # クリックされたアクションの表示
    for key, clicked in result.items():
        if clicked:
            st.write(f"「{key}」ボタンがクリックされました")

elif category == "アラート":
    st.header("アラートコンポーネント")
    
    # 基本アラートの例
    st.subheader("基本アラート")
    create_info_alert("これは情報アラートです。一般的な情報を表示します。")
    create_success_alert("これは成功アラートです。操作が正常に完了したことを示します。")
    create_warning_alert("これは警告アラートです。注意が必要な情報を表示します。")
    create_error_alert("これはエラーアラートです。エラーや問題を表示します。")
    
    # カスタムアイコン付きアラート
    st.subheader("カスタムアイコン付きアラート")
    create_info_alert("カスタムアイコン付き情報アラート", icon="fas fa-info")
    create_success_alert("カスタムアイコン付き成功アラート", icon="fas fa-thumbs-up")
    
    # 閉じることができるアラート
    st.subheader("閉じることができるアラート")
    if 'alert_closed' not in st.session_state:
        st.session_state.alert_closed = False
    
    if not st.session_state.alert_closed:
        closed = create_warning_alert(
            "この警告アラートは閉じることができます。右上の✕ボタンをクリックしてください。",
            dismissible=True
        )
        if closed:
            st.session_state.alert_closed = True
    else:
        if st.button("アラートを再表示"):
            st.session_state.alert_closed = False
            st.experimental_rerun()

elif category == "バッジとツールチップ":
    st.header("バッジとツールチップ")
    
    # バッジの例
    st.subheader("バッジ")
    badge_cols = st.columns(5)
    with badge_cols[0]:
        st.write("プライマリバッジ")
        create_badge("プライマリ", badge_type="primary")
    
    with badge_cols[1]:
        st.write("セカンダリバッジ")
        create_badge("セカンダリ", badge_type="secondary")
    
    with badge_cols[2]:
        st.write("成功バッジ")
        create_badge("成功", badge_type="success")
    
    with badge_cols[3]:
        st.write("警告バッジ")
        create_badge("警告", badge_type="warning")
    
    with badge_cols[4]:
        st.write("エラーバッジ")
        create_badge("エラー", badge_type="error")
    
    # サイズ違いのバッジ
    st.subheader("バッジサイズ")
    size_badge_cols = st.columns(3)
    with size_badge_cols[0]:
        st.write("小")
        create_badge("小サイズ", size="small")
    
    with size_badge_cols[1]:
        st.write("中（デフォルト）")
        create_badge("中サイズ", size="medium")
    
    with size_badge_cols[2]:
        st.write("大")
        create_badge("大サイズ", size="large")
    
    # アイコン付きバッジ
    st.subheader("アイコン付きバッジ")
    icon_badge_cols = st.columns(4)
    with icon_badge_cols[0]:
        create_badge("新機能", badge_type="primary", icon="fas fa-star")
    
    with icon_badge_cols[1]:
        create_badge("beta", badge_type="secondary", icon="fas fa-flask")
    
    with icon_badge_cols[2]:
        create_badge("完了", badge_type="success", icon="fas fa-check")
    
    with icon_badge_cols[3]:
        create_badge("注意", badge_type="warning", icon="fas fa-exclamation")
    
    # ツールチップの例
    st.subheader("ツールチップ")
    tooltip_cols = st.columns(4)
    
    with tooltip_cols[0]:
        st.write("上部に表示")
        create_tooltip(
            "ホバーしてください",
            "これは上部に表示されるツールチップです。",
            position="top"
        )
    
    with tooltip_cols[1]:
        st.write("右側に表示")
        create_tooltip(
            "ホバーしてください",
            "これは右側に表示されるツールチップです。",
            position="right"
        )
    
    with tooltip_cols[2]:
        st.write("下部に表示")
        create_tooltip(
            "ホバーしてください",
            "これは下部に表示されるツールチップです。",
            position="bottom"
        )
    
    with tooltip_cols[3]:
        st.write("左側に表示")
        create_tooltip(
            "ホバーしてください",
            "これは左側に表示されるツールチップです。",
            position="left"
        )
    
    # アイコンのみのツールチップ
    st.subheader("アイコンのみのツールチップ")
    icon_tooltip_cols = st.columns(4)
    
    with icon_tooltip_cols[0]:
        create_tooltip(
            None,
            "これは情報アイコンのツールチップです。",
            icon="fas fa-info-circle"
        )
    
    with icon_tooltip_cols[1]:
        create_tooltip(
            None,
            "これは疑問アイコンのツールチップです。",
            icon="fas fa-question-circle"
        )
    
    with icon_tooltip_cols[2]:
        create_tooltip(
            None,
            "これは警告アイコンのツールチップです。",
            icon="fas fa-exclamation-circle"
        )
    
    with icon_tooltip_cols[3]:
        create_tooltip(
            None,
            "これはヘルプアイコンのツールチップです。",
            icon="fas fa-lightbulb"
        )

elif category == "レイアウトヘルパー":
    st.header("レイアウトヘルパー")
    
    # スペーサーの例
    st.subheader("スペーサー")
    st.write("テキスト1")
    create_spacer(size="XS")
    st.write("テキスト2（XSスペーサー）")
    create_spacer(size="S")
    st.write("テキスト3（Sスペーサー）")
    create_spacer(size="M")
    st.write("テキスト4（Mスペーサー）")
    create_spacer(size="L")
    st.write("テキスト5（Lスペーサー）")
    
    # 区切り線の例
    st.subheader("区切り線")
    st.write("テキスト1")
    create_divider(margin="S")
    st.write("テキスト2（S区切り線）")
    create_divider(margin="M")
    st.write("テキスト3（M区切り線）")
    create_divider(margin="L", color="#1565C0")
    st.write("テキスト4（L区切り線、カスタム色）")
    
    # コンテナの例
    st.subheader("コンテナ")
    create_container(
        content="<p>これは基本的なコンテナです。</p>",
        padding="M",
        border=True
    )
    
    create_container(
        content="<p>これはシャドウ付きコンテナです。</p>",
        padding="M",
        shadow="SHADOW_1"
    )
    
    create_container(
        content="<p>これはカスタム背景色のコンテナです。</p>",
        padding="M",
        bg_color="#E3F2FD",
        border_radius="LARGE"
    )
    
    # レスポンシブな幅のコンテナ
    st.subheader("レスポンシブなコンテナ")
    create_container(
        content="<p>これは50%幅のコンテナです。</p>",
        width="50%",
        padding="M",
        border=True,
        shadow="SHADOW_1"
    )
    
    # 複数のコンテナを含むレイアウト
    st.subheader("複合レイアウト")
    cols = st.columns(2)
    
    with cols[0]:
        create_container(
            content="<h4>左側のコンテナ</h4><p>このコンテナは左カラムに配置されています。</p>",
            padding="M",
            border=True,
            shadow="SHADOW_1"
        )
    
    with cols[1]:
        create_container(
            content="<h4>右側のコンテナ</h4><p>このコンテナは右カラムに配置されています。</p>",
            padding="M",
            bg_color="#E8F5E9",
            border_radius="LARGE"
        )

elif category == "フォーム要素":
    st.header("フォーム要素")
    
    # テキスト入力の例
    st.subheader("テキスト入力")
    text_cols = st.columns(2)
    
    with text_cols[0]:
        name = create_text_input(
            label="名前",
            placeholder="名前を入力してください",
            help="氏名を入力してください"
        )
        if name:
            st.write(f"入力された名前: {name}")
    
    with text_cols[1]:
        email = create_text_input(
            label="メールアドレス",
            placeholder="example@example.com",
            help="有効なメールアドレスを入力してください"
        )
        if email:
            st.write(f"入力されたメールアドレス: {email}")
    
    # 数値入力とパスワード入力
    st.subheader("数値入力とパスワード入力")
    num_pass_cols = st.columns(2)
    
    with num_pass_cols[0]:
        num = create_number_input(
            label="年齢",
            min_value=0,
            max_value=120,
            step=1,
            help="年齢を入力してください"
        )
        if num:
            st.write(f"入力された年齢: {num}")
    
    with num_pass_cols[1]:
        password = create_password_input(
            label="パスワード",
            help="安全なパスワードを入力してください"
        )
        if password:
            st.write("パスワードが入力されました")
    
    # 選択コンポーネントの例
    st.subheader("選択コンポーネント")
    select_cols = st.columns(2)
    
    with select_cols[0]:
        option = create_select(
            label="お好みのセーリングクラス",
            options=["レーザー", "470", "49er", "ナクラ17", "フィン"],
            help="セーリングクラスを選択してください"
        )
        st.write(f"選択されたクラス: {option}")
    
    with select_cols[1]:
        multi_options = create_multi_select(
            label="参加したレース",
            options=["ワールドカップ", "全日本選手権", "インターハイ", "アジア選手権", "オリンピック"],
            default=["全日本選手権"],
            help="参加したレースを全て選択してください"
        )
        if multi_options:
            st.write(f"選択されたレース: {', '.join(multi_options)}")
    
    # チェックボックスの例
    st.subheader("チェックボックス")
    check_cols = st.columns(2)
    
    with check_cols[0]:
        checked = create_checkbox(
            label="利用規約に同意する",
            help="続行するには利用規約に同意する必要があります"
        )
        if checked:
            st.write("利用規約に同意しました")
    
    with check_cols[1]:
        skills = create_checkbox_group(
            label="あなたのスキル",
            options=["セーリング", "ナビゲーション", "気象学", "戦術", "レース規則"],
            default=["セーリング"],
            help="あなたが持っているスキルを選択してください"
        )
        if skills:
            st.write(f"選択されたスキル: {', '.join(skills)}")

# Font Awesome読み込み（アイコン表示用）
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# フッター
create_divider()
st.caption("セーリング戦略分析システム - UIコンポーネントデモ v1.0")
