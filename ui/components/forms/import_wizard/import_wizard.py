# -*- coding: utf-8 -*-
"""
ui.components.forms.import_wizard.import_wizard

データインポートウィザードコンポーネント
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
from sailing_data_processor.importers.csv_importer import CSVImporter
from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator


class ImportWizard:
    """
    データインポートウィザードコンポーネント
    
    複数ステップにわたるデータインポートプロセスを提供するコンポーネント
    """
    
    def __init__(self, 
                 key: str = "import_wizard", 
                 on_import_complete: Optional[Callable[[GPSDataContainer], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "import_wizard"
        on_import_complete : Optional[Callable[[GPSDataContainer], None]], optional
            インポート完了時のコールバック関数, by default None
        """
        self.key = key
        self.on_import_complete = on_import_complete
        
        # ウィザードの状態を初期化
        if f"{self.key}_step" not in st.session_state:
            st.session_state[f"{self.key}_step"] = 1
        if f"{self.key}_uploaded_file" not in st.session_state:
            st.session_state[f"{self.key}_uploaded_file"] = None
        if f"{self.key}_file_format" not in st.session_state:
            st.session_state[f"{self.key}_file_format"] = None
        if f"{self.key}_column_mapping" not in st.session_state:
            st.session_state[f"{self.key}_column_mapping"] = {}
        if f"{self.key}_metadata" not in st.session_state:
            st.session_state[f"{self.key}_metadata"] = {}
        if f"{self.key}_preview_data" not in st.session_state:
            st.session_state[f"{self.key}_preview_data"] = None
        if f"{self.key}_imported_container" not in st.session_state:
            st.session_state[f"{self.key}_imported_container"] = None
        if f"{self.key}_import_errors" not in st.session_state:
            st.session_state[f"{self.key}_import_errors"] = []
        if f"{self.key}_import_warnings" not in st.session_state:
            st.session_state[f"{self.key}_import_warnings"] = []
        if f"{self.key}_validation_results" not in st.session_state:
            st.session_state[f"{self.key}_validation_results"] = None
        if f"{self.key}_validator" not in st.session_state:
            st.session_state[f"{self.key}_validator"] = DataValidator()
        
        # 拡張設定の初期化
        if f"{self.key}_import_settings" not in st.session_state:
            st.session_state[f"{self.key}_import_settings"] = {
                "delimiter": ",",  # 区切り文字
                "encoding": "utf-8",  # エンコーディング
                "auto_mapping": True,  # 自動列マッピング
                "skiprows": 0,  # スキップする行数
                "date_format": None,  # タイムスタンプ形式
                "include_extensions": True,  # 拡張データを含めるか
                "prefer_trkpt": True,  # トラックポイントを優先するか（GPX）
                "include_waypoints": False,  # ウェイポイントを含めるか（GPX）
            }
        
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
        st.session_state[f"{self.key}_column_mapping"] = {}
        st.session_state[f"{self.key}_metadata"] = {}
        st.session_state[f"{self.key}_preview_data"] = None
        st.session_state[f"{self.key}_imported_container"] = None
        st.session_state[f"{self.key}_import_errors"] = []
        st.session_state[f"{self.key}_import_warnings"] = []
        st.session_state[f"{self.key}_validation_results"] = None
        
        # 拡張設定のリセット
        st.session_state[f"{self.key}_import_settings"] = {
            "delimiter": ",",  # 区切り文字
            "encoding": "utf-8",  # エンコーディング
            "auto_mapping": True,  # 自動列マッピング
            "skiprows": 0,  # スキップする行数
            "date_format": None,  # タイムスタンプ形式
            "include_extensions": True,  # 拡張データを含めるか
            "prefer_trkpt": True,  # トラックポイントを優先するか（GPX）
            "include_waypoints": False,  # ウェイポイントを含めるか（GPX）
        }
    
    def render(self):
        """ウィザードをレンダリング"""
        step = st.session_state[f"{self.key}_step"]
        
        # ステップに応じて表示を切り替え
        if step == 1:
            self._render_step1_file_upload()
        elif step == 2:
            self._render_step2_format_detection()
        elif step == 3:
            self._render_step3_column_mapping()
        elif step == 4:
            self._render_step4_metadata()
        elif step == 5:
            self._render_step5_preview()
        elif step == 6:
            self._render_step6_import()
    
    def _render_step1_file_upload(self):
        """ステップ1: ファイルアップロード"""
        st.header("ステップ1: ファイルのアップロード")
        
        # 対応形式を表示
        st.write("インポートするGPSデータファイルをアップロードしてください。以下の形式に対応しています：")
        
        # ファイル形式のカード表示
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        
        for i, fmt in enumerate(self.supported_formats):
            with cols[i]:
                st.markdown(
                    f"""
                    <div style="padding:10px; border:1px solid #ddd; border-radius:5px; text-align:center; height:100px;">
                        <div style="font-size:24px;">{fmt["icon"]}</div>
                        <div style="font-weight:bold;">{fmt["name"]}</div>
                        <div style="font-size:12px; color:#666;">{fmt["desc"]}</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        
        st.write("---")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "GPSデータファイル", 
            type=["csv", "gpx", "tcx", "fit"], 
            key=f"{self.key}_file_uploader"
        )
        
        if uploaded_file is not None:
            # ファイル情報を表示
            file_ext = Path(uploaded_file.name).suffix.lower()[1:]
            file_format = next((fmt for fmt in self.supported_formats if fmt["ext"] == file_ext), None)
            
            if file_format:
                st.success(f"{file_format['icon']} {file_format['name']}ファイルを検出しました")
                
                col1, col2 = st.columns(2)
                col1.write(f"📄 **ファイル名:** {uploaded_file.name}")
                col2.write(f"📏 **ファイルサイズ:** {self._format_size(uploaded_file.size)}")
                
                # 詳細設定オプション（折りたたみ可能）
                with st.expander("詳細設定", expanded=False):
                    self._render_advanced_settings(file_format["name"])
                
                # セッション状態に保存
                st.session_state[f"{self.key}_uploaded_file"] = uploaded_file
                
                # 次のステップへ
                st.button("次へ", key=f"{self.key}_step1_next", on_click=self._go_to_step2, type="primary")
            else:
                st.error(f"サポートされていないファイル形式です: {file_ext}")
    
    def _render_advanced_settings(self, file_format: str):
        """詳細設定オプションを表示"""
        settings = st.session_state[f"{self.key}_import_settings"]
        
        if file_format == "CSV":
            # CSV固有の設定
            settings["delimiter"] = st.selectbox(
                "区切り文字", 
                options=[",", ";", "\t", "|", " "], 
                index=[",", ";", "\t", "|", " "].index(settings["delimiter"]),
                format_func=lambda x: {"," : "カンマ (,)", ";" : "セミコロン (;)", "\t" : "タブ (\\t)", "|" : "パイプ (|)", " " : "スペース ( )"}[x],
                key=f"{self.key}_delimiter"
            )
            
            settings["encoding"] = st.selectbox(
                "文字エンコーディング", 
                options=["utf-8", "shift-jis", "euc-jp", "cp932", "iso-2022-jp", "latin1", "cp1252"],
                index=["utf-8", "shift-jis", "euc-jp", "cp932", "iso-2022-jp", "latin1", "cp1252"].index(settings["encoding"]), 
                key=f"{self.key}_encoding"
            )
            
            settings["skiprows"] = st.number_input(
                "スキップする行数", 
                min_value=0, 
                value=settings["skiprows"],
                help="ヘッダー前にスキップする行数",
                key=f"{self.key}_skiprows"
            )
            
            settings["auto_mapping"] = st.checkbox(
                "自動列マッピング", 
                value=settings["auto_mapping"],
                help="列名を自動的に認識",
                key=f"{self.key}_auto_mapping"
            )
            
            settings["date_format"] = st.text_input(
                "日付形式（空白で自動検出）",
                value=settings["date_format"] or "",
                help="例: %Y-%m-%d %H:%M:%S",
                key=f"{self.key}_date_format"
            )
            if settings["date_format"] == "":
                settings["date_format"] = None
        
        elif file_format == "GPX":
            # GPX固有の設定
            settings["include_extensions"] = st.checkbox(
                "拡張データを含める", 
                value=settings["include_extensions"],
                help="心拍数、速度などの拡張データを含める",
                key=f"{self.key}_include_extensions"
            )
            
            settings["prefer_trkpt"] = st.checkbox(
                "トラックポイントを優先", 
                value=settings["prefer_trkpt"],
                help="トラックポイントがある場合はルートポイントを無視",
                key=f"{self.key}_prefer_trkpt"
            )
            
            settings["include_waypoints"] = st.checkbox(
                "ウェイポイントを含める", 
                value=settings["include_waypoints"],
                help="ウェイポイントデータを含める",
                key=f"{self.key}_include_waypoints"
            )
        
        elif file_format == "TCX" or file_format == "FIT":
            # TCX/FIT共通の設定
            settings["include_extensions"] = st.checkbox(
                "拡張データを含める", 
                value=settings["include_extensions"],
                help="心拍数、速度などの拡張データを含める",
                key=f"{self.key}_include_extensions"
            )
        
        # セッション状態に保存
        st.session_state[f"{self.key}_import_settings"] = settings
    
    def _render_step2_format_detection(self):
        """ステップ2: フォーマット検出"""
        st.header("ステップ2: ファイル形式の確認と設定")
        
        uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
        if uploaded_file is None:
            st.error("ファイルがアップロードされていません。")
            st.button("戻る", key=f"{self.key}_step2_back", on_click=self._go_to_step1)
            return
        
        # ファイル解析を表示するためのプログレスバー
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("ファイルを解析中...")
            for i in range(100):
                # 実際の処理はもっと早く終わるが、視覚的なフィードバックとして
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            status_text.text("解析完了！")
        
        # 利用可能なインポーターを取得
        importers = ImporterFactory.get_all_importers()
        
        # アップロードされたファイルをテンポラリファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{Path(uploaded_file.name).suffix}") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        try:
            # 各インポーターでフォーマット検出を試みる
            detected_formats = []
            for importer in importers:
                if importer.can_import(tmp_path):
                    importer_class = importer.__class__.__name__
                    format_name = importer_class.replace("Importer", "")
                    detected_formats.append(format_name)
            
            if detected_formats:
                st.success(f"検出されたファイル形式: {', '.join(detected_formats)}")
                
                # 検出された形式が複数ある場合は選択
                if len(detected_formats) > 1:
                    selected_format = st.selectbox(
                        "使用する形式を選択してください",
                        detected_formats,
                        key=f"{self.key}_format_select"
                    )
                else:
                    selected_format = detected_formats[0]
                
                # CSVファイルの場合は構造分析を試みる
                if selected_format == "CSV":
                    csv_importer = CSVImporter(config=st.session_state[f"{self.key}_import_settings"])
                    csv_info = csv_importer.analyze_csv_structure(tmp_path)
                    
                    if csv_info and 'columns' in csv_info:
                        st.write("### ファイル構造情報")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"区切り文字: `{csv_info['delimiter'] if 'delimiter' in csv_info else ','}`")
                            st.info(f"エンコーディング: `{csv_info['encoding'] if 'encoding' in csv_info else 'utf-8'}`")
                        with col2:
                            st.info(f"列数: `{len(csv_info['columns'])}`")
                            st.info(f"ヘッダー: `{'あり' if 'has_header' in csv_info and csv_info['has_header'] else '不明'}`")
                        
                        # ファイル設定を自動更新
                        settings = st.session_state[f"{self.key}_import_settings"]
                        if 'delimiter' in csv_info:
                            settings["delimiter"] = csv_info['delimiter']
                        if 'encoding' in csv_info:
                            settings["encoding"] = csv_info['encoding']
                        st.session_state[f"{self.key}_import_settings"] = settings
                        
                        # サンプルデータがあれば表示
                        if 'sample_data' in csv_info and csv_info['sample_data']:
                            st.write("### データサンプル")
                            st.dataframe(pd.DataFrame(csv_info['sample_data']))
                            
                            # 自動マッピングの提案があれば保存
                            if 'suggested_mapping' in csv_info and csv_info['suggested_mapping']:
                                st.session_state[f"{self.key}_column_mapping"] = csv_info['suggested_mapping']
                
                # 形式情報を保存
                st.session_state[f"{self.key}_file_format"] = selected_format
                
                # ナビゲーションボタン
                col1, col2 = st.columns(2)
                with col1:
                    st.button("戻る", key=f"{self.key}_step2_back", on_click=self._go_to_step1)
                with col2:
                    st.button("次へ", key=f"{self.key}_step2_next", on_click=self._go_to_step3, type="primary")
            else:
                st.error("対応するファイル形式が検出できませんでした。")
                st.button("戻る", key=f"{self.key}_step2_back", on_click=self._go_to_step1)
        
        finally:
            # テンポラリファイルを削除
            os.unlink(tmp_path)
    
    def _render_step3_column_mapping(self):
        """ステップ3: 列マッピング（CSVの場合）"""
        st.header("ステップ3: 列マッピング")
        
        uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
        file_format = st.session_state[f"{self.key}_file_format"]
        
        if uploaded_file is None or file_format is None:
            st.error("ファイル情報がありません。")
            st.button("最初から始める", key=f"{self.key}_step3_reset", on_click=self.reset)
            return
        
        # CSVの場合のみ列マッピングを行う
        if file_format == "CSV":
            # CSVを読み込み
            settings = st.session_state[f"{self.key}_import_settings"]
            try:
                df = pd.read_csv(
                    io.BytesIO(uploaded_file.getvalue()),
                    delimiter=settings["delimiter"],
                    encoding=settings["encoding"],
                    skiprows=settings["skiprows"]
                )
                
                # 列名の表示前に先頭と末尾の空白を削除
                df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
                columns = df.columns.tolist()
                
                st.write("CSVファイルの列を必須フィールドにマッピングしてください。")
                
                # 現在のマッピングを取得または初期化
                column_mapping = st.session_state.get(f"{self.key}_column_mapping", {})
                
                # 必須フィールドのマッピング
                st.write("### 必須フィールド")
                st.info("以下の列は正しくマッピングする必要があります。自動検出された場合は確認してください。")
                
                # マッピング表示をカードスタイルに
                col1, col2, col3 = st.columns(3)
                
                # タイムスタンプ列
                with col1:
                    st.markdown(
                        """
                        <div style="padding:10px; border:1px solid #4CAF50; border-radius:5px; margin-bottom:10px;">
                            <div style="font-weight:bold; color:#4CAF50;">⏱️ タイムスタンプ</div>
                            <div style="font-size:12px; color:#666; margin-bottom:5px;">時刻・日時情報を含む列</div>
                        """,
                        unsafe_allow_html=True
                    )
                    timestamp_col = st.selectbox(
                        "タイムスタンプ列",
                        columns,
                        index=columns.index(column_mapping.get("timestamp", columns[0])) if column_mapping.get("timestamp") in columns else 0,
                        key=f"{self.key}_timestamp_col",
                        label_visibility="collapsed"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 緯度列
                with col2:
                    st.markdown(
                        """
                        <div style="padding:10px; border:1px solid #2196F3; border-radius:5px; margin-bottom:10px;">
                            <div style="font-weight:bold; color:#2196F3;">🌍 緯度</div>
                            <div style="font-size:12px; color:#666; margin-bottom:5px;">緯度情報 (-90〜90度)</div>
                        """,
                        unsafe_allow_html=True
                    )
                    latitude_col = st.selectbox(
                        "緯度列",
                        columns,
                        index=columns.index(column_mapping.get("latitude", columns[0])) if column_mapping.get("latitude") in columns else 0,
                        key=f"{self.key}_latitude_col",
                        label_visibility="collapsed"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 経度列
                with col3:
                    st.markdown(
                        """
                        <div style="padding:10px; border:1px solid #FF9800; border-radius:5px; margin-bottom:10px;">
                            <div style="font-weight:bold; color:#FF9800;">🧭 経度</div>
                            <div style="font-size:12px; color:#666; margin-bottom:5px;">経度情報 (-180〜180度)</div>
                        """,
                        unsafe_allow_html=True
                    )
                    longitude_col = st.selectbox(
                        "経度列",
                        columns,
                        index=columns.index(column_mapping.get("longitude", columns[0])) if column_mapping.get("longitude") in columns else 0,
                        key=f"{self.key}_longitude_col",
                        label_visibility="collapsed"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 選択された列マッピングを保存
                column_mapping = {
                    "timestamp": timestamp_col,
                    "latitude": latitude_col,
                    "longitude": longitude_col
                }
                
                # オプションフィールド
                st.write("### オプションフィールド")
                st.write("データに含まれる場合は選択してください。これらのデータはパフォーマンス分析に役立ちます。")
                
                optional_fields = [
                    ("speed", "速度", "⚡", "#9C27B0"),
                    ("course", "方位", "🧭", "#795548"),
                    ("elevation", "高度", "🏔️", "#607D8B"),
                    ("heart_rate", "心拍数", "❤️", "#F44336"),
                    ("cadence", "ケイデンス", "🔄", "#FF9800"),
                    ("power", "パワー", "💪", "#FFEB3B"),
                    ("distance", "距離", "📏", "#8BC34A"),
                    ("temperature", "温度", "🌡️", "#009688")
                ]
                
                # 1行に4カラムで表示
                cols = st.columns(4)
                
                for i, (field_key, field_label, icon, color) in enumerate(optional_fields):
                    col_index = i % 4
                    with cols[col_index]:
                        st.markdown(
                            f"""
                            <div style="padding:10px; border:1px solid {color}; border-radius:5px; margin-bottom:10px;">
                                <div style="font-weight:bold; color:{color};">{icon} {field_label}</div>
                            """,
                            unsafe_allow_html=True
                        )
                        options = ["（なし）"] + columns
                        current_value = column_mapping.get(field_key, "（なし）")
                        selected = st.selectbox(
                            f"{field_label}",
                            options,
                            index=options.index(current_value) if current_value in options else 0,
                            key=f"{self.key}_{field_key}_col",
                            label_visibility="collapsed"
                        )
                        
                        if selected != "（なし）":
                            column_mapping[field_key] = selected
                        elif field_key in column_mapping:
                            del column_mapping[field_key]
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # マッピングをセッションに保存
                st.session_state[f"{self.key}_column_mapping"] = column_mapping
                
                # プレビュー
                st.write("### マッピングプレビュー")
                preview_df = pd.DataFrame()
                for target, source in column_mapping.items():
                    if source in df.columns:
                        preview_df[target] = df[source]
                
                if not preview_df.empty:
                    st.dataframe(preview_df.head())
                else:
                    st.warning("マッピングデータがありません。列の選択を確認してください。")
                
                # 検証実行
                if st.button("マッピングを検証", key=f"{self.key}_validate_mapping"):
                    if "timestamp" in preview_df.columns and "latitude" in preview_df.columns and "longitude" in preview_df.columns:
                        # タイムスタンプの変換を試行
                        try:
                            preview_df["timestamp"] = pd.to_datetime(preview_df["timestamp"])
                            st.success("✅ タイムスタンプ列の検証に成功しました。")
                        except Exception as e:
                            st.error(f"❌ タイムスタンプ列の変換に失敗しました: {e}")
                        
                        # 緯度・経度の範囲検証
                        lat_valid = (preview_df["latitude"] >= -90) & (preview_df["latitude"] <= 90)
                        if not lat_valid.all():
                            st.warning(f"⚠️ 緯度列に範囲外の値があります: {sum(~lat_valid)}行")
                        else:
                            st.success("✅ 緯度列の検証に成功しました。")
                        
                        lon_valid = (preview_df["longitude"] >= -180) & (preview_df["longitude"] <= 180)
                        if not lon_valid.all():
                            st.warning(f"⚠️ 経度列に範囲外の値があります: {sum(~lon_valid)}行")
                        else:
                            st.success("✅ 経度列の検証に成功しました。")
                    else:
                        st.error("❌ 必須列（timestamp, latitude, longitude）が見つかりません。")
            
            except Exception as e:
                st.error(f"CSVの読み込み中にエラーが発生しました: {e}")
                st.button("戻る", key=f"{self.key}_step3_back_error", on_click=self._go_to_step2)
                return
        else:
            st.info(f"{file_format}ファイルは自動的に列がマッピングされます。")
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る", key=f"{self.key}_step3_back", on_click=self._go_to_step2)
        with col2:
            st.button("次へ", key=f"{self.key}_step3_next", on_click=self._go_to_step4, type="primary")
    
    def _render_step4_metadata(self):
        """ステップ4: メタデータ入力"""
        st.header("ステップ4: メタデータ入力")
        
        # 現在のメタデータを取得または初期化
        metadata = st.session_state.get(f"{self.key}_metadata", {})
        
        # メタデータ入力フォーム
        st.write("データに関する追加情報を入力してください。これらの情報は分析時に参照できます。")
        
        col1, col2 = st.columns(2)
        
        with col1:
            boat_name = st.text_input(
                "ボート名",
                value=metadata.get("boat_name", ""),
                key=f"{self.key}_boat_name"
            )
            
            boat_class = st.text_input(
                "艇種",
                value=metadata.get("boat_class", ""),
                key=f"{self.key}_boat_class"
            )
            
            location = st.text_input(
                "場所",
                value=metadata.get("location", ""),
                key=f"{self.key}_location"
            )
        
        with col2:
            sailor_name = st.text_input(
                "セーラー名",
                value=metadata.get("sailor_name", ""),
                key=f"{self.key}_sailor_name"
            )
            
            event_type = st.selectbox(
                "イベントタイプ",
                options=["", "練習", "レース", "クルージング", "その他"],
                index=["", "練習", "レース", "クルージング", "その他"].index(metadata.get("event_type", "")),
                key=f"{self.key}_event_type"
            )
            
            weather = st.text_input(
                "天候",
                value=metadata.get("weather", ""),
                key=f"{self.key}_weather"
            )
        
        notes = st.text_area(
            "備考",
            value=metadata.get("notes", ""),
            key=f"{self.key}_notes"
        )
        
        # 入力されたメタデータを保存
        metadata = {
            "boat_name": boat_name,
            "sailor_name": sailor_name,
            "boat_class": boat_class,
            "location": location,
            "event_type": event_type,
            "weather": weather,
            "notes": notes
        }
        
        # 空の値を持つキーを削除
        metadata = {k: v for k, v in metadata.items() if v}
        
        # メタデータをセッションに保存
        st.session_state[f"{self.key}_metadata"] = metadata
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る", key=f"{self.key}_step4_back", on_click=self._go_to_step3)
        with col2:
            st.button("次へ", key=f"{self.key}_step4_next", on_click=self._go_to_step5, type="primary")
    
    def _render_step5_preview(self):
        """ステップ5: インポート前プレビュー"""
        st.header("ステップ5: インポート前プレビュー")
        
        uploaded_file = st.session_state[f"{self.key}_uploaded_file"]
        file_format = st.session_state[f"{self.key}_file_format"]
        column_mapping = st.session_state[f"{self.key}_column_mapping"]
        metadata = st.session_state[f"{self.key}_metadata"]
        settings = st.session_state[f"{self.key}_import_settings"]
        
        if uploaded_file is None or file_format is None:
            st.error("ファイル情報がありません。")
            st.button("最初から始める", key=f"{self.key}_step5_reset", on_click=self.reset)
            return
        
        # インポート設定の概要を表示
        with st.expander("インポート設定", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### ファイル情報")
                st.write(f"**ファイル名:** {uploaded_file.name}")
                st.write(f"**ファイル形式:** {file_format}")
                st.write(f"**ファイルサイズ:** {self._format_size(uploaded_file.size)}")
            
            with col2:
                st.write("#### インポート設定")
                if file_format == "CSV":
                    st.write(f"**区切り文字:** {settings['delimiter']}")
                    st.write(f"**エンコーディング:** {settings['encoding']}")
                    st.write(f"**スキップする行数:** {settings['skiprows']}")
                    if settings['date_format']:
                        st.write(f"**日付形式:** {settings['date_format']}")
                
                if file_format in ["GPX", "TCX", "FIT"]:
                    st.write(f"**拡張データ:** {'含める' if settings.get('include_extensions', True) else '含めない'}")
                
                if file_format == "GPX":
                    st.write(f"**トラックポイント優先:** {'はい' if settings.get('prefer_trkpt', True) else 'いいえ'}")
                    st.write(f"**ウェイポイント:** {'含める' if settings.get('include_waypoints', False) else '含めない'}")
        
        # メタデータ表示
        if metadata:
            with st.expander("メタデータ", expanded=True):
                meta_col1, meta_col2 = st.columns(2)
                
                # メタデータを2カラムに分けて表示
                meta_items = list(metadata.items())
                mid = len(meta_items) // 2 + len(meta_items) % 2
                
                with meta_col1:
                    for key, value in meta_items[:mid]:
                        st.write(f"**{key}:** {value}")
                
                with meta_col2:
                    for key, value in meta_items[mid:]:
                        st.write(f"**{key}:** {value}")
        
        # CSVの場合は列マッピング表示
        if file_format == "CSV" and column_mapping:
            with st.expander("列マッピング", expanded=True):
                for target, source in column_mapping.items():
                    st.write(f"**{target}:** {source}")
        
        # プログレスバー表示
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            st.write("#### データのプレビューを生成中...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(50):
                # 視覚的なフィードバック
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # アップロードされたファイルをテンポラリファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{Path(uploaded_file.name).suffix}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # インポーターを取得
                importer = None
                if file_format == "CSV":
                    from sailing_data_processor.importers.csv_importer import CSVImporter
                    importer = CSVImporter({
                        "column_mapping": column_mapping,
                        "delimiter": settings["delimiter"],
                        "encoding": settings["encoding"],
                        "skiprows": settings["skiprows"],
                        "date_format": settings["date_format"],
                        "auto_mapping": settings["auto_mapping"]
                    })
                elif file_format == "GPX":
                    from sailing_data_processor.importers.gpx_importer import GPXImporter
                    importer = GPXImporter({
                        "include_extensions": settings["include_extensions"],
                        "prefer_trkpt": settings["prefer_trkpt"],
                        "include_waypoints": settings["include_waypoints"]
                    })
                elif file_format == "TCX":
                    from sailing_data_processor.importers.tcx_importer import TCXImporter
                    importer = TCXImporter({
                        "include_extensions": settings["include_extensions"]
                    })
                elif file_format == "FIT":
                    from sailing_data_processor.importers.fit_importer import FITImporter
                    importer = FITImporter({
                        "include_extensions": settings["include_extensions"]
                    })
                
                if importer:
                    # プログレスバーを進める
                    for i in range(50, 75):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                        status_text.text(f"データを解析中... {i+1}%")
                    
                    # プレビューデータの取得
                    if f"{self.key}_preview_data" not in st.session_state or st.session_state[f"{self.key}_preview_data"] is None:
                        container = importer.import_data(tmp_path, metadata)
                        
                        # プログレスバーを完了
                        for i in range(75, 100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)
                            status_text.text(f"データ処理中... {i+1}%")
                        
                        if container:
                            # プレビューデータを保存
                            st.session_state[f"{self.key}_preview_data"] = container
                            # エラーと警告を保存
                            st.session_state[f"{self.key}_import_errors"] = importer.get_errors()
                            st.session_state[f"{self.key}_import_warnings"] = importer.get_warnings()
                            
                            # データ検証
                            validator = DataValidator()
                            validation_valid, validation_results = validator.validate(container)
                            st.session_state[f"{self.key}_validation_results"] = (validation_valid, validation_results)
                            
                            status_text.text("データ解析完了！")
                            time.sleep(0.3)  # 完了メッセージを少し表示
                        else:
                            status_text.text("データのインポートに失敗しました")
                            st.error("データのインポートに失敗しました。")
                            st.write("### エラー")
                            for error in importer.get_errors():
                                st.error(error)
                
                # プレビューデータの表示
                progress_placeholder.empty()  # プログレスバーを消去
                
                preview_container = st.session_state[f"{self.key}_preview_data"]
                if preview_container:
                    st.write("### データプレビュー")
                    
                    # インポート結果の統計情報
                    preview_df = preview_container.data
                    st.success(f"インポート成功: {len(preview_df)}ポイントのデータが読み込まれました")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("データポイント数", f"{len(preview_df):,}")
                    with col2:
                        time_range = preview_container.get_time_range()
                        duration_minutes = time_range['duration_seconds'] / 60
                        st.metric("記録時間", f"{duration_minutes:.1f} 分")
                    with col3:
                        if 'speed' in preview_df.columns:
                            max_speed = preview_df['speed'].max()
                            st.metric("最高速度", f"{max_speed:.1f} m/s")
                        elif 'distance' in preview_df.columns:
                            total_distance = preview_df['distance'].max() / 1000  # mをkmに変換
                            st.metric("総距離", f"{total_distance:.2f} km")
                        else:
                            lat_range = preview_df['latitude'].max() - preview_df['latitude'].min()
                            lon_range = preview_df['longitude'].max() - preview_df['longitude'].min()
                            st.metric("領域範囲", f"{lat_range:.2f}°× {lon_range:.2f}°")
                    
                    # タブでデータ表示を分ける
                    tab1, tab2, tab3 = st.tabs(["データサンプル", "統計情報", "検証結果"])
                    
                    with tab1:
                        # データサンプル表示
                        st.dataframe(preview_df.head(10))
                        st.caption("最初の10行のみ表示しています")
                    
                    with tab2:
                        # データの基本統計
                        if len(preview_df) > 0:
                            # 時間範囲
                            st.write("#### 時間範囲")
                            time_range = preview_container.get_time_range()
                            st.write(f"- 開始時刻: {time_range['start']}")
                            st.write(f"- 終了時刻: {time_range['end']}")
                            st.write(f"- 期間: {time_range['duration_seconds'] / 60:.1f}分")
                            
                            # 座標範囲
                            st.write("#### 座標範囲")
                            lat_range = f"{preview_df['latitude'].min():.6f} 〜 {preview_df['latitude'].max():.6f}"
                            lon_range = f"{preview_df['longitude'].min():.6f} 〜 {preview_df['longitude'].max():.6f}"
                            st.write(f"- 緯度範囲: {lat_range}")
                            st.write(f"- 経度範囲: {lon_range}")
                            
                            # サンプリング間隔（平均）
                            if len(preview_df) > 1:
                                time_diffs = preview_df['timestamp'].diff().dropna()
                                avg_interval = time_diffs.mean().total_seconds()
                                st.write(f"- 平均サンプリング間隔: {avg_interval:.1f}秒")
                            
                            # 数値フィールドの統計
                            numeric_cols = [col for col in preview_df.columns 
                                       if col not in ['timestamp'] and pd.api.types.is_numeric_dtype(preview_df[col])]
                            
                            if numeric_cols:
                                st.write("#### 数値フィールド統計")
                                stats_df = preview_df[numeric_cols].describe().T[['mean', 'min', 'max']]
                                stats_df = stats_df.round(2)
                                stats_df.columns = ['平均', '最小', '最大']
                                st.dataframe(stats_df)
                    
                    with tab3:
                        # 検証結果
                        validation_results = st.session_state.get(f"{self.key}_validation_results")
                        if validation_results:
                            validation_valid, results = validation_results
                            
                            # 全体の結果をサマリー表示
                            if validation_valid:
                                st.success("✅ データは検証に合格しました")
                            else:
                                st.warning("⚠️ データに問題が見つかりました")
                            
                            # 警告とエラーを表示
                            issues = []
                            for result in results:
                                if result["severity"] == "error" and not result["is_valid"]:
                                    issues.append((result, "error"))
                                elif result["severity"] == "warning" and not result["is_valid"]:
                                    issues.append((result, "warning"))
                            
                            if issues:
                                st.write("#### 検出された問題")
                                for result, issue_type in issues:
                                    with st.expander(f"{'🚫' if issue_type == 'error' else '⚠️'} {result['rule_name']} ({result['severity']})"):
                                        st.write(f"**説明:** {result['description']}")
                                        for key, value in result["details"].items():
                                            if isinstance(value, list) and len(value) > 10:
                                                st.write(f"**{key}:** {value[:10]} ... (他 {len(value)-10} 件)")
                                            else:
                                                st.write(f"**{key}:** {value}")
                            else:
                                st.success("問題は検出されませんでした。データは有効です。")
                    
                    # 警告表示
                    warnings = st.session_state[f"{self.key}_import_warnings"]
                    if warnings:
                        with st.expander("警告メッセージ", expanded=False):
                            for warning in warnings:
                                st.warning(warning)
                else:
                    st.error("プレビューデータを取得できませんでした。")
            
            finally:
                # テンポラリファイルを削除
                os.unlink(tmp_path)
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("戻る", key=f"{self.key}_step5_back", on_click=self._go_to_step4)
        with col2:
            st.button("インポート", key=f"{self.key}_step5_next", on_click=self._go_to_step6, type="primary")
    
    def _render_step6_import(self):
        """ステップ6: インポート完了"""
        st.header("ステップ6: インポート完了")
        
        preview_container = st.session_state.get(f"{self.key}_preview_data")
        
        if preview_container:
            # インポートを完了
            st.session_state[f"{self.key}_imported_container"] = preview_container
            
            st.success("✅ データのインポートが完了しました！")
            
            # データの概要を表示
            df = preview_container.data
            
            # タブで表示を分ける
            tab1, tab2 = st.tabs(["データサマリー", "マップビュー"])
            
            with tab1:
                # インポート結果の統計情報
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("データポイント数", f"{len(df):,}")
                with col2:
                    time_range = preview_container.get_time_range()
                    duration_minutes = time_range['duration_seconds'] / 60
                    st.metric("記録時間", f"{duration_minutes:.1f} 分")
                with col3:
                    if 'speed' in df.columns:
                        max_speed = df['speed'].max()
                        st.metric("最高速度", f"{max_speed:.1f} m/s")
                    elif 'distance' in df.columns:
                        total_distance = df['distance'].max() / 1000  # mをkmに変換
                        st.metric("総距離", f"{total_distance:.2f} km")
                    else:
                        samples_per_minute = len(df) / (time_range['duration_seconds'] / 60)
                        st.metric("サンプル密度", f"{samples_per_minute:.1f} /分")
                
                st.write("### データ詳細")
                st.write(f"期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")
                st.write(f"緯度範囲: {df['latitude'].min():.6f} ～ {df['latitude'].max():.6f}")
                st.write(f"経度範囲: {df['longitude'].min():.6f} ～ {df['longitude'].max():.6f}")
                
                # メタデータ表示
                if preview_container.metadata:
                    st.write("### メタデータ")
                    metadata_df = pd.DataFrame({
                        "項目": preview_container.metadata.keys(),
                        "値": preview_container.metadata.values()
                    })
                    st.dataframe(metadata_df)
            
            with tab2:
                # マップ表示
                st.write("### 位置データマップ")
                map_data = df[["latitude", "longitude"]].copy()
                st.map(map_data)
            
            # コールバック関数を実行
            if self.on_import_complete:
                self.on_import_complete(preview_container)
        else:
            st.error("インポートするデータがありません。")
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        with col1:
            st.button("プレビューに戻る", key=f"{self.key}_step6_back", on_click=self._go_to_step5)
        with col2:
            st.button("新しいインポートを開始", key=f"{self.key}_step6_reset", on_click=self.reset, type="primary")
    
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
        # プレビューデータをリセット
        st.session_state[f"{self.key}_preview_data"] = None
        st.session_state[f"{self.key}_validation_results"] = None
    
    def _go_to_step6(self):
        """ステップ6へ移動"""
        st.session_state[f"{self.key}_step"] = 6
    
    def get_imported_container(self) -> Optional[GPSDataContainer]:
        """
        インポートされたデータコンテナを取得
        
        Returns
        -------
        Optional[GPSDataContainer]
            インポートされたデータコンテナ（インポートされていない場合はNone）
        """
        return st.session_state.get(f"{self.key}_imported_container")
    
    def _format_size(self, size_bytes: int) -> str:
        """
        バイト数を人間が読みやすい形式に変換
        
        Parameters
        ----------
        size_bytes : int
            バイト数
            
        Returns
        -------
        str
            人間が読みやすいサイズ表記
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"