"""
ブラウザローカルストレージ実装モジュール

このモジュールではブラウザのlocalStorageを利用したストレージバックエンドを提供します。
streamlit_js_evalを使用してJavaScriptを実行し、ブラウザのストレージにアクセスします。
"""

import json
import base64
import time
from typing import Any, Dict, List, Optional, Union, Tuple

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

from .storage_interface import StorageInterface, StorageError, StorageQuotaExceededError, StorageNotAvailableError


class BrowserStorage(StorageInterface):
    """
    ブラウザのlocalStorageを利用したストレージ実装。
    
    この実装はStreamlitアプリのブラウザセッションに依存し、JavaScriptを介して
    ブラウザのlocalStorageにアクセスします。大きなデータは自動的に分割して保存します。
    """
    
    # ブラウザのlocalStorageには通常5-10MBの制限があるため
    # チャンクサイズを小さく設定（文字列長）
    DEFAULT_CHUNK_SIZE = 500 * 1024  # 500KB
    
    # キープレフィックス
    KEY_PREFIX = "sailing_analyzer_"
    
    # チャンク管理用のメタデータキーサフィックス
    META_SUFFIX = "_meta"
    
    def __init__(self, namespace: str = "default", chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        初期化。
        
        Args:
            namespace: データ分離のための名前空間
            chunk_size: データ分割時の最大チャンクサイズ（文字数）
        """
        self.namespace = namespace
        self.chunk_size = chunk_size
        
        # ローカルストレージが使用可能かチェック
        if not self._is_storage_available():
            raise StorageNotAvailableError("ブラウザのローカルストレージが利用できません")
    
    def _get_full_key(self, key: str) -> str:
        """
        完全なストレージキーを取得する。
        
        Args:
            key: 基本キー
            
        Returns:
            str: 名前空間とプレフィックスを含む完全なキー
        """
        return f"{self.KEY_PREFIX}{self.namespace}_{key}"
    
    def _is_storage_available(self) -> bool:
        """
        ブラウザのlocalStorageが利用可能かチェックする。
        
        Returns:
            bool: 利用可能な場合はTrue
        """
        try:
            # 存在確認と書き込みテスト
            test_key = self._get_full_key("_test")
            result = streamlit_js_eval(
                f"""
                try {{
                    localStorage.setItem('{test_key}', '1');
                    localStorage.removeItem('{test_key}');
                    return true;
                }} catch (e) {{
                    return false;
                }}
                """,
                key=f"test_storage_{time.time()}"
            )
            return result == True
        except Exception:
            return False
    
    def save(self, key: str, data: Any) -> bool:
        """
        データをブラウザのlocalStorageに保存する。
        大きなデータは自動的に分割して保存される。
        
        Args:
            key: データキー
            data: 保存するデータ（JSON化可能なオブジェクト）
            
        Returns:
            bool: 保存に成功した場合はTrue
            
        Raises:
            StorageError: JSON変換エラーなど
            StorageQuotaExceededError: ストレージ容量超過
        """
        try:
            # JSON文字列に変換
            json_str = json.dumps(data)
            
            # チャンク分割が必要か確認
            if len(json_str) <= self.chunk_size:
                # 単一キーで保存
                full_key = self._get_full_key(key)
                return self._set_item(full_key, json_str)
            else:
                # 複数チャンクに分割して保存
                return self._save_chunked(key, json_str)
        except Exception as e:
            if "exceeded" in str(e).lower() or "quota" in str(e).lower():
                raise StorageQuotaExceededError(f"ストレージ容量を超過しました: {str(e)}")
            else:
                raise StorageError(f"データの保存に失敗しました: {str(e)}")
    
    def _save_chunked(self, key: str, data_str: str) -> bool:
        """
        大きなデータを複数のチャンクに分割して保存する。
        
        Args:
            key: ベースキー
            data_str: 保存するデータ文字列
            
        Returns:
            bool: 保存に成功した場合はTrue
        """
        base_key = self._get_full_key(key)
        meta_key = f"{base_key}{self.META_SUFFIX}"
        
        # 既存のチャンクを削除（もしあれば）
        self._delete_chunks(base_key)
        
        # データを分割
        total_chunks = (len(data_str) + self.chunk_size - 1) // self.chunk_size
        chunks = [data_str[i:i+self.chunk_size] for i in range(0, len(data_str), self.chunk_size)]
        
        # メタデータを保存
        metadata = {
            "total_chunks": total_chunks,
            "total_size": len(data_str),
            "timestamp": time.time()
        }
        if not self._set_item(meta_key, json.dumps(metadata)):
            return False
        
        # チャンクを保存
        for i, chunk in enumerate(chunks):
            chunk_key = f"{base_key}_chunk_{i}"
            if not self._set_item(chunk_key, chunk):
                # 保存失敗時は部分的に保存されたチャンクをクリア
                self._delete_chunks(base_key)
                return False
        
        return True
    
    def _delete_chunks(self, base_key: str) -> None:
        """
        指定したベースキーに関連するチャンクをすべて削除する。
        
        Args:
            base_key: ベースキー
        """
        meta_key = f"{base_key}{self.META_SUFFIX}"
        
        # メタデータを取得
        meta_json = self._get_item(meta_key)
        if meta_json:
            try:
                metadata = json.loads(meta_json)
                total_chunks = metadata.get("total_chunks", 0)
                
                # 各チャンクを削除
                for i in range(total_chunks):
                    chunk_key = f"{base_key}_chunk_{i}"
                    streamlit_js_eval(
                        f"localStorage.removeItem('{chunk_key}')",
                        key=f"remove_chunk_{base_key}_{i}_{time.time()}"
                    )
                
                # メタデータを削除
                streamlit_js_eval(
                    f"localStorage.removeItem('{meta_key}')",
                    key=f"remove_meta_{base_key}_{time.time()}"
                )
            except Exception:
                pass
    
    def _set_item(self, key: str, value: str) -> bool:
        """
        単一キーの値を設定する。
        
        Args:
            key: 保存するキー
            value: 保存する値（文字列）
            
        Returns:
            bool: 成功した場合はTrue
        """
        try:
            result = streamlit_js_eval(
                f"""
                try {{
                    localStorage.setItem('{key}', '{value.replace("'", "\\'")}');
                    return true;
                }} catch (e) {{
                    console.error('Storage error:', e);
                    return false;
                }}
                """,
                key=f"set_{key}_{time.time()}"
            )
            return result == True
        except Exception as e:
            st.error(f"ストレージエラー: {str(e)}")
            return False
    
    def _get_item(self, key: str) -> Optional[str]:
        """
        単一キーの値を取得する。
        
        Args:
            key: 取得するキー
            
        Returns:
            Optional[str]: 取得した値（存在しない場合はNone）
        """
        try:
            result = streamlit_js_eval(
                f"""
                try {{
                    return localStorage.getItem('{key}');
                }} catch (e) {{
                    console.error('Storage error:', e);
                    return null;
                }}
                """,
                key=f"get_{key}_{time.time()}"
            )
            return result
        except Exception:
            return None
    
    def load(self, key: str) -> Optional[Any]:
        """
        データをブラウザのlocalStorageから読み込む。
        チャンク分割されたデータは自動的に再結合される。
        
        Args:
            key: データキー
            
        Returns:
            Optional[Any]: 読み込んだデータ、キーが存在しない場合はNone
            
        Raises:
            StorageError: 読み込みエラー
        """
        full_key = self._get_full_key(key)
        meta_key = f"{full_key}{self.META_SUFFIX}"
        
        # メタデータの存在をチェック（チャンク分割されているか）
        meta_json = self._get_item(meta_key)
        
        if meta_json:
            # チャンク分割されたデータを読み込む
            try:
                metadata = json.loads(meta_json)
                total_chunks = metadata.get("total_chunks", 0)
                
                # 全チャンクを読み込んで結合
                chunks = []
                for i in range(total_chunks):
                    chunk_key = f"{full_key}_chunk_{i}"
                    chunk = self._get_item(chunk_key)
                    if chunk is None:
                        raise StorageError(f"チャンクの読み込みに失敗しました: {chunk_key}")
                    chunks.append(chunk)
                
                data_str = "".join(chunks)
                return json.loads(data_str)
                
            except json.JSONDecodeError as e:
                raise StorageError(f"JSON解析エラー: {str(e)}")
            except Exception as e:
                raise StorageError(f"データの読み込みに失敗しました: {str(e)}")
        else:
            # 単一キーのデータを読み込む
            data_str = self._get_item(full_key)
            if data_str is None:
                return None
                
            try:
                return json.loads(data_str)
            except json.JSONDecodeError as e:
                raise StorageError(f"JSON解析エラー: {str(e)}")
    
    def delete(self, key: str) -> bool:
        """
        指定したキーのデータをストレージから削除する。
        
        Args:
            key: 削除するデータのキー
            
        Returns:
            bool: 削除に成功した場合はTrue
        """
        full_key = self._get_full_key(key)
        meta_key = f"{full_key}{self.META_SUFFIX}"
        
        # メタデータの存在をチェック（チャンク分割されているか）
        if self._get_item(meta_key):
            # チャンク分割されたデータを削除
            self._delete_chunks(full_key)
            return True
        else:
            # 単一キーのデータを削除
            try:
                streamlit_js_eval(
                    f"localStorage.removeItem('{full_key}')",
                    key=f"delete_{full_key}_{time.time()}"
                )
                return True
            except Exception:
                return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        ストレージ内のキーを列挙する。
        
        Args:
            prefix: キーのプレフィックス（指定した場合はプレフィックスでフィルタリング）
            
        Returns:
            List[str]: キーのリスト（名前空間プレフィックスは除去済み）
        """
        namespace_prefix = f"{self.KEY_PREFIX}{self.namespace}_"
        search_prefix = f"{namespace_prefix}{prefix}"
        
        try:
            # JavaScriptでキーをリストアップ
            keys_json = streamlit_js_eval(
                f"""
                try {{
                    const keys = [];
                    for (let i = 0; i < localStorage.length; i++) {{
                        const key = localStorage.key(i);
                        if (key && key.startsWith('{search_prefix}') && !key.endsWith('{self.META_SUFFIX}') && !key.includes('_chunk_')) {{
                            keys.push(key);
                        }}
                    }}
                    return JSON.stringify(keys);
                }} catch (e) {{
                    console.error('Error listing keys:', e);
                    return '[]';
                }}
                """,
                key=f"list_keys_{prefix}_{time.time()}"
            )
            
            keys = json.loads(keys_json)
            
            # プレフィックスを取り除く
            return [key[len(namespace_prefix):] for key in keys]
        except Exception:
            return []
    
    def clear(self) -> bool:
        """
        この名前空間のすべてのデータをクリアする。
        
        Returns:
            bool: クリア操作が成功した場合はTrue
        """
        namespace_prefix = f"{self.KEY_PREFIX}{self.namespace}_"
        
        try:
            result = streamlit_js_eval(
                f"""
                try {{
                    const keysToRemove = [];
                    for (let i = 0; i < localStorage.length; i++) {{
                        const key = localStorage.key(i);
                        if (key && key.startsWith('{namespace_prefix}')) {{
                            keysToRemove.push(key);
                        }}
                    }}
                    
                    // 別ループで削除（削除中にインデックスがずれるため）
                    for (const key of keysToRemove) {{
                        localStorage.removeItem(key);
                    }}
                    
                    return true;
                }} catch (e) {{
                    console.error('Error clearing storage:', e);
                    return false;
                }}
                """,
                key=f"clear_storage_{time.time()}"
            )
            return result == True
        except Exception:
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        ストレージの使用状況に関する情報を取得する。
        
        Returns:
            Dict[str, Any]: ストレージ情報
                - used_space: 使用容量（バイト数）
                - namespace_used: この名前空間の使用容量（バイト数）
                - item_count: アイテム数
                - namespace_item_count: この名前空間のアイテム数
                - estimated_max: 推定最大容量（バイト数、ブラウザによる）
        """
        namespace_prefix = f"{self.KEY_PREFIX}{self.namespace}_"
        
        try:
            info_json = streamlit_js_eval(
                f"""
                try {{
                    const info = {{}};
                    let totalSize = 0;
                    let namespaceSize = 0;
                    let itemCount = 0;
                    let namespaceItemCount = 0;
                    
                    for (let i = 0; i < localStorage.length; i++) {{
                        const key = localStorage.key(i);
                        if (!key) continue;
                        
                        const value = localStorage.getItem(key);
                        const size = (key.length + (value ? value.length : 0)) * 2; // UTF-16 文字は2バイト
                        
                        totalSize += size;
                        itemCount++;
                        
                        if (key.startsWith('{namespace_prefix}')) {{
                            namespaceSize += size;
                            namespaceItemCount++;
                        }}
                    }}
                    
                    // 最大容量を推定（一般的な値）
                    let estimatedMax = 5 * 1024 * 1024; // 5MB（一般的なブラウザの制限）
                    
                    // ブラウザの判定と最大容量の推定
                    if (navigator.userAgent.includes('Chrome')) {{
                        estimatedMax = 10 * 1024 * 1024; // Chrome: ~10MB
                    }} else if (navigator.userAgent.includes('Firefox')) {{
                        estimatedMax = 10 * 1024 * 1024; // Firefox: ~10MB
                    }} else if (navigator.userAgent.includes('Safari') && !navigator.userAgent.includes('Chrome')) {{
                        estimatedMax = 5 * 1024 * 1024; // Safari: ~5MB
                    }} else if (navigator.userAgent.includes('Edge') || navigator.userAgent.includes('Edg')) {{
                        estimatedMax = 10 * 1024 * 1024; // Edge: ~10MB
                    }}
                    
                    return JSON.stringify({{
                        used_space: totalSize,
                        namespace_used: namespaceSize,
                        item_count: itemCount,
                        namespace_item_count: namespaceItemCount,
                        estimated_max: estimatedMax
                    }});
                }} catch (e) {{
                    console.error('Error getting storage info:', e);
                    return JSON.stringify({{
                        used_space: 0,
                        namespace_used: 0,
                        item_count: 0,
                        namespace_item_count: 0,
                        estimated_max: 5 * 1024 * 1024 // デフォルト5MB
                    }});
                }}
                """,
                key=f"get_info_{time.time()}"
            )
            
            return json.loads(info_json)
        except Exception as e:
            # エラー時はデフォルト値を返す
            return {
                "used_space": 0,
                "namespace_used": 0,
                "item_count": 0,
                "namespace_item_count": 0,
                "estimated_max": 5 * 1024 * 1024  # デフォルト5MB
            }
