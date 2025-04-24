# -*- coding: utf-8 -*-
"""
sailing_data_processor.sharing.storage

共有機能のデータ保存クラス
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional, Union, Set


class StorageManager:
    """
    共有機能のデータを保存・読み込みするクラス
    
    ファイルベースの永続化ストレージを提供します。
    """
    
    def __init__(self, storage_dir: str = None):
        """
        初期化
        
        Parameters
        ----------
        storage_dir : str, optional
            ストレージディレクトリ, by default None
            Noneの場合はデフォルトディレクトリを使用
        """
        # デフォルトのストレージディレクトリ
        if storage_dir is None:
            # ユーザーホームディレクトリ + .sailing_analyzer/sharing
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".sailing_analyzer", "sharing")
        
        self.storage_dir = storage_dir
        
        # ディレクトリの存在確認・作成
        os.makedirs(storage_dir, exist_ok=True)
        
        # 各データ種別のファイルパス
        self.links_file = os.path.join(storage_dir, "links.json")
        self.teams_file = os.path.join(storage_dir, "teams.json")
        self.memberships_file = os.path.join(storage_dir, "memberships.json")
        self.invitations_file = os.path.join(storage_dir, "invitations.json")
        self.comments_file = os.path.join(storage_dir, "comments.json")
        self.item_comments_file = os.path.join(storage_dir, "item_comments.json")
        self.notifications_file = os.path.join(storage_dir, "notifications.json")
    
    def _ensure_directory(self) -> None:
        """ストレージディレクトリの存在を確認・作成"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """
        JSONファイルの読み込み
        
        Parameters
        ----------
        file_path : str
            ファイルパス
            
        Returns
        -------
        Dict[str, Any]
            読み込んだデータ
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return {}
    
    def _save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        JSONファイルへの保存
        
        Parameters
        ----------
        file_path : str
            ファイルパス
        data : Dict[str, Any]
            保存するデータ
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        try:
            self._ensure_directory()
            
            # セット型をリストに変換（JSON化のため）
            data_copy = self._prepare_data_for_json(data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_copy, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {str(e)}")
            return False
    
    def _prepare_data_for_json(self, data: Any) -> Any:
        """
        データをJSON保存用に変換
        
        セット型をリストに変換するなど
        
        Parameters
        ----------
        data : Any
            変換するデータ
            
        Returns
        -------
        Any
            変換後のデータ
        """
        if isinstance(data, dict):
            return {k: self._prepare_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_data_for_json(item) for item in data]
        elif isinstance(data, set):
            return list(data)
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # その他のオブジェクトは文字列化
            return str(data)
    
    # リンク管理関連のメソッド
    def load_links(self) -> Dict[str, Any]:
        """
        共有リンク情報の読み込み
        
        Returns
        -------
        Dict[str, Any]
            リンク情報
        """
        return self._load_json(self.links_file)
    
    def save_links(self, links: Dict[str, Any]) -> bool:
        """
        共有リンク情報の保存
        
        Parameters
        ----------
        links : Dict[str, Any]
            リンク情報
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.links_file, links)
    
    # チーム管理関連のメソッド
    def load_teams(self) -> Dict[str, Any]:
        """
        チーム情報の読み込み
        
        Returns
        -------
        Dict[str, Any]
            チーム情報
        """
        return self._load_json(self.teams_file)
    
    def save_teams(self, teams: Dict[str, Any]) -> bool:
        """
        チーム情報の保存
        
        Parameters
        ----------
        teams : Dict[str, Any]
            チーム情報
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.teams_file, teams)
    
    def load_memberships(self) -> Dict[str, Any]:
        """
        メンバーシップ情報の読み込み
        
        Returns
        -------
        Dict[str, Any]
            メンバーシップ情報
        """
        return self._load_json(self.memberships_file)
    
    def save_memberships(self, memberships: Dict[str, Any]) -> bool:
        """
        メンバーシップ情報の保存
        
        Parameters
        ----------
        memberships : Dict[str, Any]
            メンバーシップ情報
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.memberships_file, memberships)
    
    def load_invitations(self) -> Dict[str, Any]:
        """
        招待情報の読み込み
        
        Returns
        -------
        Dict[str, Any]
            招待情報
        """
        return self._load_json(self.invitations_file)
    
    def save_invitations(self, invitations: Dict[str, Any]) -> bool:
        """
        招待情報の保存
        
        Parameters
        ----------
        invitations : Dict[str, Any]
            招待情報
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.invitations_file, invitations)
    
    # コメント関連のメソッド
    def load_comments(self) -> Dict[str, Any]:
        """
        コメント情報の読み込み
        
        Returns
        -------
        Dict[str, Any]
            コメント情報
        """
        comments = self._load_json(self.comments_file)
        
        # 既読情報をセットに変換
        for comment_id, comment in comments.items():
            if "read_by" in comment and isinstance(comment["read_by"], list):
                comment["read_by"] = set(comment["read_by"])
        
        return comments
    
    def save_comments(self, comments: Dict[str, Any]) -> bool:
        """
        コメント情報の保存
        
        Parameters
        ----------
        comments : Dict[str, Any]
            コメント情報
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.comments_file, comments)
    
    def load_item_comments(self) -> Dict[str, List[str]]:
        """
        アイテムとコメントの関連付け情報の読み込み
        
        Returns
        -------
        Dict[str, List[str]]
            アイテムIDとコメントIDの関連付け
        """
        return self._load_json(self.item_comments_file)
    
    def save_item_comments(self, item_comments: Dict[str, List[str]]) -> bool:
        """
        アイテムとコメントの関連付け情報の保存
        
        Parameters
        ----------
        item_comments : Dict[str, List[str]]
            アイテムIDとコメントIDの関連付け
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.item_comments_file, item_comments)
    
    # 通知関連のメソッド
    def load_notifications(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        通知情報の読み込み
        
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            ユーザーIDごとの通知リスト
        """
        return self._load_json(self.notifications_file)
    
    def save_notifications(self, notifications: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        通知情報の保存
        
        Parameters
        ----------
        notifications : Dict[str, List[Dict[str, Any]]]
            ユーザーIDごとの通知リスト
            
        Returns
        -------
        bool
            保存成功かどうか
        """
        return self._save_json(self.notifications_file, notifications)
