# -*- coding: utf-8 -*-
"""
ui.integrated.components.reporting.report_builder

セーリング戦略分析システムのレポートビルダーモジュール
"""

import os
import json
import base64
import datetime
import tempfile
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Dict, Any, List, Optional, Tuple, Union

from .template_manager import TemplateManager


class ReportBuilder:
    """
    レポートの生成と編集を行うクラス。
    テンプレート適用、コンテンツ編集、プレビュー、エクスポート機能を提供します。
    """
    
    # サポートするエクスポート形式
    EXPORT_FORMATS = ["PDF", "HTML", "Markdown", "PNG"]
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        レポートビルダーの初期化
        
        Args:
            template_manager: テンプレートマネージャーのインスタンス
                             指定がない場合は新しいインスタンスを作成
        """
        # テンプレートマネージャーの設定
        self.template_manager = template_manager or TemplateManager()
        
        # レポートの保存先ディレクトリ
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
        self.reports_dir = os.path.join(root_dir, 'data', 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # セッション状態の初期化
        if 'current_report' not in st.session_state:
            st.session_state.current_report = None
        if 'report_preview' not in st.session_state:
            st.session_state.report_preview = None

    def create_report(self, template_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レポートを新規作成
        
        Args:
            template_id: 使用するテンプレートのID
            session_data: レポートに含めるセッションデータ
            
        Returns:
            作成されたレポート
        """
        # テンプレートを取得
        template = self.template_manager.get_template(template_id)
        
        # レポートの基本情報
        report = {
            "id": f"report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": f"レポート: {session_data.get('name', '無題セッション')}",
            "template_id": template_id,
            "session_id": session_data.get("id", ""),
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "sections": [],
            "metadata": {
                "session_name": session_data.get("name", ""),
                "session_date": session_data.get("date", ""),
                "session_location": session_data.get("location", ""),
                "boat_type": session_data.get("boat_type", ""),
                "wind_conditions": session_data.get("wind_conditions", ""),
                "report_creator": session_data.get("user", ""),
                "notes": ""
            }
        }
        
        # テンプレートのセクションをコピー
        for section_template in template.get("sections", []):
            section = section_template.copy()
            
            # セクションの内容に変数を適用
            content = section.get("content", "")
            content = self._apply_variables(content, report, session_data)
            section["content"] = content
            
            # 生成されたコンテンツの追加
            section["generated_content"] = self._generate_section_content(
                section["type"], 
                section.get("options", {}), 
                session_data
            )
            
            report["sections"].append(section)
        
        return report

    def update_report(self, report: Dict[str, Any], 
                      updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存のレポートを更新
        
        Args:
            report: 更新するレポート
            updates: 更新内容
            
        Returns:
            更新されたレポート
        """
        updated_report = report.copy()
        
        # 基本フィールドの更新
        for field in ["title", "metadata"]:
            if field in updates:
                updated_report[field] = updates[field]
        
        # セクションの更新
        if "sections" in updates:
            updated_report["sections"] = updates["sections"]
        
        # 更新日時の設定
        updated_report["updated_at"] = datetime.datetime.now().isoformat()
        
        return updated_report

    def save_report(self, report: Dict[str, Any]) -> str:
        """
        レポートを保存
        
        Args:
            report: 保存するレポート
            
        Returns:
            保存されたレポートのID
        """
        report_id = report["id"]
        file_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(report, file, ensure_ascii=False, indent=2)
        
        return report_id

    def load_report(self, report_id: str) -> Dict[str, Any]:
        """
        保存されたレポートを読み込み
        
        Args:
            report_id: 読み込むレポートのID
            
        Returns:
            読み込まれたレポート
            
        Raises:
            FileNotFoundError: 指定されたIDのレポートが存在しない場合
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"レポートID '{report_id}' は存在しません")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            report = json.load(file)
        
        return report

    def delete_report(self, report_id: str) -> bool:
        """
        レポートを削除
        
        Args:
            report_id: 削除するレポートのID
            
        Returns:
            削除が成功したかどうか
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
        return False

    def list_reports(self) -> List[Dict[str, Any]]:
        """
        保存されているレポートの一覧を取得
        
        Returns:
            レポートのリスト
        """
        reports = []
        
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.reports_dir, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            report = json.load(file)
                            reports.append({
                                "id": report["id"],
                                "title": report["title"],
                                "created_at": report["created_at"],
                                "updated_at": report["updated_at"],
                                "session_id": report.get("session_id", ""),
                                "template_id": report.get("template_id", "")
                            })
                    except Exception as e:
                        st.warning(f"レポートファイル '{filename}' の読み込みに失敗しました: {e}")
        
        # 更新日時の新しい順にソート
        reports.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return reports

    def export_report(self, report: Dict[str, Any], 
                      format: str = "PDF") -> Tuple[bytes, str]:
        """
        レポートを指定された形式でエクスポート
        
        Args:
            report: エクスポートするレポート
            format: エクスポート形式（"PDF", "HTML", "Markdown", "PNG"のいずれか）
            
        Returns:
            エクスポートされたデータとファイル名のタプル
            
        Raises:
            ValueError: サポートされていない形式が指定された場合
        """
        if format not in self.EXPORT_FORMATS:
            raise ValueError(f"サポートされていないエクスポート形式: {format}")
        
        if format == "PDF":
            return self._export_pdf(report)
        elif format == "HTML":
            return self._export_html(report)
        elif format == "Markdown":
            return self._export_markdown(report)
        elif format == "PNG":
            return self._export_png(report)

    def render_report_builder(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        レポートビルダーUIを描画
        
        Args:
            session_data: レポートに含めるセッションデータ
            
        Returns:
            作成または編集されたレポート（完了していない場合はNone）
        """
        st.subheader("レポートビルダー")
        
        # 既存レポートの選択または新規作成
        create_new = st.checkbox("新規レポートを作成", value=True)
        
        if create_new:
            # テンプレート選択
            template_id, _ = self.template_manager.render_template_selection()
            
            if st.button("レポートを生成"):
                report = self.create_report(template_id, session_data)
                st.session_state.current_report = report
                st.session_state.report_preview = self._generate_preview(report)
                st.experimental_rerun()
        else:
            # 既存レポートの一覧
            reports = self.list_reports()
            
            if not reports:
                st.info("保存されたレポートがありません。新規レポートを作成してください。")
                return None
            
            # レポート選択
            report_options = [(r["id"], f"{r['title']} ({self._format_datetime(r['updated_at'])})") 
                              for r in reports]
            
            selected_idx = st.selectbox(
                "レポートを選択",
                range(len(report_options)),
                format_func=lambda i: report_options[i][1]
            )
            
            selected_report_id = report_options[selected_idx][0]
            
            if st.button("レポートを読み込む"):
                report = self.load_report(selected_report_id)
                st.session_state.current_report = report
                st.session_state.report_preview = self._generate_preview(report)
                st.experimental_rerun()
        
        # 現在のレポートがある場合は編集UIとプレビューを表示
        if st.session_state.current_report:
            report = st.session_state.current_report
            
            # タブでエディタとプレビューを切り替え
            tab1, tab2 = st.tabs(["エディタ", "プレビュー"])
            
            with tab1:
                # レポート基本情報の編集
                report["title"] = st.text_input("レポートタイトル", report["title"])
                
                # メタデータの編集
                st.subheader("メタデータ")
                metadata = report.get("metadata", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    metadata["session_name"] = st.text_input("セッション名", metadata.get("session_name", ""))
                    metadata["session_date"] = st.text_input("日付", metadata.get("session_date", ""))
                    metadata["boat_type"] = st.text_input("艇種", metadata.get("boat_type", ""))
                
                with col2:
                    metadata["session_location"] = st.text_input("場所", metadata.get("session_location", ""))
                    metadata["wind_conditions"] = st.text_input("風況", metadata.get("wind_conditions", ""))
                    metadata["report_creator"] = st.text_input("作成者", metadata.get("report_creator", ""))
                
                metadata["notes"] = st.text_area("備考", metadata.get("notes", ""))
                
                report["metadata"] = metadata
                
                # セクションの編集
                st.subheader("セクション")
                
                # セッション状態の初期化（セクション編集用）
                if "editing_report_section" not in st.session_state:
                    st.session_state.editing_report_section = -1  # -1: 編集なし
                
                # セクション一覧の表示
                for i, section in enumerate(report.get("sections", [])):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{i+1}. {section['title']}** ({section['type']})")
                    
                    with col2:
                        if st.button("編集", key=f"edit_report_section_{i}"):
                            st.session_state.editing_report_section = i
                    
                    with col3:
                        if st.button("削除", key=f"delete_report_section_{i}"):
                            report["sections"].pop(i)
                            st.experimental_rerun()
                
                # セクションの追加ボタン
                if st.button("セクションを追加"):
                    st.session_state.editing_report_section = len(report.get("sections", []))
                    report["sections"].append({
                        "title": "新しいセクション",
                        "type": "カスタムセクション",
                        "content": "",
                        "options": {},
                        "generated_content": {}
                    })
                    st.experimental_rerun()
                
                # セクション編集UI
                if st.session_state.editing_report_section >= 0:
                    st.markdown("---")
                    st.subheader("セクションの編集")
                    
                    i = st.session_state.editing_report_section
                    if i < len(report.get("sections", [])):
                        section = report["sections"][i]
                        
                        # セクション情報の編集
                        section["title"] = st.text_input("セクションタイトル", section["title"])
                        section["type"] = st.selectbox(
                            "セクションタイプ", 
                            self.template_manager.SECTION_TYPES,
                            index=self.template_manager.SECTION_TYPES.index(section["type"]) 
                                  if section["type"] in self.template_manager.SECTION_TYPES 
                                  else 0
                        )
                        
                        # セクションの内容（テキスト）
                        section["content"] = st.text_area("内容（マークダウン形式）", section["content"], height=200)
                        
                        # セクションオプションの編集
                        st.subheader("セクションオプション")
                        
                        options = section.get("options", {}).copy()
                        
                        if section["type"] == "基本情報":
                            options["show_date"] = st.checkbox("日時を表示", options.get("show_date", True))
                            options["show_location"] = st.checkbox("場所を表示", options.get("show_location", True))
                            options["show_boat_type"] = st.checkbox("艇種を表示", options.get("show_boat_type", True))
                            options["show_conditions"] = st.checkbox("風況を表示", options.get("show_conditions", True))
                        
                        elif section["type"] in ["風向分析", "パフォーマンス指標", "データ品質"]:
                            options["show_charts"] = st.checkbox("チャートを表示", options.get("show_charts", True))
                            options["show_summary"] = st.checkbox("サマリーを表示", options.get("show_summary", True))
                            options["show_details"] = st.checkbox("詳細を表示", options.get("show_details", False))
                        
                        elif section["type"] == "マップビュー":
                            map_types = ["標準マップ", "風向マップ", "速度ヒートマップ", "VMGヒートマップ"]
                            options["map_type"] = st.selectbox(
                                "マップタイプ", 
                                map_types, 
                                index=map_types.index(options.get("map_type", "標準マップ")) 
                                      if options.get("map_type") in map_types 
                                      else 0
                            )
                            options["show_track"] = st.checkbox("トラックを表示", options.get("show_track", True))
                            options["show_points"] = st.checkbox("ポイントを表示", options.get("show_points", True))
                        
                        section["options"] = options
                        
                        # セクションの更新
                        if st.button("セクションを更新"):
                            # 生成されたコンテンツを更新
                            section["generated_content"] = self._generate_section_content(
                                section["type"], 
                                section["options"], 
                                session_data
                            )
                            
                            report["sections"][i] = section
                            st.session_state.report_preview = self._generate_preview(report)
                            st.session_state.editing_report_section = -1
                            st.experimental_rerun()
                        
                        if st.button("キャンセル"):
                            st.session_state.editing_report_section = -1
                            st.experimental_rerun()
                
                # レポートの保存
                st.markdown("---")
                if st.button("レポートを保存"):
                    # 更新日時の設定
                    report["updated_at"] = datetime.datetime.now().isoformat()
                    
                    # レポートの保存
                    self.save_report(report)
                    st.success("レポートを保存しました")
                    
                    # プレビューの更新
                    st.session_state.report_preview = self._generate_preview(report)
            
            with tab2:
                # レポートのプレビュー表示
                if st.session_state.report_preview:
                    st.markdown(st.session_state.report_preview, unsafe_allow_html=True)
                else:
                    st.session_state.report_preview = self._generate_preview(report)
                    st.experimental_rerun()
            
            # エクスポートオプション
            st.subheader("エクスポート")
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox("エクスポート形式", self.EXPORT_FORMATS)
            
            with col2:
                if st.button("エクスポート"):
                    try:
                        export_data, filename = self.export_report(report, export_format)
                        
                        # ダウンロードリンクの提供
                        b64_data = base64.b64encode(export_data).decode()
                        href = f'<a href="data:application/octet-stream;base64,{b64_data}" download="{filename}">クリックしてダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                        st.success(f"{export_format}形式でエクスポートしました")
                    except Exception as e:
                        st.error(f"エクスポート中にエラーが発生しました: {e}")
            
            return report
        
        return None

    def _apply_variables(self, content: str, report: Dict[str, Any], 
                         session_data: Dict[str, Any]) -> str:
        """
        テンプレートコンテンツに変数を適用
        
        Args:
            content: 元のコンテンツ
            report: レポート情報
            session_data: セッションデータ
            
        Returns:
            変数が適用されたコンテンツ
        """
        # メタデータ変数の置換
        metadata = report.get("metadata", {})
        replacements = {
            "{session_name}": metadata.get("session_name", ""),
            "{session_date}": metadata.get("session_date", ""),
            "{session_location}": metadata.get("session_location", ""),
            "{boat_type}": metadata.get("boat_type", ""),
            "{wind_conditions}": metadata.get("wind_conditions", ""),
            "{report_date}": datetime.datetime.now().strftime("%Y年%m月%d日"),
            "{analyst_name}": metadata.get("report_creator", "")
        }
        
        # セッションデータから変数を追加
        if "performance" in session_data:
            perf = session_data["performance"]
            replacements.update({
                "{avg_speed}": str(perf.get("avg_speed", "-")),
                "{max_speed}": str(perf.get("max_speed", "-")),
                "{upwind_vmg}": str(perf.get("upwind_vmg", "-")),
                "{downwind_vmg}": str(perf.get("downwind_vmg", "-"))
            })
        
        # 戦略ポイントのサマリー
        if "strategy_points" in session_data and session_data["strategy_points"]:
            points = session_data["strategy_points"]
            summary = "\n".join([f"- {point.get('time', '')}: {point.get('description', '')}" 
                                for point in points[:5]])
            replacements["{strategy_points_summary}"] = summary
        else:
            replacements["{strategy_points_summary}"] = "戦略ポイントのデータがありません。"
        
        # 変数の置換
        result = content
        for var, value in replacements.items():
            result = result.replace(var, value)
        
        return result

    def _generate_section_content(self, section_type: str, options: Dict[str, Any], 
                                 session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        セクションタイプに応じた生成コンテンツを作成
        
        Args:
            section_type: セクションのタイプ
            options: セクションオプション
            session_data: セッションデータ
            
        Returns:
            生成されたコンテンツ
        """
        generated = {}
        
        # セクションタイプに応じたコンテンツ生成
        if section_type == "基本情報":
            generated["metadata"] = {
                "session_name": session_data.get("name", ""),
                "session_date": session_data.get("date", ""),
                "session_location": session_data.get("location", ""),
                "boat_type": session_data.get("boat_type", ""),
                "wind_conditions": session_data.get("wind_conditions", "")
            }
        
        elif section_type == "風向分析":
            if options.get("show_charts", True) and "wind_data" in session_data:
                # 風向分析のチャートを生成（サンプル）
                generated["wind_direction_chart"] = self._generate_chart_image("風向の時間変化")
                generated["wind_speed_chart"] = self._generate_chart_image("風速の時間変化")
            
            if options.get("show_summary", True):
                # サマリーテキスト（サンプル）
                generated["summary"] = """
                セッション中の平均風向は210度（南南西）、平均風速は12.5ノットでした。
                主な風向シフトは13:15頃（右15度）、13:42頃（左12度）、14:35頃（右20度）に観測されました。
                特に14:35の右シフトは大きく、コース選択に影響しました。
                """
        
        elif section_type == "パフォーマンス指標":
            if options.get("show_charts", True) and "performance" in session_data:
                # パフォーマンスチャートを生成（サンプル）
                generated["vmg_chart"] = self._generate_chart_image("VMG分析")
                generated["speed_chart"] = self._generate_chart_image("速度分布")
                generated["polar_chart"] = self._generate_chart_image("ポーラーチャート")
            
            if options.get("show_summary", True):
                # サマリーテキスト（サンプル）
                generated["summary"] = """
                平均速度: 6.2kt、最高速度: 8.5kt
                風上VMG: 3.2kt（理論最大の85%）
                風下VMG: 4.5kt（理論最大の88%）
                タック効率: 92%、ジャイブ効率: 86%
                """
        
        elif section_type == "戦略ポイント分析":
            if "strategy_points" in session_data:
                # 戦略ポイントのサマリー（サンプル）
                generated["points_summary"] = """
                検出された主要な戦略ポイント:
                - 13:15 - 右シフト15度への早期対応（最適）
                - 13:42 - レイライン接近時のタック（改善必要）
                - 14:10 - 風向シフトでの様子見（不適切）
                - 14:35 - 大きな右シフトの見逃し（不適切）
                - 15:00 - 風上へのコース変更（最適）
                """
                
                if options.get("show_map", True):
                    generated["strategy_map"] = self._generate_chart_image("戦略ポイントマップ")
                
                if options.get("show_timeline", True):
                    generated["timeline_chart"] = self._generate_chart_image("戦略ポイントタイムライン")
        
        elif section_type == "マップビュー":
            # マップ画像の生成（サンプル）
            map_type = options.get("map_type", "標準マップ")
            generated["map_image"] = self._generate_chart_image(f"{map_type}")
        
        elif section_type == "データ品質":
            if options.get("show_charts", True):
                # データ品質チャートを生成（サンプル）
                generated["quality_chart"] = self._generate_chart_image("データ品質スコア")
                generated["completeness_chart"] = self._generate_chart_image("データ完全性")
            
            if options.get("show_summary", True):
                # サマリーテキスト（サンプル）
                generated["summary"] = """
                データ完全性: 98.2%
                データ一貫性: 95.5%
                GPS精度: 92.3%
                サンプリング均一性: 96.7%
                異常値比率: 1.8%
                総合品質スコア: 94.6%
                """
        
        elif section_type == "改善提案":
            # 改善提案（サンプル）
            generated["recommendations"] = """
            分析結果に基づく改善提案:
            
            1. **風向シフトの予測と対応**: 右シフトパターンをより早く察知し、事前対応することで約30秒の利得が期待できます。
            2. **タック実行の判断**: オーバースタンドが2回観測されました。レイライン接近時の判断を改善してください。
            3. **風下での艇速**: 風下走行時の艇速が理想値を10%下回っています。セールトリムの調整を検討してください。
            """
        
        return generated

    def _generate_preview(self, report: Dict[str, Any]) -> str:
        """
        レポートのプレビューHTMLを生成
        
        Args:
            report: プレビューするレポート
            
        Returns:
            HTMLマークアップ
        """
        # HTMLヘッダー
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{report["title"]}</h1>
        """
        
        # メタデータセクション
        metadata = report.get("metadata", {})
        html += """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        """
        
        if metadata.get("session_name"):
            html += f"<p><strong>セッション名:</strong> {metadata['session_name']}</p>"
        if metadata.get("session_date"):
            html += f"<p><strong>日付:</strong> {metadata['session_date']}</p>"
        if metadata.get("session_location"):
            html += f"<p><strong>場所:</strong> {metadata['session_location']}</p>"
        if metadata.get("boat_type"):
            html += f"<p><strong>艇種:</strong> {metadata['boat_type']}</p>"
        if metadata.get("wind_conditions"):
            html += f"<p><strong>風況:</strong> {metadata['wind_conditions']}</p>"
        if metadata.get("report_creator"):
            html += f"<p><strong>作成者:</strong> {metadata['report_creator']}</p>"
        if metadata.get("notes"):
            html += f"<p><strong>備考:</strong> {metadata['notes']}</p>"
        
        html += "</div>"
        
        # セクション
        for section in report.get("sections", []):
            html += f"""
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-left: 4px solid #3498db; padding-left: 10px;">{section["title"]}</h2>
                <div style="margin-left: 15px;">
            """
            
            # マークダウンコンテンツ
            if section.get("content"):
                # 簡易的なマークダウン変換（より高度な変換が必要な場合はライブラリを使用）
                content = section["content"]
                # 見出し
                content = content.replace("# ", "<h1>").replace(" #", "</h1>")
                content = content.replace("## ", "<h2>").replace(" ##", "</h2>")
                content = content.replace("### ", "<h3>").replace(" ###", "</h3>")
                # 太字
                content = content.replace("**", "<strong>").replace("**", "</strong>")
                # 箇条書き
                content = content.replace("\n- ", "<br>• ")
                # 改行
                content = content.replace("\n", "<br>")
                
                html += f"<div>{content}</div>"
            
            # 生成されたコンテンツ
            generated = section.get("generated_content", {})
            
            if section["type"] == "基本情報":
                # 基本情報はメタデータセクションで表示済み
                pass
            
            elif section["type"] == "風向分析":
                if "wind_direction_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['wind_direction_chart']}" 
                             style="max-width: 100%; height: auto;" alt="風向の時間変化">
                    </div>
                    """
                
                if "wind_speed_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['wind_speed_chart']}" 
                             style="max-width: 100%; height: auto;" alt="風速の時間変化">
                    </div>
                    """
                
                if "summary" in generated:
                    html += f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        {generated['summary']}
                    </div>
                    """
            
            elif section["type"] == "パフォーマンス指標":
                if "vmg_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['vmg_chart']}" 
                             style="max-width: 100%; height: auto;" alt="VMG分析">
                    </div>
                    """
                
                if "speed_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['speed_chart']}" 
                             style="max-width: 100%; height: auto;" alt="速度分布">
                    </div>
                    """
                
                if "polar_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['polar_chart']}" 
                             style="max-width: 100%; height: auto;" alt="ポーラーチャート">
                    </div>
                    """
                
                if "summary" in generated:
                    html += f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        {generated['summary']}
                    </div>
                    """
            
            elif section["type"] == "戦略ポイント分析":
                if "points_summary" in generated:
                    html += f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        {generated['points_summary']}
                    </div>
                    """
                
                if "strategy_map" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['strategy_map']}" 
                             style="max-width: 100%; height: auto;" alt="戦略ポイントマップ">
                    </div>
                    """
                
                if "timeline_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['timeline_chart']}" 
                             style="max-width: 100%; height: auto;" alt="戦略ポイントタイムライン">
                    </div>
                    """
            
            elif section["type"] == "マップビュー":
                if "map_image" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['map_image']}" 
                             style="max-width: 100%; height: auto;" alt="コースマップ">
                    </div>
                    """
            
            elif section["type"] == "データ品質":
                if "quality_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['quality_chart']}" 
                             style="max-width: 100%; height: auto;" alt="データ品質スコア">
                    </div>
                    """
                
                if "completeness_chart" in generated:
                    html += f"""
                    <div style="margin: 15px 0;">
                        <img src="data:image/png;base64,{generated['completeness_chart']}" 
                             style="max-width: 100%; height: auto;" alt="データ完全性">
                    </div>
                    """
                
                if "summary" in generated:
                    html += f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        {generated['summary']}
                    </div>
                    """
            
            elif section["type"] == "改善提案":
                if "recommendations" in generated:
                    html += f"""
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        {generated['recommendations']}
                    </div>
                    """
            
            html += """
                </div>
            </div>
            """
        
        # フッター
        html += f"""
        <div style="text-align: center; margin-top: 50px; color: #7f8c8d; font-size: 12px;">
            <p>セーリング戦略分析システムによって生成されたレポート</p>
            <p>作成日時: {self._format_datetime(report.get("created_at", ""))}</p>
            <p>更新日時: {self._format_datetime(report.get("updated_at", ""))}</p>
        </div>
        """
        
        html += "</div>"
        
        return html

    def _export_pdf(self, report: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        レポートをPDF形式でエクスポート
        
        Args:
            report: エクスポートするレポート
            
        Returns:
            PDFデータとファイル名のタプル
        """
        try:
            import pdfkit
            
            # HTMLをPDFに変換
            html_content = self._generate_preview(report)
            
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as html_file:
                html_file.write(html_content.encode('utf-8'))
                html_path = html_file.name
            
            # PDFに変換（wkhtmltopdfがインストールされている必要があります）
            pdf_data = pdfkit.from_file(html_path, False)
            
            # 一時ファイルを削除
            os.unlink(html_path)
            
            # ファイル名の生成
            filename = f"{report['title'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
            
            return pdf_data, filename
        
        except ImportError:
            # pdfkitがインストールされていない場合
            st.error("PDFエクスポートにはpdfkitライブラリが必要です")
            
            # 代わりにHTMLでエクスポート
            return self._export_html(report)

    def _export_html(self, report: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        レポートをHTML形式でエクスポート
        
        Args:
            report: エクスポートするレポート
            
        Returns:
            HTMLデータとファイル名のタプル
        """
        html_content = self._generate_preview(report)
        filename = f"{report['title'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.html"
        
        return html_content.encode('utf-8'), filename

    def _export_markdown(self, report: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        レポートをMarkdown形式でエクスポート
        
        Args:
            report: エクスポートするレポート
            
        Returns:
            Markdownデータとファイル名のタプル
        """
        # マークダウンの生成
        markdown = f"# {report['title']}\n\n"
        
        # メタデータセクション
        metadata = report.get("metadata", {})
        markdown += "## メタデータ\n\n"
        
        if metadata.get("session_name"):
            markdown += f"- **セッション名:** {metadata['session_name']}\n"
        if metadata.get("session_date"):
            markdown += f"- **日付:** {metadata['session_date']}\n"
        if metadata.get("session_location"):
            markdown += f"- **場所:** {metadata['session_location']}\n"
        if metadata.get("boat_type"):
            markdown += f"- **艇種:** {metadata['boat_type']}\n"
        if metadata.get("wind_conditions"):
            markdown += f"- **風況:** {metadata['wind_conditions']}\n"
        if metadata.get("report_creator"):
            markdown += f"- **作成者:** {metadata['report_creator']}\n"
        if metadata.get("notes"):
            markdown += f"- **備考:** {metadata['notes']}\n"
        
        markdown += "\n"
        
        # セクション
        for section in report.get("sections", []):
            markdown += f"## {section['title']}\n\n"
            
            # セクションコンテンツ
            if section.get("content"):
                markdown += f"{section['content']}\n\n"
            
            # 生成されたコンテンツ（テキストのみ）
            generated = section.get("generated_content", {})
            
            if "summary" in generated:
                markdown += f"{generated['summary']}\n\n"
            
            if "points_summary" in generated:
                markdown += f"{generated['points_summary']}\n\n"
            
            if "recommendations" in generated:
                markdown += f"{generated['recommendations']}\n\n"
            
            # 画像は参照情報を追加
            image_keys = [k for k in generated.keys() if k.endswith("_chart") or k.endswith("_image")]
            if image_keys:
                markdown += "### 画像\n\n"
                for key in image_keys:
                    image_name = key.replace("_", " ").title()
                    markdown += f"- {image_name} (エクスポート時に画像は含まれません)\n"
                
                markdown += "\n"
        
        # フッター
        markdown += "---\n\n"
        markdown += "セーリング戦略分析システムによって生成されたレポート\n\n"
        markdown += f"作成日時: {self._format_datetime(report.get('created_at', ''))}\n\n"
        markdown += f"更新日時: {self._format_datetime(report.get('updated_at', ''))}\n"
        
        filename = f"{report['title'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.md"
        
        return markdown.encode('utf-8'), filename

    def _export_png(self, report: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        レポートの最初のページをPNG形式でエクスポート
        
        Args:
            report: エクスポートするレポート
            
        Returns:
            PNGデータとファイル名のタプル
        """
        try:
            from PIL import Image
            
            # サンプル画像を生成（実際の実装では、レポートのプレビューをPNGに変換）
            fig, ax = plt.subplots(figsize=(10, 14))
            ax.text(0.5, 0.9, report["title"], fontsize=24, ha='center')
            
            metadata = report.get("metadata", {})
            metadata_text = (
                f"セッション: {metadata.get('session_name', '')}\n"
                f"日付: {metadata.get('session_date', '')}\n"
                f"場所: {metadata.get('session_location', '')}\n"
                f"艇種: {metadata.get('boat_type', '')}\n"
            )
            ax.text(0.5, 0.8, metadata_text, fontsize=14, ha='center')
            
            # サンプルコンテンツ
            sections_text = "\n".join([f"- {section['title']}" for section in report.get("sections", [])])
            ax.text(0.5, 0.5, f"セクション:\n{sections_text}", fontsize=12, ha='center')
            
            ax.text(0.5, 0.1, f"作成日時: {self._format_datetime(report.get('created_at', ''))}", fontsize=10, ha='center')
            
            ax.axis('off')
            
            # 画像データを取得
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            
            # ファイル名の生成
            filename = f"{report['title'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.png"
            
            return buf.getvalue(), filename
        
        except Exception as e:
            st.error(f"PNG生成エラー: {e}")
            
            # エラーが発生した場合はHTMLエクスポートにフォールバック
            return self._export_html(report)

    def _generate_chart_image(self, chart_name: str) -> str:
        """
        サンプルチャート画像を生成し、Base64エンコードで返す
        
        Args:
            chart_name: チャートの名前
            
        Returns:
            Base64エンコードされた画像データ
        """
        # サンプルチャートの生成
        fig, ax = plt.subplots(figsize=(8, 5))
        
        if "風向" in chart_name:
            # 風向のサンプルチャート
            x = np.arange(100)
            y = np.sin(x/10) * 30 + 180  # 180度を中心に±30度の変動
            ax.plot(x, y)
            ax.set_ylabel('風向 (度)')
            ax.set_xlabel('時間')
            ax.set_title(chart_name)
            ax.grid(True)
            
        elif "風速" in chart_name:
            # 風速のサンプルチャート
            x = np.arange(100)
            y = np.sin(x/20) * 3 + 12  # 12ノットを中心に±3ノットの変動
            ax.plot(x, y)
            ax.set_ylabel('風速 (kt)')
            ax.set_xlabel('時間')
            ax.set_title(chart_name)
            ax.grid(True)
            
        elif "VMG" in chart_name:
            # VMGのサンプルチャート
            labels = ['風上VMG', '風下VMG']
            actual_values = [3.2, 4.5]  # 実際の値
            optimal_values = [3.8, 5.0]  # 最適値
            
            x = np.arange(len(labels))
            width = 0.35
            
            ax.bar(x - width/2, actual_values, width, label='実測値')
            ax.bar(x + width/2, optimal_values, width, label='最適値')
            
            ax.set_ylabel('VMG (kt)')
            ax.set_title(chart_name)
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            ax.grid(True, axis='y')
            
        elif "速度分布" in chart_name:
            # 速度分布のサンプルチャート
            data = np.random.normal(6.2, 1.2, 1000)  # 平均6.2ノット、標準偏差1.2のデータ
            ax.hist(data, bins=20, alpha=0.7)
            ax.set_xlabel('速度 (kt)')
            ax.set_ylabel('頻度')
            ax.set_title(chart_name)
            ax.grid(True)
            
        elif "ポーラー" in chart_name:
            # ポーラーチャートのサンプル
            theta = np.linspace(0, 2*np.pi, 100)
            r = 5 + 2 * np.sin(2*theta)  # 基本形状
            
            ax.plot(theta, r, 'r-')
            ax.fill(theta, r, 'r', alpha=0.2)
            
            ax.set_rmax(8)
            ax.set_rticks([2, 4, 6, 8])
            ax.set_rlabel_position(-22.5)
            ax.grid(True)
            ax.set_title(chart_name)
            
        elif "戦略ポイント" in chart_name and "マップ" in chart_name:
            # 戦略ポイントマップのサンプル
            x = np.arange(100)
            y = np.cumsum(np.random.normal(0, 1, 100))  # ランダムウォーク
            
            ax.plot(x, y, 'b-', alpha=0.7)
            
            # 戦略ポイントのマーク
            points_idx = [20, 35, 50, 70, 85]
            points_x = [x[i] for i in points_idx]
            points_y = [y[i] for i in points_idx]
            
            ax.scatter(points_x, points_y, c='r', s=100, marker='o')
            
            for i, idx in enumerate(points_idx):
                ax.annotate(f"Point {i+1}", (x[idx], y[idx]), 
                            xytext=(10, 10), textcoords='offset points')
            
            ax.grid(True)
            ax.set_title(chart_name)
            
        elif "タイムライン" in chart_name:
            # タイムラインのサンプル
            events = ['シフト対応', 'レイライン', 'シフト対応', '障害物回避', 'コース変更']
            times = ['13:10', '13:38', '14:05', '14:32', '15:00']
            quality = [4, 2, 1, 3, 4]  # 4=最適, 3=適切, 2=改善必要, 1=不適切
            
            # 品質に応じた色
            colors = ['green', 'yellow', 'orange', 'red']
            event_colors = [colors[4-q] for q in quality]
            
            y_pos = np.arange(len(events))
            
            ax.barh(y_pos, [1]*len(events), color=event_colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(events)
            ax.set_xticks([])
            
            # 時刻のアノテーション
            for i, time in enumerate(times):
                ax.annotate(time, (0.5, y_pos[i]), 
                            ha='center', va='center', color='black')
            
            ax.invert_yaxis()  # 上から下へ時系列表示
            ax.set_title(chart_name)
            
        elif "品質スコア" in chart_name:
            # データ品質スコアのサンプル
            categories = ['完全性', '一貫性', 'GPS精度', 'サンプリング均一性', '異常値比率', '総合']
            values = [98.2, 95.5, 92.3, 96.7, 98.2, 94.6]
            
            y_pos = np.arange(len(categories))
            
            # 値に応じた色付け
            colors = ['green' if v >= 95 else 'orange' if v >= 90 else 'red' for v in values]
            
            ax.barh(y_pos, values, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(categories)
            ax.set_xlim(85, 100)
            ax.grid(True, axis='x')
            
            # 値のアノテーション
            for i, value in enumerate(values):
                ax.annotate(f"{value}%", (value, y_pos[i]), 
                            xytext=(5, 0), textcoords='offset points')
            
            ax.set_title(chart_name)
            
        elif "完全性" in chart_name:
            # データ完全性のサンプル
            fields = ['GPS位置', '速度', '方位', '風向', '風速', '水温', '気圧', '潮流']
            completeness = [99.8, 99.5, 98.7, 95.2, 94.8, 90.3, 92.6, 88.5]
            
            y_pos = np.arange(len(fields))
            
            # 値に応じた色付け
            colors = ['green' if v >= 95 else 'orange' if v >= 90 else 'red' for v in completeness]
            
            ax.barh(y_pos, completeness, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(fields)
            ax.set_xlim(85, 100)
            ax.grid(True, axis='x')
            
            # 値のアノテーション
            for i, value in enumerate(completeness):
                ax.annotate(f"{value}%", (value, y_pos[i]), 
                            xytext=(5, 0), textcoords='offset points')
            
            ax.set_title(chart_name)
            
        elif "マップ" in chart_name:
            # 簡易的なコースマップ（サンプル）
            # ダミーのGPSトラックを生成
            theta = np.linspace(0, 2*np.pi, 100)
            r = 5 + np.sin(5*theta)
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            
            ax.plot(x, y, 'b-')
            
            # マーク位置
            marks_x = [0, 5, 0, -5]
            marks_y = [5, 0, -5, 0]
            
            ax.scatter(marks_x, marks_y, c='r', s=100, marker='s')
            
            # マークの番号
            for i, (mx, my) in enumerate(zip(marks_x, marks_y)):
                ax.annotate(f"{i+1}", (mx, my), ha='center', va='center', color='white')
            
            # コースの始点と終点
            ax.scatter([x[0]], [y[0]], c='g', s=150, marker='o')
            ax.scatter([x[-1]], [y[-1]], c='r', s=150, marker='o')
            
            ax.annotate("Start", (x[0], y[0]), xytext=(10, 10), textcoords='offset points')
            ax.annotate("Finish", (x[-1], y[-1]), xytext=(10, 10), textcoords='offset points')
            
            # 風向を示す矢印
            ax.arrow(0, -6, 0, 2, head_width=0.5, head_length=0.5, fc='blue', ec='blue')
            ax.text(0, -7, "風向", ha='center', va='center', color='blue')
            
            ax.set_aspect('equal')
            ax.grid(True)
            ax.set_title(chart_name)
        
        else:
            # 汎用的なサンプルチャート
            x = np.arange(100)
            y = np.cumsum(np.random.normal(0, 1, 100))
            ax.plot(x, y)
            ax.set_title(chart_name)
            ax.grid(True)
        
        # 画像をBase64エンコード
        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='png')
        plt.close(fig)
        
        buf.seek(0)
        img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        return img_data

    def _format_datetime(self, datetime_str: str) -> str:
        """
        ISO形式の日時文字列を読みやすい形式に変換
        
        Args:
            datetime_str: ISO形式の日時文字列
            
        Returns:
            読みやすい形式の日時文字列
        """
        try:
            dt = datetime.datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y年%m月%d日 %H:%M")
        except:
            return datetime_str
