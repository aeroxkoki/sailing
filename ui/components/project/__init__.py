"""
ui.components.project

Project management components for the sailing strategy analyzer UI.
"""

from ui.components.project.project_list import project_list_view as ProjectListView
from ui.components.project.project_detail import ProjectDetailView
from ui.components.project.project_create import ProjectCreateView
# ProjectManagerViewのインポートを一時的に削除（存在しないため）
# from ui.components.project.project_manager import ProjectManagerView

__all__ = [
    'ProjectListView',
    'ProjectDetailView',
    'ProjectCreateView',
    # 'ProjectManagerView'  # 一時的にコメントアウト
]
