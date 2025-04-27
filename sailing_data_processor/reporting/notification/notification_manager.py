# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.notification.notification_manager

通知管理システムを提供するモジュール
"""

import uuid
import datetime
import logging
import json
from typing import Dict, List, Optional, Any, Callable, Union, Set

# ロガーの設定
logger = logging.getLogger(__name__)

class BaseNotificationChannel:
    """
    通知チャネルの基底クラス
    
    通知の送信方法を実装するための基底クラスです。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            チャネル設定, by default None
        """
        self.config = config or {}
        
    def send(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        通知を送信
        
        Parameters
        ----------
        user_id : str
            送信先ユーザーID
        notification : Dict[str, Any]
            送信する通知データ
            
        Returns
        -------
        bool
            送信成功したかどうか
        """
        raise NotImplementedError("This method should be implemented by subclasses")


class AppNotificationChannel(BaseNotificationChannel):
    """アプリ内通知チャネル"""
    
    def send(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        アプリ内通知を送信（通知ストレージに保存するだけ）
        
        Parameters
        ----------
        user_id : str
            送信先ユーザーID
        notification : Dict[str, Any]
            送信する通知データ
            
        Returns
        -------
        bool
            送信成功したかどうか
        """
        try:
            logger.info(f"App notification sent to user {user_id}: {notification['title']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send app notification: {str(e)}")
            return False


class EmailNotificationChannel(BaseNotificationChannel):
    """メール通知チャネル"""
    
    def send(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        メール通知を送信
        
        Parameters
        ----------
        user_id : str
            送信先ユーザーID
        notification : Dict[str, Any]
            送信する通知データ
            
        Returns
        -------
        bool
            送信成功したかどうか
        """
        try:
            # 実際のメール送信はここで実装
            # ここではログ出力のみ
            logger.info(f"Email notification would be sent to user {user_id}: {notification['title']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False


class SlackNotificationChannel(BaseNotificationChannel):
    """Slack通知チャネル"""
    
    def send(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Slack通知を送信
        
        Parameters
        ----------
        user_id : str
            送信先ユーザーID
        notification : Dict[str, Any]
            送信する通知データ
            
        Returns
        -------
        bool
            送信成功したかどうか
        """
        try:
            # 実際のSlack送信はここで実装
            # ここではログ出力のみ
            logger.info(f"Slack notification would be sent to user {user_id}: {notification['title']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False


class NotificationManager:
    """
    通知管理クラス
    
    イベントに基づいて通知を生成し、配信を管理します。
    """
    
    def __init__(self, storage_manager=None, user_manager=None, template_manager=None):
        """
        初期化
        
        Parameters
        ----------
        storage_manager : object, optional
            ストレージ管理オブジェクト, by default None
        user_manager : object, optional
            ユーザー管理オブジェクト, by default None
        template_manager : object, optional
            テンプレート管理オブジェクト, by default None
        """
        self.storage_manager = storage_manager
        self.user_manager = user_manager
        self.template_manager = template_manager
        
        # 通知ストレージ
        self._notifications = {}  # {user_id: [notifications]}
        
        # 購読管理
        self._subscriptions = {}  # {event_type: user_id: settings}}
        
        # 通知チャネル
        self._channels = {}
            "app": AppNotificationChannel(),
            "email": EmailNotificationChannel(),
            "slack": SlackNotificationChannel()
        }
        
        # 通知キュー (非同期処理用)
        self._notification_queue = []
        
        # 保存データの読み込み
        self._load_data()
        
        logger.info("NotificationManager initialized")
    
    def _load_data(self):
        """保存された通知データの読み込み"""
        if self.storage_manager:
            try:
                # 通知データの読み込み
                notifications = self.storage_manager.load_notifications()
                if notifications:
                    self._notifications = notifications
                    logger.info(f"Loaded notifications for {len(notifications)} users")
                
                # 購読設定の読み込み
                subscriptions = self.storage_manager.load_subscriptions()
                if subscriptions:
                    self._subscriptions = subscriptions
                    logger.info(f"Loaded {len(subscriptions)} event type subscriptions")
            except Exception as e:
                logger.error(f"Failed to load notification data: {str(e)}")
    
    def _save_data(self):
        """通知データの保存"""
        if self.storage_manager:
            try:
                # 通知データの保存
                self.storage_manager.save_notifications(self._notifications)
                
                # 購読設定の保存
                self.storage_manager.save_subscriptions(self._subscriptions)
                
                logger.info("Notification data saved")
            except Exception as e:
                logger.error(f"Failed to save notification data: {str(e)}")
    
    def create_notification(self, event_type: str, event_data: Dict[str, Any], 
                          recipients: List[str] = None, priority: str = "normal",
                          metadata: Dict[str, Any] = None) -> List[str]:
        """
        通知を作成
        
        Parameters
        ----------
        event_type : str
            イベントタイプ
        event_data : Dict[str, Any]
            イベントデータ
        recipients : List[str], optional
            受信者リスト, by default None (イベント購読者全員)
        priority : str, optional
            優先度 ("high", "normal", "low"), by default "normal"
        metadata : Dict[str, Any], optional
            メタデータ, by default None
            
        Returns
        -------
        List[str]
            作成された通知IDのリスト
        """
        # 優先度の検証
        if priority not in ["high", "normal", "low"]:
            priority = "normal"
        
        # 受信者の決定
        target_recipients = recipients or self._get_event_subscribers(event_type)
        if not target_recipients:
            logger.info(f"No recipients for event type {event_type}")
            return []
        
        # テンプレートから通知内容を生成
        notification_content = self._format_notification(event_type, event_data)
        
        # 現在時刻
        now = datetime.datetime.now()
        
        # 作成された通知のIDリスト
        notification_ids = []
        
        # 各受信者に通知を作成
        for recipient in target_recipients:
            # ユーザーが存在するか確認
            if self.user_manager and not self.user_manager.user_exists(recipient):
                logger.warning(f"User {recipient} does not exist, skipping notification")
                continue
            
            # ユーザーの通知設定を取得
            user_settings = self._get_user_notification_settings(recipient, event_type)
            
            # 通知をミュートしている場合はスキップ
            if user_settings.get("muted", False):
                logger.info(f"User {recipient} has muted notifications for event type {event_type}")
                continue
            
            # 通知IDの生成
            notification_id = str(uuid.uuid4())
            
            # 通知の作成
            notification = {
                "notification_id": notification_id,
                "user_id": recipient,
                "event_type": event_type,
                "title": notification_content.get("title", "通知"),
                "body": notification_content.get("body", ""),
                "created_at": now.isoformat(),
                "read": False,
                "priority": priority,
                "metadata": metadata or },
                "event_data": event_data
            }
            
            # ユーザーの通知リストを初期化
            if recipient not in self._notifications:
                self._notifications[recipient] = []
            
            # 通知をリストに追加
            self._notifications[recipient].append(notification)
            notification_ids.append(notification_id)
            
            # 通知キューに追加
            self._notification_queue.append({
                "notification_id": notification_id,
                "user_id": recipient,
                "channels": user_settings.get("channels", ["app"]),
                "notification": notification
            })
        
        # データの保存
        self._save_data()
        
        # 非同期送信処理を開始（実際の実装ではバックグラウンドタスクで処理）
        self._process_notification_queue()
        
        logger.info(f"Created {len(notification_ids)} notifications for event {event_type}")
        return notification_ids
    
    def _format_notification(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, str]:
        """
        通知内容を書式設定
        
        Parameters
        ----------
        event_type : str
            イベントタイプ
        event_data : Dict[str, Any]
            イベントデータ
            
        Returns
        -------
        Dict[str, str]
            書式設定された通知内容
        """
        # テンプレートマネージャーがある場合はそれを利用
        if self.template_manager:
            return self.template_manager.format_notification(event_type, event_data)
        
        # 標準フォーマット
        title = event_type.replace("_", " ").title()
        body = "詳細を確認してください。"
        
        # イベントタイプ別のフォーマット
        if event_type == "report_shared":
            if "user_name" in event_data and "report_name" in event_data:
                title = f"{event_data['user_name']}がレポートを共有しました"
                body = f"{event_data['user_name']}があなたとレポート「{event_data['report_name']}」を共有しました。"
        
        elif event_type == "comment_added":
            if "user_name" in event_data and "item_name" in event_data:
                title = "コメントが追加されました"
                body = f"{event_data['user_name']}が{event_data.get('item_type', 'アイテム')}「{event_data['item_name']}」にコメントを追加しました。"
                if "comment_text" in event_data:
                    body += f"\n\"{event_data['comment_text']}\""
        
        elif event_type == "report_updated":
            if "user_name" in event_data and "report_name" in event_data:
                title = "レポートが更新されました"
                body = f"{event_data['user_name']}がレポート「{event_data['report_name']}」を更新しました。"
        
        return {"title": title, "body": body}
    
    def _get_event_subscribers(self, event_type: str) -> List[str]:
        """
        イベントタイプの購読者リストを取得
        
        Parameters
        ----------
        event_type : str
            イベントタイプ
            
        Returns
        -------
        List[str]
            ユーザーIDのリスト
        """
        if event_type not in self._subscriptions:
            return []
        
        return list(self._subscriptions[event_type].keys())
    
    def _get_user_notification_settings(self, user_id: str, event_type: str) -> Dict[str, Any]:
        """
        ユーザーのイベントタイプ別通知設定を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str
            イベントタイプ
            
        Returns
        -------
        Dict[str, Any]
            通知設定
        """
        # デフォルト設定
        default_settings = {
            "channels": ["app"],
            "muted": False,
            "schedule": None,
            "filters": None
        }
        
        # イベントタイプの設定を取得
        if event_type in self._subscriptions and user_id in self._subscriptions[event_type]:
            return {**default_settings, **self._subscriptions[event_type][user_id]}
        
        return default_settings
    
    def send_notification(self, notification_id: str, channels: List[str] = None) -> Dict[str, bool]:
        """
        通知を送信
        
        Parameters
        ----------
        notification_id : str
            通知ID
        channels : List[str], optional
            送信チャネル, by default None
            
        Returns
        -------
        Dict[str, bool]
            チャネル別の送信結果
        """
        # 通知の検索
        notification = None
        user_id = None
        
        for uid, notifications in self._notifications.items():
            for notif in notifications:
                if notif.get("notification_id") == notification_id:
                    notification = notif
                    user_id = uid
                    break
            if notification:
                break
        
        if not notification or not user_id:
            logger.warning(f"Notification {notification_id} not found")
            return {}
        
        # チャネルの決定
        if not channels:
            # ユーザーの通知設定からチャネルを取得
            user_settings = self._get_user_notification_settings(
                user_id, notification.get("event_type", "default")
            )
            channels = user_settings.get("channels", ["app"])
        
        # 送信結果
        results = {}
        
        # 各チャネルで送信
        for channel_name in channels:
            if channel_name in self._channels:
                channel = self._channels[channel_name]
                try:
                    success = channel.send(user_id, notification)
                    results[channel_name] = success
                    
                    # 送信日時を記録
                    if success and "sent_on" not in notification:
                        notification["sent_on"] = {}
                    
                    if success:
                        notification["sent_on"][channel_name] = datetime.datetime.now().isoformat()
                        
                except Exception as e:
                    logger.error(f"Error sending notification via {channel_name}: {str(e)}")
                    results[channel_name] = False
            else:
                logger.warning(f"Channel {channel_name} not found")
                results[channel_name] = False
        
        # データの保存
        self._save_data()
        
        return results
    
    def _process_notification_queue(self):
        """通知キューを処理（実際の実装ではバックグラウンドタスク）"""
        if not self._notification_queue:
            return
        
        logger.info(f"Processing notification queue ({len(self._notification_queue)} items)")
        
        while self._notification_queue:
            item = self._notification_queue.pop(0)
            
            # 通知送信
            self.send_notification(
                item["notification_id"],
                item["channels"]
            )
        
        logger.info("Notification queue processed")
    
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        通知を既読にマーク
        
        Parameters
        ----------
        notification_id : str
            通知ID
        user_id : str
            ユーザーID
            
        Returns
        -------
        bool
            成功したかどうか
        """
        if user_id not in self._notifications:
            logger.warning(f"User {user_id} has no notifications")
            return False
        
        # 通知の検索
        for notification in self._notifications[user_id]:
            if notification.get("notification_id") == notification_id:
                # 既に既読ならスキップ
                if notification.get("read", False):
                    return True
                
                # 既読にマーク
                notification["read"] = True
                notification["read_at"] = datetime.datetime.now().isoformat()
                
                # データの保存
                self._save_data()
                
                logger.info(f"Notification {notification_id} marked as read for user {user_id}")
                return True
        
        logger.warning(f"Notification {notification_id} not found for user {user_id}")
        return False
    
    def mark_all_as_read(self, user_id: str, event_type: str = None) -> int:
        """
        すべての通知を既読にマーク
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str, optional
            イベントタイプ（指定した場合はそのタイプのみ）, by default None
            
        Returns
        -------
        int
            既読にマークした通知の数
        """
        if user_id not in self._notifications:
            logger.warning(f"User {user_id} has no notifications")
            return 0
        
        # 現在時刻
        now = datetime.datetime.now().isoformat()
        
        # 既読にマークする通知を検索
        count = 0
        for notification in self._notifications[user_id]:
            # 既に既読ならスキップ
            if notification.get("read", False):
                continue
            
            # イベントタイプでフィルタリング
            if event_type and notification.get("event_type") != event_type:
                continue
            
            # 既読にマーク
            notification["read"] = True
            notification["read_at"] = now
            count += 1
        
        # データの保存
        if count > 0:
            self._save_data()
            logger.info(f"Marked {count} notifications as read for user {user_id}")
        
        return count
    
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        通知を削除
        
        Parameters
        ----------
        notification_id : str
            通知ID
        user_id : str
            ユーザーID
            
        Returns
        -------
        bool
            成功したかどうか
        """
        if user_id not in self._notifications:
            logger.warning(f"User {user_id} has no notifications")
            return False
        
        # 削除前の通知数
        initial_count = len(self._notifications[user_id])
        
        # 通知を削除
        self._notifications[user_id] = [
            n for n in self._notifications[user_id]
            if n.get("notification_id") != notification_id
        ]
        
        # 削除されたかどうか
        if len(self._notifications[user_id]) < initial_count:
            # データの保存
            self._save_data()
            
            logger.info(f"Notification {notification_id} deleted for user {user_id}")
            return True
        
        logger.warning(f"Notification {notification_id} not found for user {user_id}")
        return False
    
    def delete_all_notifications(self, user_id: str, event_type: str = None, 
                               read_only: bool = False) -> int:
        """
        通知を一括削除
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str, optional
            イベントタイプ（指定した場合はそのタイプのみ）, by default None
        read_only : bool, optional
            既読のみ削除するかどうか, by default False
            
        Returns
        -------
        int
            削除した通知の数
        """
        if user_id not in self._notifications:
            logger.warning(f"User {user_id} has no notifications")
            return 0
        
        # 削除前の通知数
        initial_count = len(self._notifications[user_id])
        
        # 削除条件に合わない通知を抽出
        self._notifications[user_id] = [
            n for n in self._notifications[user_id]
            if (event_type and n.get("event_type") != event_type) or
               (read_only and not n.get("read", False))
        ]
        
        # 削除された通知の数
        deleted_count = initial_count - len(self._notifications[user_id])
        
        # データの保存
        if deleted_count > 0:
            self._save_data()
            logger.info(f"Deleted {deleted_count} notifications for user {user_id}")
        
        return deleted_count
    
    def subscribe_to_event(self, user_id: str, event_type: str, channels: List[str] = None, 
                         filters: Dict[str, Any] = None, schedule: Dict[str, Any] = None) -> bool:
        """
        イベントを購読
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str
            イベントタイプ
        channels : List[str], optional
            通知チャネル, by default None
        filters : Dict[str, Any], optional
            イベントフィルター, by default None
        schedule : Dict[str, Any], optional
            通知スケジュール, by default None
            
        Returns
        -------
        bool
            成功したかどうか
        """
        # イベントタイプの初期化
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = {}
        
        # ユーザーの購読設定を作成
        subscription = {
            "channels": channels or ["app"],
            "filters": filters,
            "schedule": schedule,
            "subscribed_at": datetime.datetime.now().isoformat(),
            "muted": False
        }
        
        # 購読設定を保存
        self._subscriptions[event_type][user_id] = subscription
        
        # データの保存
        self._save_data()
        
        logger.info(f"User {user_id} subscribed to event type {event_type}")
        return True
    
    def unsubscribe_from_event(self, user_id: str, event_type: str) -> bool:
        """
        イベント購読を解除
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str
            イベントタイプ
            
        Returns
        -------
        bool
            成功したかどうか
        """
        if event_type not in self._subscriptions or user_id not in self._subscriptions[event_type]:
            logger.warning(f"User {user_id} is not subscribed to event type {event_type}")
            return False
        
        # ユーザーの購読を削除
        del self._subscriptions[event_type][user_id]
        
        # イベントタイプの購読者がいなくなった場合、イベントタイプも削除
        if not self._subscriptions[event_type]:
            del self._subscriptions[event_type]
        
        # データの保存
        self._save_data()
        
        logger.info(f"User {user_id} unsubscribed from event type {event_type}")
        return True
    
    def update_subscription(self, user_id: str, event_type: str, 
                         settings: Dict[str, Any]) -> bool:
        """
        購読設定を更新
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str
            イベントタイプ
        settings : Dict[str, Any]
            更新する設定
            
        Returns
        -------
        bool
            成功したかどうか
        """
        if event_type not in self._subscriptions or user_id not in self._subscriptions[event_type]:
            logger.warning(f"User {user_id} is not subscribed to event type {event_type}")
            return False
        
        # 現在の設定を取得
        subscription = self._subscriptions[event_type][user_id]
        
        # 設定を更新
        for key, value in settings.items():
            subscription[key] = value
        
        # 更新日時を設定
        subscription["updated_at"] = datetime.datetime.now().isoformat()
        
        # データの保存
        self._save_data()
        
        logger.info(f"Updated subscription settings for user {user_id} and event type {event_type}")
        return True
    
    def mute_event(self, user_id: str, event_type: str, muted: bool = True) -> bool:
        """
        イベントをミュート/ミュート解除
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str
            イベントタイプ
        muted : bool, optional
            ミュート状態, by default True
            
        Returns
        -------
        bool
            成功したかどうか
        """
        return self.update_subscription(user_id, event_type, {"muted": muted})
    
    def get_user_notifications(self, user_id: str, filters: Dict[str, Any] = None,
                            limit: int = 50, offset: int = 0,
                            unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        ユーザーの通知を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        filters : Dict[str, Any], optional
            フィルター条件, by default None
        limit : int, optional
            取得する最大数, by default 50
        offset : int, optional
            取得開始位置, by default 0
        unread_only : bool, optional
            未読のみ取得するかどうか, by default False
            
        Returns
        -------
        List[Dict[str, Any]]
            通知のリスト
        """
        if user_id not in self._notifications:
            return []
        
        # ユーザーの通知を取得
        notifications = self._notifications[user_id]
        
        # 未読フィルタリング
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        # フィルター条件の適用
        if filters:
            filtered_notifications = []
            for notification in notifications:
                match = True
                
                for key, value in filters.items():
                    # ネストされたフィールドに対応
                    if "." in key:
                        parts = key.split(".")
                        current = notification
                        for part in parts:
                            if isinstance(current, dict) and part in current:
                                current = current[part]
                            else:
                                current = None
                                break
                        
                        if current != value:
                            match = False
                            break
                    # 通常のフィールド
                    elif key not in notification or notification[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_notifications.append(notification)
            
            notifications = filtered_notifications
        
        # 時間順にソート
        sorted_notifications = sorted(
            notifications,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        # ページング
        paginated_notifications = sorted_notifications[offset:offset + limit]
        
        return paginated_notifications
    
    def get_unread_count(self, user_id: str, event_type: str = None) -> int:
        """
        未読通知の数を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        event_type : str, optional
            イベントタイプ（指定した場合はそのタイプのみ）, by default None
            
        Returns
        -------
        int
            未読通知の数
        """
        if user_id not in self._notifications:
            return 0
        
        # 未読通知をカウント
        count = 0
        for notification in self._notifications[user_id]:
            if notification.get("read", False):
                continue
            
            if event_type and notification.get("event_type") != event_type:
                continue
            
            count += 1
        
        return count
    
    def get_user_subscriptions(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        ユーザーの購読設定を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            イベントタイプごとの購読設定
        """
        subscriptions = {}
        
        for event_type, users in self._subscriptions.items():
            if user_id in users:
                subscriptions[event_type] = users[user_id]
        
        return subscriptions
    
    def register_channel(self, channel_name: str, channel_handler: BaseNotificationChannel) -> bool:
        """
        通知チャネルを登録
        
        Parameters
        ----------
        channel_name : str
            チャネル名
        channel_handler : BaseNotificationChannel
            チャネルハンドラ
            
        Returns
        -------
        bool
            成功したかどうか
        """
        if not isinstance(channel_handler, BaseNotificationChannel):
            logger.error(f"Channel handler must be an instance of BaseNotificationChannel")
            return False
        
        # チャネルを登録
        self._channels[channel_name] = channel_handler
        
        logger.info(f"Registered notification channel: {channel_name}")
        return True
    
    def clean_old_notifications(self, max_age_days: int = 30) -> int:
        """
        古い通知を削除
        
        Parameters
        ----------
        max_age_days : int, optional
            保持する最大日数, by default 30
            
        Returns
        -------
        int
            削除された通知の数
        """
        # 基準日時
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=max_age_days)).isoformat()
        
        # 削除した通知の数
        deleted_count = 0
        
        # 各ユーザーの通知をクリーンアップ
        for user_id in list(self._notifications.keys()):
            initial_count = len(self._notifications[user_id])
            
            # 基準日より新しい通知だけを残す
            self._notifications[user_id] = [
                n for n in self._notifications[user_id]
                if n.get("created_at", "") > cutoff_date
            ]
            
            # 削除した数を加算
            current_deleted = initial_count - len(self._notifications[user_id])
            deleted_count += current_deleted
            
            # 通知が空になったらユーザーエントリを削除
            if not self._notifications[user_id]:
                del self._notifications[user_id]
        
        # データの保存
        if deleted_count > 0:
            self._save_data()
            logger.info(f"Cleaned up {deleted_count} old notifications")
        
        return deleted_count
