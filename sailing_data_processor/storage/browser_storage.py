# -*- coding: utf-8 -*-
"""
ブラウザローカルストレージ実装モジュール

このモジュールではブラウザのlocalStorageを利用したストレージバックエンドを提供します。
streamlit_js_evalを使用してJavaScriptを実行し、ブラウザのストレージにアクセスします。
"""

import json
import base64
import time
import math
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
            # データサイズチェック - メモリ効率向上のため事前検証
            # JSONオブジェクトが非常に大きい場合の事前チェック
            estimated_size = self._estimate_json_size(data)
            if estimated_size > 10 * 1024 * 1024:  # 10MB以上はリスク大
                # 巨大データを検出した場合、データを圧縮または分割するか警告
                self._optimize_large_data(data)
                
            # JSON文字列に変換 - 巨大データの場合はメモリ使用量を監視
            try:
                json_str = json.dumps(data)
            except OverflowError:
                # 数値データが大きすぎる場合は文字列に変換して対応
                json_str = self._safe_json_dumps(data)
            except RecursionError:
                # 再帰が深すぎる場合は、データ構造を平坦化
                modified_data = self._flatten_nested_structure(data)
                json_str = json.dumps(modified_data)
            
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
                # より詳細なエラーメッセージとデータサイズ情報
                size_info = self._estimate_json_size(data) / 1024
                raise StorageQuotaExceededError(f"ストレージ容量を超過しました（推定サイズ: {size_info:.2f}KB）: {str(e)}")
            else:
                raise StorageError(f"データの保存に失敗しました: {str(e)}")
                
    def _estimate_json_size(self, data: Any) -> int:
        """
        JSONデータのサイズを推定する
        
        Args:
            data: サイズを推定するデータ
            
        Returns:
            int: 推定サイズ（バイト）
        """
        if isinstance(data, dict):
            return sum(self._estimate_json_size(k) + self._estimate_json_size(v) for k, v in data.items())
        elif isinstance(data, list):
            return sum(self._estimate_json_size(item) for item in data)
        elif isinstance(data, str):
            return len(data) * 2  # UTF-16文字でエンコードされると仮定
        elif isinstance(data, (int, float, bool, type(None))):
            return 8  # 数値・論理値のための近似値
        else:
            return 64  # 未知の型の保守的な推定
            
    def _optimize_large_data(self, data: Any) -> None:
        """
        巨大データを検出した場合のヒントを表示
        
        Args:
            data: 最適化すべき大きなデータ
        """
        import streamlit as st
        
        st.warning(
            "注意: 非常に大きなデータを保存しようとしています。保存に失敗する場合は以下を試してください:\n"
            "1. 不要なデータを削除して保存データを減らす\n"
            "2. エクスポート機能を使って外部ファイルに保存する\n"
            "3. ブラウザのキャッシュをクリアする"
        )
        
    def _safe_json_dumps(self, data: Any) -> str:
        """
        安全にJSONダンプを行う（大きな数値などを文字列に変換）
        
        Args:
            data: JSON変換するデータ
            
        Returns:
            str: JSON文字列
        """
        if isinstance(data, dict):
            return json.dumps({k: self._prepare_for_json(v) for k, v in data.items()})
        else:
            return json.dumps(self._prepare_for_json(data))
            
    def _prepare_for_json(self, value: Any) -> Any:
        """
        JSONシリアル化のためにデータを準備する
        
        Args:
            value: 準備する値
            
        Returns:
            Any: JSON用に準備された値
        """
        if isinstance(value, dict):
            return {k: self._prepare_for_json(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._prepare_for_json(item) for item in value]
        elif isinstance(value, (int, float)) and (abs(value) > 1e15 or math.isnan(value) or math.isinf(value)):
            # 大きすぎる数値や特殊な値は文字列に変換
            return str(value)
        else:
            return value
            
    def _flatten_nested_structure(self, data: Any, max_depth: int = 20) -> Any:
        """
        深すぎるネストされたデータ構造を平坦化する
        
        Args:
            data: 平坦化するデータ
            max_depth: 許容する最大深さ
            
        Returns:
            Any: 平坦化されたデータ
        """
        def _flatten_helper(value, current_depth=0):
            if current_depth >= max_depth:
                if isinstance(value, (dict, list)):
                    return str(value)  # 深すぎる構造は文字列に変換
                return value
                
            if isinstance(value, dict):
                return {k: _flatten_helper(v, current_depth + 1) for k, v in value.items()}
            elif isinstance(value, list):
                return [_flatten_helper(item, current_depth + 1) for item in value]
            else:
                return value
                
        return _flatten_helper(data)
    
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
        
        # データの整合性確認用のハッシュ値を計算
        import hashlib
        data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
        
        # メタデータを保存
        metadata = {
            "total_chunks": total_chunks,
            "total_size": len(data_str),
            "timestamp": time.time(),
            "checksum": data_hash,
            "chunk_sizes": [len(chunk) for chunk in chunks]
        }
        
        # チャンクを保存（先にチャンクを保存してからメタデータ）
        saved_chunks = 0
        max_retries = 2
        
        for i, chunk in enumerate(chunks):
            chunk_key = f"{base_key}_chunk_{i}"
            retry_count = 0
            
            while retry_count <= max_retries:
                if self._set_item(chunk_key, chunk):
                    saved_chunks += 1
                    break
                else:
                    retry_count += 1
                    time.sleep(0.1)  # 短い待機時間を入れて再試行
            
            if retry_count > max_retries:
                # リトライしても保存できない場合
                st.warning(f"チャンク {i+1}/{total_chunks} の保存に失敗しました。部分的に保存されたデータをクリアします。")
                self._delete_chunks(base_key)
                return False
        
        # すべてのチャンクが保存できたらメタデータを保存
        if saved_chunks == total_chunks:
            if not self._set_item(meta_key, json.dumps(metadata)):
                # メタデータの保存に失敗した場合、チャンクを削除
                st.warning("メタデータの保存に失敗しました。部分的に保存されたデータをクリアします。")
                self._delete_chunks(base_key)
                return False
            return True
        else:
            # 一部のチャンクが保存できなかった場合
            self._delete_chunks(base_key)
            return False
    
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
        # 値が大きすぎる場合はエラーを発生
        if len(value) > 2 * 1024 * 1024:  # 2MB以上はエラー
            raise StorageQuotaExceededError(f"データサイズが大きすぎます（{len(value) / 1024 / 1024:.2f}MB）。最大2MBまで保存可能です。")
        
        try:
            # クロスブラウザ互換性のための改善
            # JavaScript内でエスケープ処理を行い、パフォーマンスと信頼性を向上
            result = streamlit_js_eval(
                f"""
                try {{
                    // 特殊文字をエスケープするのではなく、データをBase64エンコードして保存
                    // クロスブラウザ対応のより堅牢なBase64エンコーディング
                    let encodedValue;
                    try {{
                        // モダンブラウザ向け
                        encodedValue = btoa(unescape(encodeURIComponent(arguments[0])));
                    }} catch (encodeError) {{
                        // フォールバック方法（手動Base64エンコード）
                        const rawString = unescape(encodeURIComponent(arguments[0]));
                        const base64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
                        let result = '';
                        
                        // 3バイトのデータを4文字のBase64に変換
                        for (let i = 0; i < rawString.length; i += 3) {{
                            const chunk = (rawString.charCodeAt(i) << 16) | 
                                         ((i + 1 < rawString.length) ? rawString.charCodeAt(i + 1) << 8 : 0) | 
                                         ((i + 2 < rawString.length) ? rawString.charCodeAt(i + 2) : 0);
                            
                            result += base64chars.charAt((chunk & 0xfc0000) >> 18) + 
                                      base64chars.charAt((chunk & 0x03f000) >> 12) + 
                                      ((i + 1 < rawString.length) ? base64chars.charAt((chunk & 0x000fc0) >> 6) : '=') + 
                                      ((i + 2 < rawString.length) ? base64chars.charAt(chunk & 0x00003f) : '=');
                        }}
                        encodedValue = result;
                    }}
                    
                    // Edge対応：ストレージ容量チェックを先に実行
                    const testKey = '_storage_test_' + Date.now();
                    const storageInfo = {{
                        usedSize: 0,
                        remainingSize: 0,
                        key: key,
                        valueSize: encodedValue.length
                    }};
                    
                    // 現在のストレージ使用量を取得
                    for (let i = 0; i < localStorage.length; i++) {{
                        const k = localStorage.key(i);
                        if (k) {{
                            const v = localStorage.getItem(k) || '';
                            storageInfo.usedSize += k.length + v.length;
                        }}
                    }}
                    
                    // 推定残容量（5MBをデフォルト最大とする）
                    const maxSize = 5 * 1024 * 1024;
                    storageInfo.remainingSize = maxSize - storageInfo.usedSize;
                    
                    // 保存前に容量チェック
                    if (encodedValue.length * 2 > storageInfo.remainingSize - 1024) {{  // 1KB余裕を持たせる
                        return "QUOTA_EXCEEDED";
                    }}
                    
                    // 実際に保存を試行
                    localStorage.setItem('{key}', encodedValue);
                    return true;
                }} catch (e) {{
                    // 特定のエラーメッセージを返して、クライアント側でより良いエラー処理
                    if (e.name === 'QuotaExceededError' || 
                        e.code === 22 || 
                        e.code === 1014 || // Internet Explorer固有のエラーコード
                        e.number === -2147024882 || // IE/Edgeのエラー番号
                        (e.message && (
                            e.message.includes('quota') || 
                            e.message.includes('storage') || 
                            e.message.includes('exceed')
                        ))) {{
                        console.error('Storage quota exceeded:', e);
                        return "QUOTA_EXCEEDED";
                    }}
                    console.error('Storage error:', e);
                    return {{"error": e.toString()}};
                }}
                """,
                value,  # 引数としてデータを渡す（エスケープ問題の回避）
                key=f"set_{key}_{time.time()}"
            )
            
            # 特別なエラーケースを処理
            if result == "QUOTA_EXCEEDED":
                # 開発者とユーザー向けの詳細ガイダンス
                error_msg = (
                    "ストレージの容量制限を超過しました。以下の操作を試してください：\n"
                    "1. 不要なプロジェクトやセッションを削除してください。\n"
                    "2. データをCSVやGPXとしてエクスポートして、必要に応じて手動でインポートする方法に切り替えてください。\n"
                    "3. ブラウザのキャッシュをクリアしてみてください。"
                )
                raise StorageQuotaExceededError(error_msg)
            
            # エラーの詳細情報がある場合
            if isinstance(result, dict) and "error" in result:
                st.warning(f"ストレージ操作中に問題が発生しました: {result['error']}")
                # バックアップ保存方法を提案
                st.info("データをCSV形式でエクスポートして保存することをお勧めします。")
                return False
                
            return result == True
        except Exception as e:
            # 例外の詳細情報をログに記録（デバッグ用）
            error_type = type(e).__name__
            error_msg = str(e)
            
            # ユーザーフレンドリーなエラーメッセージを表示
            st.error(f"データ保存中にエラーが発生しました。お手数ですが、データをエクスポートするか、別のブラウザを試してみてください。")
            
            # 詳細なトラブルシューティング情報（開発モードでのみ表示）
            if hasattr(st, 'session_state') and st.session_state.get('debug_mode', False):
                st.warning(f"エラーの詳細: {error_type} - {error_msg}")
            
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
                expected_size = metadata.get("total_size", 0)
                expected_checksum = metadata.get("checksum")
                expected_chunk_sizes = metadata.get("chunk_sizes", [])
                
                # チャンク数の整合性チェック
                if total_chunks <= 0:
                    raise StorageError("無効なチャンク数です")
                
                # チャンクサイズの検証準備
                has_chunk_sizes = len(expected_chunk_sizes) == total_chunks
                
                # 全チャンクを読み込んで結合
                chunks = []
                total_loaded_size = 0
                
                for i in range(total_chunks):
                    chunk_key = f"{full_key}_chunk_{i}"
                    chunk = self._get_item(chunk_key)
                    
                    if chunk is None:
                        # チャンク読み込み失敗時のリカバリー試行（最大3回）
                        max_retries = 3
                        for retry in range(max_retries):
                            st.warning(f"チャンク {i+1}/{total_chunks} の読み込みに失敗しました。再試行 {retry+1}/{max_retries}...")
                            time.sleep(0.2)  # 少し待機
                            chunk = self._get_item(chunk_key)
                            if chunk is not None:
                                break
                                
                        if chunk is None:
                            raise StorageError(f"チャンク {i+1}/{total_chunks} の読み込みに失敗しました")
                    
                    # チャンクサイズの検証（もし期待値が存在する場合）
                    if has_chunk_sizes and len(chunk) != expected_chunk_sizes[i]:
                        st.warning(f"チャンク {i+1}/{total_chunks} のサイズが不一致です。データの破損の可能性があります。")
                        # 失敗するのではなく、続行を試みる
                    
                    chunks.append(chunk)
                    total_loaded_size += len(chunk)
                
                # 全データ文字列の構築
                data_str = "".join(chunks)
                
                # 総サイズの整合性チェック
                if expected_size > 0 and len(data_str) != expected_size:
                    st.warning(
                        f"データサイズの不一致: 期待={expected_size}, 実際={len(data_str)}。"
                        "一部のデータが失われている可能性があります。"
                    )
                
                # チェックサムの検証（存在する場合）
                if expected_checksum:
                    import hashlib
                    actual_checksum = hashlib.md5(data_str.encode('utf-8')).hexdigest()
                    if actual_checksum != expected_checksum:
                        st.warning(
                            "データの整合性チェックに失敗しました。データの破損の可能性があります。"
                            "最新のデータをエクスポートして保存することをお勧めします。"
                        )
                
                # JSONとしてパース
                try:
                    return json.loads(data_str)
                except json.JSONDecodeError as e:
                    # 部分的に破損したJSONの場合にリカバリー試行
                    st.error(f"JSONデータの解析に失敗しました: {str(e)}")
                    st.info("データリカバリーを試みています...")
                    
                    # JSONの基本形式をチェック
                    if data_str.startswith("{") and data_str.endswith("}"):
                        # オブジェクト形式で部分的なリカバリーを試行
                        st.warning("データは部分的に破損している可能性があります。エクスポート機能でバックアップを作成することをお勧めします。")
                        # 空のデータを返す（部分的なデータ喪失よりマシ）
                        return {}
                    elif data_str.startswith("[") and data_str.endswith("]"):
                        # 配列形式で部分的なリカバリーを試行
                        st.warning("データは部分的に破損している可能性があります。エクスポート機能でバックアップを作成することをお勧めします。")
                        return []
                    else:
                        raise StorageError(f"JSON解析エラー: {str(e)}")
                
            except json.JSONDecodeError as e:
                raise StorageError(f"メタデータのJSON解析エラー: {str(e)}")
            except Exception as e:
                # より詳細なエラーメッセージ
                error_type = type(e).__name__
                raise StorageError(f"データの読み込みに失敗しました: [{error_type}] {str(e)}")
        else:
            # 単一キーのデータを読み込む
            data_str = self._get_item(full_key)
            if data_str is None:
                return None
                
            try:
                return json.loads(data_str)
            except json.JSONDecodeError as e:
                # JSON解析エラーの詳細を提供
                st.error(f"データ形式が正しくありません: {str(e)}")
                # 基本形式に基づくリカバリーを試行
                if data_str.startswith("{") and data_str.endswith("}"):
                    st.warning("空のオブジェクトを返します")
                    return {}
                elif data_str.startswith("[") and data_str.endswith("]"):
                    st.warning("空の配列を返します")
                    return []
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
