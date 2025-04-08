"""
sailing_data_processor.project.session_model

セッションの拡張モデルを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
import os
import json
from datetime import datetime
import uuid
from pathlib import Path
import copy


class SessionModel:
    """
    拡張されたセッションモデル
    
    Parameters
    ----------
    name : str
        セッション名
    project_id : str
        所属プロジェクトID
    description : str, optional
        セッションの説明, by default ""
    purpose : str, optional
        セッションの目的, by default ""
    category : str, optional
        カテゴリ("analysis", "training", "race", "simulation", "other"), by default "analysis"
    tags : List[str], optional
        カスタムタグのリスト, by default None
    status : str, optional
        ステータス("active", "in_progress", "completed", "archived"), by default "active"
    rating : int, optional
        評価（0-5）, by default 0
    related_sessions : Dict[str, List[str]], optional
        関連セッションの辞書 {"parent": [...], "child": [...], "previous": [...], "next": [...], "related": [...]}, by default None
    metadata : Dict[str, Any], optional
        追加のメタデータ, by default None
    session_id : str, optional
        セッションID, by default None (自動生成)
    event_date : Optional[datetime], optional
        セッションの日時, by default None
    location : str, optional
        位置情報, by default ""
    importance : str, optional
        重要度 ("low", "normal", "high", "critical"), by default "normal"
    completion_percentage : int, optional
        完了の割合（0-100）, by default 0
    """
    
    def __init__(self, 
                 name: str, 
                 project_id: str,
                 description: str = "",
                 purpose: str = "",
                 category: str = "analysis",
                 tags: List[str] = None,
                 status: str = "active",
                 rating: int = 0,
                 related_sessions: Dict[str, List[str]] = None,
                 metadata: Dict[str, Any] = None,
                 session_id: str = None,
                 event_date: Optional[datetime] = None,
                 location: str = "",
                 importance: str = "normal",
                 completion_percentage: int = 0):
        """
        拡張されたイニシャライザ
        
        Parameters
        ----------
        name : str
            セッション名
        project_id : str
            所属プロジェクトID
        description : str, optional
            セッションの説明, by default ""
        purpose : str, optional
            セッションの目的, by default ""
        category : str, optional
            カテゴリ("analysis", "training", "race", "simulation", "other"), by default "analysis"
        tags : List[str], optional
            カスタムタグのリスト, by default None
        status : str, optional
            ステータス("active", "in_progress", "completed", "archived"), by default "active"
        rating : int, optional
            評価（0-5）, by default 0
        related_sessions : Dict[str, List[str]], optional
            関連セッションの辞書 {"parent": [...], "child": [...], "previous": [...], "next": [...], "related": [...]}, by default None
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        session_id : str, optional
            セッションID, by default None (自動生成)
        event_date : Optional[datetime], optional
            セッションの日時, by default None
        location : str, optional
            位置情報, by default ""
        importance : str, optional
            重要度 ("low", "normal", "high", "critical"), by default "normal"
        completion_percentage : int, optional
            完了の割合（0-100）, by default 0
        """
        self.name = name
        self.project_id = project_id
        self.description = description
        self.purpose = purpose
        self.category = category
        self.tags = tags or []
        self.status = status
        self.rating = rating
        self.related_sessions = related_sessions or {"parent": [], "child": [], "previous": [], "next": [], "related": []}
        self.metadata = metadata or {}
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.results = []  # 分析結果のIDリスト
        self.importance = importance
        self.completion_percentage = min(max(completion_percentage, 0), 100)  # 0〜100の範囲に制限
        
        # セッションの日時とロケーションを設定
        self.event_date = event_date.isoformat() if event_date else None
        self.location = location
        
        # メタデータ基本情報の設定
        if 'created_by' not in self.metadata:
            self.metadata['created_by'] = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        
        # メタデータとの互換性維持
        if self.event_date and 'event_date' not in self.metadata:
            self.metadata['event_date'] = self.event_date
        
        if self.location and 'location' not in self.metadata:
            self.metadata['location'] = self.location
            
        if self.purpose and 'purpose' not in self.metadata:
            self.metadata['purpose'] = self.purpose
            
        if 'importance' not in self.metadata:
            self.metadata['importance'] = self.importance
            
        if 'completion_percentage' not in self.metadata:
            self.metadata['completion_percentage'] = self.completion_percentage
    
    def add_tag(self, tag: str) -> None:
        """タグを追加"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
        
    def remove_tag(self, tag: str) -> None:
        """タグを削除"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now().isoformat()
        
    def add_related_session(self, session_id: str, relation_type: str = "related") -> None:
        """
        関連セッションを追加
        
        Parameters
        ----------
        session_id : str
            関連付けるセッションID
        relation_type : str, optional
            関連タイプ ("parent", "child", "related"), by default "related"
        """
        if relation_type not in self.related_sessions:
            self.related_sessions[relation_type] = []
            
        if session_id not in self.related_sessions[relation_type]:
            self.related_sessions[relation_type].append(session_id)
            self.updated_at = datetime.now().isoformat()
        
    def remove_related_session(self, session_id: str, relation_type: str = "related") -> None:
        """
        関連セッションを削除
        
        Parameters
        ----------
        session_id : str
            削除するセッションID
        relation_type : str, optional
            関連タイプ ("parent", "child", "related"), by default "related"
        """
        if relation_type in self.related_sessions and session_id in self.related_sessions[relation_type]:
            self.related_sessions[relation_type].remove(session_id)
            self.updated_at = datetime.now().isoformat()
    
    def add_result(self, result_id: str) -> None:
        """
        分析結果を追加
        
        Parameters
        ----------
        result_id : str
            追加する結果ID
        """
        if result_id not in self.results:
            self.results.append(result_id)
            self.updated_at = datetime.now().isoformat()
    
    def remove_result(self, result_id: str) -> bool:
        """
        分析結果を削除
        
        Parameters
        ----------
        result_id : str
            削除する結果ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if result_id in self.results:
            self.results.remove(result_id)
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def update_rating(self, rating: int) -> None:
        """
        セッション評価を更新
        
        Parameters
        ----------
        rating : int
            新しい評価値 (0-5)
        """
        if 0 <= rating <= 5:
            self.rating = rating
            self.updated_at = datetime.now().isoformat()
    
    def update_status(self, status: str) -> None:
        """
        セッションステータスを更新
        
        Parameters
        ----------
        status : str
            新しいステータス
        """
        self.status = status
        self.updated_at = datetime.now().isoformat()
    
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
    
    def update_event_date(self, event_date: datetime) -> None:
        """
        セッションの日時を更新
        
        Parameters
        ----------
        event_date : datetime
            新しい日時
        """
        self.event_date = event_date.isoformat() if event_date else None
        
        # メタデータも一貫性を保つために更新
        if self.event_date:
            self.metadata['event_date'] = self.event_date
        elif 'event_date' in self.metadata:
            del self.metadata['event_date']
            
        self.updated_at = datetime.now().isoformat()
    
    def update_location(self, location: str) -> None:
        """
        位置情報を更新
        
        Parameters
        ----------
        location : str
            新しい位置情報
        """
        self.location = location
        
        # メタデータも一貫性を保つために更新
        if self.location:
            self.metadata['location'] = self.location
        elif 'location' in self.metadata:
            del self.metadata['location']
            
        self.updated_at = datetime.now().isoformat()
    
    def update_purpose(self, purpose: str) -> None:
        """
        セッションの目的を更新
        
        Parameters
        ----------
        purpose : str
            新しい目的
        """
        self.purpose = purpose
        
        # メタデータも一貫性を保つために更新
        if self.purpose:
            self.metadata['purpose'] = self.purpose
        elif 'purpose' in self.metadata:
            del self.metadata['purpose']
            
        self.updated_at = datetime.now().isoformat()
    
    def update_importance(self, importance: str) -> None:
        """
        セッションの重要度を更新
        
        Parameters
        ----------
        importance : str
            新しい重要度 ("low", "normal", "high", "critical")
        """
        if importance in ["low", "normal", "high", "critical"]:
            self.importance = importance
            self.metadata['importance'] = importance
            self.updated_at = datetime.now().isoformat()
    
    def update_completion_percentage(self, percentage: int) -> None:
        """
        完了の割合を更新
        
        Parameters
        ----------
        percentage : int
            新しい完了の割合（0-100）
        """
        self.completion_percentage = min(max(percentage, 0), 100)
        self.metadata['completion_percentage'] = self.completion_percentage
        self.updated_at = datetime.now().isoformat()
    
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
            'project_id': self.project_id,
            'description': self.description,
            'purpose': self.purpose,
            'category': self.category,
            'tags': self.tags,
            'status': self.status,
            'rating': self.rating,
            'related_sessions': self.related_sessions,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'results': self.results,
            'event_date': self.event_date,
            'location': self.location,
            'importance': self.importance,
            'completion_percentage': self.completion_percentage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionModel':
        """
        辞書からセッションを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            セッション情報を含む辞書
            
        Returns
        -------
        SessionModel
            作成されたセッションインスタンス
        """
        # 互換性のためにevent_dateとlocationをメタデータから取得
        metadata = data.get('metadata', {})
        event_date_str = data.get('event_date') or metadata.get('event_date')
        location = data.get('location') or metadata.get('location', '')
        
        # event_dateが文字列の場合はdatetimeに変換
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.fromisoformat(event_date_str)
            except (ValueError, TypeError):
                # 変換エラーの場合はNoneのままにする
                pass
        
        # 新しいパラメータの取得
        purpose = data.get('purpose', '') or metadata.get('purpose', '')
        importance = data.get('importance', 'normal') or metadata.get('importance', 'normal')
        completion_percentage = data.get('completion_percentage', 0) or metadata.get('completion_percentage', 0)
        
        # related_sessionsのデフォルト値は拡張された辞書
        default_related = {"parent": [], "child": [], "previous": [], "next": [], "related": []}
        
        session = cls(
            name=data['name'],
            project_id=data.get('project_id', ''),
            description=data.get('description', ''),
            purpose=purpose,
            category=data.get('category', 'analysis'),
            tags=data.get('tags', []),
            status=data.get('status', 'active'),
            rating=data.get('rating', 0),
            related_sessions=data.get('related_sessions', default_related),
            metadata=metadata,
            session_id=data.get('session_id'),
            event_date=event_date,
            location=location,
            importance=importance,
            completion_percentage=completion_percentage
        )
        
        session.created_at = data.get('created_at', session.created_at)
        session.updated_at = data.get('updated_at', session.updated_at)
        session.results = data.get('results', [])
        
        return session
    
    def create_copy(self, new_name: Optional[str] = None) -> 'SessionModel':
        """
        セッションのコピーを作成
        
        Parameters
        ----------
        new_name : Optional[str], optional
            新しいセッション名, by default None (元の名前に "Copy of" を追加)
            
        Returns
        -------
        SessionModel
            コピーされたセッションインスタンス
        """
        if new_name is None:
            new_name = f"Copy of {self.name}"
            
        # event_dateがISO形式の文字列の場合はdatetimeに変換
        event_date = None
        if self.event_date:
            try:
                event_date = datetime.fromisoformat(self.event_date)
            except (ValueError, TypeError):
                # 変換エラーの場合はNoneのままにする
                pass
            
        new_session = SessionModel(
            name=new_name,
            project_id=self.project_id,
            description=self.description,
            purpose=self.purpose,
            category=self.category,
            tags=self.tags.copy(),
            status=self.status,
            rating=self.rating,
            related_sessions=copy.deepcopy(self.related_sessions),
            metadata=copy.deepcopy(self.metadata),
            session_id=None,  # 新しいセッションには新しいIDを生成
            event_date=event_date,
            location=self.location,
            importance=self.importance,
            completion_percentage=self.completion_percentage
        )
        
        return new_session


class SessionResult:
    """
    セッション結果モデル
    
    Parameters
    ----------
    result_id : str
        結果ID
    session_id : str
        セッションID
    result_type : str
        結果タイプ
        - "wind_estimation": 風向風速推定
        - "strategy_points": 戦略ポイント
        - "performance": パフォーマンス分析
        - "data_cleaning": データクリーニング
        - "simulation": シミュレーション結果
        - "optimization": 最適化結果
        - "comparison": 比較分析結果
        - "summary": 要約結果
        - "validation": 検証結果
        - "correction": 修正結果
        - "visualization": 可視化結果
        - "export": エクスポート結果
        - "report": レポート結果
        - "metrics": 性能指標結果
        - "custom": カスタム結果
    result_category : str, optional
        結果カテゴリ
        - "analysis": 分析結果
        - "validation": 検証結果
        - "visualization": 可視化結果
        - "report": レポート
        - "export": エクスポート結果
        - "data_processing": データ処理結果
    data : Dict[str, Any]
        結果データ
    importance : str, optional
        重要度 ("low", "normal", "high", "critical"), by default "normal"
    metadata : Dict[str, Any], optional
        結果メタデータ, by default None
    created_at : datetime, optional
        作成日時, by default None
    version : int, optional
        バージョン番号, by default 1
    is_current : bool, optional
        現在のバージョンかどうか, by default True
    """
    
    def __init__(self,
                 result_id: str,
                 session_id: str,
                 result_type: str,
                 data: Dict[str, Any],
                 result_category: str = "analysis",
                 importance: str = "normal",
                 metadata: Dict[str, Any] = None,
                 created_at: datetime = None,
                 version: int = 1,
                 is_current: bool = True,
                 tags: List[str] = None,
                 parent_version: int = None,
                 last_modified_at: datetime = None,
                 creator: str = None):
        """
        イニシャライザ
        
        Parameters
        ----------
        result_id : str
            結果ID
        session_id : str
            セッションID
        result_type : str
            結果タイプ
            - "wind_estimation": 風向風速推定
            - "strategy_points": 戦略ポイント
            - "performance": パフォーマンス分析
            - "data_cleaning": データクリーニング
            - "simulation": シミュレーション結果
            - "optimization": 最適化結果
            - "comparison": 比較分析結果
            - "summary": 要約結果
            - "validation": 検証結果
            - "correction": 修正結果
            - "visualization": 可視化結果
            - "export": エクスポート結果
            - "report": レポート結果
            - "metrics": 性能指標結果
            - "custom": カスタム結果
        data : Dict[str, Any]
            結果データ
        result_category : str, optional
            結果カテゴリ
            - "analysis": 分析結果
            - "validation": 検証結果
            - "visualization": 可視化結果
            - "report": レポート
            - "export": エクスポート結果
            - "data_processing": データ処理結果
            by default "analysis"
        importance : str, optional
            重要度 ("low", "normal", "high", "critical"), by default "normal"
        metadata : Dict[str, Any], optional
            結果メタデータ, by default None
        created_at : datetime, optional
            作成日時, by default None
        version : int, optional
            バージョン番号, by default 1
        is_current : bool, optional
            現在のバージョンかどうか, by default True
        tags : List[str], optional
            結果に付けるタグのリスト, by default None
        parent_version : int, optional
            親バージョン番号（このバージョンの元になったバージョン）, by default None
        last_modified_at : datetime, optional
            最終更新日時, by default None
        creator : str, optional
            作成者, by default None
        """
        self.result_id = result_id
        self.session_id = session_id
        self.result_type = result_type
        self.result_category = result_category
        self.data = data
        self.importance = importance
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.version = version
        self.is_current = is_current
        self.tags = tags or []
        self.parent_version = parent_version
        self.last_modified_at = last_modified_at or self.created_at
        self.creator = creator or os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        
        # メタデータの互換性維持
        if 'result_category' not in self.metadata:
            self.metadata['result_category'] = self.result_category
            
        if 'importance' not in self.metadata:
            self.metadata['importance'] = self.importance
            
        if 'creator' not in self.metadata:
            self.metadata['creator'] = self.creator
            
        if 'parent_version' not in self.metadata and self.parent_version is not None:
            self.metadata['parent_version'] = self.parent_version
    
    def update_metadata(self, metadata_updates: Dict[str, Any]) -> None:
        """
        メタデータを更新
        
        Parameters
        ----------
        metadata_updates : Dict[str, Any]
            更新するメタデータ
        """
        self.metadata.update(metadata_updates)
    
    def mark_as_current(self, current: bool = True) -> None:
        """
        現在のバージョンとしてマーク
        
        Parameters
        ----------
        current : bool, optional
            現在のバージョンかどうか, by default True
        """
        self.is_current = current
    
    def create_new_version(self, data: Dict[str, Any], metadata: Dict[str, Any] = None, 
                            result_category: str = None, importance: str = None, 
                            tags: List[str] = None, creator: str = None) -> 'SessionResult':
        """
        新しいバージョンを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            新しい結果データ
        metadata : Dict[str, Any], optional
            新しいメタデータ, by default None
        result_category : str, optional
            新しい結果カテゴリ, by default None (元のカテゴリを継承)
        importance : str, optional
            新しい重要度, by default None (元の重要度を継承)
        tags : List[str], optional
            新しいタグリスト, by default None (元のタグを継承)
        creator : str, optional
            作成者, by default None (現在のユーザー)
            
        Returns
        -------
        SessionResult
            新しいバージョンのセッション結果
        """
        # 新しいメタデータを準備
        new_metadata = metadata or copy.deepcopy(self.metadata)
        
        # バージョン履歴をメタデータに追加
        if 'version_history' not in new_metadata:
            new_metadata['version_history'] = []
            
        # 現在のバージョン情報を履歴に追加
        current_version_info = {
            'version': self.version,
            'created_at': self.created_at,
            'creator': self.creator,
            'is_current': False
        }
        new_metadata['version_history'].append(current_version_info)
        
        # 現在時刻を取得
        now = datetime.now().isoformat()
        
        # 基本IDは同じで、バージョンを増やす
        new_result = SessionResult(
            result_id=self.result_id,
            session_id=self.session_id,
            result_type=self.result_type,
            data=data,
            result_category=result_category or self.result_category,
            importance=importance or self.importance,
            metadata=new_metadata,
            version=self.version + 1,
            is_current=True,  # 新しいバージョンは現在のバージョン
            tags=tags or self.tags.copy(),
            parent_version=self.version,  # 親バージョンは現在のバージョン
            last_modified_at=now,
            creator=creator or os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        )
        
        # 自分自身は現在のバージョンではなくなる
        self.is_current = False
        self.last_modified_at = now
        
        return new_result
    
    def update_importance(self, importance: str) -> None:
        """
        結果の重要度を更新
        
        Parameters
        ----------
        importance : str
            新しい重要度 ("low", "normal", "high", "critical")
        """
        if importance in ["low", "normal", "high", "critical"]:
            self.importance = importance
            self.metadata['importance'] = importance
    
    def update_category(self, category: str) -> None:
        """
        結果カテゴリを更新
        
        Parameters
        ----------
        category : str
            新しいカテゴリ
        """
        self.result_category = category
        self.metadata['result_category'] = category
    
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
    
    def remove_tag(self, tag: str) -> None:
        """
        タグを削除
        
        Parameters
        ----------
        tag : str
            削除するタグ
        """
        if tag in self.tags:
            self.tags.remove(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            結果情報を含む辞書
        """
        return {
            'result_id': self.result_id,
            'session_id': self.session_id,
            'result_type': self.result_type,
            'result_category': self.result_category,
            'data': self.data,
            'importance': self.importance,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'version': self.version,
            'is_current': self.is_current,
            'parent_version': self.parent_version,
            'last_modified_at': self.last_modified_at,
            'creator': self.creator
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionResult':
        """
        辞書から結果を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            結果情報を含む辞書
            
        Returns
        -------
        SessionResult
            作成された結果インスタンス
        """
        # メタデータから追加情報を取得（互換性のため）
        metadata = data.get('metadata', {})
        result_category = data.get('result_category', 'analysis') or metadata.get('result_category', 'analysis')
        importance = data.get('importance', 'normal') or metadata.get('importance', 'normal')
        tags = data.get('tags', [])
        creator = data.get('creator') or metadata.get('creator')
        parent_version = data.get('parent_version') or metadata.get('parent_version')
        last_modified_at = data.get('last_modified_at') or metadata.get('last_modified_at')
        
        return cls(
            result_id=data['result_id'],
            session_id=data['session_id'],
            result_type=data['result_type'],
            data=data['data'],
            result_category=result_category,
            importance=importance,
            metadata=metadata,
            created_at=data.get('created_at'),
            version=data.get('version', 1),
            is_current=data.get('is_current', True),
            tags=tags,
            parent_version=parent_version,
            last_modified_at=last_modified_at,
            creator=creator
        )
