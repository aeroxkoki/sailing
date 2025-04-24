# -*- coding: utf-8 -*-
"""
sailing_data_processor.session.session_manager

セッション管理クラスを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
import os
import json
from datetime import datetime
import uuid
from pathlib import Path
import copy

from sailing_data_processor.data_model.container import GPSDataContainer


class SessionAnnotation:
    """
    セッション内の注釈を表すクラス
    
    Parameters
    ----------
    title : str
        注釈のタイトル
    content : str
        注釈の内容
    position : Optional[Tuple[float, float]], optional
        注釈の位置（緯度、経度）, by default None
    timestamp : Optional[datetime], optional
        注釈の時刻, by default None
    annotation_type : str, optional
        注釈の種類, by default "text"
    metadata : Dict[str, Any], optional
        追加のメタデータ, by default None
    annotation_id : str, optional
        注釈のID, by default None (自動生成)
    """
    
    def __init__(self, 
                 title: str, 
                 content: str,
                 position: Optional[Tuple[float, float]] = None,
                 timestamp: Optional[datetime] = None,
                 annotation_type: str = "text",
                 metadata: Dict[str, Any] = None,
                 annotation_id: str = None):
        """
        初期化
        
        Parameters
        ----------
        title : str
            注釈のタイトル
        content : str
            注釈の内容
        position : Optional[Tuple[float, float]], optional
            注釈の位置（緯度、経度）, by default None
        timestamp : Optional[datetime], optional
            注釈の時刻, by default None
        annotation_type : str, optional
            注釈の種類, by default "text"
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        annotation_id : str, optional
            注釈のID, by default None (自動生成)
        """
        self.title = title
        self.content = content
        self.position = position
        self.timestamp = timestamp
        self.annotation_type = annotation_type
        self.metadata = metadata or {}
        self.annotation_id = annotation_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def update(self, 
               title: Optional[str] = None,
               content: Optional[str] = None,
               position: Optional[Tuple[float, float]] = None,
               timestamp: Optional[datetime] = None,
               annotation_type: Optional[str] = None,
               metadata_updates: Dict[str, Any] = None) -> None:
        """
        注釈を更新
        
        Parameters
        ----------
        title : Optional[str], optional
            新しいタイトル, by default None (変更なし)
        content : Optional[str], optional
            新しい内容, by default None (変更なし)
        position : Optional[Tuple[float, float]], optional
            新しい位置, by default None (変更なし)
        timestamp : Optional[datetime], optional
            新しい時刻, by default None (変更なし)
        annotation_type : Optional[str], optional
            新しい種類, by default None (変更なし)
        metadata_updates : Dict[str, Any], optional
            更新するメタデータ, by default None
        """
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if position is not None:
            self.position = position
        if timestamp is not None:
            self.timestamp = timestamp
        if annotation_type is not None:
            self.annotation_type = annotation_type
        if metadata_updates:
            self.metadata.update(metadata_updates)
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            注釈情報を含む辞書
        """
        result = {
            "annotation_id": self.annotation_id,
            "title": self.title,
            "content": self.content,
            "annotation_type": self.annotation_type,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if self.position:
            result["position"] = self.position
            
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else self.timestamp
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionAnnotation':
        """
        辞書から注釈を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            注釈情報を含む辞書
            
        Returns
        -------
        SessionAnnotation
            作成された注釈インスタンス
        """
        # タイムスタンプの復元
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                pass
        
        annotation = cls(
            title=data["title"],
            content=data["content"],
            position=data.get("position"),
            timestamp=timestamp,
            annotation_type=data.get("annotation_type", "text"),
            metadata=data.get("metadata", {}),
            annotation_id=data.get("annotation_id")
        )
        
        annotation.created_at = data.get("created_at", annotation.created_at)
        annotation.updated_at = data.get("updated_at", annotation.updated_at)
        
        return annotation


class SessionState:
    """
    セッションの状態を表すクラス
    
    Parameters
    ----------
    name : str
        状態名
    state_data : Dict[str, Any]
        状態データ
    metadata : Dict[str, Any], optional
        追加のメタデータ, by default None
    state_id : str, optional
        状態ID, by default None (自動生成)
    """
    
    def __init__(self, 
                 name: str, 
                 state_data: Dict[str, Any],
                 metadata: Dict[str, Any] = None,
                 state_id: str = None):
        """
        初期化
        
        Parameters
        ----------
        name : str
            状態名
        state_data : Dict[str, Any]
            状態データ
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        state_id : str, optional
            状態ID, by default None (自動生成)
        """
        self.name = name
        self.state_data = state_data
        self.metadata = metadata or {}
        self.state_id = state_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def update_state(self, state_data: Dict[str, Any], name: Optional[str] = None) -> None:
        """
        状態を更新
        
        Parameters
        ----------
        state_data : Dict[str, Any]
            新しい状態データ
        name : Optional[str], optional
            新しい状態名, by default None (変更なし)
        """
        self.state_data = state_data
        if name:
            self.name = name
        self.updated_at = datetime.now().isoformat()
    
    def update_metadata(self, metadata_updates: Dict[str, Any]) -> None:
        """
        メタデータを更新
        
        Parameters
        ----------
        metadata_updates : Dict[str, Any]
            更新するメタデータ
        """
        self.metadata.update(metadata_updates)
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            状態情報を含む辞書
        """
        return {
            "state_id": self.state_id,
            "name": self.name,
            "state_data": self.state_data,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """
        辞書から状態を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            状態情報を含む辞書
            
        Returns
        -------
        SessionState
            作成された状態インスタンス
        """
        state = cls(
            name=data["name"],
            state_data=data["state_data"],
            metadata=data.get("metadata", {}),
            state_id=data.get("state_id")
        )
        
        state.created_at = data.get("created_at", state.created_at)
        state.updated_at = data.get("updated_at", state.updated_at)
        
        return state


class SessionManager:
    """
    セッション管理クラス
    
    セッションの状態と注釈を管理するクラス。
    また、プロジェクトとセッションの関連付けも管理します。
    
    Parameters
    ----------
    project_manager : Optional[Any], optional
        プロジェクト管理クラスのインスタンス, by default None
    base_path : str, optional
        セッションデータを保存するベースパス, by default "session_data"
    """
    
    def __init__(self, project_manager=None, base_path: str = "session_data"):
        """
        初期化
        
        Parameters
        ----------
        project_manager : Optional[Any], optional
            プロジェクト管理クラスのインスタンス, by default None
        base_path : str, optional
            セッションデータを保存するベースパス, by default "session_data"
        """
        self.project_manager = project_manager
        self.base_path = Path(base_path)
        self.states_path = self.base_path / "states"
        self.annotations_path = self.base_path / "annotations"
        self.metadata_path = self.base_path / "metadata"
        
        # ディレクトリの作成
        self._create_directories()
        
        # セッション状態とアノテーションのキャッシュ
        self.states = {}  # session_id -> Dict[state_id -> SessionState]
        self.annotations = {}  # session_id -> Dict[annotation_id -> SessionAnnotation]
        self.session_tags = {}  # タグごとのセッションID集合
        self.session_metadata = {}  # session_id -> 追加のメタデータ
        
        # キャッシュの初期化
        self.reload()
    
    def _create_directories(self) -> None:
        """必要なディレクトリを作成"""
        self.states_path.mkdir(parents=True, exist_ok=True)
        self.annotations_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
    
    def reload(self) -> None:
        """
        セッション状態、注釈、メタデータのキャッシュを再読み込み
        """
        self.states = {}
        self.annotations = {}
        self.session_metadata = {}
        self.session_tags = {}
        
        # 状態ファイルの読み込み
        for session_dir in self.states_path.glob("*"):
            if session_dir.is_dir():
                session_id = session_dir.name
                self.states[session_id] = {}
                
                for state_file in session_dir.glob("*.json"):
                    try:
                        with open(state_file, 'r', encoding='utf-8') as f:
                            state_data = json.load(f)
                            state = SessionState.from_dict(state_data)
                            self.states[session_id][state.state_id] = state
                    except Exception as e:
                        print(f"Failed to load state file {state_file}: {e}")
        
        # 注釈ファイルの読み込み
        for session_dir in self.annotations_path.glob("*"):
            if session_dir.is_dir():
                session_id = session_dir.name
                self.annotations[session_id] = {}
                
                for annotation_file in session_dir.glob("*.json"):
                    try:
                        with open(annotation_file, 'r', encoding='utf-8') as f:
                            annotation_data = json.load(f)
                            annotation = SessionAnnotation.from_dict(annotation_data)
                            self.annotations[session_id][annotation.annotation_id] = annotation
                    except Exception as e:
                        print(f"Failed to load annotation file {annotation_file}: {e}")
        
        # メタデータの読み込み
        for metadata_file in self.metadata_path.glob("*.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    session_id = metadata.get("session_id")
                    if session_id:
                        self.session_metadata[session_id] = metadata
                        
                        # タグの処理
                        tags = metadata.get("tags", [])
                        for tag in tags:
                            if tag not in self.session_tags:
                                self.session_tags[tag] = set()
                            self.session_tags[tag].add(session_id)
            except Exception as e:
                print(f"Failed to load metadata file {metadata_file}: {e}")
    
    def create_session_state(self, session_id: str, name: str, 
                             state_data: Dict[str, Any],
                             metadata: Dict[str, Any] = None) -> SessionState:
        """
        セッション状態を作成
        
        Parameters
        ----------
        session_id : str
            セッションID
        name : str
            状態名
        state_data : Dict[str, Any]
            状態データ
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        SessionState
            作成された状態インスタンス
        """
        # プロジェクトマネージャーがある場合、セッションの存在を確認
        if self.project_manager and not self.project_manager.get_session(session_id):
            raise ValueError(f"Session with ID {session_id} does not exist")
        
        # セッション用のディレクトリを作成
        session_dir = self.states_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 状態を作成
        state = SessionState(name, state_data, metadata)
        
        # キャッシュに追加
        if session_id not in self.states:
            self.states[session_id] = {}
        self.states[session_id][state.state_id] = state
        
        # 保存
        self._save_state(session_id, state)
        
        return state
    
    def update_session_state(self, session_id: str, state_id: str, 
                             state_data: Dict[str, Any],
                             name: Optional[str] = None) -> Optional[SessionState]:
        """
        セッション状態を更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        state_id : str
            状態ID
        state_data : Dict[str, Any]
            新しい状態データ
        name : Optional[str], optional
            新しい状態名, by default None (変更なし)
            
        Returns
        -------
        Optional[SessionState]
            更新された状態インスタンス (失敗した場合はNone)
        """
        if session_id not in self.states or state_id not in self.states[session_id]:
            return None
        
        state = self.states[session_id][state_id]
        state.update_state(state_data, name)
        
        # 保存
        self._save_state(session_id, state)
        
        return state
    
    def get_session_state(self, session_id: str, state_id: str) -> Optional[SessionState]:
        """
        セッション状態を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        state_id : str
            状態ID
            
        Returns
        -------
        Optional[SessionState]
            状態インスタンス (存在しない場合はNone)
        """
        if session_id not in self.states or state_id not in self.states[session_id]:
            return None
        
        return self.states[session_id][state_id]
    
    def get_session_states(self, session_id: str) -> List[SessionState]:
        """
        セッションのすべての状態を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[SessionState]
            状態インスタンスのリスト
        """
        if session_id not in self.states:
            return []
        
        return list(self.states[session_id].values())
    
    def delete_session_state(self, session_id: str, state_id: str) -> bool:
        """
        セッション状態を削除
        
        Parameters
        ----------
        session_id : str
            セッションID
        state_id : str
            状態ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if session_id not in self.states or state_id not in self.states[session_id]:
            return False
        
        # 状態ファイルを削除
        state_file = self.states_path / session_id / f"{state_id}.json"
        if state_file.exists():
            state_file.unlink()
        
        # キャッシュから削除
        del self.states[session_id][state_id]
        
        return True
    
    def create_annotation(self, session_id: str, title: str, content: str,
                          position: Optional[Tuple[float, float]] = None,
                          timestamp: Optional[datetime] = None,
                          annotation_type: str = "text",
                          metadata: Dict[str, Any] = None) -> SessionAnnotation:
        """
        セッションに注釈を作成
        
        Parameters
        ----------
        session_id : str
            セッションID
        title : str
            注釈のタイトル
        content : str
            注釈の内容
        position : Optional[Tuple[float, float]], optional
            注釈の位置（緯度、経度）, by default None
        timestamp : Optional[datetime], optional
            注釈の時刻, by default None
        annotation_type : str, optional
            注釈の種類, by default "text"
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        SessionAnnotation
            作成された注釈インスタンス
        """
        # プロジェクトマネージャーがある場合、セッションの存在を確認
        if self.project_manager and not self.project_manager.get_session(session_id):
            raise ValueError(f"Session with ID {session_id} does not exist")
        
        # セッション用のディレクトリを作成
        session_dir = self.annotations_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 注釈を作成
        annotation = SessionAnnotation(
            title, content, position, timestamp, annotation_type, metadata
        )
        
        # キャッシュに追加
        if session_id not in self.annotations:
            self.annotations[session_id] = {}
        self.annotations[session_id][annotation.annotation_id] = annotation
        
        # 保存
        self._save_annotation(session_id, annotation)
        
        return annotation
    
    def update_annotation(self, session_id: str, annotation_id: str,
                          title: Optional[str] = None,
                          content: Optional[str] = None,
                          position: Optional[Tuple[float, float]] = None,
                          timestamp: Optional[datetime] = None,
                          annotation_type: Optional[str] = None,
                          metadata_updates: Dict[str, Any] = None) -> Optional[SessionAnnotation]:
        """
        注釈を更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        annotation_id : str
            注釈ID
        title : Optional[str], optional
            新しいタイトル, by default None (変更なし)
        content : Optional[str], optional
            新しい内容, by default None (変更なし)
        position : Optional[Tuple[float, float]], optional
            新しい位置, by default None (変更なし)
        timestamp : Optional[datetime], optional
            新しい時刻, by default None (変更なし)
        annotation_type : Optional[str], optional
            新しい種類, by default None (変更なし)
        metadata_updates : Dict[str, Any], optional
            更新するメタデータ, by default None
            
        Returns
        -------
        Optional[SessionAnnotation]
            更新された注釈インスタンス (失敗した場合はNone)
        """
        if session_id not in self.annotations or annotation_id not in self.annotations[session_id]:
            return None
        
        annotation = self.annotations[session_id][annotation_id]
        annotation.update(title, content, position, timestamp, annotation_type, metadata_updates)
        
        # 保存
        self._save_annotation(session_id, annotation)
        
        return annotation
    
    def get_annotation(self, session_id: str, annotation_id: str) -> Optional[SessionAnnotation]:
        """
        注釈を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        annotation_id : str
            注釈ID
            
        Returns
        -------
        Optional[SessionAnnotation]
            注釈インスタンス (存在しない場合はNone)
        """
        if session_id not in self.annotations or annotation_id not in self.annotations[session_id]:
            return None
        
        return self.annotations[session_id][annotation_id]
    
    def get_session_annotations(self, session_id: str) -> List[SessionAnnotation]:
        """
        セッションのすべての注釈を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[SessionAnnotation]
            注釈インスタンスのリスト
        """
        if session_id not in self.annotations:
            return []
        
        return list(self.annotations[session_id].values())
    
    def delete_annotation(self, session_id: str, annotation_id: str) -> bool:
        """
        注釈を削除
        
        Parameters
        ----------
        session_id : str
            セッションID
        annotation_id : str
            注釈ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if session_id not in self.annotations or annotation_id not in self.annotations[session_id]:
            return False
        
        # 注釈ファイルを削除
        annotation_file = self.annotations_path / session_id / f"{annotation_id}.json"
        if annotation_file.exists():
            annotation_file.unlink()
        
        # キャッシュから削除
        del self.annotations[session_id][annotation_id]
        
        return True
    
    def duplicate_state(self, session_id: str, state_id: str, new_name: Optional[str] = None) -> Optional[SessionState]:
        """
        セッション状態を複製
        
        Parameters
        ----------
        session_id : str
            セッションID
        state_id : str
            複製元の状態ID
        new_name : Optional[str], optional
            新しい状態名, by default None (元の名前に "Copy of" を追加)
            
        Returns
        -------
        Optional[SessionState]
            複製された状態インスタンス (失敗した場合はNone)
        """
        original_state = self.get_session_state(session_id, state_id)
        if not original_state:
            return None
        
        # 新しい名前を設定
        if new_name is None:
            new_name = f"Copy of {original_state.name}"
        
        # 状態データのディープコピー
        state_data = copy.deepcopy(original_state.state_data)
        metadata = copy.deepcopy(original_state.metadata)
        
        # 複製を作成
        return self.create_session_state(session_id, new_name, state_data, metadata)
    
    def search_states_by_name(self, query: str) -> Dict[str, List[SessionState]]:
        """
        名前で状態を検索
        
        Parameters
        ----------
        query : str
            検索クエリ
            
        Returns
        -------
        Dict[str, List[SessionState]]
            セッションIDごとの検索結果のリスト
        """
        query = query.lower()
        results = {}
        
        for session_id, states in self.states.items():
            matching_states = [
                state for state in states.values()
                if query in state.name.lower()
            ]
            
            if matching_states:
                results[session_id] = matching_states
        
        return results
    
    def search_annotations_by_content(self, query: str) -> Dict[str, List[SessionAnnotation]]:
        """
        内容で注釈を検索
        
        Parameters
        ----------
        query : str
            検索クエリ
            
        Returns
        -------
        Dict[str, List[SessionAnnotation]]
            セッションIDごとの検索結果のリスト
        """
        query = query.lower()
        results = {}
        
        for session_id, annotations in self.annotations.items():
            matching_annotations = [
                annotation for annotation in annotations.values()
                if query in annotation.title.lower() or query in annotation.content.lower()
            ]
            
            if matching_annotations:
                results[session_id] = matching_annotations
        
        return results
    
    def _save_state(self, session_id: str, state: SessionState) -> None:
        """
        状態をファイルに保存
        
        Parameters
        ----------
        session_id : str
            セッションID
        state : SessionState
            保存する状態
        """
        state_dir = self.states_path / session_id
        state_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = state_dir / f"{state.state_id}.json"
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _save_annotation(self, session_id: str, annotation: SessionAnnotation) -> None:
        """
        注釈をファイルに保存
        
        Parameters
        ----------
        session_id : str
            セッションID
        annotation : SessionAnnotation
            保存する注釈
        """
        annotation_dir = self.annotations_path / session_id
        annotation_dir.mkdir(parents=True, exist_ok=True)
        
        annotation_file = annotation_dir / f"{annotation.annotation_id}.json"
        
        with open(annotation_file, 'w', encoding='utf-8') as f:
            json.dump(annotation.to_dict(), f, ensure_ascii=False, indent=2)
    
    def export_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        セッションデータをエクスポート
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        Dict[str, Any]
            エクスポートされたセッションデータ
        """
        # セッション状態をエクスポート
        states = {}
        if session_id in self.states:
            for state_id, state in self.states[session_id].items():
                states[state_id] = state.to_dict()
        
        # 注釈をエクスポート
        annotations = {}
        if session_id in self.annotations:
            for annotation_id, annotation in self.annotations[session_id].items():
                annotations[annotation_id] = annotation.to_dict()
        
        # セッション情報を取得
        session_info = {}
        if self.project_manager:
            session = self.project_manager.get_session(session_id)
            if session:
                session_info = session.to_dict()
        
        return {
            "session_id": session_id,
            "session_info": session_info,
            "states": states,
            "annotations": annotations,
            "exported_at": datetime.now().isoformat()
        }
    
    def import_session_data(self, data: Dict[str, Any]) -> bool:
        """
        セッションデータをインポート
        
        Parameters
        ----------
        data : Dict[str, Any]
            インポートするセッションデータ
            
        Returns
        -------
        bool
            インポートに成功した場合True
        """
        try:
            session_id = data["session_id"]
            
            # セッションの存在を確認
            if self.project_manager and not self.project_manager.get_session(session_id):
                # セッションが存在しない場合は、新しく作成
                session_info = data.get("session_info", {})
                if session_info:
                    self.project_manager.create_session(
                        name=session_info.get("name", "Imported Session"),
                        description=session_info.get("description", ""),
                        tags=session_info.get("tags", []),
                        metadata=session_info.get("metadata", {}),
                        session_id=session_id
                    )
            
            # 状態をインポート
            states = data.get("states", {})
            for state_id, state_data in states.items():
                state = SessionState.from_dict(state_data)
                
                # キャッシュに追加
                if session_id not in self.states:
                    self.states[session_id] = {}
                self.states[session_id][state_id] = state
                
                # 保存
                self._save_state(session_id, state)
            
            # 注釈をインポート
            annotations = data.get("annotations", {})
            for annotation_id, annotation_data in annotations.items():
                annotation = SessionAnnotation.from_dict(annotation_data)
                
                # キャッシュに追加
                if session_id not in self.annotations:
                    self.annotations[session_id] = {}
                self.annotations[session_id][annotation_id] = annotation
                
                # 保存
                self._save_annotation(session_id, annotation)
            
            return True
        
        except Exception as e:
            print(f"Failed to import session data: {e}")
            return False
    
    #----------------------------------------------------------------------
    # セッション管理関連の追加メソッド
    #----------------------------------------------------------------------
    
    def get_all_sessions(self) -> List[Any]:
        """
        システム内のすべてのセッションを取得
        
        Returns
        -------
        List[Any]
            すべてのセッションのリスト
        """
        if not self.project_manager:
            return []
        
        return self.project_manager.get_all_sessions()
    
    def get_project_sessions(self, project_id: str) -> List[Any]:
        """
        特定プロジェクトのセッションを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        List[Any]
            プロジェクト内のセッションのリスト
        """
        if not self.project_manager:
            return []
        
        return self.project_manager.get_project_sessions(project_id)
    
    def add_session_to_project(self, session_id: str, project_id: str) -> bool:
        """
        セッションをプロジェクトに追加
        
        Parameters
        ----------
        session_id : str
            セッションID
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        if not self.project_manager:
            return False
        
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        project.add_session(session_id)
        self.project_manager.save_project(project)
        return True
    
    def remove_session_from_project(self, session_id: str, project_id: str) -> bool:
        """
        セッションをプロジェクトから削除
        
        Parameters
        ----------
        session_id : str
            セッションID
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if not self.project_manager:
            return False
        
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        if session_id not in project.sessions:
            return False
        
        project.remove_session(session_id)
        self.project_manager.save_project(project)
        return True
    
    def move_session(self, session_id: str, source_project_id: str, target_project_id: str) -> bool:
        """
        セッションをプロジェクト間で移動
        
        Parameters
        ----------
        session_id : str
            セッションID
        source_project_id : str
            移動元プロジェクトID
        target_project_id : str
            移動先プロジェクトID
            
        Returns
        -------
        bool
            移動に成功した場合True
        """
        if not self.project_manager:
            return False
        
        # 移動元と移動先のプロジェクトを取得
        source_project = self.project_manager.get_project(source_project_id)
        target_project = self.project_manager.get_project(target_project_id)
        
        if not source_project or not target_project:
            return False
        
        # セッションの存在確認
        if session_id not in source_project.sessions:
            return False
        
        # セッションを移動
        if self.remove_session_from_project(session_id, source_project_id):
            if self.add_session_to_project(session_id, target_project_id):
                return True
            else:
                # 移動先への追加に失敗した場合、元に戻す
                self.add_session_to_project(session_id, source_project_id)
        
        return False
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        セッションメタデータを更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        metadata : Dict[str, Any]
            更新するメタデータ
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        if not self.project_manager:
            return False
        
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        # 既存のメタデータを更新
        for key, value in metadata.items():
            session.update_metadata(key, value)
        
        # セッションを保存
        self.project_manager.save_session(session)
        
        # メタデータキャッシュも更新
        if session_id in self.session_metadata:
            self.session_metadata[session_id].update(metadata)
        else:
            self.session_metadata[session_id] = metadata.copy()
        
        # タグが含まれる場合は処理
        if "tags" in metadata:
            self._update_session_tags(session_id, metadata["tags"])
        
        # メタデータファイルに保存
        self._save_session_metadata(session_id)
        
        return True
    
    def search_sessions(self, query: str = "", tags: List[str] = None, 
                        start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None,
                        location: Optional[str] = None) -> List[str]:
        """
        セッションを検索
        
        Parameters
        ----------
        query : str, optional
            検索キーワード, by default ""
        tags : List[str], optional
            タグによるフィルタリング, by default None
        start_date : Optional[datetime], optional
            開始日による範囲指定, by default None
        end_date : Optional[datetime], optional
            終了日による範囲指定, by default None
        location : Optional[str], optional
            位置情報による検索, by default None
            
        Returns
        -------
        List[str]
            条件に一致するセッションIDのリスト
        """
        if not self.project_manager:
            return []
        
        all_sessions = self.project_manager.get_all_sessions()
        matching_sessions = []
        
        for session in all_sessions:
            # クエリによる検索
            if query and query.lower() not in session.name.lower() and query.lower() not in session.description.lower():
                continue
            
            # タグによるフィルタリング
            if tags:
                if not all(tag in session.tags for tag in tags):
                    continue
            
            # 日付範囲によるフィルタリング
            if start_date or end_date:
                event_date = session.metadata.get("event_date", "")
                if event_date:
                    try:
                        session_date = datetime.fromisoformat(event_date)
                        if start_date and session_date < start_date:
                            continue
                        if end_date and session_date > end_date:
                            continue
                    except (ValueError, TypeError):
                        # 日付の形式が無効な場合はスキップ
                        continue
                else:
                    # イベント日がない場合は、作成日を使用
                    try:
                        created_at = datetime.fromisoformat(session.created_at)
                        if start_date and created_at < start_date:
                            continue
                        if end_date and created_at > end_date:
                            continue
                    except (ValueError, TypeError):
                        continue
            
            # 位置情報によるフィルタリング
            if location:
                session_location = session.metadata.get("location", "")
                if location.lower() not in session_location.lower():
                    continue
            
            matching_sessions.append(session.session_id)
        
        return matching_sessions
    
    def get_sessions_by_tag(self, tag: str) -> List[str]:
        """
        タグでセッションを検索
        
        Parameters
        ----------
        tag : str
            検索するタグ
            
        Returns
        -------
        List[str]
            タグに一致するセッションIDのリスト
        """
        if tag in self.session_tags:
            return list(self.session_tags[tag])
        return []
    
    def get_available_tags(self) -> List[str]:
        """
        利用可能なすべてのタグを取得
        
        Returns
        -------
        List[str]
            システム内のすべてのタグのリスト
        """
        return list(self.session_tags.keys())
    
    def get_sessions_not_in_project(self, project_id: str) -> List[Any]:
        """
        指定したプロジェクトに含まれていないセッションを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        List[Any]
            プロジェクトに含まれていないセッションのリスト
        """
        if not self.project_manager:
            return []
        
        project = self.project_manager.get_project(project_id)
        if not project:
            return []
        
        all_sessions = self.project_manager.get_all_sessions()
        return [session for session in all_sessions if session.session_id not in project.sessions]
    
    def copy_session_to_project(self, session_id: str, project_id: str) -> bool:
        """
        プロジェクトにセッションをコピー（複数のプロジェクトに同じセッションを所属させる）
        
        Parameters
        ----------
        session_id : str
            セッションID
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            コピーに成功した場合True
        """
        return self.add_session_to_project(session_id, project_id)
    
    def _update_session_tags(self, session_id: str, tags: List[str]) -> None:
        """
        セッションタグの内部キャッシュを更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        tags : List[str]
            新しいタグのリスト
        """
        # 古いタグからセッションを削除
        for tag, sessions in self.session_tags.items():
            if session_id in sessions:
                sessions.remove(session_id)
        
        # 新しいタグにセッションを追加
        for tag in tags:
            if tag not in self.session_tags:
                self.session_tags[tag] = set()
            self.session_tags[tag].add(session_id)
    
    def _save_session_metadata(self, session_id: str) -> None:
        """
        セッションメタデータをファイルに保存
        
        Parameters
        ----------
        session_id : str
            セッションID
        """
        if session_id not in self.session_metadata:
            return
        
        metadata_file = self.metadata_path / f"{session_id}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_metadata[session_id], f, ensure_ascii=False, indent=2)
