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
    
    .topbar-title {
        font-size: 18px;
        font-weight: bold;
        margin-right: 20px;
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
    
    .main-content {
        margin-top: 70px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def render_top_bar(active_section="dashboard"):
    """
    トップバーナビゲーションを表示
    
    Parameters:
    -----------
    active_section : str
        アクティブなセクション ('dashboard', 'data', 'analysis', 'report')
    """
    sections = {
        "dashboard": "ダッシュボード",
        "data": "データ管理",
        "analysis": "風向分析",
        "report": "レポート"
    }
    
    html = f"""
    <div class="topbar">
        <div class="topbar-title">セーリング戦略分析システム</div>
    """
    
    for key, label in sections.items():
        active_class = "active" if key == active_section else ""
        html += f'<button class="topbar-button {active_class}" onclick="handleNavigation(\'{key}\')">{label}</button>'
    
    html += """
    </div>
    <script>
    function handleNavigation(section) {
        // Streamlitのセッション状態を更新する関数
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {
                navigation: section
            }
        }, '*');
    }
    </script>
    """
    
    st.markdown(html, unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'navigation' not in st.session_state:
        st.session_state.navigation = 'dashboard'
    
    # JavaScriptからのコールバックを処理
    navigation_callback = st.experimental_get_query_params().get('nav', [None])[0]
    if navigation_callback:
        st.session_state.navigation = navigation_callback
    
    # トップバーの下にマージンを追加
    st.markdown('<div class="main-content"></div>', unsafe_allow_html=True)
    
    return st.session_state.navigation
