# -*- coding: utf-8 -*-
"""
sailing_data_processor.sharing.notification_manager

通知管理クラス
"""

import uuid
import datetime
from typing import Dict, Any, List, Optional, Callable, Union


class NotificationManager:
    """
    通知管理クラス
    
    ユーザーへの通知を管理します。
    """
    
    def __init__(self, storage_manager=None):
        """
        初期化
        
        Parameters
        ----------
        storage_manager : StorageManager, optional
            ストレージマネージャー, by default None
        """
        self.storage_manager = storage_manager
        self.notifications = {}  # {user_id: [notification_dict, ...]}
        
        # 保存データの読み込み
        self._load_notifications()
    
    def _load_notifications(self):
        """保存された通知情報の読み込み"""
        if self.storage_manager:
            notifications = self.storage_manager.load_notifications()
            if notifications:
                self.notifications = notifications
    
    def _save_notifications(self):
        """通知情報の保存"""
        if self.storage_manager:
            self.storage_manager.save_notifications(self.notifications)
    
    def create_notification(self, user_id: str, type: str, content: str,
                          reference_id: str = None, reference_type: str = None,
                          important: bool = False) -> Dict[str, Any]:
        """
        通知の作成
        
        Parameters
        ----------
        user_id : str
            通知を受け取るユーザーID
        type : str
            通知タイプ (reply, mention, share, team, etc)
        content : str
            通知内容
        reference_id : str, optional
            参照ID, by default None
        reference_type : str, optional
            参照タイプ, by default None
        important : bool, optional
            重要度, by default False
            
        Returns
        -------
        Dict[str, Any]
            作成された通知情報
        """
        # 通知IDの生成
        notification_id = str(uuid.uuid4())
        
        # 現在時刻
        now = datetime.datetime.now().isoformat()
        
        # 通知情報の作成
        notification = {
            "notification_id": notification_id,
            "user_id": user_id,
            "type": type,
            "content": content,
            "reference_id": reference_id,
            "reference_type": reference_type,
            "important": important,
            "created_at": now,
            "read": False
        }
        
        # ユーザーの通知リストに追加
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        
        self.notifications[user_id].append(notification)
        
        # 変更の保存
        self._save_notifications()
        
        return notification
    
    def get_notifications(self, user_id: str, limit: int = 50, 
                        unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        ユーザーの通知を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        limit : int, optional
            取得する最大件数, by default 50
        unread_only : bool, optional
            未読のみ取得するかどうか, by default False
            
        Returns
        -------
        List[Dict[str, Any]]
            通知のリスト
        """
        if user_id not in self.notifications:
            return []
        
        # ユーザーの通知を取得
        user_notifications = self.notifications[user_id]
        
        # 未読フィルタリング
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.get("read", False)]
        
        # 作成日時の新しい順にソート
        sorted_notifications = sorted(
            user_notifications,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        # 件数制限
        return sorted_notifications[:limit]
    
    def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """
        通知を既読にする
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        notification_id : str
            通知ID
            
        Returns
        -------
        bool
            成功かどうか
        """
        if user_id not in self.notifications:
            return False
        
        # 通知を検索
        for notification in self.notifications[user_id]:
            if notification.get("notification_id") == notification_id:
                notification["read"] = True
                self._save_notifications()
                return True
        
        return False
    
    def mark_all_as_read(self, user_id: str) -> int:
        """
        すべての通知を既読にする
        
        Parameters
        ----------
        user_id : str
            ユーザーID
            
        Returns
        -------
        int
            既読にした通知の数
        """
        if user_id not in self.notifications:
            return 0
        
        # 未読の通知をカウント
        count = 0
        for notification in self.notifications[user_id]:
            if not notification.get("read", False):
                notification["read"] = True
                count += 1
        
        if count > 0:
            self._save_notifications()
        
        return count
    
    def get_unread_count(self, user_id: str) -> int:
        """
        未読通知の数を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
            
        Returns
        -------
        int
            未読通知の数
        """
        if user_id not in self.notifications:
            return 0
        
        # 未読の通知をカウント
        return sum(1 for n in self.notifications[user_id] if not n.get("read", False))
    
    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """
        通知を削除
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        notification_id : str
            通知ID
            
        Returns
        -------
        bool
            成功かどうか
        """
        if user_id not in self.notifications:
            return False
        
        # 通知を検索して削除
        initial_count = len(self.notifications[user_id])
        self.notifications[user_id] = [
            n for n in self.notifications[user_id] 
            if n.get("notification_id") != notification_id
        ]
        
        # 変更があれば保存
        if len(self.notifications[user_id]) < initial_count:
            self._save_notifications()
            return True
        
        return False
    
    def clean_notifications(self, max_age_days: int = 30) -> int:
        """
        古い通知をクリーンアップ
        
        Parameters
        ----------
        max_age_days : int, optional
            保持する最大日数, by default 30
            
        Returns
        -------
        int
            削除された通知の数
        """
        # 現在時刻
        now = datetime.datetime.now()
        cutoff_date = (now - datetime.timedelta(days=max_age_days)).isoformat()
        
        total_removed = 0
        
        # 各ユーザーの通知をクリーンアップ
        for user_id in list(self.notifications.keys()):
            # 削除前の数を記録
            initial_count = len(self.notifications[user_id])
            
            # 新しい通知のみ残す
            self.notifications[user_id] = [
                n for n in self.notifications[user_id]
                if n.get("created_at", "") > cutoff_date
            ]
            
            # 削除された数を追加
            total_removed += initial_count - len(self.notifications[user_id])
            
            # 通知が空になったら削除
            if not self.notifications[user_id]:
                del self.notifications[user_id]
        
        # 変更があれば保存
        if total_removed > 0:
            self._save_notifications()
        
        return total_removed
