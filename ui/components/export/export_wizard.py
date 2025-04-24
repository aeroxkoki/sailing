# -*- coding: utf-8 -*-
"""
ui.components.export.export_wizard

セッション結果のエクスポートウィザードUIコンポーネント
"""

import os
import streamlit as st
import tempfile
from typing import List, Dict, Any, Optional, Callable, Union
import datetime

from sailing_data_processor.project.session_model import SessionModel
from sailing_data_processor.exporters.exporter_factory import ExporterFactory
from sailing_data_processor.exporters.template_manager import TemplateManager


class ExportWizardComponent:
    """
    エクスポートウィザードUIコンポーネント
    
    セッションのエクスポート形式や設定を選択するウィザード形式のUIを提供します。
    """
    
    def __init__(self, key: str = "export_wizard", 
                 session_manager=None, 
                 template_manager: Optional[TemplateManager] = None,
                 exporter_factory: Optional[ExporterFactory] = None,
                 on_export_complete: Optional[Callable[[List[str]], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "export_wizard"
        session_manager : optional
            セッションマネージャー, by default None
        template_manager : Optional[TemplateManager], optional
            テンプレート管理クラスのインスタンス, by default None
        exporter_factory : Optional[ExporterFactory], optional
            エクスポーターファクトリー, by default None
        on_export_complete : Optional[Callable[[List[str]], None]], optional
            エクスポート完了時のコールバック関数, by default None
        """
        self.key = key
        self.session_manager = session_manager
        self.template_manager = template_manager
        self.on_export_complete = on_export_complete
        
        # エクスポーターファクトリーの初期化
        if exporter_factory is None and template_manager is not None:
            self.exporter_factory = ExporterFactory(template_manager)
        else:
            self.exporter_factory = exporter_factory
        
        # ステート管理
        if f"{key}_selected_sessions" not in st.session_state:
            st.session_state[f"{key}_selected_sessions"] = []
        if f"{key}_export_format" not in st.session_state:
            st.session_state[f"{key}_export_format"] = "pdf"
        if f"{key}_selected_template" not in st.session_state:
            st.session_state[f"{key}_selected_template"] = "default"
        if f"{key}_export_options" not in st.session_state:
            st.session_state[f"{key}_export_options"] = {}
        if f"{key}_wizard_step" not in st.session_state:
            st.session_state[f"{key}_wizard_step"] = 1
        if f"{key}_export_result" not in st.session_state:
            st.session_state[f"{key}_export_result"] = None
    
    def render(self, sessions: Optional[List[SessionModel]] = None):
        """
        ウィザードを表示
        
        Parameters
        ----------
        sessions : Optional[List[SessionModel]], optional
            エクスポート対象のセッションリスト, by default None
            Noneの場合はセッションマネージャーから取得
        """
        st.header("エクスポートウィザード")
        
        # セッションの取得
        if sessions is None and self.session_manager is not None:
            try:
                sessions = self.session_manager.get_all_sessions()
            except:
                sessions = []
        
        if sessions is None:
            sessions = []
        
        # ステップ表示
        self._render_progress_bar()
        
        # 現在のステップに基づいて表示
        wizard_step = st.session_state[f"{self.key}_wizard_step"]
        
        if wizard_step == 1:
            self._render_step1_select_sessions(sessions)
        elif wizard_step == 2:
            self._render_step2_format_selection()
        elif wizard_step == 3:
            self._render_step3_template_selection()
        elif wizard_step == 4:
            self._render_step4_options()
        elif wizard_step == 5:
            self._render_step5_summary_and_export()
    
    def _render_progress_bar(self):
        """進行状況バーの表示"""
        step = st.session_state[f"{self.key}_wizard_step"]
        steps = ["セッション選択", "形式選択", "テンプレート選択", "オプション設定", "エクスポート"]
        
        # 進行状況の表示
        progress_html = ""
        for i, step_name in enumerate(steps, 1):
            if i < step:
                status = "complete"
            elif i == step:
                status = "active"
            else:
                status = "incomplete"
                
            progress_html += f'<div class="wizard-step {status}">{i}. {step_name}</div>'
        
        st.markdown(f"""
        <style>
        .wizard-steps {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .wizard-step {{
            flex: 1;
            text-align: center;
            padding: 8px;
            border-bottom: 3px solid #eee;
        }}
        .wizard-step.complete {{
            border-color: #4CAF50;
            color: #4CAF50;
        }}
        .wizard-step.active {{
            border-color: #2196F3;
            color: #2196F3;
            font-weight: bold;
        }}
        </style>
        <div class="wizard-steps">{progress_html}</div>
        """, unsafe_allow_html=True)
    
    def _render_step1_select_sessions(self, sessions: List[SessionModel]):
        """セッション選択ステップ"""
        st.subheader("ステップ 1: エクスポートするセッションを選択")
        
        if not sessions:
            st.warning("エクスポート可能なセッションがありません。")
            return
        
        # セッション表示のオプション
        view_option = st.radio("表示オプション", ["リスト表示", "グループ表示"], horizontal=True)
        
        if view_option == "リスト表示":
            # セッションのリスト表示
            session_options = {session.session_id: f"{session.name} ({session.category})" for session in sessions}
            selected_session_ids = st.multiselect(
                "エクスポートするセッションを選択してください",
                options=list(session_options.keys()),
                format_func=lambda x: session_options[x],
                default=st.session_state[f"{self.key}_selected_sessions"]
            )
        else:
            # カテゴリーごとのグループ表示
            st.write("カテゴリー別にセッションを選択できます")
            
            # カテゴリーごとにセッションをグループ化
            category_sessions = {}
            for session in sessions:
                category = session.category or "その他"
                if category not in category_sessions:
                    category_sessions[category] = []
                category_sessions[category].append(session)
            
            selected_session_ids = []
            
            # カテゴリーごとにマルチセレクトを表示
            for category, category_sessions_list in category_sessions.items():
                with st.expander(f"{category} ({len(category_sessions_list)}セッション)", expanded=True):
                    session_options = {s.session_id: s.name for s in category_sessions_list}
                    
                    # 現在選択されているセッションを初期値として設定
                    default_selection = [
                        session_id for session_id in st.session_state[f"{self.key}_selected_sessions"] 
                        if session_id in session_options
                    ]
                    
                    category_selected = st.multiselect(
                        f"{category}のセッションを選択",
                        options=list(session_options.keys()),
                        format_func=lambda x: session_options[x],
                        default=default_selection
                    )
                    selected_session_ids.extend(category_selected)
        
        # 選択内容を保存
        st.session_state[f"{self.key}_selected_sessions"] = selected_session_ids
        
        # 選択したセッション数を表示
        st.info(f"{len(selected_session_ids)}個のセッションが選択されています")
        
        # 次のステップへのボタン
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("次へ", disabled=len(selected_session_ids) == 0, key=f"{self.key}_step1_next"):
                st.session_state[f"{self.key}_wizard_step"] = 2
                st.experimental_rerun()
    
    def _render_step2_format_selection(self):
        """形式選択ステップ"""
        st.subheader("ステップ 2: エクスポート形式を選択")
        
        # サポートされている形式を取得
        supported_formats = {
            'pdf': "PDF文書 (ポータブルドキュメント形式)",
            'html': "HTMLウェブページ",
            'csv': "CSV (カンマ区切りテキスト)",
            'json': "JSON (JavaScriptオブジェクト表記)"
        }
        
        if self.exporter_factory:
            supported_formats = self.exporter_factory.get_supported_formats()
        
        # 形式選択UI
        format_options = list(supported_formats.keys())
        format_descriptions = list(supported_formats.values())
        
        # 形式の選択方法
        selection_method = st.radio("選択方法", ["簡易選択", "詳細選択"], horizontal=True)
        
        if selection_method == "簡易選択":
            # シンプルなセレクトボックスで選択
            selected_format = st.selectbox(
                "エクスポート形式を選択してください",
                options=format_options,
                format_func=lambda x: f"{x.upper()} - {supported_formats[x]}",
                index=format_options.index(st.session_state[f"{self.key}_export_format"]) if st.session_state[f"{self.key}_export_format"] in format_options else 0
            )
        else:
            # タイル形式で選択
            st.write("エクスポート形式を選択してください")
            
            cols = st.columns(len(format_options))
            selected_format = st.session_state[f"{self.key}_export_format"]
            
            for i, (fmt, desc) in enumerate(zip(format_options, format_descriptions)):
                with cols[i]:
                    is_selected = selected_format == fmt
                    border_color = "#2196F3" if is_selected else "#e0e0e0"
                    bg_color = "#e3f2fd" if is_selected else "#ffffff"
                    
                    st.markdown(f"""
                    <div style="
                        border: 2px solid {border_color};
                        border-radius: 5px;
                        padding: 10px;
                        text-align: center;
                        cursor: pointer;
                        background-color: {bg_color};
                        height: 100%;
                    " onclick="
                        // カスタムイベントを発生させる
                        const event = new CustomEvent('formatSelected', {{ detail: '{fmt}' }});
                        window.dispatchEvent(event);
                    ">
                        <h3>{fmt.upper()}</h3>
                        <p>{desc}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # クリックを検出するための非表示ボタン
                    if st.button(f"選択: {fmt}", key=f"{self.key}_format_{fmt}", help=f"{desc}を選択"):
                        selected_format = fmt
        
        # 選択内容を保存
        st.session_state[f"{self.key}_export_format"] = selected_format
        
        # 選択した形式の説明を表示
        st.info(f"選択された形式: {selected_format.upper()} - {supported_formats[selected_format]}")
        
        # 「形式について」の詳細説明
        with st.expander("選択した形式について詳細を表示"):
            if selected_format == "pdf":
                st.write("""
                **PDF形式**は、表示環境によらず文書の書式や体裁を保持するための標準的な文書形式です。
                
                **長所**:
                - 表示環境に依存せず、どのデバイスでも同じ見た目で表示される
                - 印刷に適している
                - セキュリティ設定が可能
                
                **短所**:
                - サイズが大きくなりがち
                - 編集が難しい
                - インタラクティブな要素を含めることができない
                
                **用途**:
                - 公式レポートやドキュメント
                - 印刷するためのデータ
                - 編集されたくない正式な文書
                """)
            elif selected_format == "html":
                st.write("""
                **HTML形式**は、Webブラウザで表示するための標準的なマークアップ言語です。
                
                **長所**:
                - インタラクティブな要素を含めることができる
                - Webサイトでの共有が容易
                - 拡張性が高い
                
                **短所**:
                - 表示環境によって見た目が変わる可能性がある
                - 複数のファイルが必要になることがある
                
                **用途**:
                - インタラクティブな分析結果の共有
                - Webサイトへの埋め込み
                - チーム内でのオンライン共有
                """)
            elif selected_format == "csv":
                st.write("""
                **CSV (Comma Separated Values) 形式**は、データを単純なテキスト形式で表現するフォーマットです。
                
                **長所**:
                - Excel やその他の表計算ソフトとの互換性が高い
                - シンプルで扱いやすい
                - サイズが小さい
                
                **短所**:
                - 複雑なデータ構造を表現できない
                - 書式設定ができない
                
                **用途**:
                - データの詳細分析
                - 他のソフトウェアでの処理
                - 生データのエクスポート
                """)
            elif selected_format == "json":
                st.write("""
                **JSON (JavaScript Object Notation) 形式**は、構造化されたデータを表現するための軽量なデータ形式です。
                
                **長所**:
                - 複雑なデータ構造を表現できる
                - プログラムでの利用が容易
                - 人間にも読みやすい形式
                
                **短所**:
                - 表計算ソフトでの直接利用には適さない
                - 一般ユーザーには馴染みが薄い
                
                **用途**:
                - プログラムによるデータ処理
                - APIとの連携
                - 完全なデータ構造の保存
                """)
        
        # 戻る・次へボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("戻る", key=f"{self.key}_step2_back"):
                st.session_state[f"{self.key}_wizard_step"] = 1
                st.experimental_rerun()
        with col2:
            if st.button("次へ", key=f"{self.key}_step2_next"):
                st.session_state[f"{self.key}_wizard_step"] = 3
                st.experimental_rerun()
    
    def _render_step3_template_selection(self):
        """テンプレート選択ステップ"""
        st.subheader("ステップ 3: レポートテンプレートの選択")
        
        # 選択された形式を取得
        selected_format = st.session_state[f"{self.key}_export_format"]
        
        # 利用可能なテンプレートを取得
        templates = {
            "default": "デフォルトテンプレート（標準的なレイアウト）"
        }
        
        # テンプレートマネージャーが利用可能な場合
        if self.template_manager:
            try:
                template_info = self.template_manager.list_templates(selected_format)
                if selected_format in template_info:
                    templates = {
                        t.get("filename", "").replace(".json", ""): t.get("name", t.get("filename", "")) 
                        for t in template_info[selected_format]
                    }
            except:
                pass
        
        # テンプレート選択UI
        template_options = list(templates.keys())
        
        if not template_options:
            template_options = ["default"]
            templates = {"default": "デフォルトテンプレート（標準的なレイアウト）"}
        
        st.write(f"{selected_format.upper()} 形式のテンプレートを選択してください")
        
        selected_template = st.selectbox(
            "テンプレート",
            options=template_options,
            format_func=lambda x: templates[x],
            index=template_options.index(st.session_state[f"{self.key}_selected_template"]) if st.session_state[f"{self.key}_selected_template"] in template_options else 0
        )
        
        # テンプレートプレビュー
        st.write("テンプレートプレビュー")
        
        # 実際のプレビュー表示（ダミー）
        st.image("https://via.placeholder.com/800x400?text=Template+Preview", use_column_width=True)
        
        # テンプレートの説明
        st.info(f"テンプレート: {templates[selected_template]}")
        
        # 選択内容を保存
        st.session_state[f"{self.key}_selected_template"] = selected_template
        
        # 戻る・次へボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("戻る", key=f"{self.key}_step3_back"):
                st.session_state[f"{self.key}_wizard_step"] = 2
                st.experimental_rerun()
        with col2:
            if st.button("次へ", key=f"{self.key}_step3_next"):
                st.session_state[f"{self.key}_wizard_step"] = 4
                st.experimental_rerun()
    
    def _render_step4_options(self):
        """オプション設定ステップ"""
        st.subheader("ステップ 4: エクスポートオプションを設定")
        
        # 選択された形式とテンプレートを取得
        selected_format = st.session_state[f"{self.key}_export_format"]
        selected_template = st.session_state[f"{self.key}_selected_template"]
        
        # オプション設定の初期値
        if f"{self.key}_export_options" not in st.session_state:
            st.session_state[f"{self.key}_export_options"] = {}
        
        # 出力先の設定
        st.write("出力設定")
        
        output_method = st.radio(
            "出力方法",
            ["ダウンロード", "アップロード (サーバーに保存)"],
            horizontal=True,
            index=0 if st.session_state[f"{self.key}_export_options"].get("output_method", "download") == "download" else 1
        )
        
        # 出力方法を保存
        st.session_state[f"{self.key}_export_options"]["output_method"] = "download" if output_method == "ダウンロード" else "upload"
        
        # ファイル名テンプレート（オプション）
        filename_template = st.text_input(
            "ファイル名テンプレート（オプション）",
            value=st.session_state[f"{self.key}_export_options"].get("filename_template", "{session_name}_{date}"),
            help="使用可能な変数: {session_name}, {date}, {time}, {category}, {id}"
        )
        
        # ファイル名テンプレートを保存
        st.session_state[f"{self.key}_export_options"]["filename_template"] = filename_template
        
        # 形式別のオプション設定
        st.write(f"{selected_format.upper()} 形式の設定")
        
        if selected_format == "pdf":
            # PDF形式の設定
            include_header = st.checkbox(
                "ヘッダーを含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_header", True)
            )
            include_footer = st.checkbox(
                "フッターを含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_footer", True)
            )
            include_page_number = st.checkbox(
                "ページ番号を含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_page_number", True)
            )
            
            # オプションを保存
            st.session_state[f"{self.key}_export_options"]["include_header"] = include_header
            st.session_state[f"{self.key}_export_options"]["include_footer"] = include_footer
            st.session_state[f"{self.key}_export_options"]["include_page_number"] = include_page_number
            
        elif selected_format == "html":
            # HTML形式の設定
            include_interactive = st.checkbox(
                "インタラクティブな要素を含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_interactive", True),
                help="グラフやマップをインタラクティブに操作できるようにします"
            )
            include_print_css = st.checkbox(
                "印刷用CSSを含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_print_css", True),
                help="印刷時に適切に表示されるようCSSを最適化します"
            )
            create_index = st.checkbox(
                "インデックスページを作成（複数セッションの場合）",
                value=st.session_state[f"{self.key}_export_options"].get("create_index", True),
                help="複数のセッションをエクスポートする場合に一覧ページを作成します"
            )
            
            # オプションを保存
            st.session_state[f"{self.key}_export_options"]["include_interactive"] = include_interactive
            st.session_state[f"{self.key}_export_options"]["include_print_css"] = include_print_css
            st.session_state[f"{self.key}_export_options"]["create_index"] = create_index
            
        elif selected_format == "csv":
            # CSV形式の設定
            delimiter = st.selectbox(
                "区切り文字",
                options=[",", ";", "\t"],
                index=0 if st.session_state[f"{self.key}_export_options"].get("delimiter", ",") == "," else 
                       1 if st.session_state[f"{self.key}_export_options"].get("delimiter", ",") == ";" else 2,
                format_func=lambda x: "カンマ (,)" if x == "," else "セミコロン (;)" if x == ";" else "タブ (\\t)"
            )
            include_headers = st.checkbox(
                "ヘッダーを含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_headers", True)
            )
            include_bom = st.checkbox(
                "BOMを含める (Excel対応)",
                value=st.session_state[f"{self.key}_export_options"].get("include_bom", True),
                help="ExcelでCSVを開く場合に日本語が正しく表示されるようにします"
            )
            
            # セクション選択
            st.write("エクスポートするセクションを選択")
            
            include_metadata = st.checkbox(
                "メタデータ", 
                value=st.session_state[f"{self.key}_export_options"].get("sections", {}).get("metadata", True)
            )
            include_wind_data = st.checkbox(
                "風データ", 
                value=st.session_state[f"{self.key}_export_options"].get("sections", {}).get("wind_data", True)
            )
            include_strategy_points = st.checkbox(
                "戦略ポイント", 
                value=st.session_state[f"{self.key}_export_options"].get("sections", {}).get("strategy_points", True)
            )
            
            # オプションを保存
            st.session_state[f"{self.key}_export_options"]["delimiter"] = delimiter
            st.session_state[f"{self.key}_export_options"]["include_headers"] = include_headers
            st.session_state[f"{self.key}_export_options"]["include_bom"] = include_bom
            
            sections = {}
            sections["metadata"] = include_metadata
            sections["wind_data"] = include_wind_data
            sections["strategy_points"] = include_strategy_points
            st.session_state[f"{self.key}_export_options"]["sections"] = sections
            
        elif selected_format == "json":
            # JSON形式の設定
            pretty_print = st.checkbox(
                "整形して出力 (Pretty Print)",
                value=st.session_state[f"{self.key}_export_options"].get("pretty_print", True),
                help="読みやすい形式でJSONを出力します"
            )
            include_metadata = st.checkbox(
                "メタデータを含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_metadata", True)
            )
            include_session_data = st.checkbox(
                "セッションデータを含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_session_data", True)
            )
            include_results = st.checkbox(
                "分析結果を含める",
                value=st.session_state[f"{self.key}_export_options"].get("include_results", True)
            )
            export_as_single_file = st.checkbox(
                "単一ファイルにエクスポート (複数セッションの場合)",
                value=st.session_state[f"{self.key}_export_options"].get("export_as_single_file", True),
                help="複数のセッションを1つのJSONファイルにまとめます"
            )
            
            # オプションを保存
            st.session_state[f"{self.key}_export_options"]["pretty_print"] = pretty_print
            st.session_state[f"{self.key}_export_options"]["include_metadata"] = include_metadata
            st.session_state[f"{self.key}_export_options"]["include_session_data"] = include_session_data
            st.session_state[f"{self.key}_export_options"]["include_results"] = include_results
            st.session_state[f"{self.key}_export_options"]["export_as_single_file"] = export_as_single_file
        
        # 共通のセクション選択
        st.write("共通設定")
        
        include_metadata = st.checkbox(
            "セッションメタデータを含める",
            value=st.session_state[f"{self.key}_export_options"].get("include_metadata", True)
        )
        include_results = st.checkbox(
            "分析結果を含める",
            value=st.session_state[f"{self.key}_export_options"].get("include_results", True)
        )
        
        # 共通オプションを保存
        st.session_state[f"{self.key}_export_options"]["include_metadata"] = include_metadata
        st.session_state[f"{self.key}_export_options"]["include_results"] = include_results
        
        # 戻る・次へボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("戻る", key=f"{self.key}_step4_back"):
                st.session_state[f"{self.key}_wizard_step"] = 3
                st.experimental_rerun()
        with col2:
            if st.button("次へ", key=f"{self.key}_step4_next"):
                st.session_state[f"{self.key}_wizard_step"] = 5
                st.experimental_rerun()
    
    def _render_step5_summary_and_export(self):
        """サマリー表示とエクスポート実行ステップ"""
        st.subheader("ステップ 5: エクスポート設定の確認と実行")
        
        # 選択内容の表示
        selected_sessions = st.session_state[f"{self.key}_selected_sessions"]
        selected_format = st.session_state[f"{self.key}_export_format"]
        selected_template = st.session_state[f"{self.key}_selected_template"]
        export_options = st.session_state[f"{self.key}_export_options"]
        
        # セッション情報を取得
        sessions = []
        if self.session_manager:
            for session_id in selected_sessions:
                try:
                    session = self.session_manager.get_session(session_id)
                    if session:
                        sessions.append(session)
                except:
                    pass
        
        # サマリー表示
        st.write("エクスポート設定の概要")
        
        # セッション情報
        st.write(f"**セッション数:** {len(selected_sessions)}個")
        if len(sessions) > 0:
            session_names = [session.name for session in sessions]
            if len(session_names) > 5:
                session_list = ", ".join(session_names[:5]) + f" など（他 {len(session_names) - 5} 個）"
            else:
                session_list = ", ".join(session_names)
            st.write(f"**セッション:** {session_list}")
        
        # 形式・テンプレート
        st.write(f"**形式:** {selected_format.upper()}")
        st.write(f"**テンプレート:** {selected_template}")
        
        # オプション
        st.write("**オプション:**")
        for key, value in export_options.items():
            if isinstance(value, dict):
                continue  # ネストされた辞書は表示しない
            st.write(f"- {key}: {value}")
        
        # 既にエクスポートを実行済みの場合の結果表示
        if f"{self.key}_export_result" in st.session_state and st.session_state[f"{self.key}_export_result"]:
            # 前回の結果を表示
            export_result = st.session_state[f"{self.key}_export_result"]
            
            st.success(f"エクスポートが完了しました！")
            
            if "download_links" in export_result:
                st.write("エクスポートされたファイル:")
                for file_name, file_data in export_result["download_links"].items():
                    st.download_button(
                        label=f"{file_name} をダウンロード",
                        data=file_data,
                        file_name=file_name,
                        mime=f"application/{selected_format}",
                        key=f"download_{file_name}"
                    )
            
            # リセットボタン
            if st.button("新しいエクスポートを開始", key=f"{self.key}_reset"):
                st.session_state[f"{self.key}_wizard_step"] = 1
                st.session_state[f"{self.key}_export_result"] = None
                st.experimental_rerun()
                
            return
        
        # エクスポート実行ボタン
        with st.expander("エクスポートを実行する前に", expanded=True):
            st.warning("""
            エクスポートを実行すると、選択したセッションが指定された形式でエクスポートされます。
            時間がかかる場合があります。
            """)
            
            # エクスポートの実行ボタン
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("戻る", key=f"{self.key}_step5_back"):
                    st.session_state[f"{self.key}_wizard_step"] = 4
                    st.experimental_rerun()
            with col2:
                start_export = st.button("エクスポートを実行", key=f"{self.key}_start_export", type="primary")
        
        # エクスポート実行
        if start_export:
            with st.spinner(f"エクスポート実行中... しばらくお待ちください"):
                try:
                    # エクスポート結果
                    export_result = self._run_export(sessions, selected_format, selected_template, export_options)
                    
                    # エクスポート結果を保存
                    st.session_state[f"{self.key}_export_result"] = export_result
                    
                    # コールバック関数を呼び出し
                    if self.on_export_complete:
                        try:
                            self.on_export_complete(export_result.get("file_paths", []))
                        except Exception as e:
                            st.error(f"コールバック実行中にエラーが発生しました: {str(e)}")
                    
                    # ページを再読み込み（結果表示のため）
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"エクスポート中にエラーが発生しました: {str(e)}")
    
    def _run_export(self, sessions: List[SessionModel], format_name: str, template: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        エクスポートを実行
        
        Parameters
        ----------
        sessions : List[SessionModel]
            エクスポート対象のセッション
        format_name : str
            エクスポート形式
        template : str
            テンプレート名
        options : Dict[str, Any]
            エクスポートオプション
            
        Returns
        -------
        Dict[str, Any]
            エクスポート結果
        """
        result = {
            "success": False,
            "file_paths": [],
            "download_links": {},
            "errors": []
        }
        
        if not sessions:
            result["errors"].append("エクスポート対象のセッションがありません")
            return result
        
        if not self.exporter_factory:
            result["errors"].append("エクスポーターが初期化されていません")
            return result
        
        try:
            # エクスポーターの取得
            exporter = self.exporter_factory.get_exporter(format_name)
            
            # 一時ディレクトリの作成
            with tempfile.TemporaryDirectory() as temp_dir:
                # 複数のセッションをエクスポート
                file_paths = exporter.export_multiple_sessions(sessions, temp_dir, template, options)
                
                # エクスポートされたファイルを読み込み
                for file_path in file_paths:
                    if not os.path.exists(file_path):
                        continue
                    
                    file_name = os.path.basename(file_path)
                    
                    # ファイルを読み込み
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    
                    # ダウンロードリンク用にデータを保存
                    result["download_links"][file_name] = file_data
                
                # ファイルパスを記録
                result["file_paths"] = file_paths
                result["success"] = True
                
                # エラーと警告を記録
                result["errors"] = exporter.get_errors()
                result["warnings"] = exporter.get_warnings()
            
            return result
            
        except Exception as e:
            result["errors"].append(f"エクスポート実行中にエラーが発生しました: {str(e)}")
            return result
