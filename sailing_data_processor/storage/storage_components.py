"""
ストレージユーティリティコンポーネントモジュール

このモジュールはStreamlitアプリケーション用のストレージ関連UIコンポーネントを提供します。
ブラウザストレージの管理、データのエクスポート/インポート用のUIなどが含まれます。
"""

import json
import base64
import io
import time
from typing import Any, Dict, List, Optional, Union, Callable

import streamlit as st
import pandas as pd

from .storage_interface import StorageInterface, StorageError
from .browser_storage import BrowserStorage
from .export_import import ExportImportManager


class StorageManagerComponent:
    """
    ストレージ管理用のUIコンポーネント。
    
    保存済みのセッションやプロジェクトの一覧表示、削除、リネームなどの
    基本的なストレージ管理機能を提供します。
    """
    
    def __init__(self, storage: StorageInterface, namespace: str = "default"):
        """
        初期化。
        
        Args:
            storage: 使用するストレージインターフェース
            namespace: 管理対象の名前空間
        """
        self.storage = storage
        self.namespace = namespace
    
    def render_storage_info(self):
        """ストレージの使用状況を表示する"""
        
        st.subheader("ストレージ情報")
        
        info = self.storage.get_storage_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 使用量をフォーマット
            used_mb = info.get("namespace_used", 0) / (1024 * 1024)
            total_mb = info.get("estimated_max", 0) / (1024 * 1024)
            usage_percent = min(100, (used_mb / total_mb * 100) if total_mb > 0 else 0)
            
            st.metric(
                "ストレージ使用量", 
                f"{used_mb:.2f} MB / {total_mb:.2f} MB",
                f"{usage_percent:.1f}%"
            )
        
        with col2:
            st.metric(
                "保存済みアイテム数", 
                str(info.get("namespace_item_count", 0))
            )
        
        # 使用量バー
        st.progress(usage_percent / 100)
        
        # 警告表示
        if usage_percent > 80:
            st.warning("ストレージ使用量が80%を超えています。不要なデータを削除するか、データをエクスポートすることをお勧めします。")
    
    def render_item_list(self, prefix: str = "", on_select: Optional[Callable] = None, on_delete: Optional[Callable] = None, on_rename: Optional[Callable] = None):
        """
        ストレージ内のアイテム一覧を表示する。
        
        Args:
            prefix: 表示するアイテムのキープレフィックス
            on_select: アイテム選択時のコールバック関数 (key: str) -> None
            on_delete: アイテム削除時のコールバック関数 (key: str) -> None
            on_rename: アイテム名変更時のコールバック関数 (old_key: str, new_key: str) -> None
        """
        st.subheader("保存済みアイテム")
        
        # キーの一覧を取得
        keys = self.storage.list_keys(prefix)
        
        if not keys:
            st.info("保存されたアイテムはありません。")
            return
        
        # アイテムのリスト表示
        for key in keys:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(key)
            
            with col2:
                if on_select and st.button("読込", key=f"load_{key}"):
                    on_select(key)
            
            with col3:
                if on_delete and st.button("削除", key=f"delete_{key}"):
                    if self.storage.delete(key):
                        st.success(f"{key} を削除しました")
                        if on_delete:
                            on_delete(key)
                        st.experimental_rerun()
                    else:
                        st.error(f"{key} の削除に失敗しました")
            
            with col4:
                if on_rename and st.button("名前変更", key=f"rename_{key}"):
                    st.session_state[f"rename_mode_{key}"] = True
            
            # 名前変更モード
            if on_rename and st.session_state.get(f"rename_mode_{key}", False):
                with st.form(key=f"rename_form_{key}"):
                    new_key = st.text_input("新しい名前", value=key, key=f"new_name_{key}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("保存"):
                            if new_key and new_key != key:
                                # データを読み込んで新しいキーで保存
                                try:
                                    data = self.storage.load(key)
                                    if data is not None and self.storage.save(new_key, data):
                                        self.storage.delete(key)
                                        st.success(f"{key} を {new_key} に変更しました")
                                        if on_rename:
                                            on_rename(key, new_key)
                                        st.session_state.pop(f"rename_mode_{key}", None)
                                        st.experimental_rerun()
                                    else:
                                        st.error("名前の変更に失敗しました")
                                except Exception as e:
                                    st.error(f"エラー: {str(e)}")
                    
                    with col2:
                        if st.form_submit_button("キャンセル"):
                            st.session_state.pop(f"rename_mode_{key}", None)
                            st.experimental_rerun()
    
    def render_clear_storage_button(self):
        """ストレージをクリアするボタンを表示する"""
        st.subheader("ストレージ管理")
        
        if st.button("すべてのデータをクリア", key="clear_all_data"):
            st.warning("この操作は元に戻せません。すべてのデータが削除されます。")
            if st.button("本当にクリアする", key="confirm_clear"):
                if self.storage.clear():
                    st.success("ストレージのすべてのデータをクリアしました")
                    st.experimental_rerun()
                else:
                    st.error("ストレージのクリアに失敗しました")
    
    def render_storage_manager(self, prefix: str = "", on_select: Optional[Callable] = None, on_delete: Optional[Callable] = None, on_rename: Optional[Callable] = None):
        """
        ストレージ管理UIの全体を表示する。
        
        Args:
            prefix: 表示するアイテムのキープレフィックス
            on_select: アイテム選択時のコールバック関数
            on_delete: アイテム削除時のコールバック関数
            on_rename: アイテム名変更時のコールバック関数
        """
        
        with st.expander("ストレージ管理", expanded=False):
            self.render_storage_info()
            st.divider()
            self.render_item_list(prefix, on_select, on_delete, on_rename)
            st.divider()
            self.render_clear_storage_button()


class ImportExportComponent:
    """
    データインポート/エクスポート用のUIコンポーネント。
    
    データのエクスポートやインポートのためのStreamlit UIコンポーネントを提供します。
    """
    
    def __init__(self, export_manager: ExportImportManager):
        """
        初期化。
        
        Args:
            export_manager: 使用するエクスポート/インポートマネージャー
        """
        self.export_manager = export_manager
    
    def render_export_button(self, data: Dict[str, Any], name: str = "export", label: str = "エクスポート", help_text: str = "データをファイルとしてエクスポートします"):
        """
        データエクスポート用のボタンを表示する。
        
        Args:
            data: エクスポートするデータ
            name: エクスポートファイルのベース名
            label: ボタンのラベル
            help_text: ヘルプテキスト
        """
        if st.button(label, help=help_text, key=f"export_btn_{name}_{id(data)}"):
            try:
                export_bytes, filename = self.export_manager.export_data(data, name)
                
                # ダウンロードリンクを作成
                st.markdown(
                    self.export_manager.create_download_link(export_bytes, filename),
                    unsafe_allow_html=True
                )
                
                # 代替としてbytesのダウンロードボタンも提供
                st.download_button(
                    label=f"{filename} をダウンロード",
                    data=export_bytes,
                    file_name=filename,
                    mime="application/octet-stream",
                    key=f"download_{name}_{time.time()}"
                )
                
                st.success(f"データのエクスポートが完了しました: {filename}")
                
            except Exception as e:
                st.error(f"エクスポートエラー: {str(e)}")
    
    def render_import_uploader(self, on_import: Callable[[Dict[str, Any]], None], label: str = "インポートするファイルをアップロード", help_text: str = "以前にエクスポートしたデータファイルをインポートします"):
        """
        インポート用のファイルアップローダーを表示する。
        
        Args:
            on_import: インポート完了時のコールバック関数 (data: Dict[str, Any]) -> None
            label: アップローダーのラベル
            help_text: ヘルプテキスト
        """
        uploaded_file = st.file_uploader(label, type=["saildata", "json"], help=help_text, key=f"import_uploader_{id(on_import)}")
        
        if uploaded_file is not None:
            try:
                # ファイル情報を取得
                info = self.export_manager.get_import_info(uploaded_file)
                
                if info.get("type") == "error":
                    st.error(f"ファイル解析エラー: {info.get('error', '不明なエラー')}")
                else:
                    # ファイル情報を表示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("ファイルタイプ:", info.get("type", "不明"))
                        st.write("バージョン:", info.get("version", "不明"))
                    with col2:
                        if "timestamp" in info:
                            try:
                                # ISO形式の日時をより読みやすい形式に変換
                                from datetime import datetime
                                dt = datetime.fromisoformat(info["timestamp"])
                                formatted_time = dt.strftime("%Y年%m月%d日 %H:%M:%S")
                                st.write("エクスポート日時:", formatted_time)
                            except:
                                st.write("エクスポート日時:", info.get("timestamp", "不明"))
                        
                        if "session_name" in info:
                            st.write("セッション名:", info["session_name"])
                        if "project_name" in info:
                            st.write("プロジェクト名:", info["project_name"])
                        if "item_count" in info:
                            st.write("アイテム数:", info["item_count"])
                    
                    # インポート実行ボタン
                    if st.button("インポートを実行", key=f"do_import_{id(on_import)}"):
                        # ファイルポインターをリセット
                        uploaded_file.seek(0)
                        
                        # データをインポート
                        import_data = self.export_manager.import_data(uploaded_file)
                        
                        # コールバックを呼び出し
                        on_import(import_data)
                        
                        st.success("データのインポートが完了しました。")
                        
                        # アップロードしたファイルをクリア
                        st.session_state.pop(f"import_uploader_{id(on_import)}", None)
                        st.experimental_rerun()
            
            except Exception as e:
                st.error(f"インポートエラー: {str(e)}")
    
    def render_export_multiple_items(self, items: Dict[str, Dict[str, Any]], export_type: str, label: str = "複数アイテムをエクスポート"):
        """
        複数アイテムのバッチエクスポート用UIを表示する。
        
        Args:
            items: エクスポートするアイテムの辞書 (id -> データ)
            export_type: エクスポートの種類（"sessions", "projects"など）
            label: ボタンのラベル
        """
        if not items:
            st.info(f"エクスポート可能なアイテムがありません。")
            return
        
        # 選択UI
        st.subheader(f"{label} ({len(items)}アイテム)")
        
        # 全選択/解除ボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("すべて選択", key=f"select_all_{export_type}"):
                for key in items.keys():
                    st.session_state[f"export_item_{export_type}_{key}"] = True
        
        with col2:
            if st.button("すべて解除", key=f"deselect_all_{export_type}"):
                for key in items.keys():
                    st.session_state[f"export_item_{export_type}_{key}"] = False
        
        # 各アイテムのチェックボックス
        selected_items = {}
        for key, item in items.items():
            name = item.get("name", key)
            if st.checkbox(name, key=f"export_item_{export_type}_{key}", value=st.session_state.get(f"export_item_{export_type}_{key}", False)):
                selected_items[key] = item
        
        # エクスポートボタン
        if selected_items:
            if st.button(f"選択した{len(selected_items)}アイテムをエクスポート", key=f"export_selected_{export_type}"):
                try:
                    export_bytes, filename = self.export_manager.export_multiple_items(selected_items, export_type)
                    
                    # ダウンロードボタン
                    st.download_button(
                        label=f"{filename} をダウンロード",
                        data=export_bytes,
                        file_name=filename,
                        mime="application/octet-stream",
                        key=f"download_{export_type}_{time.time()}"
                    )
                    
                    st.success(f"{len(selected_items)}アイテムのエクスポートが完了しました: {filename}")
                    
                except Exception as e:
                    st.error(f"エクスポートエラー: {str(e)}")
        else:
            st.info("エクスポートするアイテムを選択してください。")
