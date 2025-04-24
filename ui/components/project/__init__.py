# -*- coding: utf-8 -*-
"""
ui.components.project

Project management components for the sailing strategy analyzer UI.
"""

# UIコンポーネントの関数をクラス名のエイリアスでインポート
from ui.components.project.project_list import project_list_view as ProjectListView
# project_detail.pyが存在しなさそうなので、project_details.pyからインポート
try:
    from ui.components.project.project_detail import ProjectDetailView
except ImportError:
    # 代替としてproject_details.pyからのインポートを試みる
    try:
        from ui.components.project.project_details import project_details_view as ProjectDetailView
    except ImportError:
        # どちらのファイルからもインポートできない場合は、警告を記録してダミー関数を定義
        import logging
        logging.warning("ProjectDetailViewのインポートに失敗しました。ダミー関数を使用します。")
        def ProjectDetailView(*args, **kwargs):
            import streamlit as st
            st.error("ProjectDetailViewコンポーネントが利用できません。")

try:
    from ui.components.project.project_create import ProjectCreateView
except ImportError:
    # 代替としてproject_form.pyからのインポートを試みる
    try:
        from ui.components.project.project_form import project_form as ProjectCreateView
    except ImportError:
        # どちらのファイルからもインポートできない場合は、警告を記録してダミー関数を定義
        import logging
        logging.warning("ProjectCreateViewのインポートに失敗しました。ダミー関数を使用します。")
        def ProjectCreateView(*args, **kwargs):
            import streamlit as st
            st.error("ProjectCreateViewコンポーネントが利用できません。")

# プロジェクト管理クラスのエイリアスとして、initialize_project_manager関数をインポート
from ui.components.project.project_manager import initialize_project_manager as ProjectManagerView

__all__ = [
    'ProjectListView',
    'ProjectDetailView',
    'ProjectCreateView',
    'ProjectManagerView'
]
