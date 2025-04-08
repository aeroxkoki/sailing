"""
ui.components.forms.import_wizard.enhanced_batch

拡張バッチインポートコンポーネント
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
import tempfile
import os
import io
import time
from pathlib import Path

from sailing_data_processor.importers.batch_importer import BatchImporter, BatchImportResult
from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator

# コンポーネントをインポート
from .components.import_settings import import_settings_form
from .components.metadata_editor import metadata_editor


class EnhancedBatchImport:
    """
    拡張バッチインポートコンポーネント
    
    複数ファイルのインポートを管理し、詳細なフィードバックと可視化を提供
    """
    
    def __init__(self, 
                 key: str = "enhanced_batch_import", 
                 on_import_complete: Optional[Callable[[Union[GPSDataContainer, BatchImportResult]], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "enhanced_batch_import"
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
        if f"{self.key}_import_settings" not in st.session_state:
            st.session_state[f"{self.key}_import_settings"] = {}
        if f"{self.key}_metadata" not in st.session_state:
            st.session_state[f"{self.key}_metadata"] = {}
        if f"{self.key}_merged_container" not in st.session_state:
            st.session_state[f"{self.key}_merged_container"] = None
        if f"{self.key}_validation_results" not in st.session_state:
            st.session_state[f"{self.key}_validation_results"] = {}
    
    def render(self):
        """UIの描画"""
        # タブレイアウト
        tabs = st.tabs(["ファイル選択", "インポート設定", "共通メタデータ", "インポート結果"])
        
        # タブ1: ファイル選択
        with tabs[0]:
            self._render_file_selection()
        
        # タブ2: インポート設定
        with tabs[1]:
            self._render_import_settings()
        
        # タブ3: 共通メタデータ
        with tabs[2]:
            self._render_metadata()
        
        # タブ4: インポート結果
        with tabs[3]:
            self._render_results()
    
    def _render_file_selection(self):
        """ファイル選択UIの描画"""
        st.header("バッチインポート: ファイル選択")
        st.write("複数のGPSデータファイルを選択してインポートします。")
        
        # ファイルアップロード
        st.write("### ファイル選択")
        
        uploaded_files = st.file_uploader(
            "GPS/位置データファイル (CSV, GPX, TCX, FIT)",
            accept_multiple_files=True,
            type=["csv", "gpx", "tcx", "fit"],
            key=f"{self.key}_uploader",
            help="複数のファイルを一度に選択できます。Ctrlキーを押しながら選択するとファイルを追加できます。"
        )
        
        if uploaded_files:
            # 既存のリストに追加（重複を避ける）
            existing_files = [f.name for f in st.session_state[f"{self.key}_files"]]
            new_files = [f for f in uploaded_files if f.name not in existing_files]
            
            if new_files:
                st.session_state[f"{self.key}_files"].extend(new_files)
                st.session_state[f"{self.key}_result"] = None  # 結果をリセット
                st.success(f"{len(new_files)}ファイルが追加されました。")
        
        # マージモード選択
        if st.session_state[f"{self.key}_files"]:
            st.write("### インポート後の処理")
            
            merge_mode = st.radio(
                "インポート後の処理モード",
                options=["個別に処理", "すべてを結合"],
                index=0 if st.session_state[f"{self.key}_merge_mode"] == "separate" else 1,
                key=f"{self.key}_merge_radio",
                on_change=self._update_merge_mode,
                horizontal=True,
                help="「個別に処理」では各ファイルを別々のデータセットとして扱います。「すべてを結合」では全ファイルを1つのデータセットにマージします。"
            )
            
            # ファイルリスト表示
            self._render_file_list()
    
    def _update_merge_mode(self):
        """マージモードの更新"""
        value = st.session_state[f"{self.key}_merge_radio"]
        st.session_state[f"{self.key}_merge_mode"] = "separate" if value == "個別に処理" else "merge"
    
    def _render_file_list(self):
        """ファイルリストUIの描画"""
        files = st.session_state[f"{self.key}_files"]
        
        if not files:
            st.info("ファイルが選択されていません。")
            return
        
        st.write(f"### 選択されたファイル ({len(files)}件)")
        
        # ファイル形式ごとに分類
        file_types = {}
        for file in files:
            ext = Path(file.name).suffix.lower()[1:]  # 拡張子から先頭の.を除去
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(file)
        
        # 形式ごとの集計
        st.write("#### ファイル形式の内訳")
        col1, col2, col3, col4 = st.columns(4)
        
        columns = [col1, col2, col3, col4]
        for i, (ext, ext_files) in enumerate(file_types.items()):
            col = columns[i % 4]
            with col:
                if ext == "csv":
                    icon = "📊"
                    format_name = "CSV"
                elif ext == "gpx":
                    icon = "🛰️"
                    format_name = "GPX"
                elif ext == "tcx":
                    icon = "🏃"
                    format_name = "TCX"
                elif ext == "fit":
                    icon = "⌚"
                    format_name = "FIT"
                else:
                    icon = "📄"
                    format_name = ext.upper()
                
                st.metric(f"{icon} {format_name}", f"{len(ext_files)}ファイル")
        
        # ファイルリスト
        with st.expander("ファイル一覧", expanded=True):
            for i, file in enumerate(files):
                col1, col2, col3 = st.columns([5, 2, 1])
                
                with col1:
                    st.text(f"{i+1}. {file.name}")
                
                with col2:
                    st.text(self._get_file_size_str(file))
                
                with col3:
                    if st.button("削除", key=f"{self.key}_delete_{i}"):
                        st.session_state[f"{self.key}_files"].pop(i)
                        st.session_state[f"{self.key}_result"] = None
                        st.rerun()
        
        # 全ファイルをクリア
        col_clear = st.columns([3, 1])[1]
        with col_clear:
            if st.button("すべてクリア", key=f"{self.key}_clear_all"):
                st.session_state[f"{self.key}_files"] = []
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
    
    def _render_import_settings(self):
        """インポート設定UIの描画"""
        st.header("バッチインポート: 設定")
        
        files = st.session_state[f"{self.key}_files"]
        if not files:
            st.info("先にファイルを選択してください。")
            return
        
        st.write("各ファイル形式ごとの設定を行います。")
        
        # 形式ごとに設定タブを作成
        file_extensions = set([Path(f.name).suffix.lower()[1:] for f in files])
        
        if file_extensions:
            # 設定タブ
            setting_tabs = st.tabs([ext.upper() for ext in file_extensions])
            
            # 現在の設定を取得
            current_settings = st.session_state[f"{self.key}_import_settings"]
            
            # 各形式の設定フォームを表示
            for i, ext in enumerate(file_extensions):
                with setting_tabs[i]:
                    # ファイル形式名を取得
                    if ext == "csv":
                        format_name = "CSV"
                    elif ext == "gpx":
                        format_name = "GPX"
                    elif ext == "tcx":
                        format_name = "TCX"
                    elif ext == "fit":
                        format_name = "FIT"
                    else:
                        format_name = ext.upper()
                    
                    # その形式のファイル数
                    ext_files = [f for f in files if Path(f.name).suffix.lower()[1:] == ext]
                    st.write(f"### {format_name}形式の設定 ({len(ext_files)}ファイル)")
                    
                    # インポート設定フォームを表示
                    ext_settings = current_settings.get(ext, {})
                    updated_settings = import_settings_form(
                        format_name,
                        ext_settings,
                        key_prefix=f"{self.key}_{ext}"
                    )
                    
                    # 更新された設定を保存
                    current_settings[ext] = updated_settings
            
            # 設定を保存
            st.session_state[f"{self.key}_import_settings"] = current_settings
        
        # 並列処理設定
        st.write("### 並列処理設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_parallel = st.checkbox(
                "並列処理を使用",
                value=True,
                key=f"{self.key}_parallel",
                help="オンにすると複数ファイルを並列でインポートします。通常は高速化されますが、メモリ使用量が増加します。"
            )
        
        with col2:
            max_workers = st.number_input(
                "並列数",
                min_value=1,
                max_value=8,
                value=min(4, len(files)) if files else 4,
                key=f"{self.key}_workers",
                help="並列処理時のワーカー数。通常はCPUコア数程度が最適です。"
            )
    
    def _render_metadata(self):
        """メタデータ入力UIの描画"""
        st.header("バッチインポート: 共通メタデータ")
        
        files = st.session_state[f"{self.key}_files"]
        if not files:
            st.info("先にファイルを選択してください。")
            return
        
        st.write("すべてのファイルに共通して適用されるメタデータを入力します。")
        
        # 現在のメタデータを取得
        current_metadata = st.session_state[f"{self.key}_metadata"]
        
        # メタデータエディタを表示
        updated_metadata = metadata_editor(
            current_metadata=current_metadata,
            key_prefix=f"{self.key}_meta"
        )
        
        # 更新されたメタデータを保存
        st.session_state[f"{self.key}_metadata"] = updated_metadata
    
    def _render_results(self):
        """インポート結果UIの描画"""
        st.header("バッチインポート: 実行と結果")
        
        files = st.session_state[f"{self.key}_files"]
        if not files:
            st.info("先にファイルを選択してください。")
            return
        
        # インポート実行ボタン
        if st.button("インポート開始", key=f"{self.key}_import_btn", use_container_width=True):
            self._run_import()
        
        # 結果表示
        result = st.session_state.get(f"{self.key}_result")
        if result:
            self._show_import_results(result)
    
    def _run_import(self):
        """インポート処理の実行"""
        files = st.session_state[f"{self.key}_files"]
        settings = st.session_state[f"{self.key}_import_settings"]
        metadata = st.session_state[f"{self.key}_metadata"]
        merge_mode = st.session_state[f"{self.key}_merge_mode"]
        
        if not files:
            st.warning("インポートするファイルがありません。")
            return
        
        with st.spinner(f"{len(files)}ファイルをインポート中..."):
            try:
                # バッチインポーターの設定
                use_parallel = st.session_state.get(f"{self.key}_parallel", True)
                max_workers = st.session_state.get(f"{self.key}_workers", 4)
                
                config = {
                    'parallel': use_parallel,
                    'max_workers': max_workers
                }
                
                # ファイル形式ごとの設定を追加
                for ext, ext_settings in settings.items():
                    config[ext] = ext_settings
                
                batch_importer = BatchImporter(config)
                
                # メタデータの設定
                metadata_with_batch_info = metadata.copy()
                metadata_with_batch_info.update({
                    'import_method': 'batch',
                    'import_ui': self.key,
                    'import_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_count': len(files)
                })
                
                # インポート実行
                result = batch_importer.import_files(files, metadata_with_batch_info)
                
                # 結果を保存
                st.session_state[f"{self.key}_result"] = result
                
                # マージモードがmergeの場合、マージ結果を作成
                if merge_mode == "merge" and result.successful:
                    merged_container = result.merge_containers()
                    
                    if merged_container:
                        # バリデーション実行
                        validator = DataValidator()
                        validation_results = validator.validate(merged_container)
                        st.session_state[f"{self.key}_validation_results"]["merged"] = validation_results
                        
                        # マージ結果を保存
                        st.session_state[f"{self.key}_merged_container"] = merged_container
                        
                        # コールバック呼び出し
                        if self.on_import_complete:
                            self.on_import_complete(merged_container)
                    else:
                        st.error("データのマージに失敗しました。")
                else:
                    # 個別のコンテナに対してバリデーション実行
                    validator = DataValidator()
                    validation_results = {}
                    
                    for file_name, container in result.successful.items():
                        validation_results[file_name] = validator.validate(container)
                    
                    st.session_state[f"{self.key}_validation_results"] = validation_results
                    
                    # コールバック呼び出し（個別モードでは結果オブジェクトを渡す）
                    if self.on_import_complete:
                        self.on_import_complete(result)
                
                st.success("インポートが完了しました。")
                
            except Exception as e:
                st.error(f"インポート中にエラーが発生しました: {str(e)}")
    
    def _show_import_results(self, result: BatchImportResult):
        """
        インポート結果の表示
        
        Parameters
        ----------
        result : BatchImportResult
            バッチインポート結果
        """
        # サマリー表示
        summary = result.get_summary()
        
        # 色付きの成功率バー
        success_rate = summary["successful_count"] / summary["total_files"] if summary["total_files"] > 0 else 0
        
        st.write("### インポート結果サマリー")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総ファイル数", summary["total_files"])
        with col2:
            st.metric("成功", summary["successful_count"], 
                     delta=f"{success_rate:.1%}" if success_rate > 0 else None)
        with col3:
            st.metric("失敗", summary["failed_count"],
                     delta=f"-{summary['failed_count']}" if summary["failed_count"] > 0 else None,
                     delta_color="inverse")
        
        # 成功率のプログレスバー
        st.progress(success_rate)
        
        merge_mode = st.session_state[f"{self.key}_merge_mode"]
        
        # マージモードの結果表示
        if merge_mode == "merge" and summary["successful_count"] > 0:
            merged_container = st.session_state.get(f"{self.key}_merged_container")
            
            if merged_container:
                st.write("### マージ結果")
                
                # マージデータの概要
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**データポイント数:** {len(merged_container.data)}")
                    
                    # 時間範囲
                    time_range = merged_container.get_time_range()
                    st.write(f"**期間:** {time_range['duration_seconds'] / 60:.1f}分")
                
                with col2:
                    # ソースファイル
                    source_files = merged_container.metadata.get("source_files", [])
                    st.write(f"**ソースファイル数:** {len(source_files)}")
                    
                    # マップ表示へのリンク
                    if st.button("位置データマップを表示", key=f"{self.key}_show_map"):
                        df = merged_container.data
                        map_data = df[["latitude", "longitude"]].copy()
                        st.map(map_data)
                
                # バリデーション結果
                validation_results = st.session_state[f"{self.key}_validation_results"].get("merged")
                if validation_results:
                    passed, results = validation_results
                    
                    if passed:
                        st.success("データの検証に成功しました。")
                    else:
                        st.warning("データの検証で問題が見つかりました。")
                    
                    with st.expander("検証結果", expanded=not passed):
                        for result in results:
                            if result["is_valid"]:
                                st.success(f"✅ {result['rule_name']}: {result['description']}")
                            else:
                                if result["severity"] == "error":
                                    st.error(f"❌ {result['rule_name']}: {result['description']}")
                                elif result["severity"] == "warning":
                                    st.warning(f"⚠️ {result['rule_name']}: {result['description']}")
                                else:
                                    st.info(f"ℹ️ {result['rule_name']}: {result['description']}")
        
        # ファイル別結果
        st.write(f"### ファイル別結果")
        
        # 成功したファイル
        if summary["successful_count"] > 0:
            with st.expander(f"成功したファイル ({summary['successful_count']}件)", expanded=True):
                # ファイルリスト
                for i, (file_name, container) in enumerate(result.successful.items()):
                    time_range = container.get_time_range()
                    
                    with st.container():
                        st.write(f"**{i+1}. {file_name}**")
                        cols = st.columns([2, 1, 1])
                        
                        with cols[0]:
                            st.write(f"- データポイント数: {len(container.data)}")
                        
                        with cols[1]:
                            st.write(f"- 期間: {time_range['duration_seconds'] / 60:.1f}分")
                        
                        with cols[2]:
                            if st.button("詳細", key=f"{self.key}_detail_{i}"):
                                with st.expander(f"{file_name} - 詳細", expanded=True):
                                    st.write("#### データサンプル")
                                    st.dataframe(container.data.head(5))
                                    
                                    st.write("#### 時間範囲")
                                    st.text(f"開始: {time_range['start']}")
                                    st.text(f"終了: {time_range['end']}")
                                    st.text(f"期間: {time_range['duration_seconds'] / 60:.1f}分")
                                    
                                    # データの可視化
                                    st.write("#### 位置データ")
                                    map_data = container.data[["latitude", "longitude"]].copy()
                                    st.map(map_data)
                    
                    st.divider()
        
        # 失敗したファイル
        if summary["failed_count"] > 0:
            with st.expander(f"失敗したファイル ({summary['failed_count']}件)", 
                            expanded=summary["failed_count"] > 0 and summary["successful_count"] == 0):
                for file_name, errors in result.failed.items():
                    with st.container():
                        st.write(f"**{file_name}**")
                        
                        for error in errors:
                            st.error(error)
                    
                    st.divider()
        
        # 警告があるファイル
        if summary["warning_count"] > 0:
            with st.expander(f"警告があるファイル ({summary['warning_count']}件)", expanded=False):
                for file_name, warnings_list in result.warnings.items():
                    with st.container():
                        st.write(f"**{file_name}**")
                        
                        for warning in warnings_list:
                            st.warning(warning)
                    
                    st.divider()
    
    def get_result(self) -> Optional[Union[BatchImportResult, GPSDataContainer]]:
        """
        インポート結果を取得
        
        Returns
        -------
        Optional[Union[BatchImportResult, GPSDataContainer]]
            インポート結果（マージモードの場合はコンテナ、個別モードの場合は結果オブジェクト）
        """
        merge_mode = st.session_state.get(f"{self.key}_merge_mode")
        
        if merge_mode == "merge":
            return st.session_state.get(f"{self.key}_merged_container")
        else:
            return st.session_state.get(f"{self.key}_result")
    
    def reset(self):
        """状態をリセット"""
        st.session_state[f"{self.key}_files"] = []
        st.session_state[f"{self.key}_result"] = None
        st.session_state[f"{self.key}_merge_mode"] = "separate"
        st.session_state[f"{self.key}_import_settings"] = {}
        st.session_state[f"{self.key}_metadata"] = {}
        st.session_state[f"{self.key}_merged_container"] = None
        st.session_state[f"{self.key}_validation_results"] = {}
