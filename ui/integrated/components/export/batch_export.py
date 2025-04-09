"""
ui.integrated.components.export.batch_export

バッチエクスポートコンポーネント
複数のセッションやプロジェクトを一括でエクスポートする機能を提供します。
"""

import streamlit as st
import pandas as pd
import io
import base64
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

# 擬似的な進捗状況を管理するクラス
class ExportProgress:
    def __init__(self):
        self.progress = 0.0
        self.message = ""
        
    def update(self, progress: float, message: str):
        self.progress = progress
        self.message = message


class BatchExportComponent:
    """バッチエクスポートコンポーネント"""
    
    def __init__(self, key_prefix: str = "batch_export"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "batch_export"
        """
        self.key_prefix = key_prefix
        
        # サポートする出力形式
        self.supported_formats = {
            "csv": "CSV (カンマ区切りテキスト)",
            "json": "JSON (JavaScriptオブジェクト表記)",
            "gpx": "GPX (GPS交換フォーマット)",
            "excel": "Excel スプレッドシート"
        }
        
        # バッチジョブの進捗状況
        if f"{self.key_prefix}_progress" not in st.session_state:
            st.session_state[f"{self.key_prefix}_progress"] = {}
        
        # 完了したジョブの結果
        if f"{self.key_prefix}_results" not in st.session_state:
            st.session_state[f"{self.key_prefix}_results"] = []
    
    def render(self) -> Optional[Dict[str, Any]]:
        """
        バッチエクスポートUIの表示
        
        Returns
        -------
        Optional[Dict[str, Any]]
            エクスポート結果情報（実行された場合）
        """
        st.subheader("バッチエクスポート")
        
        # セッション/プロジェクト選択
        st.markdown("### エクスポート対象の選択")
        
        # エクスポートタイプの選択
        export_type = st.radio(
            "エクスポート対象",
            ["セッション", "プロジェクト"],
            horizontal=True,
            key=f"{self.key_prefix}_export_type"
        )
        
        # 選択UIの表示
        selected_items = []
        
        if export_type == "セッション":
            selected_items = self._render_session_selector()
        else:
            selected_items = self._render_project_selector()
        
        if not selected_items:
            st.info(f"エクスポートする{export_type}を選択してください。")
            return None
        
        # エクスポート設定
        st.markdown("### エクスポート設定")
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            # 出力形式の選択
            export_format = st.selectbox(
                "出力形式",
                options=list(self.supported_formats.keys()),
                format_func=lambda x: self.supported_formats.get(x, x),
                key=f"{self.key_prefix}_format"
            )
            
            # 出力設定
            output_option = st.radio(
                "出力方法",
                options=["個別ファイル", "結合ファイル", "ZIP圧縮"],
                index=0,
                key=f"{self.key_prefix}_output_option"
            )
            
            # 出力フォルダ名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_folder = f"sailing_export_{timestamp}"
            
            folder_name = st.text_input(
                "出力フォルダ名",
                value=default_folder,
                key=f"{self.key_prefix}_folder_name"
            )
        
        with col2:
            # データフィールド選択
            st.markdown("#### データフィールド")
            
            include_fields = {
                "GPS位置": st.checkbox("GPS位置", value=True, key=f"{self.key_prefix}_include_gps"),
                "速度": st.checkbox("速度", value=True, key=f"{self.key_prefix}_include_speed"),
                "方位": st.checkbox("方位", value=True, key=f"{self.key_prefix}_include_heading"),
                "風向": st.checkbox("風向", value=True, key=f"{self.key_prefix}_include_wind_dir"),
                "風速": st.checkbox("風速", value=True, key=f"{self.key_prefix}_include_wind_speed"),
                "タック/ジャイブポイント": st.checkbox("タック/ジャイブポイント", value=True, key=f"{self.key_prefix}_include_maneuvers"),
                "戦略ポイント": st.checkbox("戦略ポイント", value=True, key=f"{self.key_prefix}_include_strategy_points"),
                "メタデータ": st.checkbox("メタデータ", value=True, key=f"{self.key_prefix}_include_metadata")
            }
            
            selected_fields = [field for field, included in include_fields.items() if included]
            if not selected_fields:
                st.warning("少なくとも1つのデータフィールドを選択してください。")
        
        # 詳細設定
        with st.expander("詳細設定", expanded=False):
            # 形式別の設定
            if export_format == "csv":
                col1, col2 = st.columns(2)
                with col1:
                    delimiter = st.selectbox(
                        "区切り文字",
                        options=[",", ";", "\\t"],
                        format_func=lambda x: "カンマ (,)" if x == "," else "セミコロン (;)" if x == ";" else "タブ (\\t)",
                        key=f"{self.key_prefix}_delimiter"
                    )
                
                with col2:
                    encoding = st.selectbox(
                        "エンコーディング",
                        options=["utf-8", "shift-jis", "iso-8859-1"],
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
            
            elif export_format == "json":
                json_format = st.selectbox(
                    "JSON形式",
                    options=["pretty", "compact", "ndjson"],
                    format_func=lambda x: "インデント付き (読みやすい)" if x == "pretty" else "圧縮 (容量小)" if x == "compact" else "NDJSON (1行ごと)",
                    key=f"{self.key_prefix}_json_format"
                )
                
                iso_dates = st.checkbox(
                    "日時をISO形式に変換",
                    value=True,
                    key=f"{self.key_prefix}_iso_dates"
                )
            
            elif export_format == "gpx":
                gpx_version = st.selectbox(
                    "GPXバージョン",
                    options=["1.1", "1.0"],
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
            
            elif export_format == "excel":
                use_sheets = st.checkbox(
                    "セッションごとに別シートに分ける",
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
            
            # サンプリング設定
            st.markdown("#### サンプリング設定")
            
            sampling_rate = st.select_slider(
                "サンプリングレート",
                options=["元データ", "1Hz", "0.5Hz", "0.2Hz", "0.1Hz"],
                value="元データ",
                key=f"{self.key_prefix}_sampling_rate"
            )
            
            # 異常値処理
            st.markdown("#### 異常値処理")
            
            anomaly_treatment = st.radio(
                "異常値の扱い",
                options=["そのまま含める", "除外する", "補間する"],
                index=0,
                key=f"{self.key_prefix}_anomaly_treatment"
            )
            
            # 時間範囲の制限
            st.markdown("#### 時間範囲")
            use_time_filter = st.checkbox(
                "時間範囲で制限",
                value=False,
                key=f"{self.key_prefix}_use_time_filter"
            )
            
            if use_time_filter:
                time_range = st.slider(
                    "範囲選択",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    step=5,
                    key=f"{self.key_prefix}_time_range"
                )
                st.caption(f"時間範囲: {time_range[0]}% - {time_range[1]}%")
            
            # 出力ファイル命名規則
            st.markdown("#### ファイル命名規則")
            
            filename_template = st.text_input(
                "ファイル名テンプレート",
                value="{item_name}_{timestamp}",
                help="利用可能な変数: {item_name}, {item_id}, {timestamp}, {date}, {time}",
                key=f"{self.key_prefix}_filename_template"
            )
        
        # エクスポート実行ボタン
        if st.button("バッチエクスポート実行", key=f"{self.key_prefix}_export_btn", use_container_width=True):
            # エクスポート実行（バックグラウンド処理的な挙動）
            job_id = str(uuid.uuid4())
            
            # 進捗管理の初期化
            st.session_state[f"{self.key_prefix}_progress"][job_id] = ExportProgress()
            
            # バッチエクスポート処理（実際の実装ではこの部分は非同期処理になるでしょう）
            return self._run_batch_export(
                job_id=job_id,
                items=selected_items,
                export_type=export_type,
                format_type=export_format,
                output_option=output_option,
                folder_name=folder_name,
                fields=selected_fields,
                # その他の設定パラメータ
                delimiter=locals().get("delimiter", ","),
                encoding=locals().get("encoding", "utf-8"),
                include_header=locals().get("include_header", True),
                include_index=locals().get("include_index", False),
                json_format=locals().get("json_format", "pretty"),
                iso_dates=locals().get("iso_dates", True),
                gpx_version=locals().get("gpx_version", "1.1"),
                split_tracks=locals().get("split_tracks", False),
                include_extended=locals().get("include_extended", True),
                use_sheets=locals().get("use_sheets", True),
                apply_formatting=locals().get("apply_formatting", True),
                include_summary=locals().get("include_summary", True),
                sampling_rate=locals().get("sampling_rate", "元データ"),
                anomaly_treatment=locals().get("anomaly_treatment", "そのまま含める"),
                use_time_filter=locals().get("use_time_filter", False),
                time_range=locals().get("time_range", (0, 100)),
                filename_template=locals().get("filename_template", "{item_name}_{timestamp}")
            )
        
        # 進行中のエクスポートジョブがある場合は進捗状況を表示
        if st.session_state[f"{self.key_prefix}_progress"]:
            st.markdown("### 進行中のエクスポート")
            
            # 進行中のジョブを表示
            for job_id, progress in st.session_state[f"{self.key_prefix}_progress"].items():
                if progress.progress < 1.0:
                    # 進捗バー
                    st.progress(progress.progress)
                    st.text(progress.message)
                    
                    # キャンセルボタン
                    if st.button("キャンセル", key=f"{self.key_prefix}_cancel_{job_id}"):
                        # キャンセル処理（実際の実装ではジョブをキャンセル）
                        del st.session_state[f"{self.key_prefix}_progress"][job_id]
                        st.experimental_rerun()
        
        # 完了したエクスポートの表示
        if st.session_state[f"{self.key_prefix}_results"]:
            st.markdown("### 完了したエクスポート")
            
            # 最新の3つを表示
            for idx, result in enumerate(st.session_state[f"{self.key_prefix}_results"][-3:]):
                with st.expander(f"{result['timestamp']} - {result['export_type']} ({len(result['items'])}件)", expanded=idx == 0):
                    st.markdown(f"**エクスポート形式**: {result['format']}")
                    st.markdown(f"**出力方法**: {result['output_option']}")
                    st.markdown(f"**出力フォルダ**: {result['folder_name']}")
                    
                    # エクスポートしたアイテム
                    if len(result['items']) <= 5:
                        st.markdown(f"**エクスポートしたアイテム**: {', '.join(result['item_names'])}")
                    else:
                        st.markdown(f"**エクスポートしたアイテム**: {', '.join(result['item_names'][:3])} ... 他 {len(result['items']) - 3} 件")
                    
                    # ダウンロードリンク（利用可能な場合）
                    if 'download_link' in result:
                        st.markdown(result['download_link'], unsafe_allow_html=True)
                    
                    # 再実行ボタン
                    if st.button("同じ設定で再実行", key=f"{self.key_prefix}_rerun_{idx}"):
                        # 同じ設定で再実行（実際の実装では設定を復元して再実行）
                        st.session_state[f"{self.key_prefix}_export_type"] = result['export_type']
                        st.experimental_rerun()
        
        return None
    
    def _render_session_selector(self) -> List[str]:
        """
        セッション選択UIの表示
        
        Returns
        -------
        List[str]
            選択されたセッションのID
        """
        # 選択モード
        selection_mode = st.radio(
            "セッション選択モード",
            ["個別選択", "日付範囲", "プロジェクト単位", "タグとカテゴリ"],
            horizontal=True,
            key=f"{self.key_prefix}_session_selection_mode"
        )
        
        # サンプルセッションデータ（実際の実装ではセッションマネージャーから取得）
        available_sessions = [
            {"id": "session1", "name": "2025/03/27 レース練習", "date": "2025-03-27", "project": "東京湾トレーニング", "category": "レース", "tags": ["風強", "晴れ"]},
            {"id": "session2", "name": "2025/03/25 風向変化トレーニング", "date": "2025-03-25", "project": "東京湾トレーニング", "category": "トレーニング", "tags": ["風変化", "曇り"]},
            {"id": "session3", "name": "2025/03/20 スピードテスト", "date": "2025-03-20", "project": "富士山麓", "category": "テスト", "tags": ["風弱", "晴れ"]},
            {"id": "session4", "name": "2025/03/15 戦術練習", "date": "2025-03-15", "project": "相模湾", "category": "トレーニング", "tags": ["風中", "波高"]},
            {"id": "session5", "name": "2025/03/10 風上風下走行", "date": "2025-03-10", "project": "相模湾", "category": "基礎訓練", "tags": ["風中", "晴れ"]},
            {"id": "session6", "name": "2025/03/05 マーク回航練習", "date": "2025-03-05", "project": "東京湾トレーニング", "category": "基礎訓練", "tags": ["風弱", "曇り"]},
            {"id": "session7", "name": "2025/03/01 スタート練習", "date": "2025-03-01", "project": "相模湾", "category": "レース", "tags": ["風強", "波高"]}
        ]
        
        selected_sessions = []
        
        # 選択モードに応じたUI
        if selection_mode == "個別選択":
            # セッションの個別選択
            options = {s["name"]: s["id"] for s in available_sessions}
            selected_names = st.multiselect(
                "エクスポートするセッション",
                options=list(options.keys()),
                key=f"{self.key_prefix}_selected_sessions"
            )
            
            selected_sessions = [options[name] for name in selected_names]
            
            # 選択されたセッションの数を表示
            if selected_sessions:
                st.info(f"{len(selected_sessions)}個のセッションが選択されています。")
            
        elif selection_mode == "日付範囲":
            # 日付範囲での選択
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "開始日",
                    value=datetime.strptime("2025-03-01", "%Y-%m-%d").date(),
                    key=f"{self.key_prefix}_start_date"
                )
            
            with col2:
                end_date = st.date_input(
                    "終了日",
                    value=datetime.strptime("2025-03-31", "%Y-%m-%d").date(),
                    key=f"{self.key_prefix}_end_date"
                )
            
            # 日付範囲内のセッションをフィルタリング
            for session in available_sessions:
                session_date = datetime.strptime(session["date"], "%Y-%m-%d").date()
                if start_date <= session_date <= end_date:
                    selected_sessions.append(session["id"])
            
            # 選択されたセッションの表示
            if selected_sessions:
                st.info(f"{len(selected_sessions)}個のセッションが選択されています。")
                selected_names = [s["name"] for s in available_sessions if s["id"] in selected_sessions]
                st.markdown("#### 選択されたセッション:")
                for idx, name in enumerate(selected_names):
                    if idx < 5:  # 先頭5つだけ表示
                        st.markdown(f"- {name}")
                if len(selected_names) > 5:
                    st.markdown(f"- *他 {len(selected_names) - 5} 件*")
            else:
                st.warning("指定された日付範囲内にセッションがありません。")
        
        elif selection_mode == "プロジェクト単位":
            # プロジェクトの一覧を取得
            projects = list(set(s["project"] for s in available_sessions))
            
            # プロジェクトの選択
            selected_projects = st.multiselect(
                "エクスポートするプロジェクト",
                options=projects,
                key=f"{self.key_prefix}_selected_projects"
            )
            
            # 選択されたプロジェクトに含まれるセッションをフィルタリング
            for session in available_sessions:
                if session["project"] in selected_projects:
                    selected_sessions.append(session["id"])
            
            # 選択されたセッションの表示
            if selected_sessions:
                st.info(f"{len(selected_sessions)}個のセッションが選択されています。")
            else:
                st.warning("選択されたプロジェクトにセッションがありません。")
        
        elif selection_mode == "タグとカテゴリ":
            # タグとカテゴリの一覧を取得
            all_tags = list(set(tag for s in available_sessions for tag in s["tags"]))
            all_categories = list(set(s["category"] for s in available_sessions))
            
            # タグとカテゴリの選択
            col1, col2 = st.columns(2)
            
            with col1:
                selected_tags = st.multiselect(
                    "タグで絞り込み",
                    options=all_tags,
                    key=f"{self.key_prefix}_selected_tags"
                )
            
            with col2:
                selected_categories = st.multiselect(
                    "カテゴリで絞り込み",
                    options=all_categories,
                    key=f"{self.key_prefix}_selected_categories"
                )
            
            # 選択条件の組み合わせ方法
            filter_mode = st.radio(
                "条件の組み合わせ",
                options=["AND（すべての条件を満たす）", "OR（いずれかの条件を満たす）"],
                index=1,
                horizontal=True,
                key=f"{self.key_prefix}_filter_mode"
            )
            
            # セッションのフィルタリング
            for session in available_sessions:
                # タグの条件
                tag_match = not selected_tags or any(tag in session["tags"] for tag in selected_tags)
                
                # カテゴリの条件
                category_match = not selected_categories or session["category"] in selected_categories
                
                # 条件の組み合わせ
                if filter_mode == "AND（すべての条件を満たす）":
                    if tag_match and category_match:
                        selected_sessions.append(session["id"])
                else:  # OR
                    if tag_match or category_match:
                        selected_sessions.append(session["id"])
            
            # 選択されたセッションの表示
            if selected_sessions:
                st.info(f"{len(selected_sessions)}個のセッションが選択されています。")
                selected_names = [s["name"] for s in available_sessions if s["id"] in selected_sessions]
                
                # セッションの一覧表示
                if len(selected_names) <= 10:
                    st.markdown("#### 選択されたセッション:")
                    for name in selected_names:
                        st.markdown(f"- {name}")
                else:
                    st.markdown(f"#### 選択されたセッション: ({len(selected_names)}件)")
                    for idx, name in enumerate(selected_names):
                        if idx < 5:  # 先頭5つ
                            st.markdown(f"- {name}")
                    st.markdown("...")
                    for idx, name in enumerate(selected_names[-5:]):  # 末尾5つ
                        st.markdown(f"- {name}")
            else:
                st.warning("選択条件に一致するセッションがありません。")
        
        return selected_sessions
    
    def _render_project_selector(self) -> List[str]:
        """
        プロジェクト選択UIの表示
        
        Returns
        -------
        List[str]
            選択されたプロジェクトのID
        """
        # サンプルプロジェクトデータ（実際の実装ではプロジェクトマネージャーから取得）
        available_projects = [
            {"id": "project1", "name": "東京湾トレーニング", "session_count": 3, "date": "2025-03-27"},
            {"id": "project2", "name": "相模湾", "session_count": 3, "date": "2025-03-15"},
            {"id": "project3", "name": "富士山麓", "session_count": 1, "date": "2025-03-20"}
        ]
        
        # プロジェクトの選択
        options = {f"{p['name']} ({p['session_count']}セッション)": p["id"] for p in available_projects}
        selected_names = st.multiselect(
            "エクスポートするプロジェクト",
            options=list(options.keys()),
            key=f"{self.key_prefix}_selected_projects"
        )
        
        selected_projects = [options[name] for name in selected_names]
        
        # 選択されたプロジェクトの数を表示
        if selected_projects:
            st.info(f"{len(selected_projects)}個のプロジェクトが選択されています。")
        
        return selected_projects
    
    def _run_batch_export(self, job_id: str, items: List[str], export_type: str, 
                         format_type: str, output_option: str, folder_name: str, 
                         fields: List[str], **kwargs) -> Optional[Dict[str, Any]]:
        """
        バッチエクスポート処理の実行
        
        Parameters
        ----------
        job_id : str
            ジョブID
        items : List[str]
            エクスポート対象のアイテムID
        export_type : str
            エクスポート対象のタイプ("セッション"または"プロジェクト")
        format_type : str
            エクスポート形式
        output_option : str
            出力方法("個別ファイル", "結合ファイル", "ZIP圧縮")
        folder_name : str
            出力フォルダ名
        fields : List[str]
            エクスポートするデータフィールド
        **kwargs : Dict[str, Any]
            その他の設定パラメータ
            
        Returns
        -------
        Optional[Dict[str, Any]]
            エクスポート結果情報
        """
        # 進捗ステータスの取得
        progress_obj = st.session_state[f"{self.key_prefix}_progress"][job_id]
        
        # プログレスバーの表示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 進捗更新の内部関数
        def update_progress(progress: float, message: str):
            progress_obj.update(progress, message)
            progress_bar.progress(progress)
            status_text.text(message)
        
        # 進捗初期状態
        update_progress(0.0, "エクスポート準備中...")
        
        try:
            # アイテム情報の取得（実際の実装ではデータベースから取得）
            # ここではサンプルデータを使用
            item_names = []
            
            if export_type == "セッション":
                # サンプルセッションデータ
                available_sessions = [
                    {"id": "session1", "name": "2025/03/27 レース練習"},
                    {"id": "session2", "name": "2025/03/25 風向変化トレーニング"},
                    {"id": "session3", "name": "2025/03/20 スピードテスト"},
                    {"id": "session4", "name": "2025/03/15 戦術練習"},
                    {"id": "session5", "name": "2025/03/10 風上風下走行"},
                    {"id": "session6", "name": "2025/03/05 マーク回航練習"},
                    {"id": "session7", "name": "2025/03/01 スタート練習"}
                ]
                
                # 選択されたセッションの名前を取得
                session_dict = {s["id"]: s for s in available_sessions}
                for item_id in items:
                    if item_id in session_dict:
                        item_names.append(session_dict[item_id]["name"])
            
            else:  # プロジェクト
                # サンプルプロジェクトデータ
                available_projects = [
                    {"id": "project1", "name": "東京湾トレーニング"},
                    {"id": "project2", "name": "相模湾"},
                    {"id": "project3", "name": "富士山麓"}
                ]
                
                # 選択されたプロジェクトの名前を取得
                project_dict = {p["id"]: p for p in available_projects}
                for item_id in items:
                    if item_id in project_dict:
                        item_names.append(project_dict[item_id]["name"])
            
            # 進捗更新
            update_progress(0.1, "データの準備中...")
            time.sleep(0.5)  # 処理時間のシミュレーション
            
            # エクスポートオプションの表示
            message = f"{len(items)}個の{export_type}を{format_type}形式でエクスポート中..."
            update_progress(0.2, message)
            time.sleep(0.5)  # 処理時間のシミュレーション
            
            # アイテムごとの処理（実際はここで各アイテムのエクスポート処理）
            for i, item_id in enumerate(items):
                progress = 0.2 + (0.7 * (i + 1) / len(items))
                update_progress(progress, f"{i+1}/{len(items)} - {item_names[i]} をエクスポート中...")
                time.sleep(0.5)  # 処理時間のシミュレーション
            
            # 完了処理
            update_progress(0.9, "エクスポート完了！ファイルの準備中...")
            time.sleep(0.5)  # 処理時間のシミュレーション
            
            # エクスポート成功
            update_progress(1.0, "エクスポート完了！")
            
            # ダウンロードリンクの生成（実際の実装ではファイルを生成してダウンロードリンクを作成）
            download_link = self._generate_download_link(format_type, output_option, folder_name)
            
            # ジョブ完了後は進捗状況から削除
            del st.session_state[f"{self.key_prefix}_progress"][job_id]
            
            # 結果情報
            result = {
                "id": job_id,
                "export_type": export_type,
                "items": items,
                "item_names": item_names,
                "format": format_type,
                "output_option": output_option,
                "folder_name": folder_name,
                "fields": fields,
                "download_link": download_link,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # 結果を保存
            st.session_state[f"{self.key_prefix}_results"].append(result)
            
            # 結果がある程度溜まったら古いものを削除
            if len(st.session_state[f"{self.key_prefix}_results"]) > 10:
                st.session_state[f"{self.key_prefix}_results"] = st.session_state[f"{self.key_prefix}_results"][-10:]
            
            return result
            
        except Exception as e:
            # エラー処理
            update_progress(1.0, f"エクスポート失敗: {str(e)}")
            
            # ジョブ完了後は進捗状況から削除
            del st.session_state[f"{self.key_prefix}_progress"][job_id]
            
            # エラー情報
            return {
                "id": job_id,
                "export_type": export_type,
                "items": items,
                "item_names": item_names if "item_names" in locals() else [],
                "format": format_type,
                "output_option": output_option,
                "folder_name": folder_name,
                "fields": fields,
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
    
    def _generate_download_link(self, format_type: str, output_option: str, folder_name: str) -> str:
        """
        ダウンロードリンクの生成（デモ用）
        
        Parameters
        ----------
        format_type : str
            エクスポート形式
        output_option : str
            出力方法
        folder_name : str
            出力フォルダ名
            
        Returns
        -------
        str
            HTMLダウンロードリンク
        """
        # デモ用のバイナリデータ（実際の実装では実際のファイルデータ）
        if output_option == "ZIP圧縮":
            # ZIPファイルのダミーデータ
            data = b"ZIP file placeholder"
            filename = f"{folder_name}.zip"
            mime_type = "application/zip"
        elif output_option == "結合ファイル":
            # 結合ファイルのダミーデータ
            if format_type == "csv":
                data = b"Combined CSV data"
                filename = f"{folder_name}.csv"
                mime_type = "text/csv"
            elif format_type == "json":
                data = b"Combined JSON data"
                filename = f"{folder_name}.json"
                mime_type = "application/json"
            elif format_type == "gpx":
                data = b"Combined GPX data"
                filename = f"{folder_name}.gpx"
                mime_type = "application/gpx+xml"
            elif format_type == "excel":
                data = b"Combined Excel data"
                filename = f"{folder_name}.xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                data = b"Generic data"
                filename = f"{folder_name}.txt"
                mime_type = "text/plain"
        else:  # 個別ファイル
            # 個別ファイルのダミーデータ（実際はZIPか何かで圧縮）
            data = b"Multiple files placeholder"
            filename = f"{folder_name}.zip"
            mime_type = "application/zip"
        
        # Base64エンコード
        b64 = base64.b64encode(data).decode()
        
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
                <span>エクスポートデータをダウンロード ({output_option})</span>
            </a>
        </div>
        """
        
        return styled_link
