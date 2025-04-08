"""
ui.components.forms.import_wizard.enhanced_wizard

拡張インポートウィザードコンポーネント
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
import tempfile
import os
import io
import time
from pathlib import Path

from sailing_data_processor.importers.importer_factory import ImporterFactory
from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator

# 拡張インポートウィザードのコンポーネントをインポート
from .components.format_selector import format_selector_card, format_features_info
from .components.column_mapper import column_mapper
from .components.import_settings import import_settings_form
from .components.metadata_editor import metadata_editor


class EnhancedImportWizard:
    """
    拡張データインポートウィザードコンポーネント
    
    複数ステップにわたるデータインポートプロセスを提供し、
    高度な設定やカスタマイズが可能なインポートウィザード
    """
    
    def __init__(self, 
                 key: str = "enhanced_import_wizard", 
                 on_import_complete: Optional[Callable[[GPSDataContainer], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "enhanced_import_wizard"
        on_import_complete : Optional[Callable[[GPSDataContainer], None]], optional
            インポート完了時のコールバック関数, by default None
        """
        self.key = key
        self.on_import_complete = on_import_complete
        
        # ウィザードの状態を初期化
        if f"{self.key}_step" not in st.session_state:
            st.session_state[f"{self.key}_step"] = 1
        
        # ファイル関連
        if f"{self.key}_uploaded_file" not in st.session_state:
            st.session_state[f"{self.key}_uploaded_file"] = None
        if f"{self.key}_file_format" not in st.session_state:
            st.session_state[f"{self.key}_file_format"] = None
        
        # 設定関連
        if f"{self.key}_import_settings" not in st.session_state:
            st.session_state[f"{self.key}_import_settings"] = {}
        if f"{self.key}_column_mapping" not in st.session_state:
            st.session_state[f"{self.key}_column_mapping"] = {}
        if f"{self.key}_metadata" not in st.session_state:
            st.session_state[f"{self.key}_metadata"] = {}
        
        # データ関連
        if f"{self.key}_preview_data" not in st.session_state:
            st.session_state[f"{self.key}_preview_data"] = None
        if f"{self.key}_sample_data" not in st.session_state:
            st.session_state[f"{self.key}_sample_data"] = None
        if f"{self.key}_imported_container" not in st.session_state:
            st.session_state[f"{self.key}_imported_container"] = None
        
        # エラー・警告関連
        if f"{self.key}_import_errors" not in st.session_state:
            st.session_state[f"{self.key}_import_errors"] = []
        if f"{self.key}_import_warnings" not in st.session_state:
            st.session_state[f"{self.key}_import_warnings"] = []
        if f"{self.key}_validation_results" not in st.session_state:
            st.session_state[f"{self.key}_validation_results"] = None
        
        # データ検証
        if f"{self.key}_validator" not in st.session_state:
            st.session_state[f"{self.key}_validator"] = DataValidator()
        
        # サポートされるファイル形式
        self.supported_formats = [
            {"name": "CSV", "icon": "📊", "ext": "csv", "desc": "カンマ区切りテキスト"},
            {"name": "GPX", "icon": "🛰️", "ext": "gpx", "desc": "GPS Exchange Format"},
            {"name": "TCX", "icon": "🏃", "ext": "tcx", "desc": "Training Center XML"},
            {"name": "FIT", "icon": "⌚", "ext": "fit", "desc": "Flexible and Interoperable Data Transfer"}
        ]
    
    def reset(self):
        """ウィザードの状態をリセット"""
        st.session_state[f"{self.key}_step"] = 1
        st.session_state[f"{self.key}_uploaded_file"] = None
        st.session_state[f"{self.key}_file_format"] = None
        st.session_state[f"{self.key}_import_settings"] = {}
        st.session_state[f"{self.key}_column_mapping"] = {}
        st.session_state[f"{self.key}_metadata"] = {}
        st.session_state[f"{self.key}_preview_data"] = None
        st.session_state[f"{self.key}_sample_data"] = None
        st.session_state[f"{self.key}_imported_container"] = None
        st.session_state[f"{self.key}_import_errors"] = []
        st.session_state[f"{self.key}_import_warnings"] = []
        st.session_state[f"{self.key}_validation_results"] = None
    
    def render(self):
        """ウィザードをレンダリング"""
        # ステップ進行状況の表示
        self._render_progress_bar()
        
        # 現在のステップを表示
        step = st.session_state[f"{self.key}_step"]
        
        if step == 1:
            self._render_step1_file_upload()
        elif step == 2:
            self._render_step2_format_detection()
        elif step == 3:
            self._render_step3_import_settings()
        elif step == 4:
            self._render_step4_column_mapping()
        elif step == 5:
            self._render_step5_metadata()
        elif step == 6:
            self._render_step6_preview()
        elif step == 7:
            self._render_step7_import()
    
    def _render_progress_bar(self):
        """ステップ進行状況のプログレスバーを表示"""
        step = st.session_state[f"{self.key}_step"]
        total_steps = 7
        progress = (step - 1) / (total_steps - 1)
        
        # ステップ名のリスト
        step_names = [
            "ファイル選択",
            "形式検出",
            "インポート設定",
            "列マッピング",
            "メタデータ",
            "プレビュー",
            "インポート完了"
        ]
        
        # プログレスバーを表示
        st.progress(progress)
        
        # 現在のステップ名を表示
        st.write(f"**ステップ {step}/{total_steps}**: {step_names[step-1]}")
    
    def _render_step1_file_upload(self):
        """ステップ1: ファイルアップロード"""
        st.header("ファイルのアップロード")
        st.write("インポートするGPSデータファイルをアップロードしてください。")
        
        # サポートされるファイル形式を表示
        file_types = [fmt["ext"] for fmt in self.supported_formats]
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "GPSデータファイル",
            type=file_types,
            key=f"{self.key}_file_uploader",
            help="対応形式: " + ", ".join([f".{ext}" for ext in file_types])
        )
        
        if uploaded_file is not None:
            # ファイル情報の表示
            col1, col2 = st.columns(2)
            with col1:
                st.write("#### ファイル情報")
                st.write(f"**ファイル名:** {uploaded_file.name}")
                st.write(f"**ファイルサイズ:** {self._format_file_size(uploaded_file.size)}")
                st.write(f"**ファイルタイプ:** {uploaded_file.type or '不明'}")
            
            # デモンストレーション用にファイルの一部を表示（CSVの場合）
            if uploaded_file.name.endswith('.csv'):
                try:
                    with col2:
                        st.write("#### ファイルプレビュー")
                        df_preview = pd.read_csv(uploaded_file, nrows=5)
                        st.dataframe(df_preview, use_container_width=True)
                        # ファイルポインタをリセット
                        uploaded_file.seek(0)
                except Exception as e:
                    st.warning(f"プレビューの表示に失敗しました: {e}")
            
            # セッション状態に保存
            st.session_state[f"{self.key}_uploaded_file"] = uploaded_file
            
            # 次のステップへ
            st.button("次へ: 形式検出", key=f"{self.key}_step1_next", on_click=self._go_to_step2)
    
    def _render_step2_format_detection(self):
        """ステップ2: フォーマット検出"""
        st.header("ファイル形式の検出")
        
        uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
        if uploaded_file is None:
            st.error("ファイルがアップロードされていません。")
            st.button("戻る", key=f"{self.key}_step2_back", on_click=self._go_to_step1)
            return
        
        # 自動検出されたフォーマットと、サポートされるフォーマットを決定
        detected_format = self._detect_file_format(uploaded_file)
        
        if detected_format:
            st.success(f"ファイル形式 **{detected_format}** が検出されました。")
            
            # 検出されたフォーマットを選択状態にする
            selected_format = format_selector_card(
                self.supported_formats,
                selected_format=detected_format,
                key=f"{self.key}_format_select"
            )
            
            # 選択されたフォーマットの詳細情報を表示
            format_features_info(selected_format or detected_format)
            
            # 形式情報を保存
            st.session_state[f"{self.key}_file_format"] = selected_format or detected_format
        else:
            st.warning("ファイル形式を自動検出できませんでした。手動で選択してください。")
            
            # フォーマット選択カード
            selected_format = format_selector_card(
                self.supported_formats,
                key=f"{self.key}_format_select"
            )
            
            if selected_format:
                st.session_state[f"{self.key}_file_format"] = selected_format
                format_features_info(selected_format)
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る: ファイル選択", key=f"{self.key}_step2_back", on_click=self._go_to_step1)
        with col2:
            # 選択されたフォーマットがある場合のみ次のステップを有効化
            if st.session_state[f"{self.key}_file_format"]:
                st.button("次へ: インポート設定", key=f"{self.key}_step2_next", on_click=self._go_to_step3)
            else:
                st.button("次へ: インポート設定", key=f"{self.key}_step2_next", disabled=True)
    
    def _render_step3_import_settings(self):
        """ステップ3: インポート設定"""
        st.header("インポート設定")
        
        file_format = st.session_state[f"{self.key}_file_format"]
        if not file_format:
            st.error("ファイル形式が選択されていません。")
            st.button("戻る", key=f"{self.key}_step3_back", on_click=self._go_to_step2)
            return
        
        # 現在の設定を取得
        current_settings = st.session_state[f"{self.key}_import_settings"]
        
        # インポート設定フォームを表示
        updated_settings = import_settings_form(
            file_format,
            current_settings,
            key_prefix=f"{self.key}_settings"
        )
        
        # 更新された設定を保存
        st.session_state[f"{self.key}_import_settings"] = updated_settings
        
        # CSVの場合、サンプルデータの読み込みを実行
        if file_format == "CSV" and st.session_state[f"{self.key}_uploaded_file"]:
            if st.button("サンプルデータを読み込む", key=f"{self.key}_load_sample", type="secondary"):
                with st.spinner("サンプルデータを読み込んでいます..."):
                    self._load_sample_data()
        
        # サンプルデータが読み込まれている場合は表示
        sample_data = st.session_state.get(f"{self.key}_sample_data")
        if sample_data is not None and not sample_data.empty:
            st.write("#### サンプルデータ")
            st.dataframe(sample_data.head(5), use_container_width=True)
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る: 形式検出", key=f"{self.key}_step3_back", on_click=self._go_to_step2)
        with col2:
            st.button("次へ: 列マッピング", key=f"{self.key}_step3_next", on_click=self._go_to_step4)
    
    def _render_step4_column_mapping(self):
        """ステップ4: 列マッピング（CSVの場合）"""
        st.header("列マッピング")
        
        file_format = st.session_state[f"{self.key}_file_format"]
        
        if file_format != "CSV":
            st.info(f"{file_format}形式は自動的に列がマッピングされます。追加設定は必要ありません。")
            
            # ナビゲーションボタン
            col1, col2 = st.columns(2)
            with col1:
                st.button("戻る: インポート設定", key=f"{self.key}_step4_back", on_click=self._go_to_step3)
            with col2:
                st.button("次へ: メタデータ", key=f"{self.key}_step4_next", on_click=self._go_to_step5)
            
            return
        
        # サンプルデータがなければ読み込む
        if f"{self.key}_sample_data" not in st.session_state or st.session_state[f"{self.key}_sample_data"] is None:
            with st.spinner("サンプルデータを読み込んでいます..."):
                self._load_sample_data()
        
        sample_data = st.session_state.get(f"{self.key}_sample_data")
        if sample_data is None or sample_data.empty:
            st.error("サンプルデータの読み込みに失敗しました。設定を見直してください。")
            st.button("戻る: インポート設定", key=f"{self.key}_step4_back", on_click=self._go_to_step3)
            return
        
        # 現在のマッピングを取得
        current_mapping = st.session_state[f"{self.key}_column_mapping"]
        
        # 必須フィールドとオプションフィールドの定義
        required_fields = ["timestamp", "latitude", "longitude"]
        optional_fields = [
            {"key": "speed", "label": "速度"},
            {"key": "course", "label": "方位"},
            {"key": "elevation", "label": "高度"},
            {"key": "heart_rate", "label": "心拍数"},
            {"key": "cadence", "label": "ケイデンス"},
            {"key": "power", "label": "パワー"},
            {"key": "distance", "label": "距離"},
            {"key": "temperature", "label": "温度"},
            {"key": "wind_speed", "label": "風速"},
            {"key": "wind_direction", "label": "風向"}
        ]
        
        # カラムマッパーを表示
        updated_mapping = column_mapper(
            columns=sample_data.columns.tolist(),
            required_fields=required_fields,
            optional_fields=optional_fields,
            current_mapping=current_mapping,
            sample_data=sample_data,
            key_prefix=f"{self.key}_mapper"
        )
        
        # 更新されたマッピングを保存
        st.session_state[f"{self.key}_column_mapping"] = updated_mapping
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る: インポート設定", key=f"{self.key}_step4_back", on_click=self._go_to_step3)
        with col2:
            # 必須フィールドがすべてマッピングされている場合のみ次のステップを有効化
            required_mapped = all(field in updated_mapping for field in required_fields)
            
            if required_mapped:
                st.button("次へ: メタデータ", key=f"{self.key}_step4_next", on_click=self._go_to_step5)
            else:
                st.button("次へ: メタデータ", key=f"{self.key}_step4_next", disabled=True)
                st.warning("必須フィールド（タイムスタンプ、緯度、経度）をすべてマッピングしてください。")
    
    def _render_step5_metadata(self):
        """ステップ5: メタデータ入力"""
        st.header("メタデータ入力")
        
        # 現在のメタデータを取得
        current_metadata = st.session_state[f"{self.key}_metadata"]
        
        # メタデータエディタを表示
        updated_metadata = metadata_editor(
            current_metadata=current_metadata,
            key_prefix=f"{self.key}_meta"
        )
        
        # 更新されたメタデータを保存
        st.session_state[f"{self.key}_metadata"] = updated_metadata
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る: 列マッピング", key=f"{self.key}_step5_back", on_click=self._go_to_step4)
        with col2:
            st.button("次へ: プレビュー", key=f"{self.key}_step5_next", on_click=self._go_to_step6)
    
    def _render_step6_preview(self):
        """ステップ6: インポート前プレビュー"""
        st.header("インポート前プレビュー")
        
        uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
        file_format = st.session_state[f"{self.key}_file_format"]
        import_settings = st.session_state[f"{self.key}_import_settings"]
        column_mapping = st.session_state[f"{self.key}_column_mapping"]
        metadata = st.session_state[f"{self.key}_metadata"]
        
        if uploaded_file is None or file_format is None:
            st.error("ファイル情報がありません。")
            st.button("最初から始める", key=f"{self.key}_step6_reset", on_click=self.reset)
            return
        
        # インポート設定の概要を表示
        with st.expander("インポート設定", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**ファイル情報:**")
                st.write(f"- ファイル名: {uploaded_file.name}")
                st.write(f"- ファイルサイズ: {self._format_file_size(uploaded_file.size)}")
                st.write(f"- ファイル形式: {file_format}")
            
            with col2:
                if file_format == "CSV":
                    st.write("**CSVインポート設定:**")
                    st.write(f"- 区切り文字: '{import_settings.get('delimiter', ',')}'")
                    st.write(f"- エンコーディング: {import_settings.get('encoding', 'utf-8')}")
                    if import_settings.get('skiprows'):
                        st.write(f"- スキップする行数: {import_settings.get('skiprows')}")
                    if import_settings.get('date_format'):
                        st.write(f"- 日付形式: {import_settings.get('date_format')}")
                else:
                    st.write("**インポート設定:**")
                    for key, value in import_settings.items():
                        if isinstance(value, bool):
                            st.write(f"- {key}: {'有効' if value else '無効'}")
                        else:
                            st.write(f"- {key}: {value}")
        
        # 列マッピングがある場合は表示（CSVの場合）
        if file_format == "CSV" and column_mapping:
            with st.expander("列マッピング", expanded=True):
                st.write("**列マッピング:**")
                for target, source in column_mapping.items():
                    st.write(f"- {target}: {source}")
        
        # メタデータがある場合は表示
        if metadata:
            with st.expander("メタデータ", expanded=True):
                st.write("**メタデータ:**")
                # 一時的なキーを除外
                display_metadata = {k: v for k, v in metadata.items() 
                                   if k not in ["created_at", "updated_at"]}
                
                # メタデータを2列で表示
                meta_items = list(display_metadata.items())
                mid_point = len(meta_items) // 2 + len(meta_items) % 2
                
                col1, col2 = st.columns(2)
                with col1:
                    for key, value in meta_items[:mid_point]:
                        st.write(f"- {key}: {value}")
                with col2:
                    for key, value in meta_items[mid_point:]:
                        st.write(f"- {key}: {value}")
        
        # インポートのプレビューを実行
        if st.button("インポートをプレビュー", key=f"{self.key}_preview_import"):
            with st.spinner("データをプレビューしています..."):
                preview_container = self._preview_import()
                
                if preview_container:
                    # プレビューデータを保存
                    st.session_state[f"{self.key}_preview_data"] = preview_container
                    
                    # エラーと警告があれば表示
                    if st.session_state[f"{self.key}_import_errors"]:
                        with st.expander("エラー", expanded=True):
                            st.error("インポート中にエラーが発生しました。")
                            for error in st.session_state[f"{self.key}_import_errors"]:
                                st.write(f"- {error}")
                    
                    if st.session_state[f"{self.key}_import_warnings"]:
                        with st.expander("警告", expanded=True):
                            st.warning("インポート中に警告が発生しました。")
                            for warning in st.session_state[f"{self.key}_import_warnings"]:
                                st.write(f"- {warning}")
                    
                    # バリデーション結果
                    validation_results = st.session_state.get(f"{self.key}_validation_results")
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
                else:
                    st.error("データのプレビューに失敗しました。前のステップに戻って設定を見直してください。")
        
        # プレビューデータがあれば表示
        preview_container = st.session_state.get(f"{self.key}_preview_data")
        if preview_container:
            st.write("### データプレビュー")
            
            # データフレーム情報
            preview_df = preview_container.data
            
            # サマリー統計量
            col1, col2 = st.columns(2)
            with col1:
                st.write("**データ統計:**")
                st.write(f"- データポイント数: {len(preview_df)}")
                
                # 時間範囲
                time_range = preview_container.get_time_range()
                st.write(f"- 開始時刻: {time_range['start']}")
                st.write(f"- 終了時刻: {time_range['end']}")
                st.write(f"- 期間: {time_range['duration_seconds'] / 60:.1f}分")
            
            with col2:
                # 座標範囲
                lat_range = f"{preview_df['latitude'].min():.6f} 〜 {preview_df['latitude'].max():.6f}"
                lon_range = f"{preview_df['longitude'].min():.6f} 〜 {preview_df['longitude'].max():.6f}"
                st.write("**位置情報:**")
                st.write(f"- 緯度範囲: {lat_range}")
                st.write(f"- 経度範囲: {lon_range}")
                
                # サンプリング間隔
                if len(preview_df) > 1:
                    time_diffs = preview_df['timestamp'].diff().dropna()
                    avg_interval = time_diffs.mean().total_seconds()
                    st.write(f"- 平均サンプリング間隔: {avg_interval:.1f}秒")
            
            # データサンプル
            with st.expander("データサンプル", expanded=True):
                st.dataframe(preview_df.head(10), use_container_width=True)
            
            # 数値フィールドの統計
            numeric_cols = [col for col in preview_df.columns 
                           if col not in ['timestamp'] and pd.api.types.is_numeric_dtype(preview_df[col])]
            
            if numeric_cols:
                with st.expander("数値フィールド統計", expanded=False):
                    stats_df = preview_df[numeric_cols].describe().T[['mean', 'min', 'max', 'std']]
                    stats_df = stats_df.round(2)
                    stats_df.columns = ['平均', '最小', '最大', '標準偏差']
                    stats_df.index.name = 'フィールド'
                    st.dataframe(stats_df, use_container_width=True)
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る: メタデータ", key=f"{self.key}_step6_back", on_click=self._go_to_step5)
        with col2:
            # プレビューデータがある場合のみインポートを有効化
            if preview_container:
                st.button("インポート", key=f"{self.key}_step6_next", on_click=self._go_to_step7)
            else:
                st.button("インポート", key=f"{self.key}_step6_next", disabled=True)
                st.info("先にインポートをプレビューしてください。")
    
    def _render_step7_import(self):
        """ステップ7: インポート完了"""
        st.header("インポート完了")
        
        preview_container = st.session_state.get(f"{self.key}_preview_data")
        
        if preview_container:
            # インポートを完了
            st.session_state[f"{self.key}_imported_container"] = preview_container
            
            st.success("データのインポートが完了しました！")
            
            # データの概要を表示
            st.write("### インポートされたデータ")
            
            df = preview_container.data
            st.write(f"**データポイント数:** {len(df)}")
            
            time_range = preview_container.get_time_range()
            st.write(f"**期間:** {time_range['start']} ～ {time_range['end']}")
            
            st.write(f"**座標範囲:** 緯度 {df['latitude'].min():.6f} ～ {df['latitude'].max():.6f}, "
                    f"経度 {df['longitude'].min():.6f} ～ {df['longitude'].max():.6f}")
            
            # データの可視化
            if len(df) > 0:
                st.write("### 位置データの可視化")
                
                # マップ表示
                map_data = df[["latitude", "longitude"]].copy()
                st.map(map_data)
                
                # 速度グラフ（速度列がある場合）
                if "speed" in df.columns:
                    st.write("### 速度の推移")
                    speed_chart = pd.DataFrame({
                        "時刻": df["timestamp"],
                        "速度": df["speed"]
                    })
                    st.line_chart(speed_chart.set_index("時刻"))
            
            # コールバック関数を実行
            if self.on_import_complete:
                self.on_import_complete(preview_container)
        else:
            st.error("インポートするデータがありません。")
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("プレビューに戻る", key=f"{self.key}_step7_back", on_click=self._go_to_step6)
        with col2:
            st.button("新しいインポートを開始", key=f"{self.key}_step7_reset", on_click=self.reset)
    
    def _detect_file_format(self, file_obj) -> Optional[str]:
        """
        ファイル形式を検出
        
        Parameters
        ----------
        file_obj : UploadedFile
            アップロードされたファイルオブジェクト
            
        Returns
        -------
        Optional[str]
            検出されたファイル形式（CSV, GPX, TCX, FIT）、検出できない場合はNone
        """
        # 拡張子による検出
        filename = file_obj.name.lower()
        
        if filename.endswith('.csv'):
            return "CSV"
        elif filename.endswith('.gpx'):
            return "GPX"
        elif filename.endswith('.tcx'):
            return "TCX"
        elif filename.endswith('.fit'):
            return "FIT"
        
        # MIMEタイプによる検出
        mime_type = getattr(file_obj, 'type', '').lower()
        
        if mime_type in ['text/csv', 'application/csv']:
            return "CSV"
        elif mime_type in ['application/gpx+xml', 'application/xml'] and filename.endswith('.gpx'):
            return "GPX"
        elif mime_type in ['application/tcx+xml', 'application/xml'] and filename.endswith('.tcx'):
            return "TCX"
        elif mime_type in ['application/octet-stream'] and filename.endswith('.fit'):
            return "FIT"
        
        # ファイル内容による検出（最初の数バイトを読む）
        try:
            file_obj.seek(0)
            header = file_obj.read(128)
            file_obj.seek(0)
            
            if isinstance(header, bytes):
                header_str = header.decode('utf-8', errors='ignore')
            else:
                header_str = header
            
            # GPXファイルはXMLファイルで、通常「<gpx」で始まる
            if '<gpx' in header_str.lower():
                return "GPX"
            
            # TCXファイルはXMLファイルで、通常「<TrainingCenterDatabase」を含む
            if '<trainingcenterdatabase' in header_str.lower():
                return "TCX"
            
            # CSVファイルはテキストファイルで、通常は最初の行に列名がある
            if ',' in header_str and len(header_str.split(',')) > 1:
                return "CSV"
        
        except Exception as e:
            st.warning(f"ファイル形式の自動検出中にエラーが発生しました: {e}")
        
        return None
    
    def _load_sample_data(self):
        """サンプルデータをロード（CSV用）"""
        try:
            uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
            import_settings = st.session_state[f"{self.key}_import_settings"]
            
            if uploaded_file is None:
                return
            
            # 現在のファイル位置を保存
            if hasattr(uploaded_file, 'seek'):
                uploaded_file.seek(0)
            
            # CSVデータの読み込み
            try:
                df = pd.read_csv(
                    uploaded_file,
                    delimiter=import_settings.get('delimiter', ','),
                    encoding=import_settings.get('encoding', 'utf-8'),
                    skiprows=import_settings.get('skiprows', 0),
                    nrows=10  # サンプル用に10行だけ読み込む
                )
                
                # サンプルデータを保存
                st.session_state[f"{self.key}_sample_data"] = df
            except Exception as e:
                st.warning(f"サンプルデータの読み込みに失敗しました: {e}")
                st.session_state[f"{self.key}_sample_data"] = None
            
            # ファイル位置をリセット
            if hasattr(uploaded_file, 'seek'):
                uploaded_file.seek(0)
                
        except Exception as e:
            st.error(f"サンプルデータのロード中にエラーが発生しました: {e}")
            st.session_state[f"{self.key}_sample_data"] = None
    
    def _preview_import(self) -> Optional[GPSDataContainer]:
        """
        インポートのプレビューを実行
        
        Returns
        -------
        Optional[GPSDataContainer]
            プレビューデータのコンテナ（失敗した場合はNone）
        """
        try:
            uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
            file_format = st.session_state[f"{self.key}_file_format"]
            import_settings = st.session_state[f"{self.key}_import_settings"]
            column_mapping = st.session_state[f"{self.key}_column_mapping"]
            metadata = st.session_state[f"{self.key}_metadata"]
            
            if uploaded_file is None or file_format is None:
                return None
            
            # アップロードされたファイルをテンポラリファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{Path(uploaded_file.name).suffix}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # インポーターを取得
                importer = None
                
                if file_format == "CSV":
                    from sailing_data_processor.importers.csv_importer import CSVImporter
                    # インポート設定を適用
                    config = import_settings.copy()
                    config["column_mapping"] = column_mapping
                    importer = CSVImporter(config)
                elif file_format == "GPX":
                    from sailing_data_processor.importers.gpx_importer import GPXImporter
                    importer = GPXImporter(import_settings)
                elif file_format == "TCX":
                    from sailing_data_processor.importers.tcx_importer import TCXImporter
                    importer = TCXImporter(import_settings)
                elif file_format == "FIT":
                    from sailing_data_processor.importers.fit_importer import FITImporter
                    importer = FITImporter(import_settings)
                
                if importer:
                    # インポートを実行
                    container = importer.import_data(tmp_path, metadata)
                    
                    # エラーと警告を保存
                    st.session_state[f"{self.key}_import_errors"] = importer.get_errors()
                    st.session_state[f"{self.key}_import_warnings"] = importer.get_warnings()
                    
                    if container:
                        # データの検証
                        validator = st.session_state[f"{self.key}_validator"]
                        validation_results = validator.validate(container)
                        st.session_state[f"{self.key}_validation_results"] = validation_results
                        
                        return container
                    else:
                        return None
                else:
                    st.session_state[f"{self.key}_import_errors"] = [f"サポートされていないファイル形式: {file_format}"]
                    return None
            
            finally:
                # テンポラリファイルを削除
                os.unlink(tmp_path)
        
        except Exception as e:
            st.session_state[f"{self.key}_import_errors"] = [f"データのプレビュー中にエラーが発生しました: {e}"]
            return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        ファイルサイズを読みやすい形式に変換
        
        Parameters
        ----------
        size_bytes : int
            バイト単位のサイズ
            
        Returns
        -------
        str
            読みやすい形式のサイズ（例: 1.23 MB）
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def _go_to_step1(self):
        """ステップ1へ移動"""
        st.session_state[f"{self.key}_step"] = 1
    
    def _go_to_step2(self):
        """ステップ2へ移動"""
        st.session_state[f"{self.key}_step"] = 2
    
    def _go_to_step3(self):
        """ステップ3へ移動"""
        st.session_state[f"{self.key}_step"] = 3
    
    def _go_to_step4(self):
        """ステップ4へ移動"""
        st.session_state[f"{self.key}_step"] = 4
    
    def _go_to_step5(self):
        """ステップ5へ移動"""
        st.session_state[f"{self.key}_step"] = 5
    
    def _go_to_step6(self):
        """ステップ6へ移動"""
        st.session_state[f"{self.key}_step"] = 6
    
    def _go_to_step7(self):
        """ステップ7へ移動"""
        st.session_state[f"{self.key}_step"] = 7
    
    def get_imported_container(self) -> Optional[GPSDataContainer]:
        """
        インポートされたデータコンテナを取得
        
        Returns
        -------
        Optional[GPSDataContainer]
            インポートされたデータコンテナ（インポートされていない場合はNone）
        """
        return st.session_state.get(f"{self.key}_imported_container")
