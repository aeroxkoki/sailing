# -*- coding: utf-8 -*-
"""
ui.integrated.pages.export

統合エクスポート機能ページ
セッションデータ、分析結果、可視化、レポートのエクスポートを提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
import uuid
import base64
import io
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# コンポーネントのインポート
from ui.integrated.components.navigation.breadcrumb import BreadcrumbComponent
from ui.integrated.components.help.help_component import HelpComponent
from ui.integrated.components.feedback.feedback_component import FeedbackComponent
from ui.integrated.components.export.data_export import DataExportComponent
from ui.integrated.components.export.batch_export import BatchExportComponent
from ui.integrated.components.export.visualization_export import VisualizationExportComponent
from ui.integrated.components.export.report_export import ReportExportComponent
from ui.integrated.components.export.export_controller import ExportController

def render_page():
    """統合エクスポートページをレンダリングする関数"""
    
    # パンくずナビゲーションの表示
    breadcrumb = BreadcrumbComponent()
    breadcrumb_path = breadcrumb.create_path("export")
    breadcrumb.render(breadcrumb_path)
    
    st.title('エクスポート・共有')
    
    # セッション状態の初期化
    if 'export_initialized' not in st.session_state:
        st.session_state.export_initialized = True
        st.session_state.selected_export_items = []
        st.session_state.export_format = "csv"
        st.session_state.export_history = []
        st.session_state.export_current_tab = "data"
    
    # ヘルプコンポーネントの初期化
    help_component = HelpComponent()
    
    # フィードバックコンポーネントの初期化
    feedback = FeedbackComponent()
    
    # エクスポートコントローラーの初期化
    export_controller = ExportController()
    
    # タブ切り替え用のラジオボタン
    # タブには「データエクスポート」「可視化エクスポート」「レポートエクスポート」「バッチエクスポート」「エクスポート履歴」の5つのタブを表示
    tab_options = {
        "data": "データエクスポート",
        "visualization": "可視化エクスポート",
        "report": "レポートエクスポート",
        "batch": "バッチエクスポート",
        "history": "エクスポート履歴"
    }
    
    selected_tab = st.radio(
        "エクスポート機能を選択",
        options=list(tab_options.keys()),
        format_func=lambda x: tab_options[x],
        horizontal=True,
        key="export_tab_selector"
    )
    
    st.session_state.export_current_tab = selected_tab
    
    # 区切り線
    st.markdown("---")
    
    # 各タブのコンテンツ表示
    if selected_tab == "data":
        _render_data_export_tab(help_component, feedback, export_controller)
    elif selected_tab == "visualization":
        _render_visualization_export_tab(help_component, feedback, export_controller)
    elif selected_tab == "report":
        _render_report_export_tab(help_component, feedback, export_controller)
    elif selected_tab == "batch":
        _render_batch_export_tab(help_component, feedback, export_controller)
    elif selected_tab == "history":
        _render_history_tab(help_component, feedback, export_controller)
    
    # サイドバーにエクスポート設定を表示
    _render_export_sidebar()

def _render_data_export_tab(help_component, feedback, export_controller):
    """データエクスポートタブをレンダリング"""
    
    # ヘッダー表示
    st.header("データエクスポート")
    
    # ヘルプボタンを表示
    col1, col2 = st.columns([9, 1])
    with col2:
        help_component.render_help_button("data_export")
    
    # 説明文
    st.markdown("""
    セッションデータや分析結果を様々な形式でエクスポートできます。
    各種ファイル形式に対応しており、データ分析ツールやGPSビューアなどで利用できます。
    """)
    
    # データエクスポートコンポーネントを使用
    data_export = DataExportComponent(key_prefix="integrated_data_export")
    
    # セッションデータを取得（実際の実装ではセッションマネージャーからデータを取得）
    # ここではダミーデータを使用
    session_data = None
    projects_data = None
    analysis_results = None
    
    # データエクスポートコンポーネントのレンダリング
    export_result = data_export.render(
        session_data=session_data,
        projects_data=projects_data,
        analysis_results=analysis_results
    )
    
    # エクスポート結果が返ってきた場合（エクスポートが実行された）
    if export_result:
        # エクスポート履歴に追加
        if export_result not in st.session_state.export_history:
            st.session_state.export_history.append(export_result)
            # 最新のエクスポートを履歴の先頭に表示するため、履歴を逆順にします
            st.session_state.export_history = sorted(
                st.session_state.export_history,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
        # フィードバックメッセージを表示
        feedback.show_success(
            f"エクスポートが完了しました。ファイル: {export_result.get('filename', '不明なファイル')}", 
            duration=5
        )
    
    # エクスポート形式の説明
    with st.expander("利用可能なエクスポート形式", expanded=False):
        st.markdown("""
        ### エクスポート形式

        **CSV (Comma-Separated Values)**
        最も広く使われるデータ形式で、Excel、Google Spreadsheets、Rなど多くのソフトウェアで開くことができます。
        時系列データや数値データの分析に適しています。

        **JSON (JavaScript Object Notation)**
        構造化されたデータ形式で、プログラミングでの処理やWeb APIとの連携に適しています。
        階層的なデータや複雑なデータ構造を保持できます。

        **GPX (GPS Exchange Format)**
        GPSトラックデータの標準形式で、多くのGPSデバイスやマッピングソフトウェアでサポートされています。
        位置情報を中心としたデータのエクスポートに最適です。

        **Excel (XLSX)**
        Microsoft Excelの標準形式で、複数のシートにデータを整理し、書式設定や数式も含めることができます。
        レポートや詳細な分析用のエクスポートに適しています。
        """)

def _render_visualization_export_tab(help_component, feedback, export_controller):
    """可視化エクスポートタブをレンダリング"""
    
    # ヘッダー表示
    st.header("可視化エクスポート")
    
    # ヘルプボタンを表示
    col1, col2 = st.columns([9, 1])
    with col2:
        help_component.render_help_button("visualization_export")
    
    # 説明文
    st.markdown("""
    マップ、チャート、グラフなどの可視化を画像形式でエクスポートできます。
    プレゼンテーションやレポートに組み込むための高品質な画像を生成します。
    """)
    
    # 可視化エクスポートコンポーネントを使用
    viz_export = VisualizationExportComponent(key_prefix="integrated_viz_export")
    
    # 可視化データを取得（実際の実装では可視化マネージャーからデータを取得）
    # ここではダミーデータを使用
    visualization_data = None
    viz_type = "chart"  # または "map", "timeline" など
    
    # 可視化エクスポートコンポーネントのレンダリング
    export_result = viz_export.render(
        visualization=visualization_data,
        viz_type=viz_type
    )
    
    # エクスポート結果が返ってきた場合（エクスポートが実行された）
    if export_result:
        # エクスポート履歴に追加
        if export_result not in st.session_state.export_history:
            st.session_state.export_history.append(export_result)
            # 最新のエクスポートを履歴の先頭に表示するため、履歴を逆順にします
            st.session_state.export_history = sorted(
                st.session_state.export_history,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
        # フィードバックメッセージを表示
        feedback.show_success(
            f"可視化のエクスポートが完了しました。ファイル: {export_result.get('filename', '不明なファイル')}", 
            duration=5
        )
    
    # エクスポート形式の説明
    with st.expander("利用可能な画像形式", expanded=False):
        st.markdown("""
        ### 画像形式

        **PNG (Portable Network Graphics)**
        透過背景をサポートする高品質な画像形式です。
        グラフやチャートのエクスポートに最適で、シャープな線と文字を維持します。

        **SVG (Scalable Vector Graphics)**
        ベクター形式の画像で、任意のサイズに拡大してもぼやけません。
        プレゼンテーションや印刷物に最適です。編集も可能です。

        **JPG/JPEG (Joint Photographic Experts Group)**
        写真や複雑な画像に適した圧縮形式です。
        ファイルサイズを小さくできますが、透過背景はサポートしていません。

        **PDF (Portable Document Format)**
        印刷やドキュメント共有に適した形式です。
        複数のチャートを1つのファイルにまとめることができます。
        """)

def _render_report_export_tab(help_component, feedback, export_controller):
    """レポートエクスポートタブをレンダリング"""
    
    # ヘッダー表示
    st.header("レポートエクスポート")
    
    # ヘルプボタンを表示
    col1, col2 = st.columns([9, 1])
    with col2:
        help_component.render_help_button("report_export")
    
    # 説明文
    st.markdown("""
    セッションデータと分析結果を統合したレポートを生成します。
    PDFやHTML形式で共有可能なレポートを簡単に作成できます。
    """)
    
    # レポートエクスポートコンポーネントを使用
    report_export = ReportExportComponent(key_prefix="integrated_report_export")
    
    # レポートエクスポートコンポーネントのレンダリング
    export_result = report_export.render()
    
    # エクスポート結果が返ってきた場合（エクスポートが実行された）
    if export_result:
        # エクスポート履歴に追加
        if export_result not in st.session_state.export_history:
            st.session_state.export_history.append(export_result)
            # 最新のエクスポートを履歴の先頭に表示するため、履歴を逆順にします
            st.session_state.export_history = sorted(
                st.session_state.export_history,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
        # フィードバックメッセージを表示
        feedback.show_success(
            f"レポートのエクスポートが完了しました。ファイル: {export_result.get('filename', '不明なファイル')}", 
            duration=5
        )
    
    # レポート形式の説明
    with st.expander("利用可能なレポート形式", expanded=False):
        st.markdown("""
        ### レポート形式

        **PDF (Portable Document Format)**
        どのデバイスでも同じように表示される標準的なドキュメント形式です。
        印刷やメール共有に最適で、プロフェッショナルな見栄えのレポートを作成できます。

        **HTML (HyperText Markup Language)**
        インタラクティブな要素を含められるウェブページ形式です。
        ブラウザで開くことができ、動的なチャートやマップを組み込めます。

        **マークダウン (Markdown)**
        シンプルなテキストベースの形式で、簡単に編集できます。
        GitHub等のプラットフォームでの共有に適しています。
        """)

def _render_batch_export_tab(help_component, feedback, export_controller):
    """バッチエクスポートタブをレンダリング"""
    
    # ヘッダー表示
    st.header("バッチエクスポート")
    
    # ヘルプボタンを表示
    col1, col2 = st.columns([9, 1])
    with col2:
        help_component.render_help_button("batch_export")
    
    # 説明文
    st.markdown("""
    複数のセッションやプロジェクトを一括でエクスポートします。
    一度に多くのデータを処理する場合に便利です。
    """)
    
    # バッチエクスポートコンポーネントを使用
    batch_export = BatchExportComponent(key_prefix="integrated_batch_export")
    
    # バッチエクスポートコンポーネントのレンダリング
    export_result = batch_export.render()
    
    # エクスポート結果が返ってきた場合（エクスポートが実行された）
    if export_result:
        # エクスポート履歴に追加
        if export_result not in st.session_state.export_history:
            st.session_state.export_history.append(export_result)
            # 最新のエクスポートを履歴の先頭に表示するため、履歴を逆順にします
            st.session_state.export_history = sorted(
                st.session_state.export_history,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
        # フィードバックメッセージを表示
        feedback.show_success(
            f"バッチエクスポートが完了しました。{len(export_result.get('items', []))}個のアイテムを処理しました。", 
            duration=5
        )
    
    # バッチエクスポートの説明
    with st.expander("バッチエクスポートのヒント", expanded=False):
        st.markdown("""
        ### バッチエクスポートのヒント

        **セッションの選択**
        - 日付範囲での一括選択が可能です
        - タグやカテゴリでフィルタリングして選択できます
        - 検索機能を使って特定のセッションを見つけられます

        **出力オプション**
        - 個別ファイルとして出力: 各セッションが別ファイルになります
        - 結合ファイルとして出力: すべてのセッションが1つのファイルにまとまります
        - ZIP圧縮: 複数ファイルをまとめて圧縮できます

        **処理のヒント**
        - 大量のデータをエクスポートする場合は、処理に時間がかかる場合があります
        - エクスポート中も他の作業を続けることができます
        - エクスポート結果はエクスポート履歴から確認できます
        """)

def _render_history_tab(help_component, feedback, export_controller):
    """エクスポート履歴タブをレンダリング"""
    
    # ヘッダー表示
    st.header("エクスポート履歴")
    
    # ヘルプボタンを表示
    col1, col2 = st.columns([9, 1])
    with col2:
        help_component.render_help_button("export_history")
    
    # 説明文
    st.markdown("""
    過去にエクスポートしたファイルの履歴を表示します。
    同じ設定で再エクスポートすることもできます。
    """)
    
    # エクスポート履歴の表示
    if not st.session_state.export_history:
        st.info("まだエクスポート履歴がありません。データのエクスポートを行うと、ここに履歴が表示されます。")
    else:
        # 履歴のフィルタリングオプション
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            filter_type = st.multiselect(
                "種類でフィルタ",
                options=["データ", "可視化", "レポート", "バッチ"],
                default=[]
            )
        
        with filter_col2:
            days_filter = st.slider(
                "期間でフィルタ (日)",
                min_value=1,
                max_value=90,
                value=30,
                help="指定した日数以内のエクスポート履歴を表示します"
            )
        
        # 履歴データの表示（最新のものから表示）
        for idx, export in enumerate(st.session_state.export_history):
            # フィルタリング（実装例）
            if filter_type and export.get("type", "").capitalize() not in filter_type:
                continue
                
            # エクスポート情報の表示
            export_type = export.get("type", "不明")
            export_date = datetime.fromisoformat(export.get("timestamp", datetime.now().isoformat()))
            export_filename = export.get("filename", "不明なファイル")
            
            # セッション名またはアイテム名
            if "items" in export:
                items = export.get("items", [])
                item_count = len(items)
                item_display = f"{item_count}個のアイテム"
            elif "sessions" in export:
                sessions = export.get("sessions", [])
                item_display = ", ".join(sessions) if len(sessions) <= 3 else f"{len(sessions)}個のセッション"
            else:
                item_display = "不明なアイテム"
            
            # エクスポート形式
            format_type = export.get("format", "不明").upper()
            
            # エクスポート情報をExpander内に表示
            with st.expander(f"{export_date.strftime('%Y-%m-%d %H:%M')} - {export_type}: {item_display} ({format_type})", expanded=idx == 0):
                st.markdown(f"**エクスポート種類**: {export_type}")
                st.markdown(f"**ファイル名**: {export_filename}")
                st.markdown(f"**日時**: {export_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # エクスポート内容に応じた情報表示
                if "sessions" in export:
                    st.markdown(f"**セッション**: {', '.join(export['sessions'])}")
                
                if "format" in export:
                    st.markdown(f"**形式**: {export['format'].upper()}")
                
                if "fields" in export and export["fields"]:
                    st.markdown(f"**フィールド**: {', '.join(export['fields'])}")
                
                if "size" in export:
                    st.markdown(f"**サイズ**: {export['size']}")
                
                # アクションボタン
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    # 再エクスポートボタン
                    if st.button("同じ設定で再エクスポート", key=f"reexport_{idx}"):
                        # 設定を復元して再エクスポート（実際の実装ではエクスポート設定を復元）
                        feedback.show_info("エクスポート設定を復元しました。エクスポートタブで実行してください。", duration=3)
                
                with action_col2:
                    # ダウンロードボタン（可能な場合）
                    if "download_link" in export:
                        st.markdown(export["download_link"], unsafe_allow_html=True)
                    else:
                        if st.button("再ダウンロード", key=f"redownload_{idx}"):
                            # 実際の実装ではファイルを再生成してダウンロード
                            feedback.show_info("ファイルを再生成しています...", duration=3)
                
                with action_col3:
                    # 履歴から削除ボタン
                    if st.button("履歴から削除", key=f"delete_{idx}"):
                        # 実際の履歴から削除
                        st.session_state.export_history.remove(export)
                        feedback.show_info("エクスポート履歴から削除しました", duration=3)
                        st.experimental_rerun()

def _render_export_sidebar():
    """サイドバーにエクスポート設定を表示"""
    
    with st.sidebar:
        st.subheader("エクスポート設定")
        
        # 共通のエクスポート設定
        st.markdown("#### 共通設定")
        
        # テーマ選択
        theme = st.selectbox(
            "テーマ",
            options=["標準", "ダーク", "レースレポート", "トレーニング分析", "カスタム"],
            index=0,
            help="エクスポートするファイルの視覚的なテーマを選択します"
        )
        
        # ブランディングオプション
        include_branding = st.checkbox(
            "ブランディングを含める",
            value=True,
            help="エクスポートにブランドロゴや情報を含めます"
        )
        
        # 言語設定
        language = st.selectbox(
            "言語",
            options=["日本語", "English", "自動検出"],
            index=0,
            help="エクスポートするファイルの言語を選択します"
        )
        
        # 詳細設定（形式に応じた設定）
        st.markdown("#### 詳細設定")
        
        with st.expander("エクスポート後の処理", expanded=False):
            # エクスポート後のアクション
            post_export_action = st.radio(
                "エクスポート完了時",
                options=[
                    "通知のみ",
                    "自動的にダウンロード",
                    "メールで送信",
                    "クラウドに保存"
                ],
                index=0
            )
            
            # メール送信オプション（メール送信選択時）
            if post_export_action == "メールで送信":
                email = st.text_input(
                    "送信先メールアドレス",
                    placeholder="email@example.com"
                )
                
                include_message = st.checkbox("メッセージを含める", value=True)
                
                if include_message:
                    message = st.text_area(
                        "メッセージ",
                        placeholder="エクスポートファイルを送付します。"
                    )
            
            # クラウド保存オプション（クラウド保存選択時）
            elif post_export_action == "クラウドに保存":
                cloud_service = st.selectbox(
                    "クラウドサービス",
                    options=["Google Drive", "Dropbox", "OneDrive", "iCloud"],
                    index=0
                )
                
                st.info("クラウド連携を設定するには、設定メニューからアカウント連携を行ってください。")
        
        # 高度な設定
        with st.expander("高度な設定", expanded=False):
            # 圧縮オプション
            compression = st.checkbox(
                "ZIP圧縮",
                value=False,
                help="複数ファイルをZIPファイルにまとめます"
            )
            
            # パスワード保護
            password_protect = st.checkbox(
                "パスワード保護",
                value=False,
                help="エクスポートファイルをパスワードで保護します"
            )
            
            if password_protect:
                password = st.text_input(
                    "パスワード",
                    type="password",
                    help="ファイルを開くためのパスワードを設定します"
                )
            
            # メタデータオプション
            include_metadata = st.checkbox(
                "メタデータを含める",
                value=True,
                help="ファイルにメタデータ情報を埋め込みます"
            )
            
            # バージョン情報
            include_version = st.checkbox(
                "バージョン情報を含める",
                value=True,
                help="エクスポートしたアプリケーションのバージョン情報を含めます"
            )
        
        # ヘルプ情報
        st.markdown("---")
        st.markdown("**ヘルプ:** エクスポート機能について詳しくは、[ユーザーガイド](https://example.com/guide)をご覧ください。")

if __name__ == "__main__":
    render_page()
