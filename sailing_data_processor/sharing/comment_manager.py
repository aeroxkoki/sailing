"""
sailing_data_processor.sharing.comment_manager

セッション結果へのコメント機能を提供するモジュール
"""

import uuid
import datetime
import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class Comment:
    """
    セッションやプロジェクトへのコメントを表すクラス
    
    Parameters
    ----------
    comment_id : str
        コメントID
    content : str
        コメント内容
    user_id : str
        コメント投稿者のユーザーID
    user_name : str
        コメント投稿者の表示名
    parent_id : Optional[str], optional
        親コメントのID (返信の場合), by default None
    """
    
    def __init__(self, comment_id: str, content: str, user_id: str, user_name: str, 
                parent_id: Optional[str] = None):
        """初期化"""
        self.comment_id = comment_id
        self.content = content
        self.user_id = user_id
        self.user_name = user_name
        self.parent_id = parent_id
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
        self.deleted = False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            'comment_id': self.comment_id,
            'content': self.content,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'parent_id': self.parent_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deleted': self.deleted
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """辞書からインスタンスを作成"""
        comment = cls(
            comment_id=data['comment_id'],
            content=data['content'],
            user_id=data['user_id'],
            user_name=data['user_name'],
            parent_id=data.get('parent_id')
        )
        comment.created_at = data.get('created_at', comment.created_at)
        comment.updated_at = data.get('updated_at', comment.updated_at)
        comment.deleted = data.get('deleted', False)
        return comment


class PointComment(Comment):
    """
    特定の戦略ポイントに対するコメントを表すクラス
    
    Parameters
    ----------
    comment_id : str
        コメントID
    content : str
        コメント内容
    user_id : str
        コメント投稿者のユーザーID
    user_name : str
        コメント投稿者の表示名
    point_id : str
        戦略ポイントのID
    timestamp : Optional[str], optional
        タイムスタンプ, by default None
    lat : Optional[float], optional
        緯度, by default None
    lon : Optional[float], optional
        経度, by default None
    parent_id : Optional[str], optional
        親コメントのID (返信の場合), by default None
    """
    
    def __init__(self, comment_id: str, content: str, user_id: str, user_name: str, 
                point_id: str, timestamp: Optional[str] = None,
                lat: Optional[float] = None, lon: Optional[float] = None,
                parent_id: Optional[str] = None):
        """初期化"""
        super().__init__(comment_id, content, user_id, user_name, parent_id)
        self.point_id = point_id
        self.timestamp = timestamp
        self.lat = lat
        self.lon = lon
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        data = super().to_dict()
        data.update({
            'point_id': self.point_id,
            'timestamp': self.timestamp,
            'lat': self.lat,
            'lon': self.lon
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointComment':
        """辞書からインスタンスを作成"""
        comment = cls(
            comment_id=data['comment_id'],
            content=data['content'],
            user_id=data['user_id'],
            user_name=data['user_name'],
            point_id=data['point_id'],
            timestamp=data.get('timestamp'),
            lat=data.get('lat'),
            lon=data.get('lon'),
            parent_id=data.get('parent_id')
        )
        comment.created_at = data.get('created_at', comment.created_at)
        comment.updated_at = data.get('updated_at', comment.updated_at)
        comment.deleted = data.get('deleted', False)
        return comment


class CommentManager:
    """
    コメント管理クラス
    
    セッション、プロジェクト、戦略ポイントに対するコメントを管理します。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初期化
        
        Parameters
        ----------
        storage_path : Optional[str], optional
            コメント情報を保存するディレクトリパス, by default None
            Noneの場合はデフォルトの保存先を使用
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # デフォルトの保存先
            self.storage_path = Path.home() / ".sailing_analyzer" / "comments"
        
        # 保存先ディレクトリの作成
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # コメントの辞書
        # item_id -> item_type -> コメントリスト
        self.comments: Dict[str, Dict[str, List[Union[Comment, PointComment]]]] = {}
        
        # コメント情報の読み込み
        self._load_comments()
    
    def _load_comments(self) -> None:
        """保存されたコメント情報を読み込む"""
        comments_dir = self.storage_path
        
        try:
            # コメントファイルを検索
            for comment_file in comments_dir.glob("*.json"):
                try:
                    with open(comment_file, 'r', encoding='utf-8') as f:
                        item_comments = json.load(f)
                    
                    # ファイル名から item_id を取得
                    item_id = comment_file.stem
                    
                    # コメントデータを変換
                    item_type_comments = {}
                    for item_type, comments_data in item_comments.items():
                        comments_list = []
                        for comment_data in comments_data:
                            if 'point_id' in comment_data:
                                comment = PointComment.from_dict(comment_data)
                            else:
                                comment = Comment.from_dict(comment_data)
                            comments_list.append(comment)
                        
                        item_type_comments[item_type] = comments_list
                    
                    self.comments[item_id] = item_type_comments
                    
                except Exception as e:
                    print(f"コメント情報の読み込みに失敗しました: {str(e)}")
        except Exception as e:
            print(f"コメントディレクトリの読み込みに失敗しました: {str(e)}")
    
    def _save_item_comments(self, item_id: str) -> bool:
        """
        特定のアイテムのコメント情報を保存
        
        Parameters
        ----------
        item_id : str
            アイテムID
            
        Returns
        -------
        bool
            保存に成功したかどうか
        """
        if item_id not in self.comments:
            return True  # 保存するものがないので成功
        
        comment_file = self.storage_path / f"{item_id}.json"
        
        try:
            # コメントデータを変換
            item_comments = {}
            for item_type, comments_list in self.comments[item_id].items():
                item_comments[item_type] = [comment.to_dict() for comment in comments_list]
            
            # ファイルに保存
            with open(comment_file, 'w', encoding='utf-8') as f:
                json.dump(item_comments, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"コメント情報の保存に失敗しました: {str(e)}")
            return False
    
    def add_comment(self, item_id: str, item_type: str, content: str, 
                   user_id: str, user_name: str,
                   parent_id: Optional[str] = None) -> Optional[Comment]:
        """
        コメントを追加
        
        Parameters
        ----------
        item_id : str
            コメント対象のアイテムID (セッションIDやプロジェクトID)
        item_type : str
            アイテムの種類 ('session', 'project', 'result' など)
        content : str
            コメント内容
        user_id : str
            ユーザーID
        user_name : str
            ユーザー表示名
        parent_id : Optional[str], optional
            親コメントのID (返信の場合), by default None
            
        Returns
        -------
        Optional[Comment]
            作成されたコメント (失敗した場合はNone)
        """
        # コメント構造を初期化
        if item_id not in self.comments:
            self.comments[item_id] = {}
        
        if item_type not in self.comments[item_id]:
            self.comments[item_id][item_type] = []
        
        # コメントIDを生成
        comment_id = str(uuid.uuid4())
        
        # コメントを作成
        comment = Comment(
            comment_id=comment_id,
            content=content,
            user_id=user_id,
            user_name=user_name,
            parent_id=parent_id
        )
        
        # コメントを追加
        self.comments[item_id][item_type].append(comment)
        
        # 変更を保存
        if self._save_item_comments(item_id):
            return comment
        return None
    
    def add_point_comment(self, item_id: str, item_type: str, content: str, 
                         user_id: str, user_name: str, point_id: str,
                         timestamp: Optional[str] = None,
                         lat: Optional[float] = None, lon: Optional[float] = None,
                         parent_id: Optional[str] = None) -> Optional[PointComment]:
        """
        戦略ポイントにコメントを追加
        
        Parameters
        ----------
        item_id : str
            コメント対象のアイテムID (セッションIDなど)
        item_type : str
            アイテムの種類 ('session' など)
        content : str
            コメント内容
        user_id : str
            ユーザーID
        user_name : str
            ユーザー表示名
        point_id : str
            戦略ポイントID
        timestamp : Optional[str], optional
            タイムスタンプ, by default None
        lat : Optional[float], optional
            緯度, by default None
        lon : Optional[float], optional
            経度, by default None
        parent_id : Optional[str], optional
            親コメントのID (返信の場合), by default None
            
        Returns
        -------
        Optional[PointComment]
            作成されたポイントコメント (失敗した場合はNone)
        """
        # コメント構造を初期化
        if item_id not in self.comments:
            self.comments[item_id] = {}
        
        if item_type not in self.comments[item_id]:
            self.comments[item_id][item_type] = []
        
        # コメントIDを生成
        comment_id = str(uuid.uuid4())
        
        # ポイントコメントを作成
        point_comment = PointComment(
            comment_id=comment_id,
            content=content,
            user_id=user_id,
            user_name=user_name,
            point_id=point_id,
            timestamp=timestamp,
            lat=lat,
            lon=lon,
            parent_id=parent_id
        )
        
        # コメントを追加
        self.comments[item_id][item_type].append(point_comment)
        
        # 変更を保存
        if self._save_item_comments(item_id):
            return point_comment
        return None
    
    def get_comments(self, item_id: str, item_type: Optional[str] = None) -> List[Union[Comment, PointComment]]:
        """
        アイテムのコメントを取得
        
        Parameters
        ----------
        item_id : str
            アイテムID
        item_type : Optional[str], optional
            アイテムの種類, by default None (すべての種類)
            
        Returns
        -------
        List[Union[Comment, PointComment]]
            コメントのリスト
        """
        if item_id not in self.comments:
            return []
        
        if item_type is not None:
            return self.comments[item_id].get(item_type, [])
        
        # すべてのタイプのコメントを結合
        all_comments = []
        for comments_list in self.comments[item_id].values():
            all_comments.extend(comments_list)
        
        # 作成日順に並べ替え
        all_comments.sort(key=lambda c: c.created_at)
        
        return all_comments
    
    def get_point_comments(self, item_id: str, point_id: str, item_type: str = 'session') -> List[PointComment]:
        """
        特定の戦略ポイントのコメントを取得
        
        Parameters
        ----------
        item_id : str
            アイテムID (セッションIDなど)
        point_id : str
            戦略ポイントID
        item_type : str, optional
            アイテムの種類, by default 'session'
            
        Returns
        -------
        List[PointComment]
            ポイントコメントのリスト
        """
        if item_id not in self.comments or item_type not in self.comments[item_id]:
            return []
        
        # 指定されたポイントに対するコメントをフィルタリング
        point_comments = []
        for comment in self.comments[item_id][item_type]:
            if isinstance(comment, PointComment) and comment.point_id == point_id:
                point_comments.append(comment)
        
        # 作成日順に並べ替え
        point_comments.sort(key=lambda c: c.created_at)
        
        return point_comments
    
    def update_comment(self, item_id: str, comment_id: str, content: str) -> bool:
        """
        コメントを更新
        
        Parameters
        ----------
        item_id : str
            アイテムID
        comment_id : str
            コメントID
        content : str
            新しいコメント内容
            
        Returns
        -------
        bool
            更新に成功したかどうか
        """
        if item_id not in self.comments:
            return False
        
        # 全てのタイプのコメントを検索
        for item_type, comments_list in self.comments[item_id].items():
            for i, comment in enumerate(comments_list):
                if comment.comment_id == comment_id:
                    # コメントを更新
                    self.comments[item_id][item_type][i].content = content
                    self.comments[item_id][item_type][i].updated_at = datetime.datetime.now().isoformat()
                    return self._save_item_comments(item_id)
        
        return False
    
    def delete_comment(self, item_id: str, comment_id: str, soft_delete: bool = True) -> bool:
        """
        コメントを削除
        
        Parameters
        ----------
        item_id : str
            アイテムID
        comment_id : str
            コメントID
        soft_delete : bool, optional
            論理削除するかどうか, by default True
            Trueの場合は内容を残したまま「削除済み」としてマーク
            Falseの場合は物理的に削除
            
        Returns
        -------
        bool
            削除に成功したかどうか
        """
        if item_id not in self.comments:
            return False
        
        # 全てのタイプのコメントを検索
        for item_type, comments_list in self.comments[item_id].items():
            for i, comment in enumerate(comments_list):
                if comment.comment_id == comment_id:
                    if soft_delete:
                        # 論理削除
                        self.comments[item_id][item_type][i].deleted = True
                        self.comments[item_id][item_type][i].updated_at = datetime.datetime.now().isoformat()
                    else:
                        # 物理削除
                        del self.comments[item_id][item_type][i]
                    
                    return self._save_item_comments(item_id)
        
        return False
    
    def get_comment_threads(self, item_id: str, item_type: Optional[str] = None) -> Dict[str, List[Union[Comment, PointComment]]]:
        """
        コメントのスレッド構造を取得
        
        Parameters
        ----------
        item_id : str
            アイテムID
        item_type : Optional[str], optional
            アイテムの種類, by default None (すべての種類)
            
        Returns
        -------
        Dict[str, List[Union[Comment, PointComment]]]
            親コメントID -> 返信のリスト の辞書
            親コメントIDがNoneのものはトップレベルコメント
        """
        comments = self.get_comments(item_id, item_type)
        
        threads = {"root": []}  # トップレベルコメント用
        
        # コメントをスレッド構造に整理
        for comment in comments:
            if comment.parent_id is None:
                threads["root"].append(comment)
            else:
                if comment.parent_id not in threads:
                    threads[comment.parent_id] = []
                threads[comment.parent_id].append(comment)
        
        return threads
    
    def get_recent_comments(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        最近のコメントを取得
        
        Parameters
        ----------
        n : int, optional
            取得するコメント数, by default 10
            
        Returns
        -------
        List[Dict[str, Any]]
            最近のコメント情報のリスト
        """
        all_comments = []
        
        # 全てのコメントを収集
        for item_id, item_comments in self.comments.items():
            for item_type, comments_list in item_comments.items():
                for comment in comments_list:
                    if not comment.deleted:  # 削除されていないコメントのみ
                        all_comments.append({
                            'comment': comment,
                            'item_id': item_id,
                            'item_type': item_type
                        })
        
        # 作成日時の降順でソート
        all_comments.sort(key=lambda x: x['comment'].created_at, reverse=True)
        
        # 指定数のコメントを取得
        recent_comments = all_comments[:n]
        
        # 結果をフォーマット
        result = []
        for comment_info in recent_comments:
            comment = comment_info['comment']
            result.append({
                'comment_id': comment.comment_id,
                'content': comment.content,
                'user_name': comment.user_name,
                'created_at': comment.created_at,
                'item_id': comment_info['item_id'],
                'item_type': comment_info['item_type'],
                'is_point_comment': isinstance(comment, PointComment)
            })
        
        return result
    
    def get_user_comments(self, user_id: str) -> List[Dict[str, Any]]:
        """
        特定ユーザーのコメントを取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
            
        Returns
        -------
        List[Dict[str, Any]]
            ユーザーのコメント情報のリスト
        """
        user_comments = []
        
        # 指定ユーザーのコメントを収集
        for item_id, item_comments in self.comments.items():
            for item_type, comments_list in item_comments.items():
                for comment in comments_list:
                    if comment.user_id == user_id and not comment.deleted:
                        user_comments.append({
                            'comment': comment,
                            'item_id': item_id,
                            'item_type': item_type
                        })
        
        # 作成日時の降順でソート
        user_comments.sort(key=lambda x: x['comment'].created_at, reverse=True)
        
        # 結果をフォーマット
        result = []
        for comment_info in user_comments:
            comment = comment_info['comment']
            result.append({
                'comment_id': comment.comment_id,
                'content': comment.content,
                'created_at': comment.created_at,
                'updated_at': comment.updated_at,
                'item_id': comment_info['item_id'],
                'item_type': comment_info['item_type'],
                'is_point_comment': isinstance(comment, PointComment),
                'parent_id': comment.parent_id
            })
        
        return result
