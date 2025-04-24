# -*- coding: utf-8 -*-
"""
sailing_data_processor.sharing.link_manager

共有リンク管理機能を提供するモジュール
"""

import uuid
import datetime
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class LinkManager:
    """
    共有リンク管理クラス
    
    セッションやプロジェクト、エクスポート結果の共有リンクを管理します。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初期化
        
        Parameters
        ----------
        storage_path : Optional[str], optional
            リンク情報を保存するディレクトリパス, by default None
            Noneの場合はデフォルトの保存先を使用
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # デフォルトの保存先
            self.storage_path = Path.home() / ".sailing_analyzer" / "shared_links"
        
        # 保存先ディレクトリの作成
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # リンク情報ファイルパス
        self.links_file = self.storage_path / "links.json"
        
        # 一時共有ファイル保存ディレクトリ
        self.shared_files_dir = self.storage_path / "files"
        self.shared_files_dir.mkdir(exist_ok=True)
        
        # リンク情報の読み込み
        self.links = self._load_links()
    
    def _load_links(self) -> Dict[str, Dict[str, Any]]:
        """
        保存されたリンク情報の読み込み
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            リンク情報の辞書
        """
        if not self.links_file.exists():
            return {}
        
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"リンク情報の読み込みに失敗しました: {e}")
            return {}
    
    def _save_links(self) -> bool:
        """
        リンク情報の保存
        
        Returns
        -------
        bool
            保存に成功した場合True
        """
        try:
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(self.links, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"リンク情報の保存に失敗しました: {e}")
            return False
    
    def create_link(self, item_id: str, item_type: str, 
                   expiration_days: int = 7, 
                   access_restriction: Dict[str, Any] = None,
                   file_path: Optional[str] = None) -> Optional[str]:
        """
        共有リンクの作成
        
        Parameters
        ----------
        item_id : str
            共有するアイテムのID
        item_type : str
            アイテムの種類（'session', 'project', 'report', 'export'など）
        expiration_days : int, optional
            リンクの有効期間（日数）, by default 7
        access_restriction : Dict[str, Any], optional
            アクセス制限の設定, by default None
        file_path : Optional[str], optional
            共有するファイルのパス, by default None
            
        Returns
        -------
        Optional[str]
            生成されたリンクID (失敗した場合はNone)
        """
        link_id = str(uuid.uuid4())
        
        # 有効期限の設定
        expiration_date = datetime.datetime.now() + datetime.timedelta(days=expiration_days)
        
        # 共有ファイルの処理
        shared_file_path = None
        if file_path:
            try:
                # 共有ファイルを保存先にコピー
                file_name = os.path.basename(file_path)
                target_file = self.shared_files_dir / f"{link_id}_{file_name}"
                
                # ファイルコピー
                with open(file_path, 'rb') as src_file, open(target_file, 'wb') as dest_file:
                    dest_file.write(src_file.read())
                
                shared_file_path = str(target_file.relative_to(self.storage_path))
            except Exception as e:
                print(f"ファイルのコピーに失敗しました: {e}")
                return None
        
        # リンク情報の保存
        self.links[link_id] = {
            'item_id': item_id,
            'item_type': item_type,
            'created_at': datetime.datetime.now().isoformat(),
            'expires_at': expiration_date.isoformat(),
            'access_restriction': access_restriction or {},
            'visit_count': 0,
            'shared_file_path': shared_file_path,
            'creator': os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
        }
        
        if self._save_links():
            return link_id
        return None
    
    def get_link_info(self, link_id: str) -> Optional[Dict[str, Any]]:
        """
        リンク情報の取得
        
        Parameters
        ----------
        link_id : str
            リンクID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            リンク情報 (存在しない場合やリンクが期限切れの場合はNone)
        """
        if link_id not in self.links:
            return None
            
        link_info = self.links[link_id].copy()
        
        # 有効期限のチェック
        if datetime.datetime.now() > datetime.datetime.fromisoformat(link_info['expires_at']):
            # 期限切れのリンクは削除
            self.delete_link(link_id)
            return None
            
        # アクセスカウントの更新
        self.links[link_id]['visit_count'] += 1
        self._save_links()
        
        return link_info
    
    def delete_link(self, link_id: str) -> bool:
        """
        リンクの削除
        
        Parameters
        ----------
        link_id : str
            削除するリンクID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if link_id not in self.links:
            return False
        
        # 共有ファイルがある場合は削除
        link_info = self.links[link_id]
        if link_info.get('shared_file_path'):
            try:
                file_path = self.storage_path / link_info['shared_file_path']
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"共有ファイルの削除に失敗しました: {e}")
        
        # リンク情報の削除
        del self.links[link_id]
        return self._save_links()
    
    def update_link(self, link_id: str, updates: Dict[str, Any]) -> bool:
        """
        リンク情報の更新
        
        Parameters
        ----------
        link_id : str
            更新するリンクID
        updates : Dict[str, Any]
            更新内容
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        if link_id not in self.links:
            return False
            
        # 更新対象フィールドのチェックと更新
        allowed_fields = ['expires_at', 'access_restriction']
        for field, value in updates.items():
            if field in allowed_fields:
                self.links[link_id][field] = value
                
        return self._save_links()
    
    def get_links_by_item(self, item_id: str, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        アイテムに関連するリンクの取得
        
        Parameters
        ----------
        item_id : str
            アイテムID
        item_type : Optional[str], optional
            アイテムの種類, by default None (すべての種類)
            
        Returns
        -------
        List[Dict[str, Any]]
            リンク情報のリスト
        """
        result = []
        
        for link_id, link_info in self.links.items():
            if link_info['item_id'] == item_id:
                if item_type is None or link_info['item_type'] == item_type:
                    # 有効期限のチェック
                    if datetime.datetime.now() <= datetime.datetime.fromisoformat(link_info['expires_at']):
                        result.append({
                            'link_id': link_id,
                            **link_info
                        })
                    
        return result
    
    def clean_expired_links(self) -> int:
        """
        期限切れリンクの一括削除
        
        Returns
        -------
        int
            削除したリンクの数
        """
        now = datetime.datetime.now()
        expired_links = []
        
        for link_id, link_info in self.links.items():
            if now > datetime.datetime.fromisoformat(link_info['expires_at']):
                # 共有ファイルがある場合は削除
                if link_info.get('shared_file_path'):
                    try:
                        file_path = self.storage_path / link_info['shared_file_path']
                        if file_path.exists():
                            file_path.unlink()
                    except Exception as e:
                        print(f"共有ファイルの削除に失敗しました: {e}")
                
                expired_links.append(link_id)
                
        for link_id in expired_links:
            del self.links[link_id]
            
        if expired_links:
            self._save_links()
            
        return len(expired_links)
    
    def get_shared_file_path(self, link_id: str) -> Optional[str]:
        """
        共有ファイルの実際のパスを取得
        
        Parameters
        ----------
        link_id : str
            リンクID
            
        Returns
        -------
        Optional[str]
            共有ファイルのパス (ファイルが存在しない場合はNone)
        """
        link_info = self.get_link_info(link_id)
        if not link_info or not link_info.get('shared_file_path'):
            return None
        
        file_path = self.storage_path / link_info['shared_file_path']
        return str(file_path) if file_path.exists() else None
    
    def extend_link_expiration(self, link_id: str, days: int) -> bool:
        """
        リンクの有効期限を延長
        
        Parameters
        ----------
        link_id : str
            リンクID
        days : int
            延長する日数
            
        Returns
        -------
        bool
            延長に成功した場合True
        """
        if link_id not in self.links:
            return False
        
        try:
            # 現在の有効期限を取得
            current_expiry = datetime.datetime.fromisoformat(self.links[link_id]['expires_at'])
            
            # 有効期限を延長
            new_expiry = current_expiry + datetime.timedelta(days=days)
            self.links[link_id]['expires_at'] = new_expiry.isoformat()
            
            return self._save_links()
        except Exception as e:
            print(f"有効期限の延長に失敗しました: {e}")
            return False
    
    def get_all_active_links(self) -> List[Dict[str, Any]]:
        """
        すべての有効なリンクを取得
        
        Returns
        -------
        List[Dict[str, Any]]
            有効なリンク情報のリスト
        """
        now = datetime.datetime.now()
        return [
            {'link_id': link_id, **link_info}
            for link_id, link_info in self.links.items()
            if now <= datetime.datetime.fromisoformat(link_info['expires_at'])
        ]
    
    def get_link_count_by_type(self) -> Dict[str, int]:
        """
        種類ごとのリンク数を取得
        
        Returns
        -------
        Dict[str, int]
            種類ごとのリンク数
        """
        counts = {}
        now = datetime.datetime.now()
        
        for link_info in self.links.values():
            # 期限切れのリンクはカウントしない
            if now > datetime.datetime.fromisoformat(link_info['expires_at']):
                continue
            
            item_type = link_info['item_type']
            if item_type not in counts:
                counts[item_type] = 0
            counts[item_type] += 1
        
        return counts
