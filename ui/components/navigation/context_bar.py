"""
セーリング戦略分析システム - コンテキストバーコンポーネント

各セクションのコンテキスト依存のナビゲーションバーを提供します。
"""

import streamlit as st

def render_context_bar(active_section):
    """
    コンテキストに応じたセカンダリナビゲーションバーを表示
    
    Parameters:
    -----------
    active_section : str
        現在のセクション
    """
    st.markdown("""
    <style>
    .context-bar {
        background: #f0f7ff;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .context-item {
        margin-right: 15px;
    }
    
    .action-button {
        background: #1565C0;
        color: white;
        border: none;
        padding: 5px 15px;
        border-radius: 4px;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([7, 3])
    
    with col1:
        if active_section == 'dashboard':
            # プロジェクト/セッション選択
            projects = ["Tokyo Bay Race 2025", "Training Session 04-10", "New Project"]
            selected_project = st.selectbox("プロジェクト", projects)
            
            # セッション選択はプロジェクトが選択されている場合のみ表示
            if selected_project != "New Project":
                sessions = ["Session 1", "Session 2", "Session 3"]
                st.selectbox("セッション", sessions)
        
        elif active_section == 'data':
            st.selectbox("データソース", ["GPSデータ", "外部風データ", "コースデータ"])
            st.file_uploader("ファイルをアップロード", type=['csv', 'gpx', 'tcx', 'fit'])
    
    with col2:
        if active_section == 'dashboard':
            # アクションボタン
            st.button("解析実行", type="primary")
            st.button("データ比較")
