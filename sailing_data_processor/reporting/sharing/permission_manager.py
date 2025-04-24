# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.sharing.permission_manager

レポート・データに対するアクセス権限を管理するモジュール
"""

import datetime
import uuid
import json
import logging
from typing import Dict, List, Optional, Union, Any, Set

# ロガーの設定
logger = logging.getLogger(__name__)

class Permission:
    """権限の定義クラス"""
    NONE = "none"
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    MANAGE = "manage"
    
    # 権限の階層関係（上位権限は下位権限を含む）
    HIERARCHY = {
        MANAGE: {VIEW, COMMENT, EDIT, MANAGE},
        EDIT: {VIEW, COMMENT, EDIT},
        COMMENT: {VIEW, COMMENT},
        VIEW: {VIEW},
        NONE: set()
    }
    
    @classmethod
    def includes(cls, higher_permission: str, lower_permission: str) -> bool:
        """
        higher_permission が lower_permission を含んでいるかどうかを判定
        
        Parameters
        ----------
        higher_permission : str
            上位権限
        lower_permission : str
            下位権限
            
        Returns
        -------
        bool
            higher_permission が lower_permission を含んでいるかどうか
        """
        if higher_permission not in cls.HIERARCHY or lower_permission not in cls.HIERARCHY:
            return False
        
        return lower_permission in cls.HIERARCHY[higher_permission]
    
    @classmethod
    def get_highest(cls, permissions: List[str]) -> str:
        """
        複数の権限から最も高い権限を取得
        
        Parameters
        ----------
        permissions : List[str]
            権限のリスト
            
        Returns
        -------
        str
            最も高い権限
        """
        if not permissions:
            return cls.NONE
        
        priority = {
            cls.MANAGE: 4,
            cls.EDIT: 3,
            cls.COMMENT: 2,
            cls.VIEW: 1,
            cls.NONE: 0
        }
        
        highest = cls.NONE
        highest_priority = 0
        
        for perm in permissions:
            if perm in priority and priority[perm] > highest_priority:
                highest = perm
                highest_priority = priority[perm]
        
        return highest

class PermissionManager:
    """
    権限管理クラス
    
    アクセス権限の管理、検証を行います。
    """
    
    def __init__(self, storage_manager=None, auth_manager=None):
        """
        初期化
        
        Parameters
        ----------
        storage_manager : object, optional
            ストレージ管理オブジェクト, by default None
        auth_manager : object, optional
            認証管理オブジェクト, by default None
        """
        self.storage_manager = storage_manager
        self.auth_manager = auth_manager
        
        # 権限マッピング: {resource_id: {section_id: {role_id: permission}}}
        self._permissions = {}
        
        # ロールマッピング: {user_id: {resource_id: [role_ids]}}
        self._user_roles = {}
        
        # ロール定義: {role_id: {name, description, resource_id}}
        self._roles = {}
        
        # グループ定義: {group_id: {name, description, members: [user_ids]}}
        self._groups = {}
        
        # 監査ログ
        self._audit_log = []
        
        logger.info("PermissionManager initialized")
    
    def define_role(self, name: str, description: str = None, resource_id: str = None) -> str:
        """
        ロールを定義
        
        Parameters
        ----------
        name : str
            ロール名
        description : str, optional
            説明, by default None
        resource_id : str, optional
            リソースID（特定リソース用のロールの場合）, by default None
            
        Returns
        -------
        str
            ロールID
        """
        role_id = str(uuid.uuid4())
        
        role = {
            "role_id": role_id,
            "name": name,
            "description": description,
            "resource_id": resource_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        self._roles[role_id] = role
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_role(role_id, role)
                logger.info(f"Role {role_id} saved to storage")
            except Exception as e:
                logger.error(f"Failed to save role: {str(e)}")
        
        # 監査ログに記録
        self._record_audit_log("role_defined", role)
        
        logger.info(f"Role '{name}' defined with ID {role_id}")
        return role_id
    
    def assign_role_to_user(self, user_id: str, role_id: str, resource_id: str = None) -> bool:
        """
        ユーザーにロールを割り当て
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        role_id : str
            ロールID
        resource_id : str, optional
            リソースID（特定リソース用のロールの場合）, by default None
            
        Returns
        -------
        bool
            割り当て成功したかどうか
        """
        # ロールの存在チェック
        if role_id not in self._roles:
            logger.warning(f"Role {role_id} not found")
            return False
        
        role = self._roles[role_id]
        
        # リソース固有ロールの場合、resource_idの整合性をチェック
        if role.get("resource_id") and role.get("resource_id") != resource_id:
            logger.warning(f"Role {role_id} is specific to resource {role.get('resource_id')}, not {resource_id}")
            return False
        
        # ユーザーロールマップを初期化
        if user_id not in self._user_roles:
            self._user_roles[user_id] = {}
        
        # リソースIDを決定（ロールに紐づくか、指定されたもの）
        target_resource_id = role.get("resource_id") or resource_id
        
        if target_resource_id:
            if target_resource_id not in self._user_roles[user_id]:
                self._user_roles[user_id][target_resource_id] = []
            
            if role_id not in self._user_roles[user_id][target_resource_id]:
                self._user_roles[user_id][target_resource_id].append(role_id)
        else:
            # グローバルロール（全リソースに適用）
            if "global" not in self._user_roles[user_id]:
                self._user_roles[user_id]["global"] = []
            
            if role_id not in self._user_roles[user_id]["global"]:
                self._user_roles[user_id]["global"].append(role_id)
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_user_roles(user_id, self._user_roles[user_id])
                logger.info(f"User roles for {user_id} saved to storage")
            except Exception as e:
                logger.error(f"Failed to save user roles: {str(e)}")
        
        # 監査ログに記録
        self._record_audit_log("role_assigned", {
            "user_id": user_id,
            "role_id": role_id,
            "resource_id": target_resource_id
        })
        
        logger.info(f"Role {role_id} assigned to user {user_id} for resource {target_resource_id or 'global'}")
        return True
    
    def create_group(self, name: str, description: str = None, members: List[str] = None) -> str:
        """
        グループを作成
        
        Parameters
        ----------
        name : str
            グループ名
        description : str, optional
            説明, by default None
        members : List[str], optional
            メンバーのユーザーIDリスト, by default None
            
        Returns
        -------
        str
            グループID
        """
        group_id = str(uuid.uuid4())
        
        group = {
            "group_id": group_id,
            "name": name,
            "description": description,
            "members": members or [],
            "created_at": datetime.datetime.now().isoformat()
        }
        
        self._groups[group_id] = group
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_group(group_id, group)
                logger.info(f"Group {group_id} saved to storage")
            except Exception as e:
                logger.error(f"Failed to save group: {str(e)}")
        
        # 監査ログに記録
        self._record_audit_log("group_created", group)
        
        logger.info(f"Group '{name}' created with ID {group_id}")
        return group_id
    
    def add_user_to_group(self, user_id: str, group_id: str) -> bool:
        """
        ユーザーをグループに追加
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        group_id : str
            グループID
            
        Returns
        -------
        bool
            追加成功したかどうか
        """
        # グループの存在チェック
        if group_id not in self._groups:
            logger.warning(f"Group {group_id} not found")
            return False
        
        # すでにメンバーの場合
        if user_id in self._groups[group_id]["members"]:
            logger.info(f"User {user_id} is already a member of group {group_id}")
            return True
        
        # メンバー追加
        self._groups[group_id]["members"].append(user_id)
        self._groups[group_id]["updated_at"] = datetime.datetime.now().isoformat()
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_group(group_id, self._groups[group_id])
                logger.info(f"Group {group_id} updated in storage")
            except Exception as e:
                logger.error(f"Failed to update group: {str(e)}")
        
        # 監査ログに記録
        self._record_audit_log("user_added_to_group", {
            "user_id": user_id,
            "group_id": group_id
        })
        
        logger.info(f"User {user_id} added to group {group_id}")
        return True
    
    def remove_user_from_group(self, user_id: str, group_id: str) -> bool:
        """
        ユーザーをグループから削除
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        group_id : str
            グループID
            
        Returns
        -------
        bool
            削除成功したかどうか
        """
        # グループの存在チェック
        if group_id not in self._groups:
            logger.warning(f"Group {group_id} not found")
            return False
        
        # メンバーでない場合
        if user_id not in self._groups[group_id]["members"]:
            logger.info(f"User {user_id} is not a member of group {group_id}")
            return True
        
        # メンバー削除
        self._groups[group_id]["members"].remove(user_id)
        self._groups[group_id]["updated_at"] = datetime.datetime.now().isoformat()
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_group(group_id, self._groups[group_id])
                logger.info(f"Group {group_id} updated in storage")
            except Exception as e:
                logger.error(f"Failed to update group: {str(e)}")
        
        # 監査ログに記録
        self._record_audit_log("user_removed_from_group", {
            "user_id": user_id,
            "group_id": group_id
        })
        
        logger.info(f"User {user_id} removed from group {group_id}")
        return True
    
    def set_permission(self, resource_id: str, role_id: str, permission: str, section_id: str = None) -> bool:
        """
        リソースに対するロールの権限を設定
        
        Parameters
        ----------
        resource_id : str
            リソースID
        role_id : str
            ロールID
        permission : str
            権限 (Permission.VIEW, Permission.COMMENT, Permission.EDIT, Permission.MANAGE)
        section_id : str, optional
            セクションID（リソース内の特定部分）, by default None
            
        Returns
        -------
        bool
            設定成功したかどうか
        """
        # 権限の妥当性チェック
        if permission not in Permission.HIERARCHY:
            logger.warning(f"Invalid permission: {permission}")
            return False
        
        # ロールの存在チェック
        if role_id not in self._roles:
            logger.warning(f"Role {role_id} not found")
            return False
        
        # リソースの権限マップを初期化
        if resource_id not in self._permissions:
            self._permissions[resource_id] = {}
        
        section_key = section_id or "default"
        
        if section_key not in self._permissions[resource_id]:
            self._permissions[resource_id][section_key] = {}
        
        # 権限設定
        self._permissions[resource_id][section_key][role_id] = permission
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_permissions(resource_id, self._permissions[resource_id])
                logger.info(f"Permissions for resource {resource_id} saved to storage")
            except Exception as e:
                logger.error(f"Failed to save permissions: {str(e)}")
        
        # 監査ログに記録
        self._record_audit_log("permission_set", {
            "resource_id": resource_id,
            "section_id": section_id,
            "role_id": role_id,
            "permission": permission
        })
        
        logger.info(f"Permission {permission} set for role {role_id} on resource {resource_id}, section {section_id or 'default'}")
        return True
    
    def get_user_permission(self, user_id: str, resource_id: str, section_id: str = None) -> str:
        """
        ユーザーのリソースに対する権限を取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        resource_id : str
            リソースID
        section_id : str, optional
            セクションID, by default None
            
        Returns
        -------
        str
            権限
        """
        # デフォルトの権限
        result = Permission.NONE
        user_permissions = []
        
        section_key = section_id or "default"
        
        # ユーザーのロールを取得
        user_resource_roles = []
        
        # リソース固有のロール
        if user_id in self._user_roles and resource_id in self._user_roles[user_id]:
            user_resource_roles.extend(self._user_roles[user_id][resource_id])
        
        # グローバルロール
        if user_id in self._user_roles and "global" in self._user_roles[user_id]:
            user_resource_roles.extend(self._user_roles[user_id]["global"])
        
        # グループのロールを取得
        user_groups = []
        for group_id, group in self._groups.items():
            if user_id in group["members"]:
                user_groups.append(group_id)
        
        # ロールの権限を取得
        if resource_id in self._permissions:
            # 該当セクションの権限
            if section_key in self._permissions[resource_id]:
                for role_id, permission in self._permissions[resource_id][section_key].items():
                    if role_id in user_resource_roles:
                        user_permissions.append(permission)
            
            # デフォルトセクションの権限（section_keyがデフォルトでない場合）
            if section_key != "default" and "default" in self._permissions[resource_id]:
                for role_id, permission in self._permissions[resource_id]["default"].items():
                    if role_id in user_resource_roles:
                        user_permissions.append(permission)
        
        # 最高権限を取得
        if user_permissions:
            result = Permission.get_highest(user_permissions)
        
        return result
    
    def check_permission(self, user_id: str, resource_id: str, required_permission: str, section_id: str = None) -> bool:
        """
        ユーザーが特定の権限を持っているかチェック
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        resource_id : str
            リソースID
        required_permission : str
            必要な権限
        section_id : str, optional
            セクションID, by default None
            
        Returns
        -------
        bool
            権限を持っているかどうか
        """
        user_permission = self.get_user_permission(user_id, resource_id, section_id)
        return Permission.includes(user_permission, required_permission)
    
    def get_resources_with_permission(self, user_id: str, permission: str) -> List[Dict[str, Any]]:
        """
        ユーザーが特定の権限を持つリソースを取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        permission : str
            権限
            
        Returns
        -------
        List[Dict[str, Any]]
            リソース情報のリスト
        """
        result = []
        
        # ユーザーのロールを取得
        user_roles = {}
        
        # リソース固有のロール
        if user_id in self._user_roles:
            for resource_id, roles in self._user_roles[user_id].items():
                if resource_id != "global":
                    if resource_id not in user_roles:
                        user_roles[resource_id] = []
                    user_roles[resource_id].extend(roles)
            
            # グローバルロール（全リソースに適用）
            if "global" in self._user_roles[user_id]:
                global_roles = self._user_roles[user_id]["global"]
                for resource_id in self._permissions:
                    if resource_id not in user_roles:
                        user_roles[resource_id] = []
                    user_roles[resource_id].extend(global_roles)
        
        # 権限チェック
        for resource_id, sections in self._permissions.items():
            resource_permissions = []
            
            # リソースのロールがない場合はスキップ
            if resource_id not in user_roles:
                continue
            
            # デフォルトセクションの権限
            if "default" in sections:
                for role_id, perm in sections["default"].items():
                    if role_id in user_roles[resource_id]:
                        resource_permissions.append(perm)
            
            # 最高権限を取得
            if resource_permissions:
                highest_permission = Permission.get_highest(resource_permissions)
                if Permission.includes(highest_permission, permission):
                    result.append({
                        "resource_id": resource_id,
                        "permission": highest_permission
                    })
        
        return result
    
    def _record_audit_log(self, action: str, data: Dict[str, Any]) -> None:
        """
        監査ログに記録
        
        Parameters
        ----------
        action : str
            実行されたアクション
        data : Dict[str, Any]
            関連データ
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "data": data
        }
        
        self._audit_log.append(log_entry)
        
        # ストレージマネージャーがある場合は永続化
        if self.storage_manager:
            try:
                self.storage_manager.save_audit_log(log_entry)
            except Exception as e:
                logger.error(f"Failed to save audit log: {str(e)}")
