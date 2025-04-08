"""
ui.components.export.export_settings

エクスポート設定UIコンポーネント
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import os

from sailing_data_processor.exporters.exporter_factory import ExporterFactory
from sailing_data_processor.exporters.template_manager import TemplateManager


class ExportSettingsComponent:
    """
    エクスポート設定UIコンポーネント
    
    セッション結果をエクスポートするための設定UIを提供します。
    """
    
    def __init__(self, key="export_settings", 
                 exporter_factory=None, 
                 template_manager=None,
                 on_settings_change=None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントキー
        exporter_factory : ExporterFactory, optional
            エクスポーターファクトリーインスタンス
        template_manager : TemplateManager, optional
            テンプレート管理クラスのインスタンス
        on_settings_change : Callable, optional
            設定変更時のコールバック
        """
        self.key = key
        self.exporter_factory = exporter_factory
        self.template_manager = template_manager
        self.on_settings_change = on_settings_change
        
        # 状態の初期化
        if f"{key}_exporter_id" not in st.session_state:
            st.session_state[f"{key}_exporter_id"] = "pdf"
        if f"{key}_template_name" not in st.session_state:
            st.session_state[f"{key}_template_name"] = "default"
        if f"{key}_options" not in st.session_state:
            st.session_state[f"{key}_options"] = {}
        if f"{key}_output_filename" not in st.session_state:
            st.session_state[f"{key}_output_filename"] = "session_export.pdf"
    
    def render(self):
        """
        コンポーネントのレンダリング
        """
        st.subheader("エクスポート設定")
        
        # エクスポーターファクトリーのチェック
        if not self.exporter_factory:
            st.warning("エクスポーターファクトリーが設定されていません。エクスポート機能は制限されます。")
            
            # 代替として簡易選択を表示
            format_options = ["pdf", "html", "csv", "json"]
            selected_format = st.selectbox(
                "エクスポート形式",
                options=format_options,
                index=format_options.index(st.session_state[f"{self.key}_exporter_id"]) if st.session_state[f"{self.key}_exporter_id"] in format_options else 0,
                key=f"{self.key}_format_select",
                on_change=self._on_format_change
            )
            
            # 出力ファイル名
            extension = f".{selected_format}"
            current_filename = st.session_state.get(f"{self.key}_output_filename", f"session_export{extension}")
            if not current_filename.endswith(extension):
                current_filename = f"session_export{extension}"
                
            output_filename = st.text_input(
                "出力ファイル名",
                value=current_filename,
                key=f"{self.key}_filename_input"
            )
            
            # オプションの設定（最小限）
            with st.expander("基本オプション", expanded=False):
                include_metadata = st.checkbox(
                    "セッションメタデータを含める",
                    value=st.session_state.get(f"{self.key}_options", {}).get("include_metadata", True),
                    key=f"{self.key}_include_metadata"
                )
                
                include_results = st.checkbox(
                    "セッション結果を含める",
                    value=st.session_state.get(f"{self.key}_options", {}).get("include_results", True),
                    key=f"{self.key}_include_results"
                )
                
                # オプションの更新
                options = st.session_state.get(f"{self.key}_options", {})
                options["include_metadata"] = include_metadata
                options["include_results"] = include_results
                st.session_state[f"{self.key}_options"] = options
                
            # 最後に状態を更新
            st.session_state[f"{self.key}_exporter_id"] = selected_format
            st.session_state[f"{self.key}_output_filename"] = output_filename
            
            return
            
        # 使用可能なエクスポーターのリスト
        supported_formats = self.exporter_factory.get_supported_formats()
        format_options = list(supported_formats.keys())
        
        # エクスポート形式選択
        selected_format = st.selectbox(
            "エクスポート形式",
            options=format_options,
            format_func=lambda x: f"{x.upper()} - {supported_formats.get(x, x)}",
            index=format_options.index(st.session_state[f"{self.key}_exporter_id"]) if st.session_state[f"{self.key}_exporter_id"] in format_options else 0,
            key=f"{self.key}_format_select",
            on_change=self._on_format_change
        )
        
        # 選択変更時の処理
        if selected_format != st.session_state[f"{self.key}_exporter_id"]:
            self._on_format_change()
        
        # 選択されたエクスポーターの取得
        exporter = self.exporter_factory.get_exporter(selected_format)
        
        # テンプレート選択
        templates = ["default", "detailed", "summary"]
        
        # テンプレートマネージャーからテンプレート一覧を取得
        if self.template_manager:
            try:
                template_info = self.template_manager.list_templates(selected_format)
                if selected_format in template_info:
                    templates = [
                        t.get("filename", "").replace(".json", "") 
                        for t in template_info[selected_format]
                    ]
            except Exception as e:
                st.warning(f"テンプレート情報の取得に失敗しました: {e}")
        
        selected_template = st.selectbox(
            "テンプレート",
            options=templates,
            index=templates.index(st.session_state[f"{self.key}_template_name"]) if st.session_state[f"{self.key}_template_name"] in templates else 0,
            key=f"{self.key}_template_select",
            on_change=self._on_template_change
        )
        
        # オプション設定
        with st.expander("詳細オプション", expanded=False):
            options = st.session_state[f"{self.key}_options"].copy()
            
            # 共通オプション
            st.write("**共通設定**")
            include_metadata = st.checkbox(
                "セッションメタデータを含める",
                value=options.get("include_metadata", True),
                key=f"{self.key}_include_metadata",
                on_change=self._on_options_change
            )
            include_results = st.checkbox(
                "セッション結果を含める",
                value=options.get("include_results", True),
                key=f"{self.key}_include_results",
                on_change=self._on_options_change
            )
            
            # 形式別オプション（エクスポーターから取得）
            if exporter:
                st.write(f"**{selected_format.upper()} 形式の設定**")
                
                # エクスポーター固有のオプションを取得
                exporter_options = exporter.get_supported_options()
                
                for option_name, option_meta in exporter_options.items():
                    # 共通オプションは既に表示しているのでスキップ
                    if option_name in ["include_metadata", "include_results"]:
                        continue
                    
                    # オプションの現在値
                    current_value = options.get(option_name, option_meta.get("default"))
                    
                    # オプションタイプによる入力UI
                    if option_meta["type"] == "boolean":
                        value = st.checkbox(
                            option_meta["description"],
                            value=current_value,
                            key=f"{self.key}_option_{option_name}",
                            on_change=self._on_options_change
                        )
                        options[option_name] = value
                    elif option_meta["type"] == "select" and "options" in option_meta:
                        option_values = option_meta["options"]
                        if current_value in option_values:
                            index = option_values.index(current_value)
                        else:
                            index = 0
                        
                        value = st.selectbox(
                            option_meta["description"],
                            options=option_values,
                            index=index,
                            key=f"{self.key}_option_{option_name}",
                            on_change=self._on_options_change
                        )
                        options[option_name] = value
                    elif option_meta["type"] == "text":
                        value = st.text_input(
                            option_meta["description"],
                            value=current_value,
                            key=f"{self.key}_option_{option_name}",
                            on_change=self._on_options_change
                        )
                        options[option_name] = value
            
            # オプション更新
            options["include_metadata"] = include_metadata
            options["include_results"] = include_results
            
            # オプション変更時の処理
            if options != st.session_state[f"{self.key}_options"]:
                st.session_state[f"{self.key}_options"] = options
                
                if self.on_settings_change:
                    self.on_settings_change()
        
        # 出力ファイル名
        extension = f".{selected_format}"
        current_filename = st.session_state.get(f"{self.key}_output_filename", f"session_export{extension}")
        
        # 拡張子が変わった場合は更新
        if not current_filename.endswith(extension):
            basename = os.path.splitext(current_filename)[0]
            current_filename = f"{basename}{extension}"
            
        output_filename = st.text_input(
            "出力ファイル名",
            value=current_filename,
            key=f"{self.key}_filename_input",
            on_change=self._on_filename_change
        )
        
        # ファイル名が変更された場合の処理
        if output_filename != st.session_state[f"{self.key}_output_filename"]:
            st.session_state[f"{self.key}_output_filename"] = output_filename
            
            if self.on_settings_change:
                self.on_settings_change()
        
        # 選択された形式とテンプレートを更新
        st.session_state[f"{self.key}_exporter_id"] = selected_format
        st.session_state[f"{self.key}_template_name"] = selected_template
    
    def get_settings(self) -> Dict[str, Any]:
        """
        現在の設定を取得
        
        Returns
        -------
        Dict[str, Any]
            現在のエクスポート設定
        """
        return {
            "exporter_id": st.session_state.get(f"{self.key}_exporter_id", "pdf"),
            "template_name": st.session_state.get(f"{self.key}_template_name", "default"),
            "options": st.session_state.get(f"{self.key}_options", {}),
            "output_filename": st.session_state.get(f"{self.key}_output_filename", "session_export.pdf")
        }
    
    def _on_format_change(self):
        """形式変更時の処理"""
        # 拡張子を更新
        selected_format = st.session_state[f"{self.key}_format_select"]
        current_filename = st.session_state.get(f"{self.key}_output_filename", "")
        basename = os.path.splitext(current_filename)[0]
        new_filename = f"{basename}.{selected_format}"
        st.session_state[f"{self.key}_output_filename"] = new_filename
        
        # エクスポーターIDを更新
        st.session_state[f"{self.key}_exporter_id"] = selected_format
        
        # コールバック呼び出し
        if self.on_settings_change:
            self.on_settings_change()
    
    def _on_template_change(self):
        """テンプレート変更時の処理"""
        st.session_state[f"{self.key}_template_name"] = st.session_state[f"{self.key}_template_select"]
        
        # コールバック呼び出し
        if self.on_settings_change:
            self.on_settings_change()
    
    def _on_options_change(self):
        """オプション変更時の処理"""
        # オプションを収集
        options = {}
        for key in st.session_state:
            if key.startswith(f"{self.key}_option_"):
                option_name = key.replace(f"{self.key}_option_", "")
                options[option_name] = st.session_state[key]
        
        # 共通オプション
        if f"{self.key}_include_metadata" in st.session_state:
            options["include_metadata"] = st.session_state[f"{self.key}_include_metadata"]
        if f"{self.key}_include_results" in st.session_state:
            options["include_results"] = st.session_state[f"{self.key}_include_results"]
        
        # 設定を更新
        st.session_state[f"{self.key}_options"] = options
        
        # コールバック呼び出し
        if self.on_settings_change:
            self.on_settings_change()
    
    def _on_filename_change(self):
        """ファイル名変更時の処理"""
        st.session_state[f"{self.key}_output_filename"] = st.session_state[f"{self.key}_filename_input"]
        
        # コールバック呼び出し
        if self.on_settings_change:
            self.on_settings_change()
