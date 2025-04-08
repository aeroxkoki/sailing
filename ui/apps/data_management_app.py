"""
ui.apps.data_management_app

データ管理UI統合アプリケーション
"""

import streamlit as st
import pandas as pd
import os
import sys
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# コンポーネントをインポート
from ui.components.forms.import_wizard import ImportWizard, BatchImportUI
from ui.components.forms.data_cleaning import DataCleaning
from ui.components.project.project_manager import initialize_project_manager
from ui.components.project.project_list import project_list_view
from ui.components.project.project_detail import project_detail_view
from ui.components.project.project_create import create_project_form
from ui.components.common.alerts import alert
from sailing_data_processor.data_model.container import GPSDataContainer


def data_management_app():
    """
    データ管理アプリケーションのメイン関数
    """
    # ページ設定
    st.set_page_config(
        page_title="データ管理 - セーリング戦略分析システム",
        page_icon="🚢",
        layout="wide",
    )

    # タイトル
    st.title("データ管理")
    st.write("GPSデータの管理、インポート、クリーニング、およびプロジェクト管理を行います")

    # セッション状態の初期化
    initialize_session_state()

    # サイドバーナビゲーション
    show_sidebar_navigation()

    # 現在の表示に応じて画面を切り替え
    if st.session_state["view"] == "projects":
        show_projects_view()
    elif st.session_state["view"] == "import":
        show_import_view()
    elif st.session_state["view"] == "batch_import":
        show_batch_import_view()
    elif st.session_state["view"] == "cleaning":
        show_cleaning_view()
    elif st.session_state["view"] == "project_detail":
        show_project_detail_view()


def initialize_session_state():
    """セッション状態を初期化"""
    if "view" not in st.session_state:
        st.session_state["view"] = "projects"
    if "imported_data" not in st.session_state:
        st.session_state["imported_data"] = None
    if "cleaned_data" not in st.session_state:
        st.session_state["cleaned_data"] = None
    if "selected_project_id" not in st.session_state:
        st.session_state["selected_project_id"] = None


def show_sidebar_navigation():
    """サイドバーナビゲーションを表示"""
    st.sidebar.title("ナビゲーション")
    
    # ナビゲーションボタン
    if st.sidebar.button("プロジェクト一覧", key="nav_projects"):
        st.session_state["view"] = "projects"
        st.session_state["selected_project_id"] = None
        st.rerun()

    if st.sidebar.button("新規データインポート", key="nav_import"):
        st.session_state["view"] = "import"
        st.rerun()
        
    if st.sidebar.button("バッチインポート", key="nav_batch_import"):
        st.session_state["view"] = "batch_import"
        st.rerun()
        
    if st.session_state["imported_data"] is not None:
        if st.sidebar.button("データクリーニング", key="nav_cleaning"):
            st.session_state["view"] = "cleaning"
            st.rerun()

    # サイドバー情報
    st.sidebar.markdown("---")
    st.sidebar.header("情報")
    st.sidebar.write("""
    このアプリでは以下の機能を利用できます:
    - プロジェクト管理: セーリングデータのプロジェクトとセッションを管理
    - データインポート: GPS位置データファイルを読み込み
    - バッチインポート: 複数ファイルを一括でインポート
    - データクリーニング: データの検証と問題の修正
    """)


def show_projects_view():
    """プロジェクト一覧ビューを表示"""
    st.header("プロジェクト管理")
    
    # タブで分けて表示
    tabs = st.tabs(["プロジェクト一覧", "新規プロジェクト作成"])
    
    with tabs[0]:  # プロジェクト一覧タブ
        selected_project_id = project_list_view()
        
        if selected_project_id:
            st.session_state["selected_project_id"] = selected_project_id
            st.session_state["view"] = "project_detail"
            st.rerun()
    
    with tabs[1]:  # プロジェクト作成タブ
        create_project_form()


def show_project_detail_view():
    """プロジェクト詳細ビューを表示"""
    project_id = st.session_state.get("selected_project_id")
    
    if not project_id:
        st.error("プロジェクトが選択されていません")
        st.session_state["view"] = "projects"
        st.rerun()
        return
    
    # 戻るボタン
    if st.button("← プロジェクト一覧に戻る"):
        st.session_state["view"] = "projects"
        st.rerun()
    
    # プロジェクト詳細を表示
    project_detail_view(project_id)


def show_import_view():
    """データインポートビューを表示"""
    st.header("データインポート")
    st.write("GPSデータをインポートするためのウィザードです")
    
    # インポートウィザードを表示
    wizard = ImportWizard(
        key="main_import_wizard",
        on_import_complete=on_import_complete
    )
    wizard.render()


def show_batch_import_view():
    """バッチインポートビューを表示"""
    st.header("バッチインポート")
    st.write("複数のGPSデータファイルを一括でインポートします")
    
    # バッチインポートUIを表示
    batch_import = BatchImportUI(
        key="main_batch_import",
        on_import_complete=on_batch_import_complete
    )
    batch_import.render()


def show_cleaning_view():
    """データクリーニングビューを表示"""
    st.header("データクリーニング")
    st.write("インポートされたデータを検証し、問題を修正します")
    
    if st.session_state["imported_data"] is None:
        st.error("インポートされたデータがありません。先にデータをインポートしてください。")
        return
    
    # データクリーニングコンポーネントを表示
    cleaner = DataCleaning(
        key="main_data_cleaning",
        on_data_cleaned=on_data_cleaned
    )
    cleaner.render(st.session_state["imported_data"])


def on_import_complete(container):
    """
    インポート完了時のコールバック
    
    Parameters
    ----------
    container : GPSDataContainer
        インポートされたデータコンテナ
    """
    st.session_state["imported_data"] = container
    st.session_state["view"] = "cleaning"
    
    # プロジェクトマネージャーを取得
    pm = initialize_project_manager()
    
    # セッションを作成
    file_name = container.metadata.get("file_name", "未命名セッション")
    session_name = f"インポート: {file_name}"
    description = f"インポートしたGPSデータ: {file_name}"
    tags = ["インポート"]
    
    session = pm.create_session(session_name, description, tags)
    
    # コンテナをセッションに保存
    if pm.save_container_to_session(container, session.session_id):
        alert(f"セッション「{session_name}」を作成し、データを保存しました", "success")
    else:
        alert("セッションの保存に失敗しました", "error")


def on_batch_import_complete(result):
    """
    バッチインポート完了時のコールバック
    
    Parameters
    ----------
    result : Union[GPSDataContainer, BatchImportResult]
        インポート結果
    """
    # プロジェクトマネージャーを取得
    pm = initialize_project_manager()
    
    if hasattr(result, 'successful'):
        # BatchImportResultの場合
        alert(f"{len(result.successful)}ファイルのインポートが完了しました", "success")
        
        # 各ファイルをセッションとして保存
        for file_name, container in result.successful.items():
            session_name = f"バッチインポート: {file_name}"
            description = f"バッチインポートしたGPSデータ: {file_name}"
            tags = ["バッチインポート"]
            
            session = pm.create_session(session_name, description, tags)
            
            # コンテナをセッションに保存
            pm.save_container_to_session(container, session.session_id)
        
        st.session_state["view"] = "projects"
    else:
        # 単一のGPSDataContainerの場合
        st.session_state["imported_data"] = result
        st.session_state["view"] = "cleaning"
        
        # セッションを作成
        file_name = result.metadata.get("file_name", "未命名セッション")
        session_name = f"バッチインポート: {file_name}"
        description = f"バッチインポートしたGPSデータ: {file_name}"
        tags = ["バッチインポート"]
        
        session = pm.create_session(session_name, description, tags)
        
        # コンテナをセッションに保存
        if pm.save_container_to_session(result, session.session_id):
            alert(f"セッション「{session_name}」を作成し、データを保存しました", "success")
        else:
            alert("セッションの保存に失敗しました", "error")


def on_data_cleaned(container):
    """
    データクリーニング完了時のコールバック
    
    Parameters
    ----------
    container : GPSDataContainer
        クリーニングされたデータコンテナ
    """
    st.session_state["cleaned_data"] = container
    
    # プロジェクトマネージャーを取得
    pm = initialize_project_manager()
    
    # セッションを作成
    file_name = container.metadata.get("file_name", "未命名セッション") 
    session_name = f"クリーニング済み: {file_name}"
    description = f"クリーニングしたGPSデータ: {file_name}"
    tags = ["クリーニング済み"]
    
    session = pm.create_session(session_name, description, tags)
    
    # コンテナをセッションに保存
    if pm.save_container_to_session(container, session.session_id):
        alert(f"クリーニングされたデータをセッション「{session_name}」として保存しました", "success")
        # プロジェクト一覧に戻る
        st.session_state["view"] = "projects"
        st.rerun()
    else:
        alert("クリーニングされたデータの保存に失敗しました", "error")


if __name__ == "__main__":
    data_management_app()
