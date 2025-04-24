# -*- coding: utf-8 -*-
"""
ui.components.export.export_result_panel

エクスポート結果表示パネルコンポーネント
"""

import streamlit as st
import os
import time
import datetime
from typing import Dict, Any, List, Optional, Callable, Union


class ExportResultPanel:
    """
    エクスポート結果表示パネルコンポーネント
    
    エクスポート結果を表示するためのUIコンポーネント。
    成功・失敗のサマリー、詳細結果、エラーメッセージなどを表示します。
    """
    
    def __init__(self, key: str = "export_result"):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントキー, by default "export_result"
        """
        self.key = key
        
        # ステート管理
        if f"{key}_results" not in st.session_state:
            st.session_state[f"{key}_results"] = None
        if f"{key}_show_details" not in st.session_state:
            st.session_state[f"{key}_show_details"] = False
    
    def set_results(self, results: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """
        エクスポート結果を設定
        
        Parameters
        ----------
        results : Union[Dict[str, Any], List[Dict[str, Any]]]
            エクスポート結果（単一または複数）
        """
        st.session_state[f"{self.key}_results"] = results
    
    def clear_results(self):
        """結果をクリア"""
        st.session_state[f"{self.key}_results"] = None
        st.session_state[f"{self.key}_show_details"] = False
    
    def render(self):
        """コンポーネントを表示"""
        results = st.session_state.get(f"{self.key}_results")
        
        if results is None:
            st.info("エクスポート結果がありません")
            return
        
        # 結果が単一の場合はリストに変換
        if not isinstance(results, list):
            results = [results]
        
        # サマリー表示
        total_count = len(results)
        success_count = sum(1 for r in results if r.get("success", False))
        fail_count = total_count - success_count
        
        # サマリータイル
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("合計", f"{total_count} 件")
        
        with col2:
            st.metric("成功", f"{success_count} 件", delta=f"{success_count/total_count*100:.1f}%" if total_count > 0 else "0%")
        
        with col3:
            st.metric("失敗", f"{fail_count} 件", delta=f"{-fail_count/total_count*100:.1f}%" if total_count > 0 else "0%", delta_color="inverse")
        
        # 詳細表示
        if st.checkbox(
            "詳細を表示", 
            value=st.session_state[f"{self.key}_show_details"],
            key=f"{self.key}_toggle_details"
        ):
            st.session_state[f"{self.key}_show_details"] = True
            self._render_result_details(results)
        else:
            st.session_state[f"{self.key}_show_details"] = False
    
    def _render_result_details(self, results: List[Dict[str, Any]]):
        """
        結果詳細を表示
        
        Parameters
        ----------
        results : List[Dict[str, Any]]
            結果リスト
        """
        # フィルタオプション
        filter_option = st.radio(
            "フィルタ",
            ["すべて", "成功のみ", "失敗のみ"],
            horizontal=True,
            key=f"{self.key}_filter_option"
        )
        
        # 結果をフィルタリング
        filtered_results = results
        if filter_option == "成功のみ":
            filtered_results = [r for r in results if r.get("success", False)]
        elif filter_option == "失敗のみ":
            filtered_results = [r for r in results if not r.get("success", False)]
        
        # 詳細リスト表示
        if not filtered_results:
            st.info(f"表示する結果がありません（フィルタ: {filter_option}）")
            return
        
        # 結果を表形式で表示
        st.write("### エクスポート詳細")
        
        # 結果データ作成
        details_data = []
        for i, result in enumerate(filtered_results, 1):
            session_name = result.get("session_name", "Unknown")
            session_id = result.get("session_id", "Unknown")
            success = result.get("success", False)
            output_path = result.get("output_path", "")
            error = result.get("error", "")
            timestamp = result.get("timestamp", datetime.datetime.now().isoformat())
            
            # 日時の整形
            if isinstance(timestamp, str):
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_time = timestamp
            else:
                formatted_time = str(timestamp)
            
            details_data.append({
                "No.": i,
                "結果": "✅ 成功" if success else "❌ 失敗",
                "セッション名": session_name,
                "セッションID": session_id,
                "出力先": os.path.basename(output_path) if output_path else "",
                "エラー": error,
                "時刻": formatted_time
            })
        
        # カラム表示で容量が少ない場合は表示しない
        columns_to_display = ["No.", "結果", "セッション名"]
        if st.checkbox("詳細情報を表示", key=f"{self.key}_show_extra_columns"):
            columns_to_display.extend(["セッションID", "出力先", "時刻"])
            if filter_option in ["すべて", "失敗のみ"]:
                columns_to_display.append("エラー")
        
        # ページネーション
        page_size = st.select_slider(
            "表示件数", 
            options=[5, 10, 20, 50, 100],
            value=10,
            key=f"{self.key}_page_size"
        )
        
        total_pages = (len(details_data) + page_size - 1) // page_size
        
        if f"{self.key}_current_page" not in st.session_state:
            st.session_state[f"{self.key}_current_page"] = 0
        
        current_page = st.session_state[f"{self.key}_current_page"]
        
        # ページネーション調整
        if current_page >= total_pages:
            current_page = total_pages - 1 if total_pages > 0 else 0
            st.session_state[f"{self.key}_current_page"] = current_page
        
        # ページネーションUI
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("前へ", key=f"{self.key}_prev_page", disabled=current_page == 0):
                    st.session_state[f"{self.key}_current_page"] = max(0, current_page - 1)
                    st.experimental_rerun()
                    
            with col2:
                st.write(f"ページ {current_page + 1} / {total_pages}")
                
            with col3:
                if st.button("次へ", key=f"{self.key}_next_page", disabled=current_page >= total_pages - 1):
                    st.session_state[f"{self.key}_current_page"] = min(total_pages - 1, current_page + 1)
                    st.experimental_rerun()
        
        # ページデータの抽出
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(details_data))
        page_data = details_data[start_idx:end_idx]
        
        # ページ情報
        st.write(f"{start_idx + 1}～{end_idx} 件目 / 全{len(details_data)}件")
        
        # データテーブル表示
        if page_data:
            # DataFrameではなくHTMLテーブルを手動で作成（より詳細な制御のため）
            table_html = """
            <style>
            .result-table {
                width: 100%;
                border-collapse: collapse;
            }
            .result-table th {
                background-color: #f0f2f6;
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .result-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .result-table td {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            .success {
                color: green;
            }
            .failure {
                color: red;
            }
            </style>
            <table class="result-table">
                <thead>
                    <tr>
            """
            
            # テーブルヘッダー
            for col in columns_to_display:
                table_html += f"<th>{col}</th>"
            
            table_html += """
                    </tr>
                </thead>
                <tbody>
            """
            
            # テーブルデータ
            for row in page_data:
                table_html += "<tr>"
                for col in columns_to_display:
                    value = row.get(col, "")
                    
                    # 結果列のスタイリング
                    if col == "結果":
                        css_class = "success" if "✅" in value else "failure"
                        table_html += f'<td class="{css_class}">{value}</td>'
                    else:
                        table_html += f"<td>{value}</td>"
                
                table_html += "</tr>"
            
            table_html += """
                </tbody>
            </table>
            """
            
            st.markdown(table_html, unsafe_allow_html=True)
            
            # エラーの詳細表示（失敗がある場合）
            if filter_option in ["すべて", "失敗のみ"] and any(not r.get("success", False) for r in filtered_results):
                with st.expander("エラー詳細", expanded=False):
                    for i, result in enumerate(filtered_results):
                        if not result.get("success", False):
                            session_name = result.get("session_name", "Unknown")
                            error = result.get("error", "")
                            
                            st.markdown(f"**{i+1}. {session_name}**")
                            st.error(error)
        else:
            st.info("表示するデータがありません")
