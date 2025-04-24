# -*- coding: utf-8 -*-
"""
ui.components.export.batch_export_panel

バッチエクスポートのUIパネルコンポーネント
"""

import streamlit as st
import os
import time
import datetime
from typing import Dict, Any, List, Optional, Callable


class BatchExportPanel:
    """
    バッチエクスポートUIコンポーネント
    
    複数セッションを一括でエクスポートするためのウィザード形式のUIを提供します。
    セッション選択、エクスポート設定、処理状況表示機能を含みます。
    """
    
    def __init__(self, key="batch_export", 
                 export_manager=None, batch_exporter=None, 
                 session_manager=None,
                 on_export_complete=None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントキー
        export_manager : ExportManager, optional
            エクスポートマネージャー
        batch_exporter : BatchExporter, optional
            バッチエクスポーター
        session_manager : SessionManager, optional
            セッションマネージャー
        on_export_complete : Callable, optional
            エクスポート完了時のコールバック
        """
        self.key = key
        self.export_manager = export_manager
        self.batch_exporter = batch_exporter
        self.session_manager = session_manager
        self.on_export_complete = on_export_complete
        
        # 状態の初期化
        if f"{key}_step" not in st.session_state:
            st.session_state[f"{key}_step"] = 1
        if f"{key}_selected_sessions" not in st.session_state:
            st.session_state[f"{key}_selected_sessions"] = []
        if f"{key}_exporter_id" not in st.session_state:
            st.session_state[f"{key}_exporter_id"] = ""
        if f"{key}_template_name" not in st.session_state:
            st.session_state[f"{key}_template_name"] = "default"
        if f"{key}_options" not in st.session_state:
            st.session_state[f"{key}_options"] = {}
        if f"{key}_output_dir" not in st.session_state:
            st.session_state[f"{key}_output_dir"] = ""
        if f"{key}_filename_template" not in st.session_state:
            st.session_state[f"{key}_filename_template"] = "{session_name}_{timestamp}"
        if f"{key}_current_job_id" not in st.session_state:
            st.session_state[f"{key}_current_job_id"] = None
        if f"{key}_job_status" not in st.session_state:
            st.session_state[f"{key}_job_status"] = None
    
    def render(self, available_sessions=None):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        available_sessions : List, optional
            選択可能なセッションのリスト
        """
        st.subheader("バッチエクスポート")
        
        # 進行ステップの表示
        current_step = st.session_state[f"{self.key}_step"]
        self._render_step_indicator(current_step)
        
        # 現在のステップに応じて表示
        if current_step == 1:
            self._render_step1_select_sessions(available_sessions)
        elif current_step == 2:
            self._render_step2_export_settings()
        elif current_step == 3:
            self._render_step3_output_settings()
        elif current_step == 4:
            self._render_step4_progress_and_results()
    
    def _render_step_indicator(self, current_step):
        """ステップインジケーターの表示"""
        steps = ["セッション選択", "エクスポート設定", "出力設定", "処理・結果"]
        cols = st.columns(len(steps))
        
        for i, (col, step_name) in enumerate(zip(cols, steps), 1):
            if i < current_step:
                col.markdown(f"✅ **{step_name}**")
            elif i == current_step:
                col.markdown(f"🔵 **{step_name}**")
            else:
                col.markdown(f"⚪ {step_name}")
    
    def _render_step1_select_sessions(self, available_sessions):
        """ステップ1: セッション選択の表示"""
        st.markdown("### 1. エクスポートするセッションを選択")
        
        # セッションのリスト取得
        sessions = available_sessions
        if sessions is None and self.session_manager:
            try:
                sessions = self.session_manager.get_all_sessions()
            except Exception as e:
                st.error(f"セッションの取得に失敗しました: {str(e)}")
                sessions = []
        
        if not sessions:
            st.warning("利用可能なセッションがありません。")
            return
        
        # セッション一覧の表示
        st.markdown("エクスポートするセッションを選択してください。")
        
        # 表示方法の選択
        display_option = st.radio(
            "表示方法",
            ["リスト表示", "カテゴリ表示", "タグ表示"],
            horizontal=True
        )
        
        selected_sessions = []
        
        if display_option == "リスト表示":
            # 全セッションをリスト表示
            session_options = {}
            for session in sessions:
                label = f"{session.name} ({session.category or '未分類'}, {session.status or '状態なし'})"
                session_options[session.session_id] = label
            
            # 「すべて選択」チェックボックス
            select_all = st.checkbox("すべて選択", key=f"{self.key}_select_all")
            if select_all:
                selected_session_ids = list(session_options.keys())
            else:
                # 検索フィルター
                search_term = st.text_input("セッション名で検索", key=f"{self.key}_session_search")
                filtered_options = {}
                if search_term:
                    for session_id, label in session_options.items():
                        if search_term.lower() in label.lower():
                            filtered_options[session_id] = label
                else:
                    filtered_options = session_options
                
                # 選択UI
                selected_session_ids = []
                for session_id, label in filtered_options.items():
                    if st.checkbox(label, key=f"{self.key}_session_{session_id}"):
                        selected_session_ids.append(session_id)
            
            # 選択されたセッションの取得
            for session in sessions:
                if session.session_id in selected_session_ids:
                    selected_sessions.append(session)
                    
        elif display_option == "カテゴリ表示":
            # カテゴリでグループ化
            categories = {}
            for session in sessions:
                category = session.category or "未分類"
                if category not in categories:
                    categories[category] = []
                categories[category].append(session)
            
            # カテゴリごとに表示
            selected_session_ids = []
            for category, category_sessions in categories.items():
                with st.expander(f"{category} ({len(category_sessions)}セッション)", expanded=True):
                    # カテゴリ全選択チェックボックス
                    category_select_all = st.checkbox(
                        f"{category}のすべてを選択", 
                        key=f"{self.key}_category_all_{category}"
                    )
                    
                    for session in category_sessions:
                        label = f"{session.name} ({session.status or '状態なし'})"
                        selected = category_select_all or st.checkbox(
                            label, 
                            key=f"{self.key}_category_session_{session.session_id}"
                        )
                        if selected:
                            selected_session_ids.append(session.session_id)
            
            # 選択されたセッションの取得
            for session in sessions:
                if session.session_id in selected_session_ids:
                    selected_sessions.append(session)
                    
        else:  # タグ表示
            # タグの抽出
            all_tags = set()
            session_tags = {}
            
            for session in sessions:
                if hasattr(session, 'tags') and session.tags:
                    session_tags[session.session_id] = set(session.tags)
                    all_tags.update(session.tags)
                else:
                    session_tags[session.session_id] = set()
            
            # タグでフィルタリング
            selected_tags = st.multiselect(
                "タグでフィルタリング",
                options=sorted(all_tags),
                key=f"{self.key}_tag_filter"
            )
            
            # 選択されたタグに基づいてセッションをフィルタリング
            filtered_sessions = []
            if selected_tags:
                for session in sessions:
                    if all(tag in session_tags.get(session.session_id, set()) for tag in selected_tags):
                        filtered_sessions.append(session)
            else:
                filtered_sessions = sessions
            
            # フィルタリングされたセッションを表示
            selected_session_ids = []
            for session in filtered_sessions:
                label = f"{session.name} ({session.category or '未分類'}, {session.status or '状態なし'})"
                if st.checkbox(label, key=f"{self.key}_tag_session_{session.session_id}"):
                    selected_session_ids.append(session.session_id)
            
            # 選択されたセッションの取得
            for session in sessions:
                if session.session_id in selected_session_ids:
                    selected_sessions.append(session)
        
        # 選択数の表示
        st.info(f"{len(selected_sessions)}個のセッションを選択中")
        
        # セッション情報を保存
        st.session_state[f"{self.key}_selected_sessions"] = selected_sessions
        
        # 次へボタン
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("次へ", key=f"{self.key}_step1_next", disabled=not selected_sessions):
                st.session_state[f"{self.key}_step"] = 2
                st.experimental_rerun()
    
    def _render_step2_export_settings(self):
        """ステップ2: エクスポート設定の表示"""
        st.markdown("### 2. エクスポート設定")
        
        # 選択されたセッション情報
        selected_sessions = st.session_state[f"{self.key}_selected_sessions"]
        st.info(f"{len(selected_sessions)}個のセッションをエクスポートします")
        
        # 使用可能なエクスポーターのリスト
        supported_formats = {
            'csv': "CSV (カンマ区切りテキスト)",
            'json': "JSON (JavaScriptオブジェクト表記)",
            'html': "HTML (ウェブページ)",
            'pdf': "PDF (ポータブルドキュメント形式)"
        }
        
        if self.export_manager:
            try:
                # エクスポートマネージャーから対応形式を取得
                formats = self.export_manager.get_supported_formats()
                if formats:
                    supported_formats = formats
            except Exception as e:
                st.warning(f"エクスポートマネージャーからの形式取得に失敗しました: {str(e)}")
        
        # 形式選択UI
        st.write("エクスポート形式を選択してください")
        
        format_cols = st.columns(len(supported_formats))
        selected_format = st.session_state.get(f"{self.key}_exporter_id", next(iter(supported_formats.keys())))
        
        for i, (fmt_id, fmt_desc) in enumerate(supported_formats.items()):
            with format_cols[i]:
                # カード形式の表示
                is_selected = selected_format == fmt_id
                card_style = "border: 2px solid #4CAF50;" if is_selected else "border: 1px solid #ddd;"
                
                st.markdown(f"""
                <div style="{card_style} padding: 10px; border-radius: 5px; text-align: center;">
                    <h3>{fmt_id.upper()}</h3>
                    <p>{fmt_desc}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"選択: {fmt_id.upper()}", key=f"{self.key}_format_{fmt_id}"):
                    st.session_state[f"{self.key}_exporter_id"] = fmt_id
                    # 新しい形式に合わせてオプションをリセット
                    st.session_state[f"{self.key}_options"] = {}
                    st.experimental_rerun()
        
        # テンプレート選択
        st.write("テンプレートを選択してください")
        
        templates = ["default", "detailed", "summary"]
        if self.export_manager and hasattr(self.export_manager, 'get_templates'):
            try:
                fmt_templates = self.export_manager.get_templates(selected_format)
                if fmt_templates:
                    templates = [t.get('name', t.get('id', 'default')) for t in fmt_templates]
            except Exception:
                pass
        
        template_name = st.selectbox(
            "テンプレート",
            options=templates,
            index=templates.index(st.session_state[f"{self.key}_template_name"]) if st.session_state[f"{self.key}_template_name"] in templates else 0,
            key=f"{self.key}_template_select"
        )
        st.session_state[f"{self.key}_template_name"] = template_name
        
        # 形式別オプション
        with st.expander("詳細オプション", expanded=False):
            options = st.session_state[f"{self.key}_options"]
            
            # 形式に応じたオプション
            if selected_format == "csv":
                # CSV形式のオプション
                col1, col2 = st.columns(2)
                with col1:
                    delimiter = st.selectbox(
                        "区切り文字",
                        options=[",", ";", "\\t"],
                        index=[",", ";", "\\t"].index(options.get("delimiter", ",")),
                        format_func=lambda x: "カンマ (,)" if x == "," else "セミコロン (;)" if x == ";" else "タブ (\\t)",
                        key=f"{self.key}_csv_delimiter"
                    )
                    options["delimiter"] = delimiter
                
                with col2:
                    include_headers = st.checkbox(
                        "ヘッダーを含める",
                        value=options.get("include_headers", True),
                        key=f"{self.key}_csv_headers"
                    )
                    options["include_headers"] = include_headers
                
                encoding = st.selectbox(
                    "エンコーディング",
                    options=["utf-8", "shift-jis", "euc-jp"],
                    index=["utf-8", "shift-jis", "euc-jp"].index(options.get("encoding", "utf-8")),
                    key=f"{self.key}_csv_encoding"
                )
                options["encoding"] = encoding
                
                include_bom = st.checkbox(
                    "BOMを含める（Excel対応）",
                    value=options.get("include_bom", True),
                    key=f"{self.key}_csv_bom"
                )
                options["include_bom"] = include_bom
                
                # CSV出力フォーマット
                output_format = st.radio(
                    "出力形式",
                    options=["flat", "hierarchical"],
                    index=0 if options.get("output_format", "flat") == "flat" else 1,
                    format_func=lambda x: "フラット形式（1ファイル）" if x == "flat" else "階層形式（複数ファイル）",
                    horizontal=True,
                    key=f"{self.key}_csv_format"
                )
                options["output_format"] = output_format
                
            elif selected_format == "json":
                # JSON形式のオプション
                pretty_print = st.checkbox(
                    "整形して出力 (Pretty Print)",
                    value=options.get("pretty_print", True),
                    key=f"{self.key}_json_pretty"
                )
                options["pretty_print"] = pretty_print
                
                if pretty_print:
                    indent = st.selectbox(
                        "インデント",
                        options=["0", "2", "4"],
                        index=["0", "2", "4"].index(options.get("indent", "2")),
                        key=f"{self.key}_json_indent"
                    )
                    options["indent"] = indent
                
                include_nulls = st.checkbox(
                    "null値を含める",
                    value=options.get("include_nulls", False),
                    key=f"{self.key}_json_nulls"
                )
                options["include_nulls"] = include_nulls
                
                date_format = st.radio(
                    "日付形式",
                    options=["iso", "timestamp"],
                    index=0 if options.get("date_format", "iso") == "iso" else 1,
                    format_func=lambda x: "ISO 8601 (YYYY-MM-DD)" if x == "iso" else "Unix タイムスタンプ",
                    horizontal=True,
                    key=f"{self.key}_json_date"
                )
                options["date_format"] = date_format
                
                # 単一ファイルでエクスポートするか
                export_as_single_file = st.checkbox(
                    "単一ファイルにエクスポート (複数セッションの場合)",
                    value=options.get("export_as_single_file", True),
                    key=f"{self.key}_json_single_file"
                )
                options["export_as_single_file"] = export_as_single_file
                
            elif selected_format in ["html", "pdf"]:
                # HTMLおよびPDF形式の共通オプション
                include_header = st.checkbox(
                    "ヘッダーを含める",
                    value=options.get("include_header", True),
                    key=f"{self.key}_doc_header"
                )
                options["include_header"] = include_header
                
                include_footer = st.checkbox(
                    "フッターを含める",
                    value=options.get("include_footer", True),
                    key=f"{self.key}_doc_footer"
                )
                options["include_footer"] = include_footer
                
                # 形式別の特有オプション
                if selected_format == "html":
                    include_interactive = st.checkbox(
                        "インタラクティブ要素を含める",
                        value=options.get("include_interactive", True),
                        key=f"{self.key}_html_interactive"
                    )
                    options["include_interactive"] = include_interactive
                    
                    create_index = st.checkbox(
                        "インデックスページを作成（複数セッションの場合）",
                        value=options.get("create_index", True),
                        key=f"{self.key}_html_index"
                    )
                    options["create_index"] = create_index
                    
                elif selected_format == "pdf":
                    include_page_number = st.checkbox(
                        "ページ番号を含める",
                        value=options.get("include_page_number", True),
                        key=f"{self.key}_pdf_page_number"
                    )
                    options["include_page_number"] = include_page_number
                    
                    paper_size = st.selectbox(
                        "用紙サイズ",
                        options=["A4", "Letter", "Legal"],
                        index=["A4", "Letter", "Legal"].index(options.get("paper_size", "A4")),
                        key=f"{self.key}_pdf_paper"
                    )
                    options["paper_size"] = paper_size
            
            # 共通オプション（すべての形式に適用）
            st.write("**共通設定**")
            
            include_metadata = st.checkbox(
                "セッションメタデータを含める",
                value=options.get("include_metadata", True),
                key=f"{self.key}_common_metadata"
            )
            options["include_metadata"] = include_metadata
            
            include_results = st.checkbox(
                "分析結果を含める",
                value=options.get("include_results", True),
                key=f"{self.key}_common_results"
            )
            options["include_results"] = include_results
            
            # オプションを保存
            st.session_state[f"{self.key}_options"] = options
        
        # 選択された形式と設定の概要
        st.info(f"選択された形式: {selected_format.upper()} - テンプレート: {template_name}")
        
        # ナビゲーションボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("戻る", key=f"{self.key}_step2_back"):
                st.session_state[f"{self.key}_step"] = 1
                st.experimental_rerun()
        with col2:
            if st.button("次へ", key=f"{self.key}_step2_next"):
                st.session_state[f"{self.key}_step"] = 3
                st.experimental_rerun()
    
    def _render_step3_output_settings(self):
        """ステップ3: 出力設定の表示"""
        st.markdown("### 3. 出力設定")
        
        # 出力ディレクトリ
        output_dir = st.text_input(
            "出力ディレクトリ",
            value=st.session_state[f"{self.key}_output_dir"] or "exports/batch",
            key=f"{self.key}_output_dir_input",
            help="エクスポートファイルを保存するディレクトリ"
        )
        st.session_state[f"{self.key}_output_dir"] = output_dir
        
        # ファイル名テンプレート
        st.markdown("ファイル名テンプレートを設定してください。以下の変数が使用できます:")
        st.markdown("- `{session_name}`: セッション名")
        st.markdown("- `{session_id}`: セッションID")
        st.markdown("- `{timestamp}`: 現在の日時")
        st.markdown("- `{index}`: セッションのインデックス番号")
        
        filename_template = st.text_input(
            "ファイル名テンプレート",
            value=st.session_state[f"{self.key}_filename_template"],
            key=f"{self.key}_filename_template_input"
        )
        st.session_state[f"{self.key}_filename_template"] = filename_template
        
        # サンプルファイル名のプレビュー
        if filename_template:
            sample_name = "サンプルセッション"
            sample_id = "abc123"
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            
            sample_filename = filename_template.format(
                session_name=sample_name,
                session_id=sample_id,
                timestamp=timestamp,
                index=1
            )
            
            # エクスポーター拡張子の追加
            exporter_id = st.session_state[f"{self.key}_exporter_id"]
            exporter_ext = exporter_id
            
            # 拡張子を追加
            if not sample_filename.endswith(f".{exporter_ext}"):
                sample_filename = f"{sample_filename}.{exporter_ext}"
            
            st.info(f"サンプルファイル名: {sample_filename}")
        
        # 設定の概要表示
        with st.expander("エクスポート設定の概要", expanded=True):
            selected_sessions = st.session_state[f"{self.key}_selected_sessions"]
            exporter_id = st.session_state[f"{self.key}_exporter_id"]
            template_name = st.session_state[f"{self.key}_template_name"]
            options = st.session_state[f"{self.key}_options"]
            
            st.markdown(f"- **セッション数**: {len(selected_sessions)} 個")
            st.markdown(f"- **エクスポート形式**: {exporter_id.upper()}")
            st.markdown(f"- **テンプレート**: {template_name}")
            st.markdown(f"- **出力ディレクトリ**: {output_dir}")
            st.markdown(f"- **ファイル名テンプレート**: {filename_template}")
            
            if options:
                st.markdown("- **設定オプション**:")
                for key, value in options.items():
                    st.markdown(f"  - {key}: {value}")
        
        # ナビゲーションボタン
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("戻る", key=f"{self.key}_step3_back"):
                st.session_state[f"{self.key}_step"] = 2
                st.experimental_rerun()
        with col3:
            if st.button("エクスポート開始", key=f"{self.key}_step3_start"):
                # エクスポート処理の開始
                self._start_batch_export()
                st.session_state[f"{self.key}_step"] = 4
                st.experimental_rerun()
    
    def _render_step4_progress_and_results(self):
        """ステップ4: 進行状況と結果の表示"""
        st.markdown("### 4. エクスポート処理と結果")
        
        # 現在のジョブID
        job_id = st.session_state[f"{self.key}_current_job_id"]
        
        if not job_id:
            st.error("エクスポートジョブが開始されていません。")
            
            # 最初のステップに戻るボタン
            if st.button("最初に戻る", key=f"{self.key}_step4_restart"):
                st.session_state[f"{self.key}_step"] = 1
                st.experimental_rerun()
            return
        
        # ジョブ状態の確認
        if self.batch_exporter:
            job_status = self.batch_exporter.get_job_status(job_id)
            st.session_state[f"{self.key}_job_status"] = job_status
            
            if job_status:
                status = job_status["status"]
                progress = job_status["progress"]
                message = job_status["message"]
                
                # 進行状況の表示
                progress_bar = st.progress(float(progress))
                st.text(f"ステータス: {status} - {message}")
                
                # 完了、失敗、キャンセル時の表示
                if status in ["completed", "failed", "cancelled"]:
                    if status == "completed":
                        st.success("エクスポートが完了しました！")
                    elif status == "failed":
                        st.error(f"エクスポートが失敗しました: {job_status.get('error', 'Unknown error')}")
                    elif status == "cancelled":
                        st.warning("エクスポートがキャンセルされました。")
                    
                    # 結果の表示
                    results = job_status.get("results", [])
                    if results:
                        st.subheader("エクスポート結果")
                        
                        # 結果のサマリー
                        success_count = sum(1 for r in results if r.get("success", False))
                        fail_count = len(results) - success_count
                        
                        st.info(f"成功: {success_count}, 失敗: {fail_count}, 合計: {len(results)}")
                        
                        # 詳細結果
                        with st.expander("詳細結果", expanded=True):
                            for result in results:
                                session_id = result.get("session_id", "Unknown")
                                session_name = result.get("session_name", "Unknown")
                                success = result.get("success", False)
                                output_path = result.get("output_path", "")
                                error = result.get("error", "")
                                
                                # 結果の表示
                                if success:
                                    st.markdown(f"✅ **{session_name}** - 出力: `{output_path}`")
                                else:
                                    st.markdown(f"❌ **{session_name}** - エラー: {error}")
                    
                    # 完了コールバックの呼び出し
                    if self.on_export_complete and status == "completed":
                        self.on_export_complete(job_status)
                    
                    # 出力ディレクトリへのリンク
                    output_dir = job_status.get("output_dir")
                    if output_dir and os.path.exists(output_dir):
                        # ユーザーにディレクトリパスを表示
                        st.info(f"エクスポートファイルは次の場所に保存されています: {output_dir}")
                    
                    # 再スタート/終了ボタン
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("別のエクスポートを開始", key=f"{self.key}_step4_new_export"):
                            st.session_state[f"{self.key}_step"] = 1
                            st.session_state[f"{self.key}_current_job_id"] = None
                            st.experimental_rerun()
                else:
                    # 実行中の場合はキャンセルボタン
                    if status == "running":
                        if st.button("キャンセル", key=f"{self.key}_step4_cancel"):
                            self.batch_exporter.cancel_job(job_id)
                            st.experimental_rerun()
                    
                    # 自動更新のためのリフレッシュ
                    time.sleep(1)  # 短い待機時間
                    st.experimental_rerun()
        else:
            st.error("バッチエクスポーターが設定されていません。")
    
    def _start_batch_export(self):
        """バッチエクスポート処理の開始"""
        if not self.batch_exporter:
            st.error("バッチエクスポーターが設定されていません。")
            return
        
        # 必要なパラメータの取得
        selected_sessions = st.session_state[f"{self.key}_selected_sessions"]
        exporter_id = st.session_state[f"{self.key}_exporter_id"]
        template_name = st.session_state[f"{self.key}_template_name"]
        options = st.session_state[f"{self.key}_options"]
        output_dir = st.session_state[f"{self.key}_output_dir"]
        filename_template = st.session_state[f"{self.key}_filename_template"]
        
        # 出力ディレクトリの作成
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # プログレスコールバック（UIの更新）
        def progress_callback(progress, message):
            # このコールバックはバックグラウンドスレッドから呼ばれるため、
            # Streamlitの状態更新には直接使用できない
            pass
        
        # バッチエクスポートの開始
        job_id = self.batch_exporter.start_batch_export(
            sessions=selected_sessions,
            exporter_id=exporter_id,
            output_dir=output_dir,
            filename_template=filename_template,
            template_name=template_name,
            options=options,
            progress_callback=progress_callback
        )
        
        # ジョブIDの保存
        st.session_state[f"{self.key}_current_job_id"] = job_id
