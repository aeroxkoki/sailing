"""
ストレージインターフェースモジュール

このモジュールではデータ永続化のための抽象インターフェースを定義します。
様々なバックエンド（ブラウザストレージ、将来的なクラウドストレージなど）に
対応できるように設計されています。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class StorageInterface(ABC):
    """
    ストレージシステムの抽象基底クラス。
    
    このクラスは永続化ストレージのための基本操作を定義します。
    全てのストレージ実装はこのインターフェースを実装する必要があります。
    """
    
    @abstractmethod
    def save(self, key: str, data: Any) -> bool:
        """
        データをストレージに保存します。
        
        Args:
            key: データを識別するためのユニークキー
            data: 保存するデータ（JSON化可能なオブジェクト）
            
        Returns:
            bool: 保存操作が成功したかどうか
        """
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """
        ストレージからデータを読み込みます。
        
        Args:
            key: 読み込むデータのキー
            
        Returns:
            Any: 読み込んだデータ、キーが存在しない場合はNone
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        指定したキーのデータをストレージから削除します。
        
        Args:
            key: 削除するデータのキー
            
        Returns:
            bool: 削除操作が成功したかどうか
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        ストレージ内のキーを列挙します。
        
        Args:
            prefix: キーのプレフィックス（指定した場合はプレフィックスでフィルタリング）
            
        Returns:
            List[str]: キーのリスト
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        ストレージをクリアします。
        
        Returns:
            bool: クリア操作が成功したかどうか
        """
        pass
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """
        ストレージの情報を取得します。
        
        Returns:
            Dict[str, Any]: ストレージの情報（使用量、上限など）
        """
        pass


class StorageError(Exception):
    """ストレージ操作に関連するエラー"""
    pass


class StorageQuotaExceededError(StorageError):
    """ストレージの容量制限を超えた場合のエラー"""
    pass


class StorageNotAvailableError(StorageError):
    """ストレージが利用できない場合のエラー"""
    pass
