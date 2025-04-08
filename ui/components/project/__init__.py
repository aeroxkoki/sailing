"""
ui.components.project

���ȡ�#nUI������ȒЛY��ñ��
"""

from ui.components.project.project_list import ProjectListView
from ui.components.project.project_detail import ProjectDetailView
from ui.components.project.project_create import ProjectCreateView
from ui.components.project.project_manager import ProjectManagerView

__all__ = [
    'ProjectListView',
    'ProjectDetailView',
    'ProjectCreateView',
    'ProjectManagerView'
]
