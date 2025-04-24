# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.project_model

プロジェクトのデータモデルを定義するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set
import os
import json
from datetime import datetime
from pathlib import Path
import uuid

class Project:
    """
    プロジェクトクラス
    
    セーリング分析プロジェクトを表現するクラス。
    メタデータと関連セッションのリストを管理します。
    
    属性
    -----
    name : str
        プロジェクト名
    description : str
        プロジェクトの説明
    tags : List[str]
        プロジェクトに関連するタグ
    metadata : Dict[str, Any]
        追加のメタデータ
    project_id : str
        プロジェクトID
    created_at : str
        作成日時（ISO形式）
    updated_at : str
        更新日時（ISO形式）
    sessions : List[str]
        関連セッションIDのリスト
    """
    
    def __init__(self, 
                 name: str, 
                 description: str = "", 
                 tags: List[str] = None,
                 metadata: Dict[str, Any] = None,
                 project_id: str = None,
                 parent_id: str = None,
                 category: str = "general",
                 color: str = "#4A90E2",
                 icon: str = "folder"):
        """
        プロジェクトの初期化
        
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
        project_id : str, optional
            プロジェクトID, by default None (自動生成)
        parent_id : str, optional
            親プロジェクトID, by default None (トップレベルプロジェクト)
        category : str, optional
            プロジェクトカテゴリ, by default "general"
        color : str, optional
            プロジェクトの表示色（HEX形式）, by default "#4A90E2"
        icon : str, optional
            プロジェクトのアイコン名, by default "folder"
        """
        self.name = name
        self.description = description
        self.tags = tags or []
        self.metadata = metadata or {}
        self.project_id = project_id or str(uuid.uuid4())
        self.parent_id = parent_id
        self.category = category
        self.color = color
        self.icon = icon
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.sessions = []
        self.sub_projects = []
        self.favorites = False
        self.view_settings = {
            "default_view": "list",
            "sort_by": "name",
            "sort_order": "asc",
            "view_mode": "compact"
        }
        
        # メタデータ基本情報の設定
        if 'created_by' not in self.metadata:
            self.metadata['created_by'] = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        if 'location' not in self.metadata:
            self.metadata['location'] = ""
        if 'event_date' not in self.metadata:
            self.metadata['event_date'] = ""
        if 'weather_conditions' not in self.metadata:
            self.metadata['weather_conditions'] = ""
    
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
    
    def add_sub_project(self, project_id: str) -> None:
        """
        サブプロジェクトを追加
        
        Parameters
        ----------
        project_id : str
            追加するプロジェクトID
        """
        if project_id not in self.sub_projects:
            self.sub_projects.append(project_id)
            self.updated_at = datetime.now().isoformat()
    
    def remove_sub_project(self, project_id: str) -> bool:
        """
        サブプロジェクトを削除
        
        Parameters
        ----------
        project_id : str
            削除するプロジェクトID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if project_id in self.sub_projects:
            self.sub_projects.remove(project_id)
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
    
    def set_favorites(self, is_favorite: bool) -> None:
        """
        お気に入り状態を設定

        Parameters
        ----------
        is_favorite : bool
            お気に入りとして設定するかどうか
        """
        self.favorites = is_favorite
        self.updated_at = datetime.now().isoformat()
    
    def update_view_settings(self, settings: Dict[str, Any]) -> None:
        """
        表示設定を更新

        Parameters
        ----------
        settings : Dict[str, Any]
            更新する表示設定
        """
        self.view_settings.update(settings)
        self.updated_at = datetime.now().isoformat()
    
    def set_color(self, color: str) -> None:
        """
        プロジェクトの色を設定

        Parameters
        ----------
        color : str
            設定する色（HEX形式）
        """
        self.color = color
        self.updated_at = datetime.now().isoformat()
    
    def set_icon(self, icon: str) -> None:
        """
        プロジェクトのアイコンを設定

        Parameters
        ----------
        icon : str
            設定するアイコン名
        """
        self.icon = icon
        self.updated_at = datetime.now().isoformat()
    
    def set_category(self, category: str) -> None:
        """
        プロジェクトのカテゴリを設定

        Parameters
        ----------
        category : str
            設定するカテゴリ
        """
        self.category = category
        self.updated_at = datetime.now().isoformat()
    
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
            'parent_id': self.parent_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'color': self.color,
            'icon': self.icon,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'sessions': self.sessions,
            'sub_projects': self.sub_projects,
            'favorites': self.favorites,
            'view_settings': self.view_settings
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
            project_id=data.get('project_id'),
            parent_id=data.get('parent_id'),
            category=data.get('category', 'general'),
            color=data.get('color', '#4A90E2'),
            icon=data.get('icon', 'folder')
        )
        
        project.created_at = data.get('created_at', project.created_at)
        project.updated_at = data.get('updated_at', project.updated_at)
        project.sessions = data.get('sessions', [])
        project.sub_projects = data.get('sub_projects', [])
        project.favorites = data.get('favorites', False)
        
        if 'view_settings' in data:
            project.view_settings = data['view_settings']
        
        return project


class Session:
    """
    セッションクラス
    
    分析セッションを表現するクラス。
    GPSデータと分析状態を管理します。
    
    属性
    -----
    name : str
        セッション名
    description : str
        セッションの説明
    tags : List[str]
        セッションに関連するタグ
    metadata : Dict[str, Any]
        追加のメタデータ
    session_id : str
        セッションID
    created_at : str
        作成日時（ISO形式）
    updated_at : str
        更新日時（ISO形式）
    data_file : str
        データファイルへのパス
    state_file : str
        状態ファイルへのパス
    analysis_results : List[str]
        分析結果のIDリスト
    """
    
    def __init__(self, 
                 name: str, 
                 description: str = "", 
                 tags: List[str] = None,
                 metadata: Dict[str, Any] = None,
                 session_id: str = None,
                 category: str = "general",
                 color: str = "#32A852",
                 icon: str = "map",
                 source_file: str = None,
                 source_type: str = None,
                 status: str = "new"):
        """
        セッションの初期化
        
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
        session_id : str, optional
            セッションID, by default None (自動生成)
        category : str, optional
            セッションカテゴリ, by default "general"
        color : str, optional
            セッションの表示色（HEX形式）, by default "#32A852"
        icon : str, optional
            セッションのアイコン名, by default "map"
        source_file : str, optional
            元のソースファイルパス, by default None
        source_type : str, optional
            ソースファイルの種類（'csv', 'gpx', 'fit', 'tcx'など）, by default None
        status : str, optional
            セッションのステータス ('new', 'validated', 'analyzed', 'completed'), by default "new"
        """
        self.name = name
        self.description = description
        self.tags = tags or []
        self.metadata = metadata or {}
        self.session_id = session_id or str(uuid.uuid4())
        self.category = category
        self.color = color
        self.icon = icon
        self.source_file = source_file
        self.source_type = source_type
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.data_file = None  # データファイルへのパス
        self.state_file = None  # 状態ファイルへのパス
        self.analysis_results = []  # 分析結果のID
        self.favorites = False
        self.validation_score = 0.0  # データ検証スコア (0.0-1.0)
        self.data_quality = {
            "completeness": 0.0,  # データの完全性スコア
            "consistency": 0.0,   # データの一貫性スコア
            "accuracy": 0.0,      # データの精度スコア
            "error_count": 0,     # エラーの数
            "warning_count": 0,   # 警告の数
            "fixed_issues": 0     # 修正された問題の数
        }
        
        # メタデータ基本情報の設定
        if 'created_by' not in self.metadata:
            self.metadata['created_by'] = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        if 'location' not in self.metadata:
            self.metadata['location'] = ""
        if 'event_date' not in self.metadata:
            self.metadata['event_date'] = ""
        if 'weather_conditions' not in self.metadata:
            self.metadata['weather_conditions'] = ""
        if 'boat_type' not in self.metadata:
            self.metadata['boat_type'] = ""
        if 'crew_info' not in self.metadata:
            self.metadata['crew_info'] = ""
    
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
    
    def set_color(self, color: str) -> None:
        """
        セッションの色を設定

        Parameters
        ----------
        color : str
            設定する色（HEX形式）
        """
        self.color = color
        self.updated_at = datetime.now().isoformat()
    
    def set_icon(self, icon: str) -> None:
        """
        セッションのアイコンを設定

        Parameters
        ----------
        icon : str
            設定するアイコン名
        """
        self.icon = icon
        self.updated_at = datetime.now().isoformat()
    
    def set_status(self, status: str) -> None:
        """
        セッションのステータスを設定

        Parameters
        ----------
        status : str
            設定するステータス ('new', 'validated', 'analyzed', 'completed')
        """
        self.status = status
        self.updated_at = datetime.now().isoformat()
    
    def set_favorites(self, is_favorite: bool) -> None:
        """
        お気に入り状態を設定

        Parameters
        ----------
        is_favorite : bool
            お気に入りとして設定するかどうか
        """
        self.favorites = is_favorite
        self.updated_at = datetime.now().isoformat()
    
    def update_validation_score(self, score: float) -> None:
        """
        データ検証スコアを更新

        Parameters
        ----------
        score : float
            新しい検証スコア (0.0-1.0)
        """
        self.validation_score = min(max(0.0, score), 1.0)  # 0.0〜1.0の範囲に制限
        self.updated_at = datetime.now().isoformat()
    
    def update_data_quality(self, quality_metrics: Dict[str, Any]) -> None:
        """
        データ品質メトリクスを更新

        Parameters
        ----------
        quality_metrics : Dict[str, Any]
            更新するデータ品質メトリクス
        """
        self.data_quality.update(quality_metrics)
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
            'description': self.description,
            'category': self.category,
            'color': self.color,
            'icon': self.icon,
            'source_file': self.source_file,
            'source_type': self.source_type,
            'status': self.status,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data_file': self.data_file,
            'state_file': self.state_file,
            'analysis_results': self.analysis_results,
            'favorites': self.favorites,
            'validation_score': self.validation_score,
            'data_quality': self.data_quality
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
            session_id=data.get('session_id'),
            category=data.get('category', 'general'),
            color=data.get('color', '#32A852'),
            icon=data.get('icon', 'map'),
            source_file=data.get('source_file'),
            source_type=data.get('source_type'),
            status=data.get('status', 'new')
        )
        
        session.created_at = data.get('created_at', session.created_at)
        session.updated_at = data.get('updated_at', session.updated_at)
        session.data_file = data.get('data_file')
        session.state_file = data.get('state_file')
        session.analysis_results = data.get('analysis_results', [])
        session.favorites = data.get('favorites', False)
        session.validation_score = data.get('validation_score', 0.0)
        
        if 'data_quality' in data:
            session.data_quality = data['data_quality']
        
        return session


class AnalysisResult:
    """
    分析結果クラス
    
    セッションの分析結果を表現するクラス。
    
    属性
    -----
    name : str
        分析結果名
    description : str
        分析結果の説明
    result_type : str
        結果タイプ（例: 'wind_analysis', 'strategy_points'）
    data : Dict[str, Any]
        結果データ
    metadata : Dict[str, Any]
        追加のメタデータ
    result_id : str
        結果ID
    created_at : str
        作成日時（ISO形式）
    updated_at : str
        更新日時（ISO形式）
    version : int
        結果のバージョン
    tags : List[str]
        結果に関連するタグ
    quality_score : float
        結果の品質スコア (0.0-1.0)
    visualization_settings : Dict[str, Any]
        可視化設定
    """
    
    def __init__(self, 
                 name: str, 
                 result_type: str,
                 data: Dict[str, Any],
                 description: str = "", 
                 metadata: Dict[str, Any] = None,
                 result_id: str = None,
                 tags: List[str] = None,
                 version: int = 1,
                 quality_score: float = 0.0,
                 visualization_settings: Dict[str, Any] = None):
        """
        分析結果の初期化
        
        Parameters
        ----------
        name : str
            分析結果名
        result_type : str
            結果タイプ（例: 'wind_analysis', 'strategy_points'）
        data : Dict[str, Any]
            結果データ
        description : str, optional
            分析結果の説明, by default ""
        metadata : Dict[str, Any], optional
            追加のメタデータ, by default None
        result_id : str, optional
            結果ID, by default None (自動生成)
        tags : List[str], optional
            結果に関連するタグ, by default None
        version : int, optional
            結果のバージョン, by default 1
        quality_score : float, optional
            結果の品質スコア (0.0-1.0), by default 0.0
        visualization_settings : Dict[str, Any], optional
            可視化設定, by default None
        """
        self.name = name
        self.description = description
        self.result_type = result_type
        self.data = data
        self.metadata = metadata or {}
        self.result_id = result_id or str(uuid.uuid4())
        self.tags = tags or []
        self.version = version
        self.quality_score = min(max(0.0, quality_score), 1.0)  # 0.0〜1.0の範囲に制限
        self.visualization_settings = visualization_settings or {
            "chart_type": "auto",
            "color_scheme": "blues",
            "show_grid": True,
            "show_legend": True,
            "show_title": True,
            "interactive": True
        }
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.summary = ""  # 結果の要約
        self.highlights = []  # 注目すべきポイント
        
        # メタデータ基本情報の設定
        if 'created_by' not in self.metadata:
            self.metadata['created_by'] = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        if 'analysis_parameters' not in self.metadata:
            self.metadata['analysis_parameters'] = {}
        if 'source_info' not in self.metadata:
            self.metadata['source_info'] = {}
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        結果データを更新
        
        Parameters
        ----------
        data : Dict[str, Any]
            新しい結果データ
        """
        self.data = data
        self.version += 1
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
    
    def update_visualization_settings(self, settings: Dict[str, Any]) -> None:
        """
        可視化設定を更新
        
        Parameters
        ----------
        settings : Dict[str, Any]
            更新する可視化設定
        """
        self.visualization_settings.update(settings)
        self.updated_at = datetime.now().isoformat()
    
    def set_summary(self, summary: str) -> None:
        """
        結果の要約を設定
        
        Parameters
        ----------
        summary : str
            設定する要約
        """
        self.summary = summary
        self.updated_at = datetime.now().isoformat()
    
    def add_highlight(self, highlight: str) -> None:
        """
        注目ポイントを追加
        
        Parameters
        ----------
        highlight : str
            追加する注目ポイント
        """
        if highlight not in self.highlights:
            self.highlights.append(highlight)
            self.updated_at = datetime.now().isoformat()
    
    def update_quality_score(self, score: float) -> None:
        """
        品質スコアを更新
        
        Parameters
        ----------
        score : float
            新しい品質スコア (0.0-1.0)
        """
        self.quality_score = min(max(0.0, score), 1.0)  # 0.0〜1.0の範囲に制限
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        分析結果を辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            分析結果情報を含む辞書
        """
        return {
            'result_id': self.result_id,
            'name': self.name,
            'description': self.description,
            'result_type': self.result_type,
            'data': self.data,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags,
            'version': self.version,
            'quality_score': self.quality_score,
            'visualization_settings': self.visualization_settings,
            'summary': self.summary,
            'highlights': self.highlights
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """
        辞書から分析結果を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            分析結果情報を含む辞書
            
        Returns
        -------
        AnalysisResult
            作成された分析結果インスタンス
        """
        result = cls(
            name=data['name'],
            result_type=data['result_type'],
            data=data['data'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {}),
            result_id=data.get('result_id'),
            tags=data.get('tags', []),
            version=data.get('version', 1),
            quality_score=data.get('quality_score', 0.0),
            visualization_settings=data.get('visualization_settings')
        )
        
        result.created_at = data.get('created_at', result.created_at)
        result.updated_at = data.get('updated_at', result.updated_at)
        result.summary = data.get('summary', '')
        result.highlights = data.get('highlights', [])
        
        return result
