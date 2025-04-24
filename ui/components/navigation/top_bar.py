# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - トップバーナビゲーションコンポーネント

トップバーメニューのコンポーネントを提供します。
"""

import streamlit as st

def apply_top_bar_style():
    """トップバーのスタイルをページに適用する"""
    st.markdown("""
    <style>
    .topbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: linear-gradient(90deg, #1565C0 0%, #3b82f6 100%);
        color: white;
        z-index: 1000;
        display: flex;
        align-items: center;
        padding: 0 20px;
    }
    
    .topbar-logo {
        font-size: 18px;
        font-weight: bold;
        margin-right: 20px;
    }
    
    .topbar-project {
        background: rgba(255,255,255,0.2);
        padding: 5px 10px;
        border-radius: 4px;
        margin-right: 20px;
        font-size: 14px;
    }
    
    .topbar-sections {
        display: flex;
        flex-grow: 1;
    }
    
    .topbar-button {
        padding: 8px 16px;
        border-radius: 4px;
        margin-right: 10px;
        cursor: pointer;
        background: transparent;
        border: none;
        color: white;
    }
    
    .topbar-button.active {
        background: #0D47A1;
    }
    
    .topbar-actions {
        display: flex;
        gap: 10px;
    }
    
    .topbar-action-button {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }
    
    .main-content {
        margin-top: 70px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def render_top_bar(active_section="dashboard", project_name=None, session_name=None):
    """
    拡張されたトップバーナビゲーションを表示
    
    Parameters:
    -----------
    active_section : str
        アクティブなセクション ('dashboard', 'data', 'analysis', 'report')
    project_name : str, optional
        現在のプロジェクト名
    session_name : str, optional
        現在のセッション名
        
    Returns:
    --------
    str
        現在のアクティブセクション
    """
    sections = {
        "dashboard": "ダッシュボード",
        "data": "データ管理",
        "analysis": "風向分析",
        "report": "レポート"
    }
    
    # プロジェクト名の表示を追加
    project_display = project_name if project_name else "プロジェクトを選択"
    session_display = session_name if session_name else ""
    project_info = f"{project_display}"
    if session_display:
        project_info += f" / {session_display}"
    
    # FontAwesomeを追加
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">', unsafe_allow_html=True)
    
    html = f"""
    <div class="topbar">
        <div class="topbar-logo">セーリング戦略分析</div>
        <div class="topbar-project">{project_info}</div>
        <div class="topbar-sections">
    """
    
    for key, label in sections.items():
        active_class = "active" if key == active_section else ""
        html += f'<button class="topbar-button {active_class}" onclick="handleNavigation(\'{key}\')">{label}</button>'
    
    html += """
        </div>
        <div class="topbar-actions">
            <button class="topbar-action-button" title="保存" onclick="handleAction('save')"><i class="fas fa-save"></i></button>
            <button class="topbar-action-button" title="共有" onclick="handleAction('share')"><i class="fas fa-share-alt"></i></button>
        </div>
    </div>
    <script>
    function handleNavigation(section) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {
                navigation: section
            }
        }, '*');
    }
    
    function handleAction(action) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {
                action: action
            }
        }, '*');
    }
    </script>
    """
    
    st.markdown(html, unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'navigation' not in st.session_state:
        st.session_state.navigation = 'dashboard'
    
    # アクション状態の初期化
    if 'action' not in st.session_state:
        st.session_state.action = None
    
    # JavaScriptからのコールバックを処理
    # st.experimental_get_query_params()は非推奨のため、st.query_paramsに置き換え
    if hasattr(st, 'query_params'):
        navigation_callback = st.query_params.get('nav', None)
        if navigation_callback:
            st.session_state.navigation = navigation_callback
    
    # アクションボタンのコールバック処理
    if st.session_state.action == 'save':
        # 保存アクションの処理
        st.toast('プロジェクトを保存しました', icon='✅')
        st.session_state.action = None
    elif st.session_state.action == 'share':
        # 共有アクションの処理
        st.toast('共有リンクをコピーしました', icon='📋')
        st.session_state.action = None
    
    # トップバーの下にマージンを追加
    st.markdown('<div class="main-content"></div>', unsafe_allow_html=True)
    
    return st.session_state.navigation
