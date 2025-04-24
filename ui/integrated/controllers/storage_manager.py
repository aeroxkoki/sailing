# -*- coding: utf-8 -*-
"""
ストレージマネージャーモジュール

このモジュールはブラウザストレージを管理するための機能を提供します。
セッションデータ、ワークフロー状態、パラメータなどを保存・復元する機能を含みます。
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import base64
import gzip

import streamlit as st
import pandas as pd
import numpy as np

from sailing_data_processor.storage.storage_interface import StorageInterface
from sailing_data_processor.storage.browser_storage import BrowserStorage
from sailing_data_processor.storage.export_import import ExportImportManager


# ロガーの設定
logger = logging.getLogger(__name__)


class StorageManager:
    """
    ストレージマネージャークラス
    
    UI層とストレージインターフェースを結合し、データの保存と復元を管理します。
    """
    
    def __init__(self, namespace: str = "sailing_analysis"):
        """
        初期化
        
        Parameters:
        -----------
        namespace : str, optional
            ストレージの名前空間
        """
        self.namespace = namespace
        
        # ブラウザストレージの初期化
        try:
            self.storage = BrowserStorage(namespace=namespace)
            self.storage_available = True
            logger.info(f"ブラウザストレージを初期化しました (namespace: {namespace})")
        except Exception as e:
            logger.warning(f"ブラウザストレージの初期化に失敗しました: {str(e)}")
            self.storage = None
            self.storage_available = False
        
        # エクスポート/インポートマネージャーの初期化
        self.export_import = ExportImportManager()
        
        # ストレージ統計情報
        self.storage_stats = {
            "last_updated": None,
            "used_space": 0,
            "item_count": 0,
            "largest_items": []
        }
        
        # 初期統計情報の更新
        if self.storage_available:
            self.update_storage_stats()
    
    def save_item(self, key: str, value: Any) -> bool:
        """
        アイテムを保存
        
        Parameters:
        -----------
        key : str
            保存するキー
        value : Any
            保存する値（JSONシリアライズ可能なもの）
            
        Returns:
        --------
        bool
            保存が成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないため保存できません")
            return False
        
        try:
            # 値を文字列に変換（必要に応じて）
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # ストレージに保存
            self.storage.set_item(key, value_str)
            
            # 統計情報の更新
            self.update_storage_stats()
            
            logger.debug(f"アイテムを保存しました: {key}")
            return True
            
        except Exception as e:
            logger.exception(f"アイテムの保存中にエラーが発生しました: {str(e)}")
            return False
    
    def load_item(self, key: str, default: Any = None) -> Any:
        """
        アイテムを読み込み
        
        Parameters:
        -----------
        key : str
            読み込むキー
        default : Any, optional
            キーが存在しない場合のデフォルト値
            
        Returns:
        --------
        Any
            読み込んだ値またはデフォルト値
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないため読み込めません")
            return default
        
        try:
            # ストレージから読み込み
            value_str = self.storage.get_item(key)
            
            if value_str is None:
                return default
            
            # JSON形式の場合はパース
            try:
                value = json.loads(value_str)
                return value
            except (json.JSONDecodeError, TypeError):
                # JSON形式でない場合はそのまま返す
                return value_str
                
        except Exception as e:
            logger.exception(f"アイテムの読み込み中にエラーが発生しました: {str(e)}")
            return default
    
    def delete_item(self, key: str) -> bool:
        """
        アイテムを削除
        
        Parameters:
        -----------
        key : str
            削除するキー
            
        Returns:
        --------
        bool
            削除が成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないため削除できません")
            return False
        
        try:
            # ストレージから削除
            self.storage.remove_item(key)
            
            # 統計情報の更新
            self.update_storage_stats()
            
            logger.debug(f"アイテムを削除しました: {key}")
            return True
            
        except Exception as e:
            logger.exception(f"アイテムの削除中にエラーが発生しました: {str(e)}")
            return False
    
    def clear_storage(self, confirm: bool = True) -> bool:
        """
        ストレージをクリア
        
        Parameters:
        -----------
        confirm : bool, optional
            確認が必要か
            
        Returns:
        --------
        bool
            クリアが成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためクリアできません")
            return False
        
        # 確認が必要な場合
        if confirm:
            confirmation = st.session_state.get("storage_clear_confirmed", False)
            
            if not confirmation:
                return False
        
        try:
            # 現在の名前空間のアイテムのみを削除
            namespace_prefix = f"{self.namespace}_"
            keys_to_delete = []
            
            # 削除対象のキーを収集
            all_keys = self.storage.get_all_keys()
            for key in all_keys:
                if key.startswith(namespace_prefix):
                    keys_to_delete.append(key)
            
            # 順次削除
            for key in keys_to_delete:
                self.storage.remove_item(key)
            
            # 統計情報の更新
            self.update_storage_stats()
            
            logger.info(f"ストレージをクリアしました ({len(keys_to_delete)}件)")
            return True
            
        except Exception as e:
            logger.exception(f"ストレージのクリア中にエラーが発生しました: {str(e)}")
            return False
    
    def update_storage_stats(self) -> Dict[str, Any]:
        """
        ストレージの統計情報を更新
        
        Returns:
        --------
        Dict[str, Any]
            ストレージの統計情報
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないため統計情報を更新できません")
            self.storage_stats = {
                "last_updated": datetime.now().isoformat(),
                "used_space": 0,
                "item_count": 0,
                "largest_items": []
            }
            return self.storage_stats
        
        try:
            # 全アイテムの取得
            all_keys = self.storage.get_all_keys()
            namespace_keys = [key for key in all_keys if key.startswith(f"{self.namespace}_")]
            
            # 使用スペースとアイテム数の計算
            used_space = 0
            item_sizes = []
            
            for key in namespace_keys:
                value = self.storage.get_item(key)
                if value:
                    item_size = len(value)
                    used_space += item_size
                    item_sizes.append((key, item_size))
            
            # サイズでソート
            item_sizes.sort(key=lambda x: x[1], reverse=True)
            
            # 統計情報の更新
            self.storage_stats = {
                "last_updated": datetime.now().isoformat(),
                "used_space": used_space,
                "item_count": len(namespace_keys),
                "largest_items": item_sizes[:5]  # 上位5件
            }
            
            logger.debug("ストレージ統計情報を更新しました")
            return self.storage_stats
            
        except Exception as e:
            logger.exception(f"ストレージ統計情報の更新中にエラーが発生しました: {str(e)}")
            
            # エラー時のデフォルト値
            self.storage_stats = {
                "last_updated": datetime.now().isoformat(),
                "used_space": 0,
                "item_count": 0,
                "largest_items": []
            }
            
            return self.storage_stats
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        ストレージの統計情報を取得
        
        Returns:
        --------
        Dict[str, Any]
            ストレージの統計情報
        """
        return self.storage_stats
    
    def compress_dataframe(self, df: pd.DataFrame) -> str:
        """
        データフレームを圧縮して文字列に変換
        
        Parameters:
        -----------
        df : pd.DataFrame
            圧縮するデータフレーム
            
        Returns:
        --------
        str
            圧縮された文字列（Base64エンコード）
        """
        try:
            # CSVへの変換
            csv_data = df.to_csv(index=False)
            
            # GZIP圧縮
            compressed_data = gzip.compress(csv_data.encode('utf-8'))
            
            # Base64エンコード
            b64_data = base64.b64encode(compressed_data).decode('utf-8')
            
            return b64_data
            
        except Exception as e:
            logger.exception(f"データフレームの圧縮中にエラーが発生しました: {str(e)}")
            raise
    
    def decompress_dataframe(self, compressed_str: str) -> Optional[pd.DataFrame]:
        """
        圧縮された文字列からデータフレームを復元
        
        Parameters:
        -----------
        compressed_str : str
            圧縮された文字列（Base64エンコード）
            
        Returns:
        --------
        Optional[pd.DataFrame]
            復元されたデータフレームまたはNone
        """
        try:
            # Base64デコード
            decoded_data = base64.b64decode(compressed_str)
            
            # GZIP解凍
            decompressed_data = gzip.decompress(decoded_data).decode('utf-8')
            
            # CSVからデータフレームへの変換
            df = pd.read_csv(pd.StringIO(decompressed_data))
            
            # 日時列の変換
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.exception(f"データフレームの解凍中にエラーが発生しました: {str(e)}")
            return None
    
    def save_dataframe(self, key: str, df: pd.DataFrame) -> bool:
        """
        データフレームを保存
        
        Parameters:
        -----------
        key : str
            保存するキー
        df : pd.DataFrame
            保存するデータフレーム
            
        Returns:
        --------
        bool
            保存が成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためデータフレームを保存できません")
            return False
        
        try:
            # データフレームの圧縮
            compressed_data = self.compress_dataframe(df)
            
            # ストレージに保存
            metadata_key = f"{key}_meta"
            data_key = f"{key}_data"
            
            # メタデータの作成
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "rows": len(df),
                "columns": list(df.columns),
                "size_bytes": len(compressed_data)
            }
            
            # メタデータとデータの保存
            self.storage.set_item(metadata_key, json.dumps(metadata))
            self.storage.set_item(data_key, compressed_data)
            
            # 統計情報の更新
            self.update_storage_stats()
            
            logger.info(f"データフレームを保存しました: {key} ({len(df)}行)")
            return True
            
        except Exception as e:
            logger.exception(f"データフレームの保存中にエラーが発生しました: {str(e)}")
            return False
    
    def load_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """
        データフレームを読み込み
        
        Parameters:
        -----------
        key : str
            読み込むキー
            
        Returns:
        --------
        Optional[pd.DataFrame]
            読み込んだデータフレームまたはNone
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためデータフレームを読み込めません")
            return None
        
        try:
            # データキーの作成
            data_key = f"{key}_data"
            
            # データの取得
            compressed_data = self.storage.get_item(data_key)
            
            if compressed_data is None:
                logger.warning(f"データフレームが見つかりません: {key}")
                return None
            
            # データフレームの解凍
            df = self.decompress_dataframe(compressed_data)
            
            if df is not None:
                logger.info(f"データフレームを読み込みました: {key} ({len(df)}行)")
            
            return df
            
        except Exception as e:
            logger.exception(f"データフレームの読み込み中にエラーが発生しました: {str(e)}")
            return None
    
    def export_data(self, data: Dict[str, Any], filename: str = None) -> Optional[Dict[str, Any]]:
        """
        データをエクスポート
        
        Parameters:
        -----------
        data : Dict[str, Any]
            エクスポートするデータ
        filename : str, optional
            エクスポートするファイル名
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            エクスポート結果情報またはNone
        """
        try:
            # データのエクスポート
            result = self.export_import.export_data(data, filename)
            
            logger.info(f"データをエクスポートしました: {result.get('filename')}")
            return result
            
        except Exception as e:
            logger.exception(f"データのエクスポート中にエラーが発生しました: {str(e)}")
            return None
    
    def import_data(self, import_data: Union[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        データをインポート
        
        Parameters:
        -----------
        import_data : Union[str, Dict[str, Any]]
            インポートするデータまたはファイルパス
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            インポートしたデータまたはNone
        """
        try:
            # データのインポート
            result = self.export_import.import_data(import_data)
            
            logger.info("データをインポートしました")
            return result
            
        except Exception as e:
            logger.exception(f"データのインポート中にエラーが発生しました: {str(e)}")
            return None
    
    def backup_session_state(self, keys: List[str] = None) -> Dict[str, Any]:
        """
        セッション状態をバックアップ
        
        Parameters:
        -----------
        keys : List[str], optional
            バックアップするキーのリスト（Noneの場合は全て）
            
        Returns:
        --------
        Dict[str, Any]
            バックアップしたデータ
        """
        backup = {}
        
        try:
            # バックアップするキーの決定
            if keys is None:
                # 特定のプレフィックスを持つキーのみをバックアップ
                prefixes = [
                    "project_", "session_", "workflow_", "param_", 
                    "analysis_", "result_", "display_"
                ]
                
                keys = []
                for key in st.session_state:
                    if any(key.startswith(prefix) for prefix in prefixes):
                        keys.append(key)
            
            # セッション状態のバックアップ
            for key in keys:
                if key in st.session_state:
                    value = st.session_state[key]
                    
                    # DataFrameの場合は特別な処理
                    if isinstance(value, pd.DataFrame):
                        # DataFrameはCSV文字列として保存
                        backup[key] = {
                            "type": "dataframe",
                            "csv": value.to_csv(index=False)
                        }
                    else:
                        # その他のデータはそのまま保存（JSONシリアライズ可能なもののみ）
                        try:
                            # シリアライズ可能かテスト
                            json.dumps({"test": value})
                            backup[key] = {
                                "type": "json",
                                "data": value
                            }
                        except (TypeError, OverflowError):
                            # シリアライズできない場合はスキップ
                            logger.warning(f"シリアライズできないデータをスキップしました: {key}")
            
            # メタデータの追加
            backup["_metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "item_count": len(backup),
                "keys": list(backup.keys())
            }
            
            logger.info(f"セッション状態をバックアップしました ({len(backup)}アイテム)")
            return backup
            
        except Exception as e:
            logger.exception(f"セッション状態のバックアップ中にエラーが発生しました: {str(e)}")
            
            # 最低限のメタデータ
            backup["_metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "item_count": len(backup),
                "keys": list(backup.keys()),
                "error": str(e)
            }
            
            return backup
    
    def restore_session_state(self, backup: Dict[str, Any], keys: List[str] = None) -> bool:
        """
        セッション状態を復元
        
        Parameters:
        -----------
        backup : Dict[str, Any]
            バックアップデータ
        keys : List[str], optional
            復元するキーのリスト（Noneの場合は全て）
            
        Returns:
        --------
        bool
            復元が成功したか
        """
        try:
            # メタデータの確認
            if "_metadata" not in backup:
                logger.warning("バックアップデータにメタデータがありません")
                return False
            
            # 復元するキーの決定
            if keys is None:
                # メタデータを除く全てのキー
                keys = [key for key in backup.keys() if key != "_metadata"]
            
            # セッション状態の復元
            restored_count = 0
            
            for key in keys:
                if key in backup and key != "_metadata":
                    item = backup[key]
                    
                    # データ形式に応じた復元
                    if isinstance(item, dict) and "type" in item:
                        if item["type"] == "dataframe" and "csv" in item:
                            # DataFrameの復元
                            try:
                                csv_data = item["csv"]
                                df = pd.read_csv(pd.StringIO(csv_data))
                                
                                # タイムスタンプ列の変換
                                if "timestamp" in df.columns:
                                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                                
                                st.session_state[key] = df
                                restored_count += 1
                            except Exception as e:
                                logger.warning(f"DataFrameの復元に失敗しました: {key} ({str(e)})")
                                
                        elif item["type"] == "json" and "data" in item:
                            # JSON形式のデータの復元
                            st.session_state[key] = item["data"]
                            restored_count += 1
                    else:
                        # 古い形式のバックアップデータの場合
                        st.session_state[key] = item
                        restored_count += 1
            
            logger.info(f"セッション状態を復元しました ({restored_count}/{len(keys)}アイテム)")
            return True
            
        except Exception as e:
            logger.exception(f"セッション状態の復元中にエラーが発生しました: {str(e)}")
            return False
    
    def save_session_state(self, name: str = None) -> bool:
        """
        現在のセッション状態を保存
        
        Parameters:
        -----------
        name : str, optional
            保存する名前（デフォルトは現在の日時）
            
        Returns:
        --------
        bool
            保存が成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためセッション状態を保存できません")
            return False
        
        try:
            # バックアップの作成
            backup_data = self.backup_session_state()
            
            # 保存名の決定
            if name is None:
                name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 保存キーの作成
            backup_key = f"{self.namespace}_backup_{name}"
            
            # ストレージに保存
            self.storage.set_item(backup_key, json.dumps(backup_data))
            
            # 保存済みのバックアップリストを更新
            backup_list = self.load_item(f"{self.namespace}_backup_list", [])
            
            # 新しいバックアップ情報
            backup_info = {
                "name": name,
                "key": backup_key,
                "timestamp": datetime.now().isoformat(),
                "item_count": backup_data["_metadata"]["item_count"]
            }
            
            # リストに追加（最大10件まで）
            backup_list.append(backup_info)
            if len(backup_list) > 10:
                # 古いバックアップの削除
                old_backup = backup_list.pop(0)
                self.delete_item(old_backup["key"])
            
            # バックアップリストの保存
            self.save_item(f"{self.namespace}_backup_list", backup_list)
            
            # 統計情報の更新
            self.update_storage_stats()
            
            logger.info(f"セッション状態を保存しました: {name}")
            return True
            
        except Exception as e:
            logger.exception(f"セッション状態の保存中にエラーが発生しました: {str(e)}")
            return False
    
    def load_session_state(self, name: str) -> bool:
        """
        保存されたセッション状態を読み込み
        
        Parameters:
        -----------
        name : str
            読み込むバックアップ名
            
        Returns:
        --------
        bool
            読み込みが成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためセッション状態を読み込めません")
            return False
        
        try:
            # バックアップリストの取得
            backup_list = self.load_item(f"{self.namespace}_backup_list", [])
            
            # 指定された名前のバックアップを検索
            backup_info = None
            for info in backup_list:
                if info["name"] == name:
                    backup_info = info
                    break
            
            if backup_info is None:
                logger.warning(f"バックアップが見つかりません: {name}")
                return False
            
            # バックアップデータの取得
            backup_key = backup_info["key"]
            backup_data_str = self.storage.get_item(backup_key)
            
            if backup_data_str is None:
                logger.warning(f"バックアップデータが見つかりません: {name}")
                return False
            
            # バックアップデータのパース
            backup_data = json.loads(backup_data_str)
            
            # セッション状態の復元
            success = self.restore_session_state(backup_data)
            
            if success:
                logger.info(f"セッション状態を読み込みました: {name}")
            
            return success
            
        except Exception as e:
            logger.exception(f"セッション状態の読み込み中にエラーが発生しました: {str(e)}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        保存済みのバックアップリストを取得
        
        Returns:
        --------
        List[Dict[str, Any]]
            バックアップリスト
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためバックアップリストを取得できません")
            return []
        
        try:
            # バックアップリストの取得
            backup_list = self.load_item(f"{self.namespace}_backup_list", [])
            
            # 日時でソート（新しい順）
            backup_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return backup_list
            
        except Exception as e:
            logger.exception(f"バックアップリストの取得中にエラーが発生しました: {str(e)}")
            return []
    
    def delete_backup(self, name: str) -> bool:
        """
        保存済みのバックアップを削除
        
        Parameters:
        -----------
        name : str
            削除するバックアップ名
            
        Returns:
        --------
        bool
            削除が成功したか
        """
        if not self.storage_available:
            logger.warning("ストレージが利用できないためバックアップを削除できません")
            return False
        
        try:
            # バックアップリストの取得
            backup_list = self.load_item(f"{self.namespace}_backup_list", [])
            
            # 指定された名前のバックアップを検索
            backup_index = None
            backup_key = None
            
            for i, info in enumerate(backup_list):
                if info["name"] == name:
                    backup_index = i
                    backup_key = info["key"]
                    break
            
            if backup_index is None or backup_key is None:
                logger.warning(f"バックアップが見つかりません: {name}")
                return False
            
            # バックアップデータの削除
            self.delete_item(backup_key)
            
            # バックアップリストから削除
            backup_list.pop(backup_index)
            
            # 更新されたバックアップリストの保存
            self.save_item(f"{self.namespace}_backup_list", backup_list)
            
            # 統計情報の更新
            self.update_storage_stats()
            
            logger.info(f"バックアップを削除しました: {name}")
            return True
            
        except Exception as e:
            logger.exception(f"バックアップの削除中にエラーが発生しました: {str(e)}")
            return False


def storage_manager_ui():
    """
    ストレージマネージャーUI
    
    ストレージの管理と操作を行うためのユーザーインターフェースを提供します。
    """
    st.title("ストレージ管理")
    
    # ストレージマネージャーの初期化
    if 'storage_manager' not in st.session_state:
        st.session_state.storage_manager = StorageManager()
    
    storage_manager = st.session_state.storage_manager
    
    # ストレージの可用性チェック
    if not storage_manager.storage_available:
        st.error("""
        ブラウザストレージが利用できません。以下の理由が考えられます：
        
        - プライベートブラウジングモードを使用している
        - ブラウザでローカルストレージが無効化されている
        - ブラウザがローカルストレージをサポートしていない
        
        代替として、エクスポート/インポート機能を使用してデータを保存できます。
        """)
    
    # タブの作成
    tab1, tab2, tab3 = st.tabs(["ストレージ状態", "バックアップ管理", "エクスポート/インポート"])
    
    # ストレージ状態タブ
    with tab1:
        st.header("ストレージ状態")
        
        # 統計情報の更新ボタン
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 統計情報の表示
            stats = storage_manager.get_storage_stats()
            
            if stats["last_updated"]:
                try:
                    updated_time = datetime.fromisoformat(stats["last_updated"])
                    st.caption(f"最終更新: {updated_time.strftime('%Y-%m-%d %H:%M:%S')}")
                except (ValueError, TypeError):
                    st.caption(f"最終更新: {stats['last_updated']}")
            
            # 使用状況メトリクス
            used_kb = stats["used_space"] / 1024
            item_count = stats["item_count"]
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("使用容量", f"{used_kb:.1f} KB")
            
            with col_b:
                st.metric("アイテム数", f"{item_count}個")
        
        with col2:
            if st.button("更新", key="update_stats", use_container_width=True):
                storage_manager.update_storage_stats()
                st.experimental_rerun()
        
        # 大きなアイテムの表示
        if stats["largest_items"]:
            st.subheader("容量の大きなアイテム")
            
            large_items_data = []
            for key, size in stats["largest_items"]:
                # キー名の整形（名前空間プレフィックスを削除）
                display_key = key
                if display_key.startswith(f"{storage_manager.namespace}_"):
                    display_key = display_key[len(f"{storage_manager.namespace}_"):]
                
                large_items_data.append({
                    "キー": display_key,
                    "サイズ": f"{size / 1024:.1f} KB"
                })
            
            large_items_df = pd.DataFrame(large_items_data)
            st.dataframe(large_items_df, use_container_width=True)
        
        # ストレージクリアオプション
        st.subheader("ストレージの管理")
        
        clear_container = st.container()
        
        with clear_container:
            if st.checkbox("ストレージをクリアする", key="confirm_clear"):
                st.session_state.storage_clear_confirmed = True
                
                st.warning("""
                注意: この操作はストレージ内のすべてのデータを削除します。
                この操作は元に戻せません。
                """)
                
                if st.button("ストレージをクリア", key="clear_storage", type="primary"):
                    success = storage_manager.clear_storage()
                    
                    if success:
                        st.success("ストレージをクリアしました。")
                        
                        # 状態のリセット
                        st.session_state.storage_clear_confirmed = False
                        
                        # 統計情報の更新
                        storage_manager.update_storage_stats()
                        
                        # 再描画
                        st.experimental_rerun()
                    else:
                        st.error("ストレージのクリアに失敗しました。")
            else:
                st.session_state.storage_clear_confirmed = False
    
    # バックアップ管理タブ
    with tab2:
        st.header("バックアップ管理")
        
        # バックアップの作成
        st.subheader("バックアップの作成")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            backup_name = st.text_input(
                "バックアップ名",
                value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                key="backup_name"
            )
        
        with col2:
            st.write("##")  # スペーサー
            if st.button("バックアップを作成", key="create_backup", use_container_width=True):
                with st.spinner("バックアップを作成中..."):
                    success = storage_manager.save_session_state(backup_name)
                    
                    if success:
                        st.success(f"バックアップを作成しました: {backup_name}")
                        
                        # 再描画
                        st.experimental_rerun()
                    else:
                        st.error("バックアップの作成に失敗しました。")
        
        # バックアップリストの表示
        st.subheader("保存済みバックアップ")
        
        backup_list = storage_manager.get_backup_list()
        
        if backup_list:
            # バックアップリストのデータフレーム作成
            backup_data = []
            
            for backup in backup_list:
                # タイムスタンプの解析
                try:
                    timestamp = datetime.fromisoformat(backup["timestamp"])
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    timestamp_str = backup.get("timestamp", "不明")
                
                backup_data.append({
                    "名前": backup["name"],
                    "作成日時": timestamp_str,
                    "アイテム数": backup.get("item_count", "不明")
                })
            
            backup_df = pd.DataFrame(backup_data)
            st.dataframe(backup_df, use_container_width=True)
            
            # バックアップの読み込みと削除
            col1, col2 = st.columns(2)
            
            with col1:
                selected_backup = st.selectbox(
                    "バックアップを選択",
                    options=[backup["name"] for backup in backup_list],
                    key="selected_backup"
                )
                
                if st.button("バックアップを読み込み", key="load_backup", use_container_width=True):
                    with st.spinner("バックアップを読み込み中..."):
                        success = storage_manager.load_session_state(selected_backup)
                        
                        if success:
                            st.success(f"バックアップを読み込みました: {selected_backup}")
                            
                            # 画面遷移を推奨
                            st.info("読み込んだデータを適用するには、ページの更新が必要な場合があります。")
                        else:
                            st.error("バックアップの読み込みに失敗しました。")
            
            with col2:
                delete_backup = st.selectbox(
                    "削除するバックアップを選択",
                    options=[backup["name"] for backup in backup_list],
                    key="delete_backup"
                )
                
                if st.button("バックアップを削除", key="delete_backup_btn", use_container_width=True):
                    with st.spinner("バックアップを削除中..."):
                        success = storage_manager.delete_backup(delete_backup)
                        
                        if success:
                            st.success(f"バックアップを削除しました: {delete_backup}")
                            
                            # 再描画
                            st.experimental_rerun()
                        else:
                            st.error("バックアップの削除に失敗しました。")
        else:
            st.info("保存済みのバックアップはありません。")
    
    # エクスポート/インポートタブ
    with tab3:
        st.header("エクスポート/インポート")
        
        # エクスポート機能
        st.subheader("データのエクスポート")
        
        export_options = [
            "現在のセッション状態",
            "現在のプロジェクト",
            "現在のセッション"
        ]
        
        export_type = st.radio(
            "エクスポートするデータ",
            options=export_options,
            key="export_type"
        )
        
        export_filename = st.text_input(
            "ファイル名",
            value=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            key="export_filename"
        )
        
        if st.button("エクスポート", key="export_data", use_container_width=True):
            with st.spinner("データをエクスポート中..."):
                # エクスポートするデータの取得
                export_data = {}
                
                if export_type == "現在のセッション状態":
                    export_data = storage_manager.backup_session_state()
                elif export_type == "現在のプロジェクト":
                    if "current_project" in st.session_state:
                        export_data = {"project": st.session_state.current_project}
                    else:
                        st.error("現在のプロジェクトが見つかりません。")
                        export_data = None
                elif export_type == "現在のセッション":
                    if "current_session" in st.session_state:
                        export_data = {"session": st.session_state.current_session}
                    else:
                        st.error("現在のセッションが見つかりません。")
                        export_data = None
                
                if export_data:
                    # エクスポート処理
                    export_json = json.dumps(export_data, indent=2)
                    
                    # ダウンロードボタンの表示
                    st.download_button(
                        label="JSONファイルをダウンロード",
                        data=export_json,
                        file_name=export_filename,
                        mime="application/json"
                    )
        
        # インポート機能
        st.subheader("データのインポート")
        
        uploaded_file = st.file_uploader(
            "JSONファイルをアップロード",
            type=["json"],
            key="import_file"
        )
        
        if uploaded_file is not None:
            try:
                # ファイルの読み込み
                import_data = json.load(uploaded_file)
                
                # データの内容を確認
                data_type = None
                
                if "_metadata" in import_data:
                    data_type = "セッション状態"
                elif "project" in import_data:
                    data_type = "プロジェクト"
                elif "session" in import_data:
                    data_type = "セッション"
                
                if data_type:
                    st.success(f"ファイルを読み込みました: {data_type}")
                    
                    # インポートオプション
                    if st.button("データをインポート", key="import_data", use_container_width=True):
                        with st.spinner("データをインポート中..."):
                            if data_type == "セッション状態":
                                success = storage_manager.restore_session_state(import_data)
                            elif data_type == "プロジェクト":
                                st.session_state.current_project = import_data["project"]
                                success = True
                            elif data_type == "セッション":
                                st.session_state.current_session = import_data["session"]
                                success = True
                            else:
                                success = False
                            
                            if success:
                                st.success(f"{data_type}のインポートが完了しました。")
                                
                                # 画面遷移を推奨
                                st.info("インポートしたデータを適用するには、ページの更新が必要な場合があります。")
                            else:
                                st.error("データのインポートに失敗しました。")
                else:
                    st.error("サポートされていないデータ形式です。")
            
            except json.JSONDecodeError:
                st.error("JSONファイルの解析に失敗しました。")
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")


if __name__ == "__main__":
    storage_manager_ui()
