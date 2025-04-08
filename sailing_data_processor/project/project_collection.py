"""
sailing_data_processor.project.project_collection

プロジェクトコレクションクラスを定義するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set
import os
import json
from datetime import datetime
import uuid
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

class ProjectCollection:
    """
    プロジェクトコレクションクラス
    
    複数のプロジェクトを管理するコレクション。
    プロジェクト階層構造の管理とプロジェクト検索機能を提供します。
    
    属性
    -----
    projects : Dict[str, Project]
        プロジェクトのマップ（ID -> Projectオブジェクト）
    root_projects : List[str]
        ルートプロジェクト（親を持たないプロジェクト）のIDリスト
    version : str
        コレクションのバージョン
    metadata : Dict[str, Any]
        コレクションに関連するメタデータ
    """
    
    def __init__(self, version: str = "1.0", metadata: Dict[str, Any] = None):
        """
        プロジェクトコレクションの初期化
        
        Parameters
        ----------
        version : str, optional
            コレクションのバージョン, by default "1.0"
        metadata : Dict[str, Any], optional
            コレクションに関連するメタデータ, by default None
        """
        self.projects = {}  # project_id -> Project
        self.root_projects = []  # 親を持たないプロジェクトのIDリスト
        self.version = version
        self.metadata = metadata or {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def add_project(self, project) -> None:
        """
        プロジェクトをコレクションに追加
        
        Parameters
        ----------
        project : Project
            追加するプロジェクト
        """
        self.projects[project.project_id] = project
        
        # 親がない場合はルートプロジェクトとして追加
        if not project.parent_id:
            if project.project_id not in self.root_projects:
                self.root_projects.append(project.project_id)
        
        # メタデータの更新日時を更新
        self.metadata["updated_at"] = datetime.now().isoformat()
    
    def remove_project(self, project_id: str, recursive: bool = False) -> bool:
        """
        プロジェクトをコレクションから削除
        
        Parameters
        ----------
        project_id : str
            削除するプロジェクトID
        recursive : bool, optional
            サブプロジェクトも削除するかどうか, by default False
        
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if project_id not in self.projects:
            logger.warning(f"プロジェクト {project_id} がコレクションに存在しません")
            return False
        
        project = self.projects[project_id]
        
        # サブプロジェクトの処理
        if recursive:
            for sub_id in project.sub_projects[:]:  # コピーを使用して反復中に変更を防ぐ
                self.remove_project(sub_id, recursive=True)
        elif project.sub_projects:
            # サブプロジェクトがある場合、それらを親プロジェクトに移動
            if project.parent_id and project.parent_id in self.projects:
                parent = self.projects[project.parent_id]
                for sub_id in project.sub_projects:
                    sub_project = self.projects.get(sub_id)
                    if sub_project:
                        sub_project.parent_id = project.parent_id
                        parent.add_sub_project(sub_id)
            else:
                # 親がない場合、サブプロジェクトをルートに移動
                for sub_id in project.sub_projects:
                    sub_project = self.projects.get(sub_id)
                    if sub_project:
                        sub_project.parent_id = None
                        if sub_id not in self.root_projects:
                            self.root_projects.append(sub_id)
        
        # ルートプロジェクトリストから削除
        if project_id in self.root_projects:
            self.root_projects.remove(project_id)
        
        # 親プロジェクトから削除
        if project.parent_id and project.parent_id in self.projects:
            parent = self.projects[project.parent_id]
            parent.remove_sub_project(project_id)
        
        # プロジェクトの削除
        del self.projects[project_id]
        
        # メタデータの更新日時を更新
        self.metadata["updated_at"] = datetime.now().isoformat()
        
        return True
    
    def get_project(self, project_id: str):
        """
        プロジェクトを取得
        
        Parameters
        ----------
        project_id : str
            取得するプロジェクトID
        
        Returns
        -------
        Optional[Project]
            プロジェクト、見つからない場合はNone
        """
        return self.projects.get(project_id)
    
    def get_root_projects(self) -> List:
        """
        ルートプロジェクトのリストを取得
        
        Returns
        -------
        List[Project]
            ルートプロジェクトのリスト
        """
        return [self.projects[pid] for pid in self.root_projects if pid in self.projects]
    
    def get_sub_projects(self, project_id: str) -> List:
        """
        サブプロジェクトのリストを取得
        
        Parameters
        ----------
        project_id : str
            親プロジェクトID
        
        Returns
        -------
        List[Project]
            サブプロジェクトのリスト
        """
        project = self.get_project(project_id)
        if not project:
            return []
        
        return [self.projects[sub_id] for sub_id in project.sub_projects if sub_id in self.projects]
    
    def search_projects(self, query: str = "", tags: List[str] = None, 
                       categories: List[str] = None) -> List:
        """
        プロジェクトを検索
        
        Parameters
        ----------
        query : str, optional
            検索クエリ（プロジェクト名と説明に対して）, by default ""
        tags : List[str], optional
            フィルタリングするタグのリスト, by default None
        categories : List[str], optional
            フィルタリングするカテゴリのリスト, by default None
        
        Returns
        -------
        List[Project]
            検索結果のプロジェクトリスト
        """
        query = query.lower()
        results = []
        
        for project in self.projects.values():
            # クエリによる検索
            match_query = (not query) or (
                query in project.name.lower() or
                query in project.description.lower()
            )
            
            # タグによるフィルタリング
            match_tags = (not tags) or all(tag in project.tags for tag in tags)
            
            # カテゴリによるフィルタリング
            match_category = (not categories) or getattr(project, 'category', '') in categories
            
            if match_query and match_tags and match_category:
                results.append(project)
        
        return sorted(results, key=lambda p: p.name)
    
    def get_all_tags(self) -> Set[str]:
        """
        すべてのタグを取得
        
        Returns
        -------
        Set[str]
            ユニークなタグのセット
        """
        tags = set()
        
        for project in self.projects.values():
            tags.update(project.tags)
        
        return tags
    
    def get_all_categories(self) -> Set[str]:
        """
        すべてのカテゴリを取得
        
        Returns
        -------
        Set[str]
            ユニークなカテゴリのセット
        """
        categories = set()
        
        for project in self.projects.values():
            category = getattr(project, 'category', '')
            if category:
                categories.add(category)
        
        return categories
    
    def move_project(self, project_id: str, new_parent_id: Optional[str] = None) -> bool:
        """
        プロジェクトを別の親プロジェクトに移動
        
        Parameters
        ----------
        project_id : str
            移動するプロジェクトID
        new_parent_id : Optional[str], optional
            新しい親プロジェクトID（Noneの場合はルートに移動）, by default None
        
        Returns
        -------
        bool
            移動に成功した場合True
        """
        project = self.get_project(project_id)
        if not project:
            return False
        
        # 循環参照の防止
        if new_parent_id and self._is_descendant(new_parent_id, project_id):
            logger.error(f"循環参照が発生するため移動できません: {project_id} -> {new_parent_id}")
            return False
        
        # 現在の親から削除
        old_parent_id = project.parent_id
        if old_parent_id and old_parent_id in self.projects:
            old_parent = self.projects[old_parent_id]
            old_parent.remove_sub_project(project_id)
        elif project_id in self.root_projects:
            self.root_projects.remove(project_id)
        
        # 新しい親に追加
        if new_parent_id and new_parent_id in self.projects:
            new_parent = self.projects[new_parent_id]
            new_parent.add_sub_project(project_id)
            project.parent_id = new_parent_id
            
            # ルートプロジェクトリストから削除（もし含まれていれば）
            if project_id in self.root_projects:
                self.root_projects.remove(project_id)
        else:
            # ルートプロジェクトに移動
            project.parent_id = None
            if project_id not in self.root_projects:
                self.root_projects.append(project_id)
        
        # メタデータの更新日時を更新
        self.metadata["updated_at"] = datetime.now().isoformat()
        
        return True
    
    def _is_descendant(self, project_id: str, ancestor_id: str) -> bool:
        """
        あるプロジェクトが別のプロジェクトの子孫かどうかを判定
        
        Parameters
        ----------
        project_id : str
            判定するプロジェクトID
        ancestor_id : str
            祖先候補のプロジェクトID
        
        Returns
        -------
        bool
            子孫である場合True
        """
        project = self.get_project(project_id)
        if not project:
            return False
        
        # 親を辿っていく
        current_id = project.parent_id
        while current_id:
            if current_id == ancestor_id:
                return True
            
            current = self.get_project(current_id)
            if not current:
                break
            
            current_id = current.parent_id
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        プロジェクトコレクションを辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            プロジェクトコレクション情報を含む辞書
        """
        return {
            "version": self.version,
            "metadata": self.metadata,
            "root_projects": self.root_projects,
            "projects": {pid: project.to_dict() for pid, project in self.projects.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        辞書からプロジェクトコレクションを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            プロジェクトコレクション情報を含む辞書
        
        Returns
        -------
        ProjectCollection
            作成されたプロジェクトコレクションインスタンス
        """
        from sailing_data_processor.project.project_model import Project
        
        collection = cls(
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {})
        )
        
        # プロジェクトの読み込み
        projects_data = data.get("projects", {})
        for pid, project_data in projects_data.items():
            try:
                project = Project.from_dict(project_data)
                collection.projects[pid] = project
            except Exception as e:
                logger.error(f"プロジェクト {pid} の読み込みに失敗しました: {e}")
        
        # ルートプロジェクトの設定
        collection.root_projects = data.get("root_projects", [])
        
        return collection
