"""
sailing_data_processor.project.project_manager

プロジェクト管理クラスを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import uuid

from sailing_data_processor.data_model.container import GPSDataContainer


class Project:
    """
    プロジェクトクラス
    
    セーリング分析プロジェクトを表現するクラス。
    メタデータと関連セッションのリストを管理します。
    
    Parameters
    ----------
    name : str
        プロジェクト名
    description : str, optional
        プロジェクトの説明, by default ""
    tags : List[str], optional
        プロジェクトに関連するタグ, by default []
    metadata : Dict[str, Any], optional
        追加のメタデータ, by default None
    project_id : str, optional
        プロジェクトID, by default None (自動生成)
    """
    
    def __init__(self, 
                 name: str, 
                 description: str = "", 
                 tags: List[str] = None,
                 metadata: Dict[str, Any] = None,
                 project_id: str = None):
        """
        プロジェクトの初期化
        
        Parameters
        ----------
        name : str
            プロジェクト名
        description : str, optional
            プロジェクトの説明, by default ""
        tags : List[str], optional
            プロジェクトに関連するタグ, by default []
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        project_id : str, optional
            プロジェクトID, by default None (自動生成)
        """
        self.name = name
        self.description = description
        self.tags = tags or []
        self.metadata = metadata or {}
        self.project_id = project_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.sessions = []
        
        # メタデータ基本情報の設定
        if 'created_by' not in self.metadata:
            self.metadata['created_by'] = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
    
    def add_session(self, session_id: str) -> None:
        """
        セッションをプロジェクトに追加
        
        Parameters
        ----------
        session_id : str
            追加するセッションID
        """
        if session_id not in self.sessions:
            self.sessions.append(session_id)
            self.updated_at = datetime.now().isoformat()
    
    def remove_session(self, session_id: str) -> bool:
        """
        セッションをプロジェクトから削除
        
        Parameters
        ----------
        session_id : str
            削除するセッションID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if session_id in self.sessions:
            self.sessions.remove(session_id)
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        メタデータを更新
        
        Parameters
        ----------
        key : str
            更新するメタデータのキー
        value : Any
            新しい値
        """
        self.metadata[key] = value
        self.updated_at = datetime.now().isoformat()
    
    def add_tag(self, tag: str) -> None:
        """
        タグを追加
        
        Parameters
        ----------
        tag : str
            追加するタグ
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
    
    def remove_tag(self, tag: str) -> bool:
        """
        タグを削除
        
        Parameters
        ----------
        tag : str
            削除するタグ
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        プロジェクトを辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            プロジェクト情報を含む辞書
        """
        return {
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'sessions': self.sessions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        辞書からプロジェクトを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            プロジェクト情報を含む辞書
            
        Returns
        -------
        Project
            作成されたプロジェクトインスタンス
        """
        project = cls(
            name=data['name'],
            description=data.get('description', ''),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            project_id=data.get('project_id')
        )
        
        project.created_at = data.get('created_at', project.created_at)
        project.updated_at = data.get('updated_at', project.updated_at)
        project.sessions = data.get('sessions', [])
        
        return project


class Session:
    """
    セッションクラス
    
    分析セッションを表現するクラス。
    GPSデータと分析状態を管理します。
    
    Parameters
    ----------
    name : str
        セッション名
    description : str, optional
        セッションの説明, by default ""
    tags : List[str], optional
        セッションに関連するタグ, by default []
    metadata : Dict[str, Any], optional
        追加のメタデータ, by default None
    session_id : str, optional
        セッションID, by default None (自動生成)
    """
    
    def __init__(self, 
                 name: str, 
                 description: str = "", 
                 tags: List[str] = None,
                 metadata: Dict[str, Any] = None,
                 session_id: str = None):
        """
        セッションの初期化
        
        Parameters
        ----------
        name : str
            セッション名
        description : str, optional
            セッションの説明, by default ""
        tags : List[str], optional
            セッションに関連するタグ, by default []
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        session_id : str, optional
            セッションID, by default None (自動生成)
        """
        self.name = name
        self.description = description
        self.tags = tags or []
        self.metadata = metadata or {}
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.data_file = None  # データファイルへのパス
        self.state_file = None  # 状態ファイルへのパス
        self.analysis_results = []  # 分析結果のID
        
        # メタデータ基本情報の設定
        if 'created_by' not in self.metadata:
            self.metadata['created_by'] = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
    
    def set_data(self, data_path: str) -> None:
        """
        セッションに関連するデータを設定
        
        Parameters
        ----------
        data_path : str
            データファイルのパス
        """
        self.data_file = data_path
        self.updated_at = datetime.now().isoformat()
    
    def set_state(self, state_path: str) -> None:
        """
        セッションに関連する状態を設定
        
        Parameters
        ----------
        state_path : str
            状態ファイルのパス
        """
        self.state_file = state_path
        self.updated_at = datetime.now().isoformat()
    
    def add_analysis_result(self, result_id: str) -> None:
        """
        分析結果をセッションに追加
        
        Parameters
        ----------
        result_id : str
            追加する分析結果ID
        """
        if result_id not in self.analysis_results:
            self.analysis_results.append(result_id)
            self.updated_at = datetime.now().isoformat()
    
    def remove_analysis_result(self, result_id: str) -> bool:
        """
        分析結果をセッションから削除
        
        Parameters
        ----------
        result_id : str
            削除する分析結果ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if result_id in self.analysis_results:
            self.analysis_results.remove(result_id)
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        メタデータを更新
        
        Parameters
        ----------
        key : str
            更新するメタデータのキー
        value : Any
            新しい値
        """
        self.metadata[key] = value
        self.updated_at = datetime.now().isoformat()
    
    def add_tag(self, tag: str) -> None:
        """
        タグを追加
        
        Parameters
        ----------
        tag : str
            追加するタグ
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
    
    def remove_tag(self, tag: str) -> bool:
        """
        タグを削除
        
        Parameters
        ----------
        tag : str
            削除するタグ
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        セッションを辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            セッション情報を含む辞書
        """
        return {
            'session_id': self.session_id,
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data_file': self.data_file,
            'state_file': self.state_file,
            'analysis_results': self.analysis_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """
        辞書からセッションを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            セッション情報を含む辞書
            
        Returns
        -------
        Session
            作成されたセッションインスタンス
        """
        session = cls(
            name=data['name'],
            description=data.get('description', ''),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            session_id=data.get('session_id')
        )
        
        session.created_at = data.get('created_at', session.created_at)
        session.updated_at = data.get('updated_at', session.updated_at)
        session.data_file = data.get('data_file')
        session.state_file = data.get('state_file')
        session.analysis_results = data.get('analysis_results', [])
        
        return session


class ProjectManager:
    """
    プロジェクト管理クラス
    
    プロジェクトとセッションの管理を行うクラス。
    ファイルシステムを使用してプロジェクトとセッションのデータを永続化します。
    
    Parameters
    ----------
    base_path : str, optional
        プロジェクトデータを保存するベースパス, by default "projects"
    """
    
    def __init__(self, base_path: str = "projects"):
        """
        プロジェクト管理クラスの初期化
        
        Parameters
        ----------
        base_path : str, optional
            プロジェクトデータを保存するベースパス, by default "projects"
        """
        # Streamlit Cloud環境を検出
        self.is_cloud_env = self._detect_cloud_environment()
        
        if self.is_cloud_env:
            # Streamlit Cloudではテンポラリディレクトリを使用
            import tempfile
            temp_dir = tempfile.gettempdir()
            self.base_path = Path(temp_dir) / "sailing_analyzer"
        else:
            # ローカル環境では指定されたパスを使用
            self.base_path = Path(base_path)
        
        self.projects_path = self.base_path / "projects"
        self.sessions_path = self.base_path / "sessions"
        self.data_path = self.base_path / "data"
        self.state_path = self.base_path / "states"
        self.results_path = self.base_path / "results"
        
        # ディレクトリの作成
        self._create_directories()
        
        # プロジェクトとセッションのキャッシュ
        self.projects = {}
        self.sessions = {}
        
        # キャッシュの初期化
        self.reload()
        
    def _detect_cloud_environment(self) -> bool:
        """
        Streamlit Cloud環境を検出する
        
        Returns
        -------
        bool
            Streamlit Cloud環境の場合True
        """
        import os
        
        # Streamlit Cloud環境で設定される環境変数を確認
        cloud_indicators = [
            "STREAMLIT_SHARING_MODE",
            "STREAMLIT_SERVER_PORT",
            "STREAMLIT_SERVER_HEADLESS"
        ]
        
        for indicator in cloud_indicators:
            if os.environ.get(indicator):
                return True
        
        # Streamlit Cloud特有のパスをチェック
        if os.path.exists("/mount/src"):
            return True
            
        return False
    
    def _create_directories(self) -> None:
        """必要なディレクトリを作成"""
        try:
            self.projects_path.mkdir(parents=True, exist_ok=True)
            self.sessions_path.mkdir(parents=True, exist_ok=True)
            self.data_path.mkdir(parents=True, exist_ok=True)
            self.state_path.mkdir(parents=True, exist_ok=True)
            self.results_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            import logging
            logging.error(f"ディレクトリ作成中にエラーが発生しました: {str(e)}")
            if self.is_cloud_env:
                # クラウド環境ではディレクトリ作成のエラーは無視する
                logging.warning("クラウド環境ではディレクトリ作成をスキップします")
    
    def reload(self) -> None:
        """
        プロジェクトとセッションのキャッシュを再読み込み
        """
        self.projects = {}
        self.sessions = {}
        
        import logging
        
        # ディレクトリが存在するか確認
        if not self.projects_path.exists():
            logging.warning(f"プロジェクトディレクトリが存在しません: {self.projects_path}")
            if self.is_cloud_env:
                logging.info("クラウド環境ではこの警告は無視されます")
        else:
            # プロジェクトの読み込み
            project_files = list(self.projects_path.glob("*.json"))
            logging.info(f"プロジェクトファイル数: {len(project_files)}")
            
            for project_file in project_files:
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                        project = Project.from_dict(project_data)
                        self.projects[project.project_id] = project
                        logging.info(f"プロジェクトを読み込みました: {project.name} ({project.project_id})")
                except Exception as e:
                    logging.error(f"プロジェクトファイルの読み込みに失敗しました {project_file}: {e}")
        
        # セッションディレクトリが存在するか確認
        if not self.sessions_path.exists():
            logging.warning(f"セッションディレクトリが存在しません: {self.sessions_path}")
            if self.is_cloud_env:
                logging.info("クラウド環境ではこの警告は無視されます")
        else:
            # セッションの読み込み
            session_files = list(self.sessions_path.glob("*.json"))
            logging.info(f"セッションファイル数: {len(session_files)}")
            
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        session = Session.from_dict(session_data)
                        self.sessions[session.session_id] = session
                        logging.info(f"セッションを読み込みました: {session.name} ({session.session_id})")
                except Exception as e:
                    logging.error(f"セッションファイルの読み込みに失敗しました {session_file}: {e}")
    
    def create_project(self, name: str, description: str = "", 
                       tags: List[str] = None, metadata: Dict[str, Any] = None) -> Project:
        """
        新しいプロジェクトを作成
        
        Parameters
        ----------
        name : str
            プロジェクト名
        description : str, optional
            プロジェクトの説明, by default ""
        tags : List[str], optional
            プロジェクトに関連するタグ, by default []
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        Project
            作成されたプロジェクトインスタンス
        """
        project = Project(name, description, tags, metadata)
        self.projects[project.project_id] = project
        self._save_project(project)
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        プロジェクトを取得
        
        Parameters
        ----------
        project_id : str
            取得するプロジェクトのID
            
        Returns
        -------
        Optional[Project]
            プロジェクトインスタンス (見つからない場合はNone)
        """
        return self.projects.get(project_id)
    
    def update_project(self, project: Project) -> bool:
        """
        プロジェクトを更新
        
        Parameters
        ----------
        project : Project
            更新するプロジェクトインスタンス
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        if project.project_id in self.projects:
            project.updated_at = datetime.now().isoformat()
            self.projects[project.project_id] = project
            self._save_project(project)
            return True
        return False
    
    def delete_project(self, project_id: str, delete_sessions: bool = False) -> bool:
        """
        プロジェクトを削除
        
        Parameters
        ----------
        project_id : str
            削除するプロジェクトのID
        delete_sessions : bool, optional
            関連するセッションも削除するかどうか, by default False
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if project_id in self.projects:
            project = self.projects[project_id]
            
            # 関連するセッションの削除
            if delete_sessions:
                for session_id in project.sessions:
                    self.delete_session(session_id)
            
            # プロジェクトの削除
            project_file = self.projects_path / f"{project_id}.json"
            if project_file.exists():
                project_file.unlink()
            
            del self.projects[project_id]
            return True
        return False
    
    def create_session(self, name: str, description: str = "", 
                       tags: List[str] = None, metadata: Dict[str, Any] = None) -> Session:
        """
        新しいセッションを作成
        
        Parameters
        ----------
        name : str
            セッション名
        description : str, optional
            セッションの説明, by default ""
        tags : List[str], optional
            セッションに関連するタグ, by default []
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        Session
            作成されたセッションインスタンス
        """
        session = Session(name, description, tags, metadata)
        self.sessions[session.session_id] = session
        self._save_session(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        セッションを取得
        
        Parameters
        ----------
        session_id : str
            取得するセッションのID
            
        Returns
        -------
        Optional[Session]
            セッションインスタンス (見つからない場合はNone)
        """
        return self.sessions.get(session_id)
    
    def update_session(self, session: Session) -> bool:
        """
        セッションを更新
        
        Parameters
        ----------
        session : Session
            更新するセッションインスタンス
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        if session.session_id in self.sessions:
            session.updated_at = datetime.now().isoformat()
            self.sessions[session.session_id] = session
            self._save_session(session)
            return True
        return False
    
    def delete_session(self, session_id: str, delete_data: bool = False) -> bool:
        """
        セッションを削除
        
        Parameters
        ----------
        session_id : str
            削除するセッションのID
        delete_data : bool, optional
            関連するデータファイルも削除するかどうか, by default False
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # 関連するデータファイルの削除
            if delete_data:
                if session.data_file and Path(session.data_file).exists():
                    Path(session.data_file).unlink()
                if session.state_file and Path(session.state_file).exists():
                    Path(session.state_file).unlink()
            
            # セッションの削除
            session_file = self.sessions_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # プロジェクトからセッションの参照を削除
            for project in self.projects.values():
                if session_id in project.sessions:
                    project.remove_session(session_id)
                    self._save_project(project)
            
            del self.sessions[session_id]
            return True
        return False
    
    def add_session_to_project(self, project_id: str, session_id: str) -> bool:
        """
        セッションをプロジェクトに追加
        
        Parameters
        ----------
        project_id : str
            追加先のプロジェクトID
        session_id : str
            追加するセッションID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        project = self.get_project(project_id)
        session = self.get_session(session_id)
        
        if project and session:
            project.add_session(session_id)
            self._save_project(project)
            return True
        return False
    
    def remove_session_from_project(self, project_id: str, session_id: str) -> bool:
        """
        セッションをプロジェクトから削除
        
        Parameters
        ----------
        project_id : str
            削除元のプロジェクトID
        session_id : str
            削除するセッションID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        project = self.get_project(project_id)
        
        if project:
            result = project.remove_session(session_id)
            if result:
                self._save_project(project)
            return result
        return False
    
    def save_container_to_session(self, container: GPSDataContainer, session_id: str) -> bool:
        """
        GPSデータコンテナをセッションに保存
        
        Parameters
        ----------
        container : GPSDataContainer
            保存するGPSデータコンテナ
        session_id : str
            保存先のセッションID
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # データファイルを作成
        data_file = self.data_path / f"{session_id}.json"
        
        try:
            # データをJSON形式で保存
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(container.to_dict(), f, ensure_ascii=False, indent=2)
            
            # セッションにデータファイルを設定
            session.set_data(str(data_file))
            self._save_session(session)
            return True
        except Exception as e:
            print(f"Failed to save container to session: {e}")
            return False
    
    def load_container_from_session(self, session_id: str) -> Optional[GPSDataContainer]:
        """
        セッションからGPSデータコンテナを読み込み
        
        Parameters
        ----------
        session_id : str
            読み込み元のセッションID
            
        Returns
        -------
        Optional[GPSDataContainer]
            読み込まれたGPSデータコンテナ (読み込みに失敗した場合はNone)
        """
        session = self.get_session(session_id)
        
        if not session or not session.data_file:
            return None
        
        data_file = Path(session.data_file)
        
        if not data_file.exists():
            return None
        
        try:
            # JSONデータを読み込み
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # データコンテナを再構築
            from sailing_data_processor.data_model.container import DataContainer, GPSDataContainer
            
            if data.get('type') == 'GPSDataContainer':
                # DataFrameの復元
                import pandas as pd
                df = pd.DataFrame(data['data'])
                
                # タイムスタンプの復元
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return GPSDataContainer(df, data['metadata'])
            
            return None
        except Exception as e:
            print(f"Failed to load container from session: {e}")
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
            return False
        
        # 状態ファイルを作成
        state_file = self.state_path / f"{session_id}.json"
        
        try:
            # 状態をJSON形式で保存
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            # セッションに状態ファイルを設定
            session.set_state(str(state_file))
            self._save_session(session)
            return True
        except Exception as e:
            print(f"Failed to save session state: {e}")
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
            読み込まれた状態 (読み込みに失敗した場合はNone)
        """
        session = self.get_session(session_id)
        
        if not session or not session.state_file:
            return None
        
        state_file = Path(session.state_file)
        
        if not state_file.exists():
            return None
        
        try:
            # JSONデータを読み込み
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            return state
        except Exception as e:
            print(f"Failed to load session state: {e}")
            return None
    
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
            return []
        
        return [self.get_session(session_id) for session_id in project.sessions 
                if self.get_session(session_id) is not None]
    
    def search_projects(self, query: str, tags: List[str] = None) -> List[Project]:
        """
        プロジェクトを検索
        
        Parameters
        ----------
        query : str
            検索クエリ（プロジェクト名と説明に対して）
        tags : List[str], optional
            フィルタリングするタグのリスト, by default None
            
        Returns
        -------
        List[Project]
            検索結果のプロジェクトリスト
        """
        query = query.lower()
        results = []
        
        for project in self.projects.values():
            # クエリによる検索
            if (query in project.name.lower() or 
                query in project.description.lower()):
                
                # タグによるフィルタリング
                if tags:
                    if all(tag in project.tags for tag in tags):
                        results.append(project)
                else:
                    results.append(project)
        
        return sorted(results, key=lambda p: p.name)
    
    def search_sessions(self, query: str, tags: List[str] = None) -> List[Session]:
        """
        セッションを検索
        
        Parameters
        ----------
        query : str
            検索クエリ（セッション名と説明に対して）
        tags : List[str], optional
            フィルタリングするタグのリスト, by default None
            
        Returns
        -------
        List[Session]
            検索結果のセッションリスト
        """
        query = query.lower()
        results = []
        
        for session in self.sessions.values():
            # クエリによる検索
            if (query in session.name.lower() or 
                query in session.description.lower()):
                
                # タグによるフィルタリング
                if tags:
                    if all(tag in session.tags for tag in tags):
                        results.append(session)
                else:
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
    
    def get_project_tags(self) -> Set[str]:
        """
        プロジェクトのタグを取得
        
        Returns
        -------
        Set[str]
            プロジェクトのユニークなタグのセット
        """
        tags = set()
        
        for project in self.projects.values():
            tags.update(project.tags)
        
        return tags
    
    def get_session_tags(self) -> Set[str]:
        """
        セッションのタグを取得
        
        Returns
        -------
        Set[str]
            セッションのユニークなタグのセット
        """
        tags = set()
        
        for session in self.sessions.values():
            tags.update(session.tags)
        
        return tags
    
    def _save_project(self, project: Project) -> None:
        """
        プロジェクトをファイルに保存
        
        Parameters
        ----------
        project : Project
            保存するプロジェクト
        """
        project_file = self.projects_path / f"{project.project_id}.json"
        
        try:
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            import logging
            logging.error(f"プロジェクト保存中にエラーが発生しました: {str(e)}")
            # クラウド環境ではファイル書き込みに失敗することがあるため、
            # メモリ内のデータだけを更新する
            if self.is_cloud_env:
                logging.warning("クラウド環境ではファイルへの書き込みをスキップします")
    
    def _save_session(self, session: Session) -> None:
        """
        セッションをファイルに保存
        
        Parameters
        ----------
        session : Session
            保存するセッション
        """
        session_file = self.sessions_path / f"{session.session_id}.json"
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            import logging
            logging.error(f"セッション保存中にエラーが発生しました: {str(e)}")
            # クラウド環境ではファイル書き込みに失敗することがあるため、
            # メモリ内のデータだけを更新する
            if self.is_cloud_env:
                logging.warning("クラウド環境ではファイルへの書き込みをスキップします")
