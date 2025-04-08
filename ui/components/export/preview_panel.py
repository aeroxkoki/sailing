"""
ui.components.export.preview_panel

エクスポートプレビューパネルUIコンポーネント
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable, Union
import os
import base64
import tempfile
import time
from pathlib import Path

from sailing_data_processor.project.session_model import SessionModel
from sailing_data_processor.exporters.exporter_factory import ExporterFactory


class PreviewPanelComponent:
    """
    エクスポートプレビューパネルUIコンポーネント
    
    エクスポート設定に基づいたプレビューを表示します。
    """
    
    def __init__(self, key="preview_panel", 
                 exporter_factory=None, 
                 on_export_click=None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントキー
        exporter_factory : ExporterFactory, optional
            エクスポーターファクトリーインスタンス
        on_export_click : Callable, optional
            エクスポートボタンクリック時のコールバック
        """
        self.key = key
        self.exporter_factory = exporter_factory
        self.on_export_click = on_export_click
        
        # 状態の初期化
        if f"{key}_preview_data" not in st.session_state:
            st.session_state[f"{key}_preview_data"] = None
        if f"{key}_is_generating" not in st.session_state:
            st.session_state[f"{key}_is_generating"] = False
        if f"{key}_export_progress" not in st.session_state:
            st.session_state[f"{key}_export_progress"] = 0.0
        if f"{key}_export_status" not in st.session_state:
            st.session_state[f"{key}_export_status"] = ""
    
    def render(self, session: Optional[SessionModel] = None, settings: Optional[Dict[str, Any]] = None):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        session : Optional[SessionModel], optional
            プレビューするセッション
        settings : Optional[Dict[str, Any]], optional
            エクスポート設定
        """
        st.subheader("プレビュー")
        
        # セッションと設定のチェック
        if not session:
            st.info("プレビューするセッションが選択されていません。")
            return
        
        if not settings:
            st.info("エクスポート設定が指定されていません。")
            return
        
        # エクスポーターファクトリーのチェック
        if not self.exporter_factory:
            st.warning("エクスポート機能が利用できません。エクスポーターファクトリーが設定されていません。")
            return
        
        # 設定から情報を取得
        exporter_id = settings.get("exporter_id", "pdf")
        template_name = settings.get("template_name", "default")
        options = settings.get("options", {})
        output_filename = settings.get("output_filename", f"session_export.{exporter_id}")
        
        # プレビュー生成ボタン
        preview_button_text = "プレビューを生成" if not st.session_state[f"{self.key}_is_generating"] else "生成中..."
        preview_button_disabled = st.session_state[f"{self.key}_is_generating"]
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(preview_button_text, disabled=preview_button_disabled, key=f"{self.key}_preview_button"):
                st.session_state[f"{self.key}_is_generating"] = True
                self._generate_preview(session, exporter_id, template_name, options)
        
        with col2:
            if st.button("エクスポート", key=f"{self.key}_export_button"):
                if self.on_export_click:
                    self.on_export_click()
        
        # 進行状況表示
        if st.session_state[f"{self.key}_is_generating"]:
            st.progress(st.session_state[f"{self.key}_export_progress"])
            st.text(st.session_state[f"{self.key}_export_status"])
        
        # プレビュー表示エリア
        preview_data = st.session_state[f"{self.key}_preview_data"]
        
        if preview_data:
            format_type = preview_data.get("format")
            content = preview_data.get("content")
            
            st.markdown("---")
            
            if format_type == "pdf":
                # PDFプレビュー表示
                st.markdown(f"**PDF プレビュー:** {output_filename}")
                pdf_base64 = base64.b64encode(content).decode("utf-8")
                pdf_display = f"""
                    <iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="500" type="application/pdf"></iframe>
                """
                st.markdown(pdf_display, unsafe_allow_html=True)
                
                # ダウンロードボタン
                st.download_button(
                    label="PDFをダウンロード",
                    data=content,
                    file_name=output_filename,
                    mime="application/pdf",
                    key=f"{self.key}_download_pdf"
                )
                
            elif format_type == "html":
                # HTMLプレビュー表示
                st.markdown(f"**HTML プレビュー:** {output_filename}")
                html_content = content.decode("utf-8") if isinstance(content, bytes) else content
                
                with st.expander("HTMLプレビュー", expanded=True):
                    st.components.v1.html(html_content, height=500, scrolling=True)
                
                # ダウンロードボタン
                st.download_button(
                    label="HTMLをダウンロード",
                    data=content,
                    file_name=output_filename,
                    mime="text/html",
                    key=f"{self.key}_download_html"
                )
                
            elif format_type in ["csv", "json"]:
                # テキスト形式のプレビュー表示
                text_content = content.decode("utf-8") if isinstance(content, bytes) else content
                mime_type = "text/csv" if format_type == "csv" else "application/json"
                
                st.markdown(f"**{format_type.upper()} プレビュー:** {output_filename}")
                st.text_area("内容", text_content, height=300)
                
                # ダウンロードボタン
                st.download_button(
                    label=f"{format_type.upper()}をダウンロード",
                    data=content,
                    file_name=output_filename,
                    mime=mime_type,
                    key=f"{self.key}_download_{format_type}"
                )
            
            else:
                st.info(f"プレビューは {format_type} 形式では利用できません。")
    
    def _generate_preview(self, session: SessionModel, exporter_id: str, template_name: str, options: Dict[str, Any]) -> None:
        """
        プレビューの生成
        
        Parameters
        ----------
        session : SessionModel
            プレビューするセッション
        exporter_id : str
            エクスポーターID
        template_name : str
            テンプレート名
        options : Dict[str, Any]
            エクスポートオプション
        """
        try:
            # 進行状況コールバック関数
            def progress_callback(progress: float, status: str):
                st.session_state[f"{self.key}_export_progress"] = progress
                st.session_state[f"{self.key}_export_status"] = status
                time.sleep(0.1)  # UIの更新を見せるための遅延
            
            # 一時ファイルを作成
            with tempfile.TemporaryDirectory() as temp_dir:
                # ファイル名
                temp_file = os.path.join(temp_dir, f"preview.{exporter_id}")
                
                # エクスポート実行
                exporter = self.exporter_factory.get_exporter(exporter_id)
                
                # 進行状況コールバックを設定
                if hasattr(exporter, 'set_progress_callback'):
                    exporter.set_progress_callback(progress_callback)
                
                # エクスポート
                exported_file = exporter.export_session(
                    session=session,
                    output_path=temp_file,
                    template=template_name,
                    options=options
                )
                
                # エクスポートが成功したかチェック
                if not os.path.exists(exported_file):
                    raise FileNotFoundError(f"エクスポートファイルが生成されませんでした: {exported_file}")
                
                # ファイルを読み込み
                with open(exported_file, "rb") as f:
                    file_content = f.read()
                
                # プレビューデータを保存
                st.session_state[f"{self.key}_preview_data"] = {
                    "format": exporter_id,
                    "content": file_content
                }
                
                # 生成完了
                st.session_state[f"{self.key}_export_progress"] = 1.0
                st.session_state[f"{self.key}_export_status"] = "プレビューの生成が完了しました"
                
        except Exception as e:
            st.error(f"プレビューの生成中にエラーが発生しました: {str(e)}")
        finally:
            # 状態をリセット
            st.session_state[f"{self.key}_is_generating"] = False
            
    def get_preview_data(self) -> Optional[Dict[str, Any]]:
        """
        現在のプレビューデータを取得
        
        Returns
        -------
        Optional[Dict[str, Any]]
            プレビューデータ
        """
        return st.session_state.get(f"{self.key}_preview_data")
