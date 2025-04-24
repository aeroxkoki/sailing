# -*- coding: utf-8 -*-
"""
ui.app_integrated

セーリング戦略分析システムの統合アプリケーションエントリーポイント
"""

import streamlit as st
import os
import sys
from urllib.parse import urlparse, parse_qs
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# カスタムCSSの読み込み
def load_custom_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.0rem;
        font-weight: 600;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 500;
        color: #0277BD;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.3rem solid #1E88E5;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.3rem solid #FFC107;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.3rem solid #4CAF50;
        margin-bottom: 1rem;
    }
    .nav-button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション状態の初期化
def initialize_session_state():
    # 現在のページ
    if "current_page" not in st.session_state:
        st.session_state.current_page = "welcome"
    
    # 現在選択中のプロジェクトID
    if "selected_project_id" not in st.session_state:
        st.session_state.selected_project_id = None
    
    # 現在選択中のセッションID
    if "selected_session_id" not in st.session_state:
        st.session_state.selected_session_id = None
    
    # 分析状態
    if "analysis_state" not in st.session_state:
        st.session_state.analysis_state = {
            "completed_steps": [],
            "current_step": None,
            "results": {}
        }

# ページの遷移関数
def navigate_to(page_name, **kwargs):
    st.session_state.current_page = page_name
    
    # 追加パラメータの処理
    for key, value in kwargs.items():
        st.session_state[key] = value

# サイドバーナビゲーションの表示
def render_sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/null/sail-boat.png", width=80)
        st.title("セーリング戦略分析")
        
        st.subheader("メインメニュー")
        
        # プロジェクト関連
        with st.expander("プロジェクト管理", expanded=True):
            st.button("プロジェクト一覧", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "projects"},
                     key="btn_projects",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "projects" else "secondary")
            
            st.button("新規プロジェクト作成", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "project_create"},
                     key="btn_project_create",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "project_create" else "secondary")
            
            # 選択中のプロジェクトがある場合
            if st.session_state.selected_project_id is not None:
                # プロジェクト名を取得する処理（実際の実装ではプロジェクトマネージャーから取得）
                project_name = f"プロジェクト詳細"  # 仮の実装
                
                st.button(project_name, 
                         on_click=navigate_to, 
                         kwargs={"page_name": "project_detail"},
                         key="btn_project_detail",
                         use_container_width=True,
                         type="primary" if st.session_state.current_page == "project_detail" else "secondary")
        
        # データ関連
        with st.expander("データ管理", expanded=True):
            st.button("データインポート", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "data_import"},
                     key="btn_data_import",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "data_import" else "secondary")
            
            st.button("データ検証", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "data_validation"},
                     key="btn_data_validation",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "data_validation" else "secondary")
        
        # 分析関連
        with st.expander("分析", expanded=True):
            st.button("風向風速分析", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "wind_analysis"},
                     key="btn_wind_analysis",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "wind_analysis" else "secondary")
            
            st.button("戦略的判断分析", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "strategy_analysis"},
                     key="btn_strategy_analysis",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "strategy_analysis" else "secondary")
            
            st.button("パフォーマンス分析", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "performance_analysis"},
                     key="btn_performance_analysis",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "performance_analysis" else "secondary")
        
        # 可視化・エクスポート
        with st.expander("レポートと可視化", expanded=True):
            st.button("結果ダッシュボード", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "results_dashboard"},
                     key="btn_results_dashboard",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "results_dashboard" else "secondary")
            
            st.button("マップビュー", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "map_view"},
                     key="btn_map_view",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "map_view" else "secondary")
            
            st.button("統計チャート", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "statistics_dashboard"},
                     key="btn_statistics",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "statistics_dashboard" else "secondary")
            
            st.button("タイムライン分析", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "timeline_view"},
                     key="btn_timeline",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "timeline_view" else "secondary")
            
            st.button("エクスポート", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "export"},
                     key="btn_export",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "export" else "secondary")
        
        # 設定
        with st.expander("設定", expanded=False):
            st.button("アプリケーション設定", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "settings"},
                     key="btn_settings",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "settings" else "secondary")
            
            st.button("ヘルプ", 
                     on_click=navigate_to, 
                     kwargs={"page_name": "help"},
                     key="btn_help",
                     use_container_width=True,
                     type="primary" if st.session_state.current_page == "help" else "secondary")
        
        # フッター
        st.sidebar.markdown('---')
        st.sidebar.info('セーリング戦略分析システム v1.0')

# 一時的なページレンダリング関数（後で実際のページに置き換える）
def render_temp_page(title, description):
    st.title(title)
    st.info(description)

# メインコンテンツの表示
def render_main_content():
    current_page = st.session_state.current_page
    
    # ウェルカムページ
    if current_page == "welcome":
        from ui.integrated.pages.welcome import render_page
        render_page()
        return
    
    # プロジェクト関連ページ
    elif current_page == "projects":
        from ui.integrated.pages.project_list import render_page
        render_page()
        return
    elif current_page == "project_create":
        from ui.integrated.pages.project_create import render_page
        render_page()
        return
    elif current_page == "project_detail":
        from ui.integrated.pages.project_detail import render_page
        render_page(st.session_state.selected_project_id)
        return
    
    # データ関連ページ
    elif current_page == "data_import":
        from ui.integrated.pages.data_import import render_page
        render_page()
        return
    elif current_page == "batch_import":
        from ui.integrated.pages.batch_import import render_page
        render_page()
        return
    elif current_page == "sample_data":
        from ui.integrated.pages.sample_data import render_page
        render_page()
        return
    elif current_page == "data_validation":
        from ui.integrated.pages.data_validation import render_page
        render_page()
        return
    
    # 分析関連ページ
    elif current_page == "wind_analysis":
        render_temp_page("風向風速分析", "風向風速分析機能のページです。実装中...")
        return
    elif current_page == "strategy_analysis":
        render_temp_page("戦略的判断分析", "戦略的判断分析機能のページです。実装中...")
        return
    elif current_page == "performance_analysis":
        render_temp_page("パフォーマンス分析", "パフォーマンス分析機能のページです。実装中...")
        return
    
    # 可視化・エクスポート関連ページ
    elif current_page == "map_view":
        from ui.integrated.pages.map_view import render_page
        render_page()
        return
    elif current_page == "statistics_dashboard":
        from ui.integrated.pages.chart_view import render_page
        render_page()
        return
    elif current_page == "timeline_view":
        from ui.integrated.pages.timeline_view import render_page
        render_page()
        return
    elif current_page == "results_dashboard":
        from ui.integrated.pages.results_dashboard import render_page
        render_page()
        return
    elif current_page == "data_export":
        from ui.integrated.pages.data_export import render_page
        render_page()
        return
    elif current_page == "export":
        from ui.integrated.pages.export import render_page
        render_page()
        return
    
    # 設定関連ページ
    elif current_page == "settings":
        render_temp_page("アプリケーション設定", "アプリケーション設定ページです。実装中...")
        return
    elif current_page == "help":
        render_temp_page("ヘルプ", "ヘルプページです。実装中...")
        return
    
    # 未知のページ
    else:
        st.error(f"不明なページ: {current_page}")
        st.button("ホームに戻る", on_click=navigate_to, kwargs={"page_name": "welcome"})
        return

# メイン関数
def main():
    # ページ設定
    st.set_page_config(
        page_title="セーリング戦略分析システム",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # カスタムCSSの読み込み
    load_custom_css()
    
    # セッション状態の初期化
    initialize_session_state()
    
    # URLパラメータの処理
    query_params = st.query_params
    if 'page' in query_params:
        page = query_params['page']
        st.session_state.current_page = page
    
    if 'project_id' in query_params:
        project_id = query_params['project_id']
        st.session_state.selected_project_id = project_id
    
    if 'session_id' in query_params:
        session_id = query_params['session_id']
        st.session_state.selected_session_id = session_id
    
    # サイドバーの表示
    render_sidebar()
    
    # メインコンテンツの表示
    render_main_content()

if __name__ == "__main__":
    main()
