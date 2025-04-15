"""
ui.app_v6

セーリング戦略分析システムの改良版バージョンのアプリケーション
このファイルはUI/UX改善を実装したアプリケーションのメインエントリーポイントです。
"""

import streamlit as st
from ui.components.navigation.top_bar import apply_top_bar_style, render_top_bar
from ui.components.navigation.context_bar import render_context_bar

# ページ設定（サイドバーを非表示に）
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# トップバースタイルの適用
apply_top_bar_style()

# トップバーの表示とナビゲーション状態の取得
active_section = render_top_bar()

# セカンダリナビゲーション
render_context_bar(active_section)

# コンテンツエリアのレイアウト
def create_horizontal_layout():
    """水平分割レイアウトの作成"""
    # セッションステートにレイアウト比率を保存
    if 'map_width' not in st.session_state:
        st.session_state.map_width = 70
    
    # 列サイズ比率の算出
    map_ratio = st.session_state.map_width
    panel_ratio = 100 - map_ratio - 1  # ハンドル用に1%確保
    
    # 水平分割レイアウトの作成
    col1, handle, col2 = st.columns([map_ratio, 1, panel_ratio])
    
    return col1, handle, col2

# セクションに応じたコンテンツ表示
if active_section == 'dashboard':
    map_col, handle_col, data_col = create_horizontal_layout()
    
    with map_col:
        st.subheader("マップビュー")
        # マップビューコンポーネントを呼び出す
        # この部分は風向風速表示の実装時に更新
        
    with handle_col:
        # リサイズハンドル（簡易版）
        st.markdown("""
        <div style="width:100%; height:100%; cursor: col-resize; background-color:#e0e0e0;"></div>
        """, unsafe_allow_html=True)
        
    with data_col:
        tabs = st.tabs(["パフォーマンス", "戦略分析", "風分析"])
        
        with tabs[0]:
            st.subheader("パフォーマンス分析")
            # パフォーマンス分析コンポーネントを呼び出す
            
        with tabs[1]:
            st.subheader("戦略分析")
            # 戦略分析コンポーネントを呼び出す
            
        with tabs[2]:
            st.subheader("風分析")
            # 風分析コンポーネントを呼び出す

elif active_section == 'data':
    st.subheader("データ管理")
    # データ管理コンポーネントを呼び出す

elif active_section == 'analysis':
    st.subheader("風向分析")
    # 風向分析コンポーネントを呼び出す

elif active_section == 'report':
    st.subheader("レポート")
    # レポートコンポーネントを呼び出す
