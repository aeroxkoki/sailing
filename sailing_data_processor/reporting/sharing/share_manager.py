# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.sharing.share_manager

レポートやデータの共有機能を管理するモジュール
"""

import uuid
import datetime
import logging
from typing import Dict, List, Optional, Union, Any, Set
import os
import json

# ロガーの設定
logger = logging.getLogger(__name__)

class ShareManager:
    """
    共有管理クラス
    
    レポートやデータの共有設定、権限管理、リンク生成を行います。
    """
    
    def __init__(self, storage_manager=None, auth_manager=None, permission_manager=None):
        """
        初期化
        
        Parameters
        ----------
        storage_manager : object, optional
            ストレージ管理オブジェクト, by default None
        auth_manager : object, optional
            認証管理オブジェクト, by default None
        permission_manager : object, optional
            権限管理オブジェクト, by default None
        """
        self.storage_manager = storage_manager
        self.auth_manager = auth_manager
        self.permission_manager = permission_manager
        
        # 共有設定ストレージ
        self._share_settings = {}  # {item_id: {settings}}
        
        # 共有リンク管理
        self._share_links = {}  # {link_id: {settings}}
        
        # 共有履歴
        self._share_history = {}  # {item_id: [history_entries]}
        
        # 保存データの読み込み
        self._load_data()
        
        logger.info("ShareManager initialized")
    
    def _load_data(self):
        """保存された共有設定データの読み込み"""
        if self.storage_manager:
            try:
                # 共有設定の読み込み
                share_settings = self.storage_manager.load_share_settings()
                if share_settings:
                    self._share_settings = share_settings
                    logger.info(f"Loaded {len(share_settings)} share settings")
                
                # 共有リンクの読み込み
                share_links = self.storage_manager.load_share_links()
                if share_links:
                    self._share_links = share_links
                    logger.info(f"Loaded {len(share_links)} share links")
                
                # 共有履歴の読み込み
                share_history = self.storage_manager.load_share_history()
                if share_history:
                    self._share_history = share_history
                    logger.info(f"Loaded share history for {len(share_history)} items")
            except Exception as e:
                logger.error(f"Failed to load share data: {str(e)}")
    
    def _save_data(self):
        """共有設定データの保存"""
        if self.storage_manager:
            try:
                # 共有設定の保存
                self.storage_manager.save_share_settings(self._share_settings)
                
                # 共有リンクの保存
                self.storage_manager.save_share_links(self._share_links)
                
                # 共有履歴の保存
                self.storage_manager.save_share_history(self._share_history)
                
                logger.info("Share data saved")
            except Exception as e:
                logger.error(f"Failed to save share data: {str(e)}")
    
    def share_item(self, item_id: str, user_id: str = None, group_id: str = None, 
                 permission: str = "view", expiration: datetime.datetime = None, 
                 access_limit: int = None, password: str = None, 
                 custom_settings: Dict[str, Any] = None) -> str:
        """
        アイテムを共有
        
        Parameters
        ----------
        item_id : str
            共有するアイテムのID
        user_id : str, optional
            共有するユーザーID
        group_id : str, optional
            共有するグループID
        permission : str, optional
            付与する権限 ("view", "edit", "manage"), by default "view"
        expiration : datetime.datetime, optional
            有効期限, by default None
        access_limit : int, optional
            アクセス回数制限, by default None
        password : str, optional
            保護パスワード, by default None
        custom_settings : Dict[str, Any], optional
            カスタム設定, by default None
            
        Returns
        -------
        str
            共有設定ID
        """
        # 引数の検証
        if not item_id:
            logger.error("Item ID is required")
            return None
        
        if not user_id and not group_id:
            logger.error("Either user_id or group_id must be specified")
            return None
        
        # 共有IDの生成
        share_id = str(uuid.uuid4())
        
        # タイムスタンプ
        now = datetime.datetime.now()
        
        # 共有設定の作成
        share_setting = {
            "share_id": share_id,
            "item_id": item_id,
            "user_id": user_id,
            "group_id": group_id,
            "permission": permission,
            "created_at": now.isoformat(),
            "created_by": self.auth_manager.get_current_user() if self.auth_manager else None,
            "access_count": 0
        }
        
        # 有効期限の設定
        if expiration:
            share_setting["expiration"] = expiration.isoformat()
        
        # アクセス回数制限の設定
        if access_limit:
            share_setting["access_limit"] = access_limit
        
        # パスワード保護の設定
        if password:
            share_setting["password"] = password  # 本番環境ではハッシュ化するべき
        
        # カスタム設定の追加
        if custom_settings:
            share_setting["custom_settings"] = custom_settings
        
        # 共有設定の保存
        if item_id not in self._share_settings:
            self._share_settings[item_id] = {}
        
        self._share_settings[item_id][share_id] = share_setting
        
        # 権限管理システムと連携
        if self.permission_manager:
            if user_id:
                self.permission_manager.grant_permission(user_id, item_id, permission)
            elif group_id:
                self.permission_manager.grant_group_permission(group_id, item_id, permission)
        
        # 共有履歴の記録
        self._record_share_history(item_id, "shared", share_setting)
        
        # データの保存
        self._save_data()
        
        logger.info(f"Item {item_id} shared with {user_id or group_id}, permission: {permission}")
        return share_id
    
    def generate_share_link(self, item_id: str, permission: str = "view", 
                         expiration_days: int = 7, access_limit: int = None, 
                         password: str = None, custom_settings: Dict[str, Any] = None) -> str:
        """
        共有リンクを生成
        
        Parameters
        ----------
        item_id : str
            共有するアイテムのID
        permission : str, optional
            付与する権限 ("view", "edit", "manage"), by default "view"
        expiration_days : int, optional
            有効期限（日数）, by default 7
        access_limit : int, optional
            アクセス回数制限, by default None
        password : str, optional
            保護パスワード, by default None
        custom_settings : Dict[str, Any], optional
            カスタム設定, by default None
            
        Returns
        -------
        str
            共有リンクID
        """
        # 引数の検証
        if not item_id:
            logger.error("Item ID is required")
            return None
        
        # リンクIDの生成
        link_id = str(uuid.uuid4())
        
        # タイムスタンプと有効期限の計算
        now = datetime.datetime.now()
        expiration = now + datetime.timedelta(days=expiration_days) if expiration_days else None
        
        # 共有リンク設定の作成
        link_setting = {
            "link_id": link_id,
            "item_id": item_id,
            "permission": permission,
            "created_at": now.isoformat(),
            "created_by": self.auth_manager.get_current_user() if self.auth_manager else None,
            "access_count": 0,
            "last_accessed": None
        }
        
        # 有効期限の設定
        if expiration:
            link_setting["expiration"] = expiration.isoformat()
        
        # アクセス回数制限の設定
        if access_limit:
            link_setting["access_limit"] = access_limit
        
        # パスワード保護の設定
        if password:
            link_setting["password"] = password  # 本番環境ではハッシュ化するべき
        
        # カスタム設定の追加
        if custom_settings:
            link_setting["custom_settings"] = custom_settings
        
        # 共有リンクの保存
        self._share_links[link_id] = link_setting
        
        # 共有履歴の記録
        self._record_share_history(item_id, "link_created", link_setting)
        
        # データの保存
        self._save_data()
        
        logger.info(f"Share link generated for item {item_id}, permission: {permission}")
        return link_id
    
    def get_share_link(self, link_id: str) -> Dict[str, Any]:
        """
        共有リンク情報を取得
        
        Parameters
        ----------
        link_id : str
            共有リンクID
            
        Returns
        -------
        Dict[str, Any]
            共有リンク設定情報
        """
        return self._share_links.get(link_id)
    
    def update_share_link_access(self, link_id: str) -> bool:
        """
        共有リンクのアクセス情報を更新
        
        Parameters
        ----------
        link_id : str
            共有リンクID
            
        Returns
        -------
        bool
            更新成功したかどうか
        """
        if link_id not in self._share_links:
            logger.warning(f"Share link {link_id} not found")
            return False
        
        # 現在の設定を取得
        link_setting = self._share_links[link_id]
        
        # アクセス回数の更新
        link_setting["access_count"] = link_setting.get("access_count", 0) + 1
        
        # 最終アクセス日時の更新
        link_setting["last_accessed"] = datetime.datetime.now().isoformat()
        
        # 共有履歴の記録
        self._record_share_history(link_setting["item_id"], "link_accessed", {
            "link_id": link_id,
            "access_count": link_setting["access_count"]
        })
        
        # アクセス制限の確認
        if "access_limit" in link_setting and link_setting["access_count"] >= link_setting["access_limit"]:
            # アクセス回数制限に達した場合は無効化
            link_setting["disabled"] = True
            link_setting["disabled_reason"] = "access_limit_reached"
            
            # 共有履歴の記録
            self._record_share_history(link_setting["item_id"], "link_disabled", {
                "link_id": link_id,
                "reason": "access_limit_reached"
            })
        
        # データの保存
        self._save_data()
        
        return True
    
    def is_link_valid(self, link_id: str, password: str = None) -> bool:
        """
        共有リンクが有効かどうかを確認
        
        Parameters
        ----------
        link_id : str
            共有リンクID
        password : str, optional
            パスワード, by default None
            
        Returns
        -------
        bool
            リンクが有効かどうか
        """
        if link_id not in self._share_links:
            logger.warning(f"Share link {link_id} not found")
            return False
        
        link_setting = self._share_links[link_id]
        
        # 無効化されているかチェック
        if link_setting.get("disabled", False):
            logger.info(f"Share link {link_id} is disabled: {link_setting.get('disabled_reason')}")
            return False
        
        # 有効期限チェック
        if "expiration" in link_setting:
            expiration = datetime.datetime.fromisoformat(link_setting["expiration"])
            if datetime.datetime.now() > expiration:
                # 有効期限切れの場合は無効化
                link_setting["disabled"] = True
                link_setting["disabled_reason"] = "expired"
                self._save_data()
                
                logger.info(f"Share link {link_id} has expired")
                return False
        
        # アクセス回数制限チェック
        if "access_limit" in link_setting and link_setting["access_count"] >= link_setting["access_limit"]:
            logger.info(f"Share link {link_id} has reached access limit")
            return False
        
        # パスワード保護チェック
        if "password" in link_setting and link_setting["password"]:
            if not password or password != link_setting["password"]:
                logger.info(f"Invalid password for share link {link_id}")
                return False
        
        return True
    
    def get_item_permissions(self, item_id: str, user_id: str = None) -> str:
        """
        アイテムに対するユーザーの権限を取得
        
        Parameters
        ----------
        item_id : str
            アイテムID
        user_id : str, optional
            ユーザーID, by default None
            
        Returns
        -------
        str
            権限レベル ("none", "view", "edit", "manage")
        """
        if not user_id:
            return "none"
        
        # 権限管理システムと連携している場合はそちらから取得
        if self.permission_manager:
            return self.permission_manager.get_permission(user_id, item_id)
        
        # 共有設定から権限を確認
        if item_id in self._share_settings:
            for share_id, setting in self._share_settings[item_id].items():
                if setting.get("user_id") == user_id:
                    # 有効期限チェック
                    if "expiration" in setting:
                        expiration = datetime.datetime.fromisoformat(setting["expiration"])
                        if datetime.datetime.now() > expiration:
                            continue
                    
                    return setting["permission"]
        
        return "none"
    
    def revoke_share(self, share_id: str) -> bool:
        """
        共有を取り消し
        
        Parameters
        ----------
        share_id : str
            共有設定ID
            
        Returns
        -------
        bool
            取り消し成功したかどうか
        """
        # 共有設定を検索
        for item_id, settings in self._share_settings.items():
            if share_id in settings:
                share_setting = settings[share_id]
                
                # 共有設定を削除
                del self._share_settings[item_id][share_id]
                
                # 共有履歴の記録
                self._record_share_history(item_id, "share_revoked", {
                    "share_id": share_id,
                    "user_id": share_setting.get("user_id"),
                    "group_id": share_setting.get("group_id")
                })
                
                # 権限管理システムと連携
                if self.permission_manager:
                    if "user_id" in share_setting and share_setting["user_id"]:
                        self.permission_manager.revoke_permission(
                            share_setting["user_id"], item_id
                        )
                    elif "group_id" in share_setting and share_setting["group_id"]:
                        self.permission_manager.revoke_group_permission(
                            share_setting["group_id"], item_id
                        )
                
                # データの保存
                self._save_data()
                
                logger.info(f"Share {share_id} revoked")
                return True
        
        logger.warning(f"Share {share_id} not found")
        return False
    
    def revoke_link(self, link_id: str) -> bool:
        """
        共有リンクを無効化
        
        Parameters
        ----------
        link_id : str
            共有リンクID
            
        Returns
        -------
        bool
            無効化成功したかどうか
        """
        if link_id not in self._share_links:
            logger.warning(f"Share link {link_id} not found")
            return False
        
        # リンク設定を取得
        link_setting = self._share_links[link_id]
        
        # リンクを無効化
        link_setting["disabled"] = True
        link_setting["disabled_reason"] = "manually_revoked"
        link_setting["disabled_at"] = datetime.datetime.now().isoformat()
        
        # 共有履歴の記録
        self._record_share_history(link_setting["item_id"], "link_revoked", {
            "link_id": link_id
        })
        
        # データの保存
        self._save_data()
        
        logger.info(f"Share link {link_id} revoked")
        return True
    
    def update_share_settings(self, share_id: str, settings: Dict[str, Any]) -> bool:
        """
        共有設定を更新
        
        Parameters
        ----------
        share_id : str
            共有設定ID
        settings : Dict[str, Any]
            更新する設定
            
        Returns
        -------
        bool
            更新成功したかどうか
        """
        # 共有設定を検索
        for item_id, item_settings in self._share_settings.items():
            if share_id in item_settings:
                share_setting = item_settings[share_id]
                
                # 更新前の設定を記録
                old_settings = share_setting.copy()
                
                # 設定を更新
                for key, value in settings.items():
                    # ユーザーIDとグループIDは変更不可
                    if key in ["share_id", "item_id", "created_at", "created_by"]:
                        continue
                    
                    # 特殊な形式の日付処理
                    if key == "expiration" and isinstance(value, datetime.datetime):
                        share_setting[key] = value.isoformat()
                    else:
                        share_setting[key] = value
                
                # 更新日時を設定
                share_setting["updated_at"] = datetime.datetime.now().isoformat()
                
                # 権限変更の場合は権限管理システムも更新
                if "permission" in settings and self.permission_manager:
                    if "user_id" in share_setting and share_setting["user_id"]:
                        self.permission_manager.update_permission(
                            share_setting["user_id"], item_id, settings["permission"]
                        )
                    elif "group_id" in share_setting and share_setting["group_id"]:
                        self.permission_manager.update_group_permission(
                            share_setting["group_id"], item_id, settings["permission"]
                        )
                
                # 共有履歴の記録
                self._record_share_history(item_id, "share_updated", {
                    "share_id": share_id,
                    "old_settings": old_settings,
                    "new_settings": share_setting
                })
                
                # データの保存
                self._save_data()
                
                logger.info(f"Share {share_id} settings updated")
                return True
        
        logger.warning(f"Share {share_id} not found")
        return False
    
    def update_link_settings(self, link_id: str, settings: Dict[str, Any]) -> bool:
        """
        共有リンク設定を更新
        
        Parameters
        ----------
        link_id : str
            共有リンクID
        settings : Dict[str, Any]
            更新する設定
            
        Returns
        -------
        bool
            更新成功したかどうか
        """
        if link_id not in self._share_links:
            logger.warning(f"Share link {link_id} not found")
            return False
        
        # リンク設定を取得
        link_setting = self._share_links[link_id]
        
        # 更新前の設定を記録
        old_settings = link_setting.copy()
        
        # 設定を更新
        for key, value in settings.items():
            # 変更不可のフィールド
            if key in ["link_id", "item_id", "created_at", "created_by"]:
                continue
            
            # 特殊な形式の日付処理
            if key == "expiration" and isinstance(value, datetime.datetime):
                link_setting[key] = value.isoformat()
            else:
                link_setting[key] = value
        
        # 更新日時を設定
        link_setting["updated_at"] = datetime.datetime.now().isoformat()
        
        # 共有履歴の記録
        self._record_share_history(link_setting["item_id"], "link_updated", {
            "link_id": link_id,
            "old_settings": old_settings,
            "new_settings": link_setting
        })
        
        # データの保存
        self._save_data()
        
        logger.info(f"Share link {link_id} settings updated")
        return True
    
    def extend_link_expiration(self, link_id: str, days: int) -> bool:
        """
        共有リンクの有効期限を延長
        
        Parameters
        ----------
        link_id : str
            共有リンクID
        days : int
            延長する日数
            
        Returns
        -------
        bool
            延長成功したかどうか
        """
        if link_id not in self._share_links:
            logger.warning(f"Share link {link_id} not found")
            return False
        
        # リンク設定を取得
        link_setting = self._share_links[link_id]
        
        # 現在の有効期限を取得
        if "expiration" in link_setting:
            current_expiration = datetime.datetime.fromisoformat(link_setting["expiration"])
        else:
            current_expiration = datetime.datetime.now()
        
        # 有効期限を延長
        new_expiration = current_expiration + datetime.timedelta(days=days)
        link_setting["expiration"] = new_expiration.isoformat()
        
        # 更新日時を設定
        link_setting["updated_at"] = datetime.datetime.now().isoformat()
        
        # 無効化されていた場合は復活
        if link_setting.get("disabled", False) and link_setting.get("disabled_reason") == "expired":
            link_setting["disabled"] = False
            link_setting.pop("disabled_reason", None)
            link_setting.pop("disabled_at", None)
        
        # 共有履歴の記録
        self._record_share_history(link_setting["item_id"], "link_extended", {
            "link_id": link_id,
            "old_expiration": current_expiration.isoformat(),
            "new_expiration": new_expiration.isoformat(),
            "extended_days": days
        })
        
        # データの保存
        self._save_data()
        
        logger.info(f"Share link {link_id} expiration extended by {days} days")
        return True
    
    def get_shared_items(self, user_id: str = None, group_id: str = None) -> List[Dict[str, Any]]:
        """
        ユーザーまたはグループに共有されているアイテムを取得
        
        Parameters
        ----------
        user_id : str, optional
            ユーザーID, by default None
        group_id : str, optional
            グループID, by default None
            
        Returns
        -------
        List[Dict[str, Any]]
            共有アイテム情報のリスト
        """
        if not user_id and not group_id:
            logger.error("Either user_id or group_id must be specified")
            return []
        
        shared_items = []
        
        # 権限管理システムと連携している場合はそちらから取得
        if self.permission_manager and user_id:
            return self.permission_manager.get_accessible_items(user_id)
        
        # 共有設定から取得
        for item_id, settings in self._share_settings.items():
            for share_id, setting in settings.items():
                if (user_id and setting.get("user_id") == user_id) or \
                   (group_id and setting.get("group_id") == group_id):
                    
                    # 有効期限チェック
                    if "expiration" in setting:
                        expiration = datetime.datetime.fromisoformat(setting["expiration"])
                        if datetime.datetime.now() > expiration:
                            continue
                    
                    shared_items.append({
                        "item_id": item_id,
                        "share_id": share_id,
                        "permission": setting["permission"],
                        "created_at": setting["created_at"]
                    })
        
        return shared_items
    
    def get_item_shares(self, item_id: str) -> List[Dict[str, Any]]:
        """
        アイテムの共有設定一覧を取得
        
        Parameters
        ----------
        item_id : str
            アイテムID
            
        Returns
        -------
        List[Dict[str, Any]]
            共有設定のリスト
        """
        if item_id not in self._share_settings:
            return []
        
        return list(self._share_settings[item_id].values())
    
    def get_active_links(self, item_id: str = None) -> List[Dict[str, Any]]:
        """
        有効な共有リンク一覧を取得
        
        Parameters
        ----------
        item_id : str, optional
            アイテムID, by default None
            
        Returns
        -------
        List[Dict[str, Any]]
            共有リンク設定のリスト
        """
        active_links = []
        
        for link_id, link in self._share_links.items():
            # 無効化されているリンクはスキップ
            if link.get("disabled", False):
                continue
            
            # 特定のアイテムIDが指定された場合はフィルタリング
            if item_id and link["item_id"] != item_id:
                continue
            
            # 有効期限チェック
            if "expiration" in link:
                expiration = datetime.datetime.fromisoformat(link["expiration"])
                if datetime.datetime.now() > expiration:
                    continue
            
            active_links.append(link)
        
        return active_links
    
    def get_item_share_history(self, item_id: str) -> List[Dict[str, Any]]:
        """
        アイテムの共有履歴を取得
        
        Parameters
        ----------
        item_id : str
            アイテムID
            
        Returns
        -------
        List[Dict[str, Any]]
            共有履歴のリスト
        """
        if item_id not in self._share_history:
            return []
        
        # 時間順にソート
        sorted_history = sorted(
            self._share_history[item_id],
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        return sorted_history
    
    def _record_share_history(self, item_id: str, action: str, details: Dict[str, Any]) -> None:
        """
        共有履歴を記録
        
        Parameters
        ----------
        item_id : str
            アイテムID
        action : str
            実行されたアクション
        details : Dict[str, Any]
            アクションの詳細
        """
        if not item_id:
            return
        
        # タイムスタンプ
        now = datetime.datetime.now()
        
        # 履歴エントリの作成
        history_entry = {
            "timestamp": now.isoformat(),
            "action": action,
            "details": details,
            "user_id": self.auth_manager.get_current_user() if self.auth_manager else None
        }
        
        # 履歴の初期化
        if item_id not in self._share_history:
            self._share_history[item_id] = []
        
        # 履歴に追加
        self._share_history[item_id].append(history_entry)
        
        logger.debug(f"Recorded share history for item {item_id}: {action}")
