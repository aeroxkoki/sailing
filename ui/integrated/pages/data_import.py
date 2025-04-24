# -*- coding: utf-8 -*-
"""
ui.integrated.pages.data_import

データインポートのメインページ
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
import os
import sys

# セッション状態キー
SESSION_STATE_KEY = "data_import_state"

def initialize_session_state():
    """セッション状態を初期化"""
    if SESSION_STATE_KEY not in st.session_state:
        st.session_state[SESSION_STATE_KEY] = {
            "selected_import_method": None,
            "import_completed": False,
            "imported_container": None
        }

def render_page():
    """データインポートページをレンダリング"""
    st.title("データインポート")
    
    # セッション状態を初期化
    initialize_session_state()
    
    # コンテナを取得
    state = st.session_state[SESSION_STATE_KEY]
    
    st.write("""
    セーリングGPSデータをインポートして分析に使用します。
    複数のファイル形式に対応しています。
    """)
    
    # インポート方法の選択
    method_options = {
        "single": "単一ファイルのインポート",
        "batch": "複数ファイルの一括インポート",
        "sample": "サンプルデータのインポート"
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("単一ファイルインポート", use_container_width=True, type="primary" if state.get("selected_import_method") == "single" else "secondary"):
            state["selected_import_method"] = "single"
            state["import_completed"] = False
    
    with col2:
        if st.button("バッチインポート", use_container_width=True, type="primary" if state.get("selected_import_method") == "batch" else "secondary"):
            state["selected_import_method"] = "batch"
            state["import_completed"] = False
            # バッチインポートページに遷移
            st.session_state.current_page = "batch_import"
            st.rerun()
    
    with col3:
        if st.button("サンプルデータ", use_container_width=True, type="primary" if state.get("selected_import_method") == "sample" else "secondary"):
            state["selected_import_method"] = "sample"
            state["import_completed"] = False
            # サンプルデータページに遷移
            st.session_state.current_page = "sample_data"
            st.rerun()
    
    # 選択されたインポート方法に基づいてUIを表示
    if state.get("selected_import_method") == "single":
        render_single_file_import()
    elif state.get("selected_import_method") == "batch":
        st.info("バッチインポートページに移動します...")
        # すでに上部のボタンでページ遷移の処理を行っているので、ここでは何もしない
    elif state.get("selected_import_method") == "sample":
        st.info("サンプルデータページに移動します...")
        # すでに上部のボタンでページ遷移の処理を行っているので、ここでは何もしない
    else:
        # 選択されていない場合は説明を表示
        render_import_explanation()

def render_single_file_import():
    """単一ファイルのインポートUI"""
    st.header("単一ファイルインポート")
    
    # インポートウィザードのインスタンス化
    with st.container():
        st.subheader("ファイルのインポート")
        st.write("""
        インポートウィザードを使用して、GPSデータファイルをステップバイステップでインポートします。
        """)
        
        # インポートコントローラーを取得
        from ui.integrated.controllers.import_controller import ImportController
        controller = ImportController()
        
        # エンハンスドインポートウィザードを表示
        from ui.components.forms.import_wizard.enhanced_wizard import EnhancedImportWizard
        
        # コールバック関数: インポート完了時にセッション状態を更新
        def on_import_complete(container):
            st.session_state[SESSION_STATE_KEY]["import_completed"] = True
            st.session_state[SESSION_STATE_KEY]["imported_container"] = container
            controller.set_imported_container(container)
        
        wizard = EnhancedImportWizard(
            key="single_file_import_wizard",
            on_import_complete=on_import_complete
        )
        wizard.render()
        
        # インポート完了後の処理
        if st.session_state[SESSION_STATE_KEY].get("import_completed"):
            container = st.session_state[SESSION_STATE_KEY].get("imported_container")
            if container:
                st.success("データインポートが完了しました。")
                
                # セッション作成オプションを表示
                st.subheader("セッション作成")
                st.write("インポートしたデータをプロジェクトのセッションとして保存できます。")
                
                # プロジェクト選択
                projects = get_available_projects()
                if projects:
                    project_options = {p["id"]: p["name"] for p in projects}
                    project_id = st.selectbox(
                        "プロジェクト",
                        options=list(project_options.keys()),
                        format_func=lambda x: project_options.get(x, "不明なプロジェクト"),
                        key="session_project_id"
                    )
                    
                    # セッション情報入力
                    session_name = st.text_input("セッション名", key="session_name")
                    session_desc = st.text_area("説明", key="session_description")
                    session_tags = st.text_input("タグ（カンマ区切り）", key="session_tags")
                    
                    tags_list = [tag.strip() for tag in session_tags.split(",")] if session_tags else []
                    
                    # セッション作成ボタン
                    if st.button("セッションを作成", key="create_session_btn"):
                        if not session_name:
                            st.error("セッション名を入力してください。")
                        else:
                            success = controller.create_session_from_container(
                                project_id=project_id,
                                name=session_name,
                                description=session_desc,
                                tags=tags_list
                            )
                            
                            if success:
                                st.success("セッションが作成されました。")
                                
                                # プロジェクト詳細ページに移動するオプション
                                if st.button("プロジェクト詳細を表示", key="goto_project_detail"):
                                    st.session_state.current_page = "project_detail"
                                    st.session_state.selected_project_id = project_id
                                    st.rerun()
                            else:
                                st.error("セッション作成に失敗しました。")
                                for error in controller.get_errors():
                                    st.error(error)
                else:
                    st.warning("利用可能なプロジェクトがありません。先にプロジェクトを作成してください。")
                    if st.button("新規プロジェクト作成", key="goto_project_create"):
                        st.session_state.current_page = "project_create"
                        st.rerun()
                
                # データ検証ページに移動するオプション
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("データ検証を実行", key="goto_data_validation"):
                        st.session_state.current_page = "data_validation"
                        st.rerun()
                
                with col2:
                    if st.button("新しいインポートを開始", key="restart_import"):
                        st.session_state[SESSION_STATE_KEY]["selected_import_method"] = None
                        st.session_state[SESSION_STATE_KEY]["import_completed"] = False
                        st.session_state[SESSION_STATE_KEY]["imported_container"] = None
                        wizard.reset()
                        st.rerun()

def render_import_explanation():
    """インポート方法の説明を表示"""
    st.subheader("インポート方法を選択")
    
    st.info("""
    👆 上記のオプションからインポート方法を選択してください。
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 単一ファイルインポート
        
        * 1つのファイルをインポート
        * 詳細な設定とプレビュー
        * ステップバイステップのウィザード
        * GPX, CSV, TCX, FITに対応
        """)
    
    with col2:
        st.markdown("""
        ### バッチインポート
        
        * 複数ファイルを一括処理
        * 共通設定を適用
        * 進捗状況の監視
        * 一括メタデータ設定
        """)
    
    with col3:
        st.markdown("""
        ### サンプルデータ
        
        * 組み込みサンプルを使用
        * テスト・学習用
        * すぐに分析開始可能
        * 設定不要
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 対応ファイル形式
    
    * **CSV** (カンマ区切りテキスト) - カスタムデータログ、エクスポートされたデータ
    * **GPX** (GPS Exchange Format) - 多くのGPSデバイスやアプリから出力される標準形式
    * **TCX** (Training Center XML) - Garmin社のトレーニングデータ形式
    * **FIT** (Flexible and Interoperable Data Transfer) - 機能拡張可能なバイナリ形式
    """)

def get_available_projects() -> List[Dict[str, Any]]:
    """
    利用可能なプロジェクトのリストを取得
    
    Returns
    -------
    List[Dict[str, Any]]
        プロジェクトの辞書のリスト
    """
    from ui.components.project.project_manager import initialize_project_manager
    
    project_manager = initialize_project_manager()
    if not project_manager:
        return []
    
    # ルートプロジェクトを取得
    root_projects = project_manager.get_root_projects()
    
    # プロジェクト情報を整形
    projects = []
    for project in root_projects:
        projects.append({
            "id": project.project_id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        })
        
        # サブプロジェクトも取得
        sub_projects = project_manager.get_sub_projects(project.project_id)
        for sub in sub_projects:
            projects.append({
                "id": sub.project_id,
                "name": f"{project.name} > {sub.name}",
                "description": sub.description,
                "created_at": sub.created_at,
                "updated_at": sub.updated_at
            })
    
    return projects

if __name__ == "__main__":
    render_page()
