"""
ui.integrated.pages.project_create

セーリング戦略分析システムのプロジェクト作成ページ
"""

import streamlit as st
import os
import sys
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# 自作モジュールのインポート
from ui.components.project.project_manager import initialize_project_manager

def render_page():
    """
    新規プロジェクト作成ページを表示する
    """
    # ヘッダー
    st.markdown("<div class='main-header'>新規プロジェクト作成</div>", unsafe_allow_html=True)

    # プロジェクトマネージャーの初期化
    pm = initialize_project_manager()
    
    # プロジェクト作成フォーム
    with st.form("project_create_form"):
        # プロジェクト基本情報
        st.subheader("基本情報")
        
        name = st.text_input("プロジェクト名 *", 
                            help="プロジェクトを識別するための名前（必須）")
        
        description = st.text_area("説明", 
                                 help="プロジェクトの目的や内容の説明")
        
        # タグ入力（カンマ区切り）
        tags_input = st.text_input(
            "タグ (カンマ区切り)", 
            help="複数のタグを入力する場合はカンマで区切ってください。例: 練習,レース,強風"
        )
        
        # 追加情報（エクスパンダー内）
        with st.expander("追加情報", expanded=False):
            location = st.text_input("場所", 
                                   help="セーリングを行った場所や水域")
            
            boat_type = st.text_input("艇種", 
                                    help="使用したボートの種類や艇種")
            
            team = st.text_input("チーム", 
                               help="所属するチームや団体")
            
            custom_field = st.text_input("その他情報", 
                                      help="その他の追加情報")
        
        # バリデーションメッセージ用のエリア
        validation_msg = st.empty()
        
        # 送信ボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            cancel_button = st.form_submit_button("キャンセル", 
                                               type="secondary", 
                                               use_container_width=True)
        with col2:
            submit_button = st.form_submit_button("プロジェクトを作成", 
                                               type="primary", 
                                               use_container_width=True)
        
        # フォーム送信処理
        if submit_button:
            # 必須フィールドの検証
            if not name:
                validation_msg.error("プロジェクト名は必須項目です。")
            else:
                # タグのリスト化
                tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
                
                # メタデータの設定
                metadata = {}
                if location:
                    metadata["location"] = location
                if boat_type:
                    metadata["boat_type"] = boat_type
                if team:
                    metadata["team"] = team
                if custom_field:
                    metadata["custom"] = custom_field
                
                # プロジェクトを作成
                new_project = pm.create_project(name, description, tags, metadata)
                
                if new_project:
                    # 成功メッセージと遷移
                    st.success(f"プロジェクト「{name}」を作成しました。")
                    
                    # プロジェクトの詳細ページに遷移
                    st.session_state.selected_project_id = new_project.project_id
                    st.session_state.current_page = "project_detail"
                    st.rerun()
                else:
                    st.error("プロジェクトの作成に失敗しました。")
        
        if cancel_button:
            # キャンセルボタンが押された場合の処理
            st.session_state.current_page = "projects"
            st.rerun()
    
    # フォームの下部にプロジェクト管理への戻るリンク
    st.markdown("---")
    
    if st.button("プロジェクト一覧に戻る", use_container_width=True):
        st.session_state.current_page = "projects"
        st.rerun()

if __name__ == "__main__":
    render_page()
