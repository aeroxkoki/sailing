# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.project_storage

プロジェクトデータの永続化を行うモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import uuid
import logging
import pandas as pd

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.project.project_model import Project, Session, AnalysisResult

# ロガーの設定
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class ProjectStorage:
    """
    プロジェクトストレージクラス
    
    プロジェクト、セッション、分析結果のデータを永続化するクラス。
    ファイルシステムを使用してデータを保存します。
    
    属性
    -----
    base_path : Path
        データを保存するベースディレクトリ
    projects_path : Path
        プロジェクトデータを保存するディレクトリ
    sessions_path : Path
        セッションデータを保存するディレクトリ
    results_path : Path
        分析結果を保存するディレクトリ
    data_path : Path
        GPSデータを保存するディレクトリ
    state_path : Path
        セッション状態を保存するディレクトリ
    projects : Dict[str, Project]
        プロジェクトのキャッシュ（ID -> Projectオブジェクト）
    sessions : Dict[str, Session]
        セッションのキャッシュ（ID -> Sessionオブジェクト）
    results : Dict[str, AnalysisResult]
        分析結果のキャッシュ（ID -> AnalysisResultオブジェクト）
    """
    
    def __init__(self, base_path: Union[str, Path] = "projects_data"):
        """
        プロジェクトストレージの初期化
        
        Parameters
        ----------
        base_path : Union[str, Path], optional
            データを保存するベースディレクトリ, by default "projects_data"
        """
        self.base_path = Path(base_path)
        self.projects_path = self.base_path / "projects"
        self.sessions_path = self.base_path / "sessions"
        self.results_path = self.base_path / "results"
        self.data_path = self.base_path / "data"
        self.state_path = self.base_path / "states"
        
        # キャッシュの初期化
        self.projects = {}
        self.sessions = {}
        self.results = {}
        
        # ディレクトリの作成
        self._create_directories()
        
        # データの読み込み
        self.reload()
    
    def _create_directories(self) -> None:
        """
        必要なディレクトリを作成
        """
        self.projects_path.mkdir(parents=True, exist_ok=True)
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.state_path.mkdir(parents=True, exist_ok=True)
    
    def reload(self) -> None:
        """
        すべてのデータを再読み込み
        """
        self._load_projects()
        self._load_sessions()
        self._load_results()
    
    def _load_projects(self) -> None:
        """
        プロジェクトデータを読み込み
        """
        self.projects = {}
        
        try:
            for project_file in self.projects_path.glob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                        project = Project.from_dict(project_data)
                        self.projects[project.project_id] = project
                except Exception as e:
                    logger.error(f"プロジェクトファイル {project_file} の読み込みに失敗しました: {e}")
        except Exception as e:
            logger.error(f"プロジェクトディレクトリの読み込みに失敗しました: {e}")
    
    def _load_sessions(self) -> None:
        """
        セッションデータを読み込み
        """
        self.sessions = {}
        
        try:
            for session_file in self.sessions_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        session = Session.from_dict(session_data)
                        self.sessions[session.session_id] = session
                except Exception as e:
                    logger.error(f"セッションファイル {session_file} の読み込みに失敗しました: {e}")
        except Exception as e:
            logger.error(f"セッションディレクトリの読み込みに失敗しました: {e}")
    
    def _load_results(self) -> None:
        """
        分析結果データを読み込み
        """
        self.results = {}
        
        try:
            for result_file in self.results_path.glob("*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        result = AnalysisResult.from_dict(result_data)
                        self.results[result.result_id] = result
                except Exception as e:
                    logger.error(f"分析結果ファイル {result_file} の読み込みに失敗しました: {e}")
        except Exception as e:
            logger.error(f"分析結果ディレクトリの読み込みに失敗しました: {e}")
    
    def save_project(self, project: Project) -> bool:
        """
        プロジェクトを保存
        
        Parameters
        ----------
        project : Project
            保存するプロジェクト
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        project_file = self.projects_path / f"{project.project_id}.json"
        
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
            
            # キャッシュを更新
            self.projects[project.project_id] = project
            
            return True
        except Exception as e:
            logger.error(f"プロジェクト {project.project_id} の保存に失敗しました: {e}")
            return False
    
    def save_session(self, session: Session) -> bool:
        """
        セッションを保存
        
        Parameters
        ----------
        session : Session
            保存するセッション
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        session_file = self.sessions_path / f"{session.session_id}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            
            # キャッシュを更新
            self.sessions[session.session_id] = session
            
            return True
        except Exception as e:
            logger.error(f"セッション {session.session_id} の保存に失敗しました: {e}")
            return False
    
    def save_result(self, result: AnalysisResult) -> bool:
        """
        分析結果を保存
        
        Parameters
        ----------
        result : AnalysisResult
            保存する分析結果
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        result_file = self.results_path / f"{result.result_id}.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            
            # キャッシュを更新
            self.results[result.result_id] = result
            
            return True
        except Exception as e:
            logger.error(f"分析結果 {result.result_id} の保存に失敗しました: {e}")
            return False
    
    def save_container(self, container: GPSDataContainer, session_id: str) -> bool:
        """
        GPSデータコンテナをセッションに関連付けて保存
        
        Parameters
        ----------
        container : GPSDataContainer
            保存するGPSデータコンテナ
        session_id : str
            関連付けるセッションID
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.error(f"セッション {session_id} が見つかりません")
            return False
        
        data_file = self.data_path / f"{session_id}.json"
        
        try:
            # コンテナデータをJSON形式で保存
            data_dict = container.to_dict()
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2)
            
            # セッションにデータファイルへの参照を設定
            session.set_data(str(data_file))
            self.save_session(session)
            
            return True
        except Exception as e:
            logger.error(f"GPSデータコンテナの保存に失敗しました: {e}")
            return False
    
    def load_container(self, session_id: str) -> Optional[GPSDataContainer]:
        """
        セッションに関連付けられたGPSデータコンテナを読み込み
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        Optional[GPSDataContainer]
            読み込まれたGPSデータコンテナ、失敗した場合はNone
        """
        session = self.get_session(session_id)
        
        if not session or not session.data_file:
            logger.error(f"セッション {session_id} にデータファイルが関連付けられていません")
            return None
        
        data_file = Path(session.data_file)
        
        if not data_file.exists():
            logger.error(f"データファイル {data_file} が存在しません")
            return None
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
            
            # コンテナの復元
            if data_dict.get('type') == 'GPSDataContainer':
                # DataFrameの復元
                df = pd.DataFrame(data_dict['data'])
                
                # タイムスタンプの復元
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return GPSDataContainer(df, data_dict['metadata'])
            
            logger.error(f"不正なデータ形式: {data_dict.get('type')}")
            return None
        except Exception as e:
            logger.error(f"GPSデータコンテナの読み込みに失敗しました: {e}")
            return None
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """
        セッションの状態を保存
        
        Parameters
        ----------
        session_id : str
            セッションID
        state : Dict[str, Any]
            保存する状態
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.error(f"セッション {session_id} が見つかりません")
            return False
        
        state_file = self.state_path / f"{session_id}.json"
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            # セッションに状態ファイルへの参照を設定
            session.set_state(str(state_file))
            self.save_session(session)
            
            return True
        except Exception as e:
            logger.error(f"セッション状態の保存に失敗しました: {e}")
            return False
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションの状態を読み込み
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            読み込まれた状態、失敗した場合はNone
        """
        session = self.get_session(session_id)
        
        if not session or not session.state_file:
            logger.error(f"セッション {session_id} に状態ファイルが関連付けられていません")
            return None
        
        state_file = Path(session.state_file)
        
        if not state_file.exists():
            logger.error(f"状態ファイル {state_file} が存在しません")
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            return state
        except Exception as e:
            logger.error(f"セッション状態の読み込みに失敗しました: {e}")
            return None
    
    def create_project(self, name: str, description: str = "", 
                      tags: List[str] = None, metadata: Dict[str, Any] = None,
                      parent_id: str = None) -> Optional[Project]:
        """
        新しいプロジェクトを作成
        
        Parameters
        ----------
        name : str
            プロジェクト名
        description : str, optional
            プロジェクトの説明, by default ""
        tags : List[str], optional
            プロジェクトに関連するタグ, by default None
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        parent_id : str, optional
            親プロジェクトID, by default None
            
        Returns
        -------
        Optional[Project]
            作成されたプロジェクト、失敗した場合はNone
        """
        project = Project(name, description, tags, metadata, parent_id=parent_id)
        
        if self.save_project(project):
            # 親プロジェクトが指定されている場合、サブプロジェクトとして追加
            if parent_id:
                parent = self.get_project(parent_id)
                if parent:
                    parent.add_sub_project(project.project_id)
                    self.save_project(parent)
            
            return project
        
        return None
    
    def create_session(self, name: str, description: str = "", 
                      tags: List[str] = None, metadata: Dict[str, Any] = None,
                      category: str = "general") -> Optional[Session]:
        """
        新しいセッションを作成
        
        Parameters
        ----------
        name : str
            セッション名
        description : str, optional
            セッションの説明, by default ""
        tags : List[str], optional
            セッションに関連するタグ, by default None
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        category : str, optional
            セッションカテゴリ, by default "general"
            
        Returns
        -------
        Optional[Session]
            作成されたセッション、失敗した場合はNone
        """
        session = Session(name, description, tags, metadata, category=category)
        
        if self.save_session(session):
            return session
        
        return None
    
    def create_result(self, name: str, result_type: str, data: Dict[str, Any],
                     description: str = "", metadata: Dict[str, Any] = None) -> Optional[AnalysisResult]:
        """
        新しい分析結果を作成
        
        Parameters
        ----------
        name : str
            分析結果名
        result_type : str
            結果タイプ
        data : Dict[str, Any]
            結果データ
        description : str, optional
            分析結果の説明, by default ""
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        Optional[AnalysisResult]
            作成された分析結果、失敗した場合はNone
        """
        result = AnalysisResult(name, result_type, data, description, metadata)
        
        if self.save_result(result):
            return result
        
        return None
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        プロジェクトを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        Optional[Project]
            プロジェクト、見つからない場合はNone
        """
        return self.projects.get(project_id)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        セッションを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        Optional[Session]
            セッション、見つからない場合はNone
        """
        return self.sessions.get(session_id)
    
    def get_result(self, result_id: str) -> Optional[AnalysisResult]:
        """
        分析結果を取得
        
        Parameters
        ----------
        result_id : str
            分析結果ID
            
        Returns
        -------
        Optional[AnalysisResult]
            分析結果、見つからない場合はNone
        """
        return self.results.get(result_id)
    
    def delete_project(self, project_id: str, delete_sessions: bool = False,
                      delete_sub_projects: bool = False) -> bool:
        """
        プロジェクトを削除
        
        Parameters
        ----------
        project_id : str
            削除するプロジェクトID
        delete_sessions : bool, optional
            関連するセッションも削除するかどうか, by default False
        delete_sub_projects : bool, optional
            サブプロジェクトも削除するかどうか, by default False
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        project = self.get_project(project_id)
        
        if not project:
            logger.error(f"プロジェクト {project_id} が見つかりません")
            return False
        
        try:
            # サブプロジェクトの削除
            if delete_sub_projects:
                for sub_project_id in project.sub_projects[:]:  # リストのコピーを使用
                    self.delete_project(sub_project_id, delete_sessions, delete_sub_projects)
            
            # 関連するセッションの削除
            if delete_sessions:
                for session_id in project.sessions[:]:  # リストのコピーを使用
                    self.delete_session(session_id, delete_data=True)
            
            # 親プロジェクトからの削除
            if project.parent_id:
                parent = self.get_project(project.parent_id)
                if parent:
                    parent.remove_sub_project(project_id)
                    self.save_project(parent)
            
            # プロジェクトファイルの削除
            project_file = self.projects_path / f"{project_id}.json"
            if project_file.exists():
                project_file.unlink()
            
            # キャッシュから削除
            if project_id in self.projects:
                del self.projects[project_id]
            
            return True
        except Exception as e:
            logger.error(f"プロジェクト {project_id} の削除に失敗しました: {e}")
            return False
    
    def delete_session(self, session_id: str, delete_data: bool = False) -> bool:
        """
        セッションを削除
        
        Parameters
        ----------
        session_id : str
            削除するセッションID
        delete_data : bool, optional
            関連するデータも削除するかどうか, by default False
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.error(f"セッション {session_id} が見つかりません")
            return False
        
        try:
            # 関連するデータファイルの削除
            if delete_data:
                if session.data_file:
                    data_file = Path(session.data_file)
                    if data_file.exists():
                        data_file.unlink()
                
                if session.state_file:
                    state_file = Path(session.state_file)
                    if state_file.exists():
                        state_file.unlink()
                
                # 関連する分析結果の削除
                for result_id in session.analysis_results[:]:  # リストのコピーを使用
                    self.delete_result(result_id)
            
            # セッションファイルの削除
            session_file = self.sessions_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # プロジェクトからの削除
            for project in self.projects.values():
                if session_id in project.sessions:
                    project.remove_session(session_id)
                    self.save_project(project)
            
            # キャッシュから削除
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            return True
        except Exception as e:
            logger.error(f"セッション {session_id} の削除に失敗しました: {e}")
            return False
    
    def delete_result(self, result_id: str) -> bool:
        """
        分析結果を削除
        
        Parameters
        ----------
        result_id : str
            削除する分析結果ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        result = self.get_result(result_id)
        
        if not result:
            logger.error(f"分析結果 {result_id} が見つかりません")
            return False
        
        try:
            # 分析結果ファイルの削除
            result_file = self.results_path / f"{result_id}.json"
            if result_file.exists():
                result_file.unlink()
            
            # セッションからの削除
            for session in self.sessions.values():
                if result_id in session.analysis_results:
                    session.remove_analysis_result(result_id)
                    self.save_session(session)
            
            # キャッシュから削除
            if result_id in self.results:
                del self.results[result_id]
            
            return True
        except Exception as e:
            logger.error(f"分析結果 {result_id} の削除に失敗しました: {e}")
            return False
    
    def add_session_to_project(self, project_id: str, session_id: str) -> bool:
        """
        セッションをプロジェクトに追加
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        project = self.get_project(project_id)
        session = self.get_session(session_id)
        
        if not project:
            logger.error(f"プロジェクト {project_id} が見つかりません")
            return False
        
        if not session:
            logger.error(f"セッション {session_id} が見つかりません")
            return False
        
        # セッションをプロジェクトに追加
        project.add_session(session_id)
        
        # プロジェクトを保存
        return self.save_project(project)
    
    def remove_session_from_project(self, project_id: str, session_id: str) -> bool:
        """
        セッションをプロジェクトから削除
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        project = self.get_project(project_id)
        
        if not project:
            logger.error(f"プロジェクト {project_id} が見つかりません")
            return False
        
        # セッションをプロジェクトから削除
        if project.remove_session(session_id):
            # プロジェクトを保存
            return self.save_project(project)
        
        return False
    
    def add_result_to_session(self, session_id: str, result_id: str) -> bool:
        """
        分析結果をセッションに追加
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_id : str
            分析結果ID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        session = self.get_session(session_id)
        result = self.get_result(result_id)
        
        if not session:
            logger.error(f"セッション {session_id} が見つかりません")
            return False
        
        if not result:
            logger.error(f"分析結果 {result_id} が見つかりません")
            return False
        
        # 分析結果をセッションに追加
        session.add_analysis_result(result_id)
        
        # セッションを保存
        return self.save_session(session)
    
    def get_projects(self, filter_func: Optional[callable] = None) -> List[Project]:
        """
        プロジェクトのリストを取得
        
        Parameters
        ----------
        filter_func : Optional[callable], optional
            フィルタリング関数, by default None
            
        Returns
        -------
        List[Project]
            プロジェクトのリスト
        """
        projects = list(self.projects.values())
        
        if filter_func:
            projects = [p for p in projects if filter_func(p)]
        
        return sorted(projects, key=lambda p: p.name)
    
    def get_sessions(self, filter_func: Optional[callable] = None) -> List[Session]:
        """
        セッションのリストを取得
        
        Parameters
        ----------
        filter_func : Optional[callable], optional
            フィルタリング関数, by default None
            
        Returns
        -------
        List[Session]
            セッションのリスト
        """
        sessions = list(self.sessions.values())
        
        if filter_func:
            sessions = [s for s in sessions if filter_func(s)]
        
        return sorted(sessions, key=lambda s: s.name)
    
    def get_results(self, filter_func: Optional[callable] = None) -> List[AnalysisResult]:
        """
        分析結果のリストを取得
        
        Parameters
        ----------
        filter_func : Optional[callable], optional
            フィルタリング関数, by default None
            
        Returns
        -------
        List[AnalysisResult]
            分析結果のリスト
        """
        results = list(self.results.values())
        
        if filter_func:
            results = [r for r in results if filter_func(r)]
        
        return sorted(results, key=lambda r: r.name)
    
    def get_project_sessions(self, project_id: str) -> List[Session]:
        """
        プロジェクトに関連するセッションのリストを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        List[Session]
            セッションのリスト
        """
        project = self.get_project(project_id)
        
        if not project:
            logger.error(f"プロジェクト {project_id} が見つかりません")
            return []
        
        sessions = []
        for session_id in project.sessions:
            session = self.get_session(session_id)
            if session:
                sessions.append(session)
        
        return sorted(sessions, key=lambda s: s.name)
    
    def get_session_results(self, session_id: str) -> List[AnalysisResult]:
        """
        セッションに関連する分析結果のリストを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[AnalysisResult]
            分析結果のリスト
        """
        session = self.get_session(session_id)
        
        if not session:
            logger.error(f"セッション {session_id} が見つかりません")
            return []
        
        results = []
        for result_id in session.analysis_results:
            result = self.get_result(result_id)
            if result:
                results.append(result)
        
        return sorted(results, key=lambda r: r.name)
    
    
    def search_sessions(self, query: str = "", tags: List[str] = None, 
                       categories: List[str] = None) -> List[Session]:
        """
        セッションを検索
        
        Parameters
        ----------
        query : str, optional
            検索クエリ（セッション名と説明に対して）, by default ""
        tags : List[str], optional
            フィルタリングするタグのリスト, by default None
        categories : List[str], optional
            フィルタリングするカテゴリのリスト, by default None
            
        Returns
        -------
        List[Session]
            検索結果のセッションリスト
        """
        query = query.lower()
        sessions = self.get_sessions()
        results = []
        
        for session in sessions:
            # クエリによる検索
            match_query = (not query) or (
                query in session.name.lower() or
                query in session.description.lower()
            )
            
            # タグによるフィルタリング
            match_tags = (not tags) or all(tag in session.tags for tag in tags)
            
            # カテゴリによるフィルタリング
            match_category = (not categories) or session.category in categories
            
            if match_query and match_tags and match_category:
                results.append(session)
        
        return sorted(results, key=lambda s: s.name)
    
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
        
        for session in self.sessions.values():
            tags.update(session.tags)
        
        return tags
    
    def get_all_categories(self) -> Set[str]:
        """
        すべてのセッションカテゴリを取得
        
        Returns
        -------
        Set[str]
            ユニークなカテゴリのセット
        """
        categories = set()
        
        for session in self.sessions.values():
            if session.category:
                categories.add(session.category)
        
        return categories
    
    def get_root_projects(self) -> List[Project]:
        """
        ルートプロジェクト（親プロジェクトを持たないプロジェクト）を取得
        
        Returns
        -------
        List[Project]
            ルートプロジェクトのリスト
        """
        projects = self.get_projects()
        return [p for p in projects if not p.parent_id]
    
    def get_sub_projects(self, project_id: str) -> List[Project]:
        """
        サブプロジェクトを取得
        
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
            logger.error(f"プロジェクト {project_id} が見つかりません")
            return []
        
        sub_projects = []
        for sub_id in project.sub_projects:
            sub = self.get_project(sub_id)
            if sub:
                sub_projects.append(sub)
        
        return sorted(sub_projects, key=lambda p: p.name)
    
    def get_project_tree(self, project_id: str = None) -> Dict[str, Any]:
        """
        プロジェクトツリーを取得
        
        Parameters
        ----------
        project_id : str, optional
            ルートプロジェクトID, by default None (すべてのルートプロジェクト)
            
        Returns
        -------
        Dict[str, Any]
            プロジェクトツリーの辞書
        """
        if project_id:
            # 特定のプロジェクトをルートとする
            project = self.get_project(project_id)
            if not project:
                logger.error(f"プロジェクト {project_id} が見つかりません")
                return {}
            
            return self._build_project_tree(project)
        else:
            # すべてのルートプロジェクト
            root_projects = self.get_root_projects()
            return {
                "type": "root",
                "name": "すべてのプロジェクト",
                "children": [self._build_project_tree(p) for p in root_projects]
            }
    
    def _build_project_tree(self, project: Project) -> Dict[str, Any]:
        """
        プロジェクトツリーを構築
        
        Parameters
        ----------
        project : Project
            プロジェクト
            
        Returns
        -------
        Dict[str, Any]
            プロジェクトツリーの辞書
        """
        # セッション情報
        sessions = []
        for session_id in project.sessions:
            session = self.get_session(session_id)
            if session:
                sessions.append({
                    "type": "session",
                    "id": session.session_id,
                    "name": session.name,
                    "category": session.category
                })
        
        # サブプロジェクト情報
        sub_projects = []
        for sub_id in project.sub_projects:
            sub = self.get_project(sub_id)
            if sub:
                sub_projects.append(self._build_project_tree(sub))
        
        return {
            "type": "project",
            "id": project.project_id,
            "name": project.name,
            "sessions": sessions,
            "children": sub_projects
        }
    
    def search_projects(self, query: str = None, tags: List[str] = None) -> List[Project]:
        """
        プロジェクトを検索
        
        Parameters
        ----------
        query : str, optional
            検索クエリ, by default None
        tags : List[str], optional
            タグでフィルタリング, by default None
            
        Returns
        -------
        List[Project]
            マッチするプロジェクトのリスト
        """
        # すべてのプロジェクトを取得
        all_projects = list(self.projects.values())
        results = []
        
        # クエリがなく、タグもない場合はすべてのプロジェクトを返す
        if not query and not tags:
            return all_projects
        
        # クエリで検索
        if query:
            query = query.lower()
            for project in all_projects:
                # テストケースの期待動作に合わせた修正: 
                # 名前または説明文に部分一致するものを追加
                if (project.name and query in project.name.lower()) or \
                   (project.description and query in project.description.lower()):
                    results.append(project)
            
            # タグがない場合は結果を返す
            if not tags:
                logger.debug(f"検索クエリ \"{query}\" で {len(results)} 件のプロジェクトを検出")
                return results
        
        # タグで検索
        if tags:
            # クエリがある場合は結果をさらにフィルタリング
            projects_to_filter = results if query else all_projects
            tag_results = []
            
            for project in projects_to_filter:
                if not tags:  # タグが空リストの場合はすべて合致と判断
                    tag_results.append(project)
                    continue
                
                # プロジェクトにタグリストがなければ空リストとして扱う
                project_tags = project.tags if project.tags else []
                    
                # 完全一致: プロジェクトのタグに検索タグのいずれかが含まれる場合
                if any(tag in project_tags for tag in tags):
                    tag_results.append(project)
            
            results = tag_results
            logger.debug(f"タグ {tags} で {len(results)} 件のプロジェクトを検出")
        
        return results
