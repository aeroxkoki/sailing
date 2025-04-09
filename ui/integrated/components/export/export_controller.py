"""
ui.integrated.components.export.export_controller

エクスポート機能コントローラー
セーリングデータの分析結果や視覚化をエクスポートするための機能を提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, BinaryIO

class ExportController:
    """エクスポート機能コントローラー"""
    
    def __init__(self):
        """初期化"""
        self.supported_formats = {
            "data": ["csv", "excel", "json"],
            "visualization": ["png", "jpg", "svg", "html"],
            "report": ["pdf", "html", "markdown"]
        }
    
    def render_export_panel(self, data_type: str = "data"):
        """
        エクスポートパネルを描画
        
        Parameters
        ----------
        data_type : str, optional
            エクスポートするデータタイプ ("data", "visualization", "report"), by default "data"
        
        Returns
        -------
        Dict[str, Any]
            エクスポート設定
        """
        # セクションヘッダー
        st.subheader("エクスポート設定")
        
        # データタイプに基づいてサポートされているフォーマットを取得
        formats = self.supported_formats.get(data_type, [])
        
        if not formats:
            st.warning(f"サポートされていないデータタイプです: {data_type}")
            return {}
        
        # エクスポート設定
        settings = {}
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            # フォーマット選択
            settings["format"] = st.selectbox(
                "出力フォーマット",
                options=formats,
                index=0
            )
            
            # 出力ファイル名
            default_filename = f"sailing_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            settings["filename"] = st.text_input(
                "ファイル名",
                value=default_filename,
                help="拡張子は自動的に追加されます"
            )
        
        with col2:
            # データタイプ固有の設定
            if data_type == "data":
                settings["include_metadata"] = st.checkbox(
                    "メタデータを含める",
                    value=True,
                    help="データの説明や作成日時などの情報を含めます"
                )
                
                settings["compress"] = st.checkbox(
                    "圧縮する",
                    value=False,
                    help="CSVやExcelの場合、zipファイルとして圧縮します"
                )
            
            elif data_type == "visualization":
                settings["dpi"] = st.slider(
                    "解像度 (DPI)",
                    min_value=72,
                    max_value=300,
                    value=150,
                    step=1,
                    help="画像の解像度。高いほど高品質ですが、ファイルサイズも大きくなります"
                )
                
                settings["transparent"] = st.checkbox(
                    "透過背景",
                    value=False,
                    help="PNG/SVG形式で背景を透過にします"
                )
            
            elif data_type == "report":
                settings["include_charts"] = st.checkbox(
                    "グラフを含める",
                    value=True,
                    help="レポートにグラフや視覚化を含めます"
                )
                
                settings["include_raw_data"] = st.checkbox(
                    "生データを含める",
                    value=False,
                    help="レポートに生データを含めます"
                )
        
        return settings
    
    def export_data(self, data: pd.DataFrame, settings: Dict[str, Any]) -> Optional[BinaryIO]:
        """
        データをエクスポート
        
        Parameters
        ----------
        data : pd.DataFrame
            エクスポートするデータ
        settings : Dict[str, Any]
            エクスポート設定
        
        Returns
        -------
        Optional[BinaryIO]
            エクスポートされたデータのバイナリストリーム
        """
        if data is None or data.empty:
            st.warning("エクスポートするデータがありません。")
            return None
        
        # データ形式の取得
        export_format = settings.get("format", "csv")
        
        # バッファの作成
        buffer = io.BytesIO()
        
        try:
            # 形式に応じたエクスポート
            if export_format == "csv":
                data.to_csv(buffer, index=False, encoding="utf-8")
            
            elif export_format == "excel":
                data.to_excel(buffer, index=False, engine="openpyxl", sheet_name="Data")
                
                # メタデータシートの追加
                if settings.get("include_metadata", False):
                    with pd.ExcelWriter(buffer, engine="openpyxl", mode="a") as writer:
                        # メタデータの作成
                        metadata = pd.DataFrame({
                            "項目": ["作成日時", "行数", "列数", "データタイプ"],
                            "値": [
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                str(len(data)),
                                str(len(data.columns)),
                                "セーリングデータ"
                            ]
                        })
                        metadata.to_excel(writer, sheet_name="Metadata", index=False)
            
            elif export_format == "json":
                # 日付時刻の処理を含む
                data.to_json(buffer, orient="records", date_format="iso")
            
            else:
                st.error(f"サポートされていない形式です: {export_format}")
                return None
            
            # 圧縮オプション（現在はプレースホルダ）
            if settings.get("compress", False):
                st.info("圧縮オプションは現在開発中です。")
            
            # バッファの位置を先頭に戻す
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            st.error(f"エクスポート中にエラーが発生しました: {str(e)}")
            return None
    
    def export_visualization(self, fig, settings: Dict[str, Any]) -> Optional[BinaryIO]:
        """
        可視化をエクスポート
        
        Parameters
        ----------
        fig : matplotlib.figure.Figure or plotly.graph_objects.Figure
            エクスポートする図
        settings : Dict[str, Any]
            エクスポート設定
        
        Returns
        -------
        Optional[BinaryIO]
            エクスポートされた画像のバイナリストリーム
        """
        if fig is None:
            st.warning("エクスポートする可視化がありません。")
            return None
        
        # データ形式の取得
        export_format = settings.get("format", "png")
        
        # バッファの作成
        buffer = io.BytesIO()
        
        try:
            # 図のタイプに応じたエクスポート
            import matplotlib.pyplot as plt
            import plotly.graph_objects as go
            
            # Matplotlib図の場合
            if hasattr(fig, "savefig"):
                fig.savefig(
                    buffer,
                    format=export_format,
                    dpi=settings.get("dpi", 150),
                    transparent=settings.get("transparent", False),
                    bbox_inches="tight"
                )
            
            # Plotly図の場合
            elif isinstance(fig, go.Figure):
                if export_format == "html":
                    import plotly.io as pio
                    html_str = pio.to_html(
                        fig,
                        include_plotlyjs=True,
                        full_html=True
                    )
                    buffer.write(html_str.encode("utf-8"))
                else:
                    fig.write_image(
                        buffer,
                        format=export_format,
                        scale=settings.get("dpi", 150) / 100,
                        width=1200,
                        height=800
                    )
            else:
                st.error("サポートされていない可視化タイプです。")
                return None
            
            # バッファの位置を先頭に戻す
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            st.error(f"エクスポート中にエラーが発生しました: {str(e)}")
            return None
    
    def create_download_link(self, buffer: BinaryIO, filename: str, format: str) -> str:
        """
        ダウンロードリンクを作成
        
        Parameters
        ----------
        buffer : BinaryIO
            ダウンロードするデータのバイナリストリーム
        filename : str
            ファイル名（拡張子なし）
        format : str
            ファイル形式
        
        Returns
        -------
        str
            ダウンロードリンクのHTML
        """
        # MIMEタイプの設定
        mime_types = {
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json",
            "png": "image/png",
            "jpg": "image/jpeg",
            "svg": "image/svg+xml",
            "html": "text/html",
            "pdf": "application/pdf",
            "markdown": "text/markdown"
        }
        
        # ファイル拡張子の設定
        extensions = {
            "csv": "csv",
            "excel": "xlsx",
            "json": "json",
            "png": "png",
            "jpg": "jpg",
            "svg": "svg",
            "html": "html",
            "pdf": "pdf",
            "markdown": "md"
        }
        
        # MIMEタイプとファイル拡張子の取得
        mime_type = mime_types.get(format, "application/octet-stream")
        extension = extensions.get(format, format)
        
        # ファイル名と拡張子の結合
        full_filename = f"{filename}.{extension}"
        
        # Base64エンコード
        b64 = base64.b64encode(buffer.read()).decode()
        
        # ダウンロードリンクの作成
        href = f'<a href="data:{mime_type};base64,{b64}" download="{full_filename}">ダウンロード（{full_filename}）</a>'
        return href
    
    def download_data(self, data: pd.DataFrame, settings: Dict[str, Any]):
        """
        データのダウンロード機能
        
        Parameters
        ----------
        data : pd.DataFrame
            ダウンロードするデータ
        settings : Dict[str, Any]
            エクスポート設定
        """
        # データのエクスポート
        buffer = self.export_data(data, settings)
        
        if buffer is not None:
            # ファイル名と形式の取得
            filename = settings.get("filename", "export")
            format = settings.get("format", "csv")
            
            # ダウンロードリンクの作成
            download_link = self.create_download_link(buffer, filename, format)
            
            # ダウンロードボタンの表示
            st.markdown(download_link, unsafe_allow_html=True)
    
    def download_visualization(self, fig, settings: Dict[str, Any]):
        """
        可視化のダウンロード機能
        
        Parameters
        ----------
        fig : matplotlib.figure.Figure or plotly.graph_objects.Figure
            ダウンロードする可視化
        settings : Dict[str, Any]
            エクスポート設定
        """
        # 可視化のエクスポート
        buffer = self.export_visualization(fig, settings)
        
        if buffer is not None:
            # ファイル名と形式の取得
            filename = settings.get("filename", "visualization")
            format = settings.get("format", "png")
            
            # ダウンロードリンクの作成
            download_link = self.create_download_link(buffer, filename, format)
            
            # ダウンロードボタンの表示
            st.markdown(download_link, unsafe_allow_html=True)
