"""
ui.integrated.components.export.data_export

データエクスポートコンポーネント
セッション、プロジェクト、分析結果のエクスポート機能を提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from sailing_data_processor.storage.export_import import ExportImportManager, convert_df_to_csv_download

class DataExportComponent:
    """データエクスポートコンポーネント"""
    
    def __init__(self, key_prefix: str = "data_export"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "data_export"
        """
        self.key_prefix = key_prefix
        self.export_manager = ExportImportManager()
        self.supported_formats = {
            "csv": "CSV (カンマ区切りテキスト)",
            "json": "JSON (JavaScriptオブジェクト表記)",
            "gpx": "GPX (GPS交換フォーマット)",
            "xlsx": "Excel スプレッドシート"
        }
    
    def render(self, session_data: Optional[Dict[str, Any]] = None, 
               projects_data: Optional[Dict[str, Any]] = None,
               analysis_results: Optional[Dict[str, Any]] = None):
        """
        データエクスポートUIの表示
        
        Parameters
        ----------
        session_data : Optional[Dict[str, Any]], optional
            エクスポート可能なセッションデータ, by default None
        projects_data : Optional[Dict[str, Any]], optional
            エクスポート可能なプロジェクトデータ, by default None
        analysis_results : Optional[Dict[str, Any]], optional
            エクスポート可能な分析結果, by default None
        
        Returns
        -------
        Dict[str, Any]
            エクスポート設定と結果
        """
        st.subheader("データエクスポート")
        
        # エクスポート対象の選択
        export_type = st.radio(
            "エクスポート対象",
            ["セッション", "プロジェクト", "分析結果"],
            horizontal=True,
            key=f"{self.key_prefix}_type"
        )
        
        # エクスポート対象のデータ確認
        if export_type == "セッション" and not session_data:
            st.warning("エクスポート可能なセッションがありません。先にデータをインポートしてください。")
            return None
        
        if export_type == "プロジェクト" and not projects_data:
            st.warning("エクスポート可能なプロジェクトがありません。先にプロジェクトを作成してください。")
            return None
        
        if export_type == "分析結果" and not analysis_results:
            st.warning("エクスポート可能な分析結果がありません。先に分析を実行してください。")
            return None
        
        # データ選択UI
        selected_items = self._render_data_selector(export_type, session_data, projects_data, analysis_results)
        
        if not selected_items:
            st.info(f"エクスポートする{export_type}を選択してください。")
            return None
        
        # エクスポート形式と設定
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "エクスポート形式",
                list(self.supported_formats.keys()),
                format_func=lambda x: self.supported_formats[x],
                key=f"{self.key_prefix}_format"
            )
            
            # 出力ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"sailing_{export_type.lower()}_{timestamp}"
            
            filename = st.text_input(
                "ファイル名",
                value=default_filename,
                key=f"{self.key_prefix}_filename"
            )
        
        with col2:
            st.markdown("#### エクスポート内容の設定")
            
            # エクスポートタイプごとの設定
            if export_type == "セッション":
                include_metadata = st.checkbox(
                    "メタデータを含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_metadata"
                )
                
                include_analysis = st.checkbox(
                    "関連する分析結果を含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_analysis"
                )
                
                # 時間範囲の制限（オプション）
                use_time_range = st.checkbox(
                    "時間範囲を制限", 
                    value=False,
                    key=f"{self.key_prefix}_use_time_range"
                )
                
                time_range = None
                if use_time_range:
                    time_range = st.slider(
                        "時間範囲 (%)",
                        min_value=0,
                        max_value=100,
                        value=(0, 100),
                        step=5,
                        key=f"{self.key_prefix}_time_range"
                    )
                
            elif export_type == "プロジェクト":
                include_sessions = st.checkbox(
                    "関連するセッションを含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_sessions"
                )
                
                include_analysis = st.checkbox(
                    "分析結果を含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_analysis"
                )
                
            elif export_type == "分析結果":
                include_source_data = st.checkbox(
                    "ソースデータを含める", 
                    value=False,
                    key=f"{self.key_prefix}_include_source"
                )
                
                include_visualizations = st.checkbox(
                    "可視化データを含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_viz"
                )
        
        # 形式ごとの詳細設定（拡張可能）
        with st.expander("詳細設定", expanded=False):
            # CSVエクスポートの設定
            if export_format == "csv":
                col1, col2 = st.columns(2)
                with col1:
                    delimiter = st.selectbox(
                        "区切り文字",
                        [",", ";", "\\t"],
                        format_func=lambda x: "カンマ (,)" if x == "," else "セミコロン (;)" if x == ";" else "タブ (\\t)",
                        key=f"{self.key_prefix}_delimiter"
                    )
                
                with col2:
                    encoding = st.selectbox(
                        "エンコーディング",
                        ["utf-8", "shift-jis", "iso-8859-1"],
                        key=f"{self.key_prefix}_encoding"
                    )
                
                include_header = st.checkbox(
                    "ヘッダー行を含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_header"
                )
                
                include_index = st.checkbox(
                    "インデックス列を含める", 
                    value=False,
                    key=f"{self.key_prefix}_include_index"
                )
            
            # JSONエクスポートの設定
            elif export_format == "json":
                json_format = st.selectbox(
                    "JSON形式",
                    ["pretty", "compact", "ndjson"],
                    format_func=lambda x: "インデント付き (読みやすい)" if x == "pretty" else "圧縮 (容量小)" if x == "compact" else "NDJSON (1行ごと)",
                    key=f"{self.key_prefix}_json_format"
                )
                
                iso_dates = st.checkbox(
                    "日時をISO形式に変換", 
                    value=True,
                    key=f"{self.key_prefix}_iso_dates"
                )
            
            # GPXエクスポートの設定
            elif export_format == "gpx":
                gpx_version = st.selectbox(
                    "GPXバージョン",
                    ["1.1", "1.0"],
                    key=f"{self.key_prefix}_gpx_version"
                )
                
                split_tracks = st.checkbox(
                    "トラックの分割", 
                    value=False,
                    key=f"{self.key_prefix}_split_tracks"
                )
                
                include_extended = st.checkbox(
                    "拡張データを含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_extended"
                )
            
            # Excelエクスポートの設定
            elif export_format == "xlsx":
                use_sheets = st.checkbox(
                    "データを別シートに分ける", 
                    value=True,
                    key=f"{self.key_prefix}_use_sheets"
                )
                
                apply_formatting = st.checkbox(
                    "書式設定を適用", 
                    value=True,
                    key=f"{self.key_prefix}_apply_formatting"
                )
                
                include_summary = st.checkbox(
                    "サマリーシートを含める", 
                    value=True,
                    key=f"{self.key_prefix}_include_summary"
                )
        
        # エクスポート実行ボタン
        if st.button("エクスポート実行", key=f"{self.key_prefix}_export_btn", use_container_width=True):
            # ダミーデータを使用してエクスポート処理（実際の実装では選択したデータを使用）
            export_data, exported_filename = self._perform_export(
                export_type, 
                selected_items, 
                export_format, 
                filename
            )
            
            if export_data:
                # ダウンロードリンクの作成
                download_link = self._create_download_link(export_data, exported_filename, export_format)
                st.success(f"{len(selected_items)}個の{export_type}をエクスポートしました。")
                st.markdown(download_link, unsafe_allow_html=True)
                
                # エクスポート履歴に追加（実際の実装ではここで履歴を保存）
                return {
                    "type": export_type,
                    "items": selected_items,
                    "format": export_format,
                    "filename": exported_filename,
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    def _render_data_selector(self, export_type: str, 
                             session_data: Optional[Dict[str, Any]], 
                             projects_data: Optional[Dict[str, Any]],
                             analysis_results: Optional[Dict[str, Any]]) -> List[str]:
        """
        データ選択UIの表示
        
        Parameters
        ----------
        export_type : str
            エクスポート対象タイプ
        session_data : Optional[Dict[str, Any]]
            セッションデータ
        projects_data : Optional[Dict[str, Any]]
            プロジェクトデータ
        analysis_results : Optional[Dict[str, Any]]
            分析結果データ
        
        Returns
        -------
        List[str]
            選択されたアイテムのID
        """
        # 実際の実装では、与えられたデータから選択肢を生成
        # ここではダミーデータを使用
        
        if export_type == "セッション":
            # サンプルのセッションリスト（実際はsession_dataから生成）
            sessions = [
                {"id": "session1", "name": "2025/03/27 レース練習", "date": "2025-03-27"},
                {"id": "session2", "name": "2025/03/25 風向変化トレーニング", "date": "2025-03-25"},
                {"id": "session3", "name": "2025/03/20 スピードテスト", "date": "2025-03-20"},
                {"id": "session4", "name": "2025/03/15 戦術練習", "date": "2025-03-15"},
                {"id": "session5", "name": "2025/03/10 風上風下走行", "date": "2025-03-10"}
            ]
            
            # セッションの選択
            selection_mode = st.radio(
                "選択モード",
                ["個別選択", "範囲選択", "条件選択"],
                horizontal=True,
                key=f"{self.key_prefix}_session_select_mode"
            )
            
            selected_items = []
            
            if selection_mode == "個別選択":
                # セッションの個別選択
                options = {f"{s['name']} ({s['date']})": s["id"] for s in sessions}
                selected_sessions = st.multiselect(
                    "エクスポートするセッション",
                    options.keys(),
                    key=f"{self.key_prefix}_selected_sessions"
                )
                
                selected_items = [options[s] for s in selected_sessions]
                
            elif selection_mode == "範囲選択":
                # 日付範囲での選択
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "開始日",
                        value=datetime.strptime("2025-03-10", "%Y-%m-%d").date(),
                        key=f"{self.key_prefix}_start_date"
                    )
                
                with col2:
                    end_date = st.date_input(
                        "終了日",
                        value=datetime.strptime("2025-03-27", "%Y-%m-%d").date(),
                        key=f"{self.key_prefix}_end_date"
                    )
                
                # 日付範囲内のセッションを選択（サンプル実装）
                for session in sessions:
                    session_date = datetime.strptime(session["date"], "%Y-%m-%d").date()
                    if start_date <= session_date <= end_date:
                        selected_items.append(session["id"])
                
                # 選択されたセッションの表示
                if selected_items:
                    selected_names = [s["name"] for s in sessions if s["id"] in selected_items]
                    st.markdown("**選択されたセッション:**")
                    for name in selected_names:
                        st.markdown(f"- {name}")
                
            elif selection_mode == "条件選択":
                # 条件による選択
                search_term = st.text_input(
                    "セッション名に含まれる文字列",
                    key=f"{self.key_prefix}_search_term"
                )
                
                session_types = st.multiselect(
                    "セッションタイプ",
                    ["レース", "トレーニング", "スピードテスト", "戦術練習"],
                    key=f"{self.key_prefix}_session_types"
                )
                
                # 条件に合うセッションを選択（サンプル実装）
                for session in sessions:
                    # 名前による絞り込み
                    name_match = True
                    if search_term:
                        name_match = search_term.lower() in session["name"].lower()
                    
                    # タイプによる絞り込み
                    type_match = True
                    if session_types:
                        type_match = any(t.lower() in session["name"].lower() for t in session_types)
                    
                    if name_match and type_match:
                        selected_items.append(session["id"])
                
                # 選択されたセッションの表示
                if selected_items:
                    selected_names = [s["name"] for s in sessions if s["id"] in selected_items]
                    st.markdown("**選択されたセッション:**")
                    for name in selected_names:
                        st.markdown(f"- {name}")
        
        elif export_type == "プロジェクト":
            # サンプルのプロジェクトリスト（実際はprojects_dataから生成）
            projects = [
                {"id": "project1", "name": "東京湾トレーニング", "session_count": 5},
                {"id": "project2", "name": "秋季レース解析", "session_count": 3},
                {"id": "project3", "name": "風向変化テスト", "session_count": 2}
            ]
            
            # プロジェクトの選択
            options = {f"{p['name']} ({p['session_count']}セッション)": p["id"] for p in projects}
            selected_projects = st.multiselect(
                "エクスポートするプロジェクト",
                options.keys(),
                key=f"{self.key_prefix}_selected_projects"
            )
            
            selected_items = [options[p] for p in selected_projects]
        
        elif export_type == "分析結果":
            # サンプルの分析結果リスト（実際はanalysis_resultsから生成）
            results = [
                {"id": "result1", "name": "風向変化分析", "date": "2025-03-25", "type": "風分析"},
                {"id": "result2", "name": "戦略ポイント検出", "date": "2025-03-26", "type": "戦略分析"},
                {"id": "result3", "name": "パフォーマンス分析", "date": "2025-03-27", "type": "性能分析"}
            ]
            
            # 分析タイプによるフィルタリング
            analysis_types = st.multiselect(
                "分析タイプ",
                ["風分析", "戦略分析", "性能分析"],
                default=["風分析", "戦略分析", "性能分析"],
                key=f"{self.key_prefix}_analysis_types"
            )
            
            # フィルタリングされた分析結果
            filtered_results = [r for r in results if r["type"] in analysis_types]
            
            # 分析結果の選択
            options = {f"{r['name']} ({r['date']})": r["id"] for r in filtered_results}
            selected_analyses = st.multiselect(
                "エクスポートする分析結果",
                options.keys(),
                key=f"{self.key_prefix}_selected_analyses"
            )
            
            selected_items = [options[a] for a in selected_analyses]
        
        return selected_items
    
    def _perform_export(self, export_type: str, selected_items: List[str], 
                       export_format: str, filename: str) -> Tuple[bytes, str]:
        """
        エクスポート処理の実行
        
        Parameters
        ----------
        export_type : str
            エクスポート対象タイプ
        selected_items : List[str]
            選択されたアイテムのID
        export_format : str
            エクスポート形式
        filename : str
            出力ファイル名
        
        Returns
        -------
        Tuple[bytes, str]
            エクスポートデータのバイト列とファイル名
        """
        # サンプルデータの生成（実際の実装では選択したアイテムを使用）
        
        # ダミーのDataFrameを生成
        index = pd.date_range(start='2025-03-27 13:00:00', periods=100, freq='30s')
        
        np.random.seed(42)
        data = pd.DataFrame({
            'latitude': 35.3000 + np.cumsum(np.random.normal(0, 0.0001, 100)),
            'longitude': 139.4800 + np.cumsum(np.random.normal(0, 0.0001, 100)),
            'speed_kt': np.abs(np.random.normal(6.0, 1.5, 100)),
            'heading_deg': (np.cumsum(np.random.normal(0, 5, 100)) % 360),
            'wind_dir_deg': (np.random.normal(210, 15, 100) % 360),
            'wind_speed_kt': np.abs(np.random.normal(12.0, 2.0, 100))
        }, index=index)
        
        # 形式に応じたエクスポート
        if export_format == "csv":
            csv_data = data.to_csv(index=True).encode('utf-8')
            return csv_data, f"{filename}.csv"
        
        elif export_format == "json":
            # DataFrameをJSON形式に変換
            json_data = data.reset_index().to_json(orient='records', date_format='iso')
            
            # メタデータを追加
            export_json = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "export_type": export_type,
                    "item_count": len(selected_items)
                },
                "data": json.loads(json_data)
            }
            
            json_bytes = json.dumps(export_json, indent=2).encode('utf-8')
            return json_bytes, f"{filename}.json"
        
        elif export_format == "gpx":
            # 簡易GPXファイルの生成
            gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="SailingStrategyAnalyzer">
    <metadata>
        <name>Sailing Session Export</name>
        <time>2025-03-27T13:00:00Z</time>
    </metadata>
    <trk>
        <name>Sample Track</name>
        <trkseg>
        """
            
            # いくつかのポイントを追加
            for i in range(min(10, len(data))):
                row = data.iloc[i]
                timestamp = data.index[i].isoformat() if isinstance(data.index[i], pd.Timestamp) else ""
                
                gpx_content += f"""
            <trkpt lat="{row['latitude']}" lon="{row['longitude']}">
                <ele>0</ele>
                <time>{timestamp}</time>
                <extensions>
                    <speed>{row['speed_kt']}</speed>
                    <course>{row['heading_deg']}</course>
                    <wind_dir>{row['wind_dir_deg']}</wind_dir>
                    <wind_speed>{row['wind_speed_kt']}</wind_speed>
                </extensions>
            </trkpt>"""
            
            # GPXファイルを閉じる
            gpx_content += """
        </trkseg>
    </trk>
</gpx>"""
            
            return gpx_content.encode('utf-8'), f"{filename}.gpx"
        
        elif export_format == "xlsx":
            # 実際の実装ではExcelファイルを生成
            # ここではダミーデータを返す
            return b"Excel data placeholder", f"{filename}.xlsx"
        
        # デフォルト
        return b"Export data placeholder", f"{filename}.bin"
    
    def _create_download_link(self, data: bytes, filename: str, format_type: str) -> str:
        """
        ダウンロードリンクの生成
        
        Parameters
        ----------
        data : bytes
            ダウンロードするデータ
        filename : str
            ファイル名
        format_type : str
            ファイル形式
        
        Returns
        -------
        str
            HTMLダウンロードリンク
        """
        b64 = base64.b64encode(data).decode()
        
        # MIMEタイプの設定
        mime_types = {
            "csv": "text/csv",
            "json": "application/json",
            "gpx": "application/gpx+xml",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        mime_type = mime_types.get(format_type, "application/octet-stream")
        
        # スタイル付きのダウンロードボタン
        styled_link = f"""
        <div style="text-align: center; margin: 10px 0;">
            <a href="data:{mime_type};base64,{b64}" 
               download="{filename}" 
               style="display: inline-block; 
                      background-color: #4CAF50; 
                      color: white; 
                      padding: 10px 20px; 
                      text-align: center; 
                      text-decoration: none; 
                      font-size: 16px; 
                      margin: 4px 2px; 
                      cursor: pointer; 
                      border-radius: 4px;">
                <span>ファイルをダウンロード ({format_type.upper()})</span>
            </a>
        </div>
        """
        
        return styled_link
