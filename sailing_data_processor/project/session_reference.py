# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.session_reference

セッション参照クラスを定義するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set
import os
import json
from datetime import datetime
import uuid

class SessionReference:
    """
    セッション参照クラス
    
    プロジェクト内のセッション参照を表現するクラス。
    セッション自体のデータは含まず、参照情報のみを保持します。
    
    属性
    -----
    session_id : str
        参照先のセッションID
    display_name : str
        プロジェクト内での表示名（未設定の場合はセッション名を使用）
    description : str
        プロジェクト内での説明
    metadata : Dict[str, Any]
        参照に関連するメタデータ
    added_at : str
        追加日時（ISO形式）
    order : int
        プロジェクト内での表示順序
    view_settings : Dict[str, Any]
        表示設定
    cached_info : Dict[str, Any]
        セッション情報のキャッシュ
    """
    
    def __init__(self, 
                 session_id: str,
                 display_name: Optional[str] = None,
                 description: str = "",
                 metadata: Dict[str, Any] = None,
                 order: int = 0,
                 view_settings: Dict[str, Any] = None,
                 cached_info: Dict[str, Any] = None):
        """
        セッション参照の初期化
        
        Parameters
        ----------
        session_id : str
            参照先のセッションID
        display_name : Optional[str], optional
            プロジェクト内での表示名, by default None
        description : str, optional
            プロジェクト内での説明, by default ""
        metadata : Dict[str, Any], optional
            参照に関連するメタデータ, by default None
        order : int, optional
            プロジェクト内での表示順序, by default 0
        view_settings : Dict[str, Any], optional
            表示設定, by default None
        cached_info : Dict[str, Any], optional
            セッション情報のキャッシュ, by default None
        """
        self.session_id = session_id
        self.display_name = display_name
        self.description = description
        self.metadata = metadata or {}
        self.added_at = datetime.now().isoformat()
        self.order = order
        self.view_settings = view_settings or {
            "visible": True,
            "highlight": False,
            "color_override": None
        }
        self.cached_info = cached_info or {}
    
    def update_cached_info(self, session) -> None:
        """
        セッション情報のキャッシュを更新
        
        Parameters
        ----------
        session : Session
            キャッシュするセッション情報
        """
        self.cached_info = {
            "name": session.name,
            "description": session.description,
            "category": getattr(session, 'category', ''),
            "color": getattr(session, 'color', ''),
            "icon": getattr(session, 'icon', ''),
            "tags": session.tags,
            "status": getattr(session, 'status', ''),
            "updated_at": session.updated_at,
            "created_at": session.created_at,
            "validation_score": getattr(session, 'validation_score', 0.0),
            "has_data": bool(session.data_file),
            "has_results": bool(session.analysis_results)
        }
    
    def set_order(self, order: int) -> None:
        """
        表示順序を設定
        
        Parameters
        ----------
        order : int
            新しい表示順序
        """
        self.order = order
    
    def set_display_name(self, display_name: str) -> None:
        """
        表示名を設定
        
        Parameters
        ----------
        display_name : str
            新しい表示名
        """
        self.display_name = display_name
    
    def update_view_settings(self, settings: Dict[str, Any]) -> None:
        """
        表示設定を更新
        
        Parameters
        ----------
        settings : Dict[str, Any]
            更新する表示設定
        """
        self.view_settings.update(settings)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        セッション参照を辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            セッション参照情報を含む辞書
        """
        return {
            "session_id": self.session_id,
            "display_name": self.display_name,
            "description": self.description,
            "metadata": self.metadata,
            "added_at": self.added_at,
            "order": self.order,
            "view_settings": self.view_settings,
            "cached_info": self.cached_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionReference':
        """
        辞書からセッション参照を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            セッション参照情報を含む辞書
        
        Returns
        -------
        SessionReference
            作成されたセッション参照インスタンス
        """
        reference = cls(
            session_id=data["session_id"],
            display_name=data.get("display_name"),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            order=data.get("order", 0),
            view_settings=data.get("view_settings"),
            cached_info=data.get("cached_info", {})
        )
        
        reference.added_at = data.get("added_at", reference.added_at)
        
        return reference
