# -*- coding: utf-8 -*-
"""
ui.components.forms.import_wizard.batch_import

バッチインポートUI機能の実装
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable
import tempfile
import os
import io
from pathlib import Path

from sailing_data_processor.importers.batch_importer import BatchImporter, BatchImportResult
from sailing_data_processor.data_model.container import GPSDataContainer


class BatchImportUI:
    """
    バッチインポートUI機能
    
    複数ファイルの一括インポートを行うUI機能
    """
    
    def __init__(self, 
                key: str = "batch_import", 
                on_import_complete: Optional[Callable[[Union[GPSDataContainer, BatchImportResult]], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "batch_import"
        on_import_complete : Optional[Callable[[Union[GPSDataContainer, BatchImportResult]], None]], optional
            インポート完了時のコールバック関数, by default None
        """
        self.key = key
        self.on_import_complete = on_import_complete
        
        # 状態の初期化
        if f"{self.key}_files" not in st.session_state:
            st.session_state[f"{self.key}_files"] = []
        if f"{self.key}_result" not in st.session_state:
            st.session_state[f"{self.key}_result"] = None
        if f"{self.key}_merge_mode" not in st.session_state:
            st.session_state[f"{self.key}_merge_mode"] = "separate"
    
    def render(self):
        """
        UIの描画
        """
        st.subheader("バッチインポート")
        
        # ファイルアップロード
        self._render_file_upload()
        
        # マージモード選択
        self._render_merge_mode()
        
        # ファイルリスト
        self._render_file_list()
        
        # インポートボタン
        self._render_import_button()
        
        # 結果表示
        self._render_result()
    
    def _render_file_upload(self):
        """
        ファイルアップロードUIの描画
        """
        st.write("インポートするファイルを選択してください")
        
        uploaded_files = st.file_uploader(
            "GPS/位置データファイル (CSV, GPX, TCX, FIT)", 
            accept_multiple_files=True,
            type=["csv", "gpx", "tcx", "fit"],
            key=f"{self.key}_uploader"
        )
        
        if uploaded_files:
            # 既存のリストに追加（重複を避ける）
            existing_files = [f.name for f in st.session_state[f"{self.key}_files"]]
            new_files = [f for f in uploaded_files if f.name not in existing_files]
            
            if new_files:
                st.session_state[f"{self.key}_files"].extend(new_files)
                st.session_state[f"{self.key}_result"] = None  # 結果をリセット
                st.success(f"{len(new_files)}ファイルが追加されました。")
    
    def _render_merge_mode(self):
        """
        マージモード選択UIの描画
        """
        if st.session_state[f"{self.key}_files"]:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.radio(
                    "インポート後の処理",
                    options=["個別に処理", "すべてを結合"],
                    index=0 if st.session_state[f"{self.key}_merge_mode"] == "separate" else 1,
                    key=f"{self.key}_merge_radio",
                    on_change=self._update_merge_mode,
                    horizontal=True
                )
            
            with col2:
                if st.button("ファイルをクリア", key=f"{self.key}_clear_btn"):
                    st.session_state[f"{self.key}_files"] = []
                    st.session_state[f"{self.key}_result"] = None
                    st.rerun()
    
    def _update_merge_mode(self):
        """
        マージモードの更新
        """
        value = st.session_state[f"{self.key}_merge_radio"]
        st.session_state[f"{self.key}_merge_mode"] = "separate" if value == "個別に処理" else "merge"
    
    def _render_file_list(self):
        """
        ファイルリストUIの描画
        """
        files = st.session_state[f"{self.key}_files"]
        
        if not files:
            st.info("ファイルが選択されていません。")
            return
        
        st.write(f"選択されたファイル ({len(files)}件):")
        
        for i, file in enumerate(files):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.text(f"{i+1}. {file.name} ({self._get_file_size_str(file)})")
            
            with col2:
                if st.button("削除", key=f"{self.key}_delete_{i}"):
                    st.session_state[f"{self.key}_files"].pop(i)
                    st.session_state[f"{self.key}_result"] = None
                    st.rerun()
    
    def _get_file_size_str(self, file) -> str:
        """
        ファイルサイズを文字列で取得
        
        Parameters
        ----------
        file : UploadedFile
            アップロードされたファイル
            
        Returns
        -------
        str
            サイズ文字列
        """
        try:
            # ファイルサイズを計算
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        except:
            return "Unknown size"
    
    def _render_import_button(self):
        """
        インポートボタンUIの描画
        """
        files = st.session_state[f"{self.key}_files"]
        
        if files:
            st.write("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                use_parallel = st.checkbox(
                    "並列処理を使用", 
                    value=True,
                    key=f"{self.key}_parallel",
                    help="オンにすると複数ファイルを並列でインポートします"
                )
            
            with col2:
                max_workers = st.number_input(
                    "並列数",
                    min_value=1,
                    max_value=8,
                    value=4,
                    key=f"{self.key}_workers",
                    help="並列処理時のワーカー数"
                )
            
            with col3:
                if st.button("インポート開始", key=f"{self.key}_import_btn"):
                    self._run_import(use_parallel, max_workers)
    
    def _run_import(self, use_parallel: bool, max_workers: int):
        """
        インポートの実行
        
        Parameters
        ----------
        use_parallel : bool
            並列処理を使用するかどうか
        max_workers : int
            並列ワーカー数
        """
        files = st.session_state[f"{self.key}_files"]
        
        if not files:
            st.warning("インポートするファイルがありません。")
            return
        
        with st.spinner(f"{len(files)}ファイルをインポート中..."):
            try:
                # バッチインポーターの設定
                config = {
                    'parallel': use_parallel,
                    'max_workers': max_workers
                }
                
                batch_importer = BatchImporter(config)
                
                # メタデータの設定
                metadata = {
                    'import_method': 'batch',
                    'import_ui': self.key
                }
                
                # インポート実行
                result = batch_importer.import_files(files, metadata)
                
                # 結果を保存
                st.session_state[f"{self.key}_result"] = result
                
                # マージモードがmergeの場合、マージ結果を作成
                if st.session_state[f"{self.key}_merge_mode"] == "merge" and result.successful:
                    merged_container = result.merge_containers()
                    
                    # コールバック呼び出し
                    if self.on_import_complete and merged_container:
                        self.on_import_complete(merged_container)
                else:
                    # コールバック呼び出し
                    if self.on_import_complete:
                        self.on_import_complete(result)
                
                st.success("インポートが完了しました。")
                
            except Exception as e:
                st.error(f"インポート中にエラーが発生しました: {str(e)}")
    
    def _render_result(self):
        """
        結果表示UIの描画
        """
        result = st.session_state.get(f"{self.key}_result")
        
        if not result:
            return
        
        st.write("---")
        st.subheader("インポート結果")
        
        # サマリー表示
        summary = result.get_summary()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総ファイル数", summary["total_files"])
        
        with col2:
            st.metric("成功", summary["successful_count"])
        
        with col3:
            st.metric("失敗", summary["failed_count"])
        
        # 成功したファイル
        if summary["successful_count"] > 0:
            st.write("### 成功したファイル")
            for file_name, container in result.successful.items():
                with st.expander(f"{file_name} - {len(container.data)}ポイント"):
                    st.write("#### データサンプル")
                    st.dataframe(container.data.head(5))
                    
                    st.write("#### 時間範囲")
                    time_range = container.get_time_range()
                    st.text(f"開始: {time_range['start']}")
                    st.text(f"終了: {time_range['end']}")
                    st.text(f"期間: {time_range['duration_seconds'] / 60:.1f}分")
        
        # 失敗したファイル
        if summary["failed_count"] > 0:
            st.write("### 失敗したファイル")
            for file_name, errors in result.failed.items():
                with st.expander(f"{file_name} - エラー"):
                    for error in errors:
                        st.error(error)
        
        # 警告があるファイル
        if summary["warning_count"] > 0:
            st.write("### 警告があるファイル")
            for file_name, warnings in result.warnings.items():
                with st.expander(f"{file_name} - 警告"):
                    for warning in warnings:
                        st.warning(warning)
