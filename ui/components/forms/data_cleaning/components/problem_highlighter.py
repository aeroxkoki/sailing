"""
ui.components.forms.data_cleaning.components.problem_highlighter

問題箇所をハイライト表示するコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator


class ProblemHighlighter:
    """
    問題箇所をハイライト表示するコンポーネント
    
    Parameters
    ----------
    data : pd.DataFrame
        ハイライト対象のデータフレーム
    problem_indices : Dict[str, List[int]]
        問題タイプごとのインデックスリスト
    key : str, optional
        コンポーネントのキー, by default "problem_highlighter"
    """
    
    def __init__(self, 
                data: pd.DataFrame, 
                problem_indices: Dict[str, List[int]],
                key: str = "problem_highlighter"):
        """
        初期化
        
        Parameters
        ----------
        data : pd.DataFrame
            ハイライト対象のデータフレーム
        problem_indices : Dict[str, List[int]]
            問題タイプごとのインデックスリスト
        key : str, optional
            コンポーネントのキー, by default "problem_highlighter"
        """
        self.data = data
        self.problem_indices = problem_indices
        self.key = key
        
        # 問題タイプの日本語表示名
        self.problem_type_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # 問題タイプの色
        self.problem_type_colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        }
        
        # 重要度の色
        self.severity_colors = {
            "error": "#f44336",   # 赤
            "warning": "#ff9800", # オレンジ
            "info": "#2196f3"     # 青
        }
        
        # セッション状態の初期化
        if f"{self.key}_selected_indices" not in st.session_state:
            st.session_state[f"{self.key}_selected_indices"] = []
        
        if f"{self.key}_filtered_problem_type" not in st.session_state:
            st.session_state[f"{self.key}_filtered_problem_type"] = "all"
        
        if f"{self.key}_show_tooltip" not in st.session_state:
            st.session_state[f"{self.key}_show_tooltip"] = False
            
        if f"{self.key}_tooltip_position" not in st.session_state:
            st.session_state[f"{self.key}_tooltip_position"] = (0, 0)
            
        if f"{self.key}_tooltip_content" not in st.session_state:
            st.session_state[f"{self.key}_tooltip_content"] = ""
            
        if f"{self.key}_context_menu_open" not in st.session_state:
            st.session_state[f"{self.key}_context_menu_open"] = False
            
        if f"{self.key}_context_menu_position" not in st.session_state:
            st.session_state[f"{self.key}_context_menu_position"] = (0, 0)
            
        if f"{self.key}_context_menu_index" not in st.session_state:
            st.session_state[f"{self.key}_context_menu_index"] = -1
        
        # ハイライト情報の初期化
        self.highlight_info = self._build_highlight_info()
    
    def render_highlighted_dataframe(self) -> Optional[int]:
        """
        問題箇所がハイライトされたデータフレームを表示
        
        Returns
        -------
        Optional[int]
            選択された問題のインデックス（選択がなければNone）
        """
        # フィルタリングコントロール
        self._render_filtering_controls()
        
        # 問題のあるレコードをハイライト
        styled_df = self._apply_highlighting_style()
        
        # データフレームの表示
        st.dataframe(styled_df, use_container_width=True)
        
        # インタラクティブなツールチップの表示（可能な場合）
        if st.session_state[f"{self.key}_show_tooltip"]:
            self._render_tooltip()
        
        # コンテキストメニューの表示（可能な場合）
        if st.session_state[f"{self.key}_context_menu_open"]:
            self._render_context_menu()
        
        # 選択したインデックスを返す処理
        selected = st.session_state.get(f"{self.key}_selected_indices", [])
        
        if selected:
            return selected[0]  # 最初の選択されたインデックスを返す
        return None
    
    def render_problem_list(self) -> Optional[int]:
        """
        問題リストを表示し、選択された問題インデックスを返す
        
        Returns
        -------
        Optional[int]
            選択された問題のインデックス（選択がなければNone）
        """
        # フィルタリングされた問題インデックスの取得
        filtered_indices = self._get_filtered_indices()
        
        if not filtered_indices:
            st.info("条件に一致する問題はありません。")
            return None
        
        # 問題レコードのデータフレームを準備
        problem_records = []
        
        for idx in filtered_indices:
            if idx < len(self.data):
                record = {
                    "インデックス": idx,
                    "問題タイプ": ", ".join([self.problem_type_names.get(pt, pt) 
                                    for pt, indices in self.problem_indices.items() 
                                    if pt != "all" and idx in indices]),
                    "重要度": self._get_issue_severity(idx)
                }
                
                # タイムスタンプがあれば追加
                if "timestamp" in self.data.columns:
                    record["タイムスタンプ"] = self.data.iloc[idx]["timestamp"]
                
                # 位置情報があれば追加
                if "latitude" in self.data.columns and "longitude" in self.data.columns:
                    record["位置"] = f"({self.data.iloc[idx]['latitude']:.6f}, {self.data.iloc[idx]['longitude']:.6f})"
                
                problem_records.append(record)
        
        # 問題レコードのデータフレームを作成
        problem_df = pd.DataFrame(problem_records)
        
        # スタイルの適用
        def highlight_severity(row):
            severity = row["重要度"]
            color = self.severity_colors.get(severity, "")
            return [f"background-color: {color}; opacity: 0.2" if i == 2 else "" for i in range(len(row))]
        
        styled_df = problem_df.style.apply(highlight_severity, axis=1)
        
        # 問題リストの表示
        st.subheader("問題リスト")
        st.write(f"合計 {len(problem_records)} 件の問題が見つかりました")
        st.dataframe(styled_df, use_container_width=True)
        
        # 問題を選択するためのセレクトボックス
        if not problem_df.empty:
            selected_index = st.selectbox(
                "詳細を表示する問題を選択:",
                options=problem_df["インデックス"].tolist(),
                format_func=lambda x: f"レコード {x}: {problem_df[problem_df['インデックス']==x]['問題タイプ'].values[0]}",
                key=f"{self.key}_problem_selector"
            )
            
            # 選択された問題インデックスを返す
            return selected_index
        
        return None
    
    def create_highlight_style(self) -> str:
        """
        ハイライトのためのCSSスタイルを生成
        
        Returns
        -------
        str
            CSSスタイル定義
        """
        css = """
        <style>
        .highlight-error {
            background-color: rgba(244, 67, 54, 0.2);
            border: 1px solid #F44336;
        }

        .highlight-warning {
            background-color: rgba(255, 152, 0, 0.2);
            border: 1px solid #FF9800;
        }

        .highlight-info {
            background-color: rgba(33, 150, 243, 0.2);
            border: 1px solid #2196F3;
        }

        .highlighted-row {
            background-color: rgba(0, 0, 0, 0.05);
        }

        .problem-tooltip {
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 300px;
        }
        
        .data-cell-highlight {
            position: relative;
        }
        
        .data-cell-highlight:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            top: 100%;
            left: 0;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
            min-width: 200px;
            white-space: normal;
        }
        
        .quick-nav-button {
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .context-menu {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        .context-menu ul {
            list-style-type: none;
            padding: 0;
            margin: 0;
        }
        
        .context-menu li {
            padding: 8px 12px;
            cursor: pointer;
        }
        
        .context-menu li:hover {
            background-color: #f5f5f5;
        }
        
        .comparison-view {
            display: flex;
            gap: 12px;
        }
        
        .comparison-card {
            flex: 1;
            padding: 12px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        </style>
        """
        return css
    
    def _render_filtering_controls(self):
        """
        フィルタリングコントロールを表示
        """
        st.subheader("問題フィルタリング")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 問題タイプのフィルタリング
            problem_types = ["all"] + list(self.problem_type_names.keys())
            problem_type_labels = ["すべての問題"] + [self.problem_type_names[pt] for pt in self.problem_type_names]
            
            # 問題タイプマッピング
            type_mapping = {label: key for key, label in zip(problem_types, problem_type_labels)}
            
            selected_type_label = st.selectbox(
                "表示する問題タイプ:",
                options=problem_type_labels,
                index=problem_types.index(st.session_state[f"{self.key}_filtered_problem_type"]) if st.session_state[f"{self.key}_filtered_problem_type"] in problem_types else 0,
                key=f"{self.key}_problem_type_filter"
            )
            
            # 選択された問題タイプを保存
            selected_type = type_mapping.get(selected_type_label, "all")
            st.session_state[f"{self.key}_filtered_problem_type"] = selected_type
        
        with col2:
            # 重要度のフィルタリング
            severity_options = ["error", "warning", "info"]
            severity_labels = {"error": "エラー", "warning": "警告", "info": "情報"}
            
            if f"{self.key}_severity_filter" not in st.session_state:
                st.session_state[f"{self.key}_severity_filter"] = severity_options
            
            selected_severity = st.multiselect(
                "表示する重要度:",
                options=severity_options,
                default=st.session_state[f"{self.key}_severity_filter"],
                format_func=lambda x: severity_labels.get(x, x),
                key=f"{self.key}_severity_selector"
            )
            
            # 重要度が何も選択されていない場合はすべて選択
            if not selected_severity:
                selected_severity = severity_options
            
            st.session_state[f"{self.key}_severity_filter"] = selected_severity
            
        with col3:
            # 表示モードの選択
            if f"{self.key}_display_mode" not in st.session_state:
                st.session_state[f"{self.key}_display_mode"] = "全データ"
            
            display_mode = st.radio(
                "表示モード:",
                options=["全データ", "問題のみ"],
                index=0 if st.session_state[f"{self.key}_display_mode"] == "全データ" else 1,
                key=f"{self.key}_display_mode_selector",
                horizontal=True
            )
            
            st.session_state[f"{self.key}_display_mode"] = display_mode
    
    def _apply_highlighting_style(self) -> pd.DataFrame:
        """
        データフレームにハイライトスタイルを適用
        
        Returns
        -------
        pd.DataFrame
            スタイル適用後のデータフレーム
        """
        display_data = self.data.copy()
        
        # 表示モードが「問題のみ」の場合、問題のあるレコードだけを表示
        if st.session_state[f"{self.key}_display_mode"] == "問題のみ":
            display_data = display_data.iloc[self._get_filtered_indices()]
        
        # セル単位のハイライト情報
        cell_highlights = self.highlight_info["cell_highlights"]
        row_problems = self.highlight_info["row_problems"]
        
        # ハイライトするインデックスと行の特定
        filtered_indices = self._get_filtered_indices()
        
        # スタイリング関数の定義
        def highlight_problems(row):
            # 初期化: すべてのセルに空のスタイル
            styles = [""] * len(row)
            
            if row.name in filtered_indices:
                # この行に問題がある場合
                severity = self._get_issue_severity(row.name)
                severity_color = self.severity_colors.get(severity, "#2196f3")
                
                # 行全体に軽いハイライト
                styles = [f"background-color: {severity_color}; opacity: 0.1"] * len(row)
                
                # 問題のあるセルに強いハイライト
                for i, col_name in enumerate(row.index):
                    cell_key = (row.name, col_name)
                    if cell_key in cell_highlights:
                        highlight = cell_highlights[cell_key]
                        cell_severity = highlight["severity"]
                        cell_color = self.severity_colors.get(cell_severity, "#2196f3")
                        styles[i] = f"background-color: {cell_color}; opacity: 0.3; border: 1px solid {cell_color}"
            
            return styles
            
        # スタイルの適用
        styled_df = display_data.style.apply(highlight_problems, axis=1)
        
        return styled_df
    
    def _render_tooltip(self):
        """
        ツールチップを表示
        """
        # ツールチップの内容と位置
        content = st.session_state[f"{self.key}_tooltip_content"]
        pos_x, pos_y = st.session_state[f"{self.key}_tooltip_position"]
        
        # CSSを使ったツールチップの表示（Streamlitの制約内）
        tooltip_html = f"""
        <div class="problem-tooltip" style="position: fixed; top: {pos_y}px; left: {pos_x}px;">
            {content}
        </div>
        """
        
        st.markdown(tooltip_html, unsafe_allow_html=True)
    
    def _render_context_menu(self):
        """
        コンテキストメニューを表示
        """
        # メニューの位置と問題インデックス
        pos_x, pos_y = st.session_state[f"{self.key}_context_menu_position"]
        problem_idx = st.session_state[f"{self.key}_context_menu_index"]
        
        if problem_idx < 0 or problem_idx >= len(self.data):
            return
        
        # 問題の種類を取得
        problem_types = []
        for pt, indices in self.problem_indices.items():
            if pt != "all" and problem_idx in indices:
                problem_types.append(pt)
        
        # メニュー項目の生成
        menu_items = []
        
        # 詳細表示項目
        menu_items.append(f'<li onclick="selectProblem({problem_idx})">詳細を表示</li>')
        
        # 問題タイプに応じた修正オプション
        if "missing_data" in problem_types:
            menu_items.append(f'<li onclick="fixProblem({problem_idx}, \'interpolate\')">欠損値を補間</li>')
            menu_items.append(f'<li onclick="fixProblem({problem_idx}, \'remove\')">このレコードを削除</li>')
        
        if "out_of_range" in problem_types:
            menu_items.append(f'<li onclick="fixProblem({problem_idx}, \'clip\')">値を範囲内に制限</li>')
        
        if "duplicates" in problem_types:
            menu_items.append(f'<li onclick="fixProblem({problem_idx}, \'deduplicate\')">重複を解消</li>')
        
        if "spatial_anomalies" in problem_types:
            menu_items.append(f'<li onclick="fixProblem({problem_idx}, \'smooth\')">位置を平滑化</li>')
        
        if "temporal_anomalies" in problem_types:
            menu_items.append(f'<li onclick="fixProblem({problem_idx}, \'adjust\')">時間を調整</li>')
        
        # 似たような問題を表示するオプション
        menu_items.append(f'<li onclick="findSimilar({problem_idx})">似た問題を検索</li>')
        
        # メニューHTML
        menu_html = f"""
        <div class="context-menu" style="position: fixed; top: {pos_y}px; left: {pos_x}px; z-index: 1000;">
            <ul>
                {"".join(menu_items)}
            </ul>
        </div>
        <script>
            function selectProblem(idx) {{
                // Streamlit向けイベント処理（実際には制約があるため疑似的なコード）
                console.log('選択:', idx);
            }}
            
            function fixProblem(idx, method) {{
                console.log('修正:', idx, method);
            }}
            
            function findSimilar(idx) {{
                console.log('類似検索:', idx);
            }}
        </script>
        """
        
        st.markdown(menu_html, unsafe_allow_html=True)
        
        # Streamlitの制約によりJavaScriptの実行は限られているため、
        # 実際のコンテキストメニュー操作はボタンで代用
        st.write("**問題に対するアクション:**")
        
        # 代替コントロール
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("詳細を表示", key=f"{self.key}_context_view_detail"):
                # 選択インデックスを設定し、詳細表示を依頼
                st.session_state[f"{self.key}_selected_indices"] = [problem_idx]
                # コンテキストメニューを閉じる
                st.session_state[f"{self.key}_context_menu_open"] = False
                # 再レンダリング
                st.experimental_rerun()
        
        with col2:
            if st.button("問題を修正", key=f"{self.key}_context_fix"):
                # 修正処理のトリガー
                st.session_state[f"{self.key}_selected_indices"] = [problem_idx]
                # コンテキストメニューを閉じる
                st.session_state[f"{self.key}_context_menu_open"] = False
                # 再レンダリング
                st.experimental_rerun()
    
    def _build_highlight_info(self) -> Dict[str, Any]:
        """
        ハイライト情報を構築
        
        Returns
        -------
        Dict[str, Any]
            ハイライト情報
        """
        cell_highlights = {}
        row_problems = {}
        
        # 各問題タイプごとの処理
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                for idx in indices:
                    if 0 <= idx < len(self.data):
                        # 行の問題情報を追加/更新
                        if idx not in row_problems:
                            row_problems[idx] = []
                        
                        if problem_type not in row_problems[idx]:
                            row_problems[idx].append(problem_type)
                        
                        # 問題タイプに応じた詳細情報
                        details = {}
                        severity = "info"  # デフォルトの重要度
                        
                        # 問題タイプ別の処理
                        if problem_type == "missing_data":
                            # 欠損値の場合、欠損しているカラムを特定
                            for col in self.data.columns:
                                if pd.isna(self.data.iloc[idx][col]):
                                    cell_key = (idx, col)
                                    cell_highlights[cell_key] = {
                                        "severity": "warning",
                                        "message": "欠損値",
                                        "problem_type": "missing_data",
                                        "details": {"column": col}
                                    }
                            
                            severity = "warning"
                        
                        elif problem_type == "out_of_range":
                            # 範囲外の値の場合、関連カラムを特定（簡易ロジック）
                            for col in self.data.columns:
                                if pd.api.types.is_numeric_dtype(self.data[col]):
                                    value = self.data.iloc[idx][col]
                                    if not pd.isna(value):
                                        # 数値カラムの場合、異常な外れ値を検出
                                        mean = self.data[col].mean()
                                        std = self.data[col].std()
                                        z_score = abs((value - mean) / std) if std > 0 else 0
                                        
                                        if z_score > 3:  # 3標準偏差を超える値は異常と判断
                                            cell_key = (idx, col)
                                            cell_highlights[cell_key] = {
                                                "severity": "error",
                                                "message": "範囲外の値",
                                                "problem_type": "out_of_range",
                                                "details": {
                                                    "column": col,
                                                    "value": value,
                                                    "mean": mean,
                                                    "std": std,
                                                    "z_score": z_score
                                                }
                                            }
                            
                            severity = "error"
                        
                        elif problem_type == "duplicates":
                            # 重複タイムスタンプの場合の処理
                            if "timestamp" in self.data.columns:
                                ts = self.data.iloc[idx]["timestamp"]
                                if ts is not None:
                                    cell_key = (idx, "timestamp")
                                    cell_highlights[cell_key] = {
                                        "severity": "warning",
                                        "message": "重複タイムスタンプ",
                                        "problem_type": "duplicates",
                                        "details": {"timestamp": ts}
                                    }
                            
                            severity = "warning"
                        
                        elif problem_type == "spatial_anomalies":
                            # 空間的異常の場合の処理
                            if "latitude" in self.data.columns and "longitude" in self.data.columns:
                                lat = self.data.iloc[idx]["latitude"]
                                lon = self.data.iloc[idx]["longitude"]
                                
                                cell_key_lat = (idx, "latitude")
                                cell_key_lon = (idx, "longitude")
                                
                                cell_highlights[cell_key_lat] = {
                                    "severity": "error",
                                    "message": "空間的異常",
                                    "problem_type": "spatial_anomalies",
                                    "details": {"lat": lat, "lon": lon}
                                }
                                
                                cell_highlights[cell_key_lon] = {
                                    "severity": "error",
                                    "message": "空間的異常",
                                    "problem_type": "spatial_anomalies",
                                    "details": {"lat": lat, "lon": lon}
                                }
                            
                            if "speed" in self.data.columns:
                                speed = self.data.iloc[idx]["speed"]
                                cell_key_speed = (idx, "speed")
                                
                                cell_highlights[cell_key_speed] = {
                                    "severity": "error",
                                    "message": "速度異常",
                                    "problem_type": "spatial_anomalies",
                                    "details": {"speed": speed}
                                }
                            
                            severity = "error"
                        
                        elif problem_type == "temporal_anomalies":
                            # 時間的異常の場合の処理
                            if "timestamp" in self.data.columns:
                                ts = self.data.iloc[idx]["timestamp"]
                                
                                cell_key = (idx, "timestamp")
                                cell_highlights[cell_key] = {
                                    "severity": "error",
                                    "message": "時間的異常",
                                    "problem_type": "temporal_anomalies",
                                    "details": {"timestamp": ts}
                                }
                            
                            severity = "error"
        
        return {
            "cell_highlights": cell_highlights,
            "row_problems": row_problems
        }
    
    def _get_issue_severity(self, idx: int) -> str:
        """
        問題の重要度を取得
        
        Parameters
        ----------
        idx : int
            問題のインデックス
            
        Returns
        -------
        str
            重要度 ("error", "warning", "info")
        """
        # 問題タイプがあれば重要度を判定
        problem_types = [pt for pt, indices in self.problem_indices.items() 
                        if pt != "all" and idx in indices]
        
        if "spatial_anomalies" in problem_types or "temporal_anomalies" in problem_types:
            return "error"
        elif "out_of_range" in problem_types or "duplicates" in problem_types:
            return "warning"
        elif "missing_data" in problem_types:
            return "warning"
        
        return "info"
    
    def _get_filtered_indices(self) -> List[int]:
        """
        フィルタリングされた問題インデックスを取得
        
        Returns
        -------
        List[int]
            フィルタリングされた問題インデックス
        """
        # 問題タイプのフィルタリング
        filtered_type = st.session_state.get(f"{self.key}_filtered_problem_type", "all")
        
        if filtered_type == "all":
            indices = self.problem_indices["all"]
        else:
            indices = self.problem_indices.get(filtered_type, [])
        
        # 重要度のフィルタリング
        severity_filter = st.session_state.get(f"{self.key}_severity_filter", ["error", "warning", "info"])
        
        # 重要度でフィルタリング
        if severity_filter != ["error", "warning", "info"]:
            indices = [idx for idx in indices if self._get_issue_severity(idx) in severity_filter]
        
        return indices
    
    def get_highlight_info(self) -> Dict[str, Any]:
        """
        ハイライト情報を取得
        
        Returns
        -------
        Dict[str, Any]
            ハイライト情報
        """
        return self.highlight_info
    
    def get_selected_indices(self) -> List[int]:
        """
        選択された問題インデックスを取得
        
        Returns
        -------
        List[int]
            選択された問題インデックス
        """
        return st.session_state.get(f"{self.key}_selected_indices", [])
    
    def set_selected_indices(self, indices: List[int]) -> None:
        """
        選択された問題インデックスを設定
        
        Parameters
        ----------
        indices : List[int]
            選択された問題インデックス
        """
        st.session_state[f"{self.key}_selected_indices"] = indices
    
    def create_problem_details_popup(self, idx: int) -> Dict[str, Any]:
        """
        問題詳細ポップアップのデータを作成
        
        Parameters
        ----------
        idx : int
            問題のインデックス
            
        Returns
        -------
        Dict[str, Any]
            ポップアップデータ
        """
        if idx < 0 or idx >= len(self.data):
            return {
                "id": f"problem_{idx}",
                "index": idx,
                "message": "インデックスが範囲外です",
                "problem_type": "unknown",
                "severity": "error"
            }
        
        # 基本情報
        popup_data = {
            "id": f"problem_{idx}",
            "index": idx,
            "problem_type": "",
            "severity": self._get_issue_severity(idx),
            "message": "",
            "details": {},
            "context": {
                "prev_points": [],
                "next_points": []
            },
            "fix_options": []
        }
        
        # 問題タイプを設定
        problem_types = []
        for pt, indices in self.problem_indices.items():
            if pt != "all" and idx in indices:
                problem_types.append(pt)
        
        if problem_types:
            popup_data["problem_type"] = problem_types[0]  # 最初の問題タイプを使用
            
            # 問題タイプの日本語名をメッセージに設定
            problem_names = [self.problem_type_names.get(pt, pt) for pt in problem_types]
            popup_data["message"] = f"{', '.join(problem_names)}が検出されました"
        
        # レコードデータを設定
        record = self.data.iloc[idx]
        
        # タイムスタンプがあれば設定
        if "timestamp" in record:
            popup_data["timestamp"] = record["timestamp"]
        
        # 位置情報があれば設定
        if "latitude" in record and "longitude" in record:
            popup_data["position"] = [record["latitude"], record["longitude"]]
        
        # 問題タイプに応じた詳細情報と修正オプションを設定
        if "missing_data" in problem_types:
            # 欠損値の詳細
            missing_cols = []
            for col in self.data.columns:
                if pd.isna(record[col]):
                    missing_cols.append(col)
            
            popup_data["details"]["missing_columns"] = missing_cols
            
            # 修正オプション
            popup_data["fix_options"].extend([
                {"id": "interpolate", "label": "欠損値を補間"},
                {"id": "ffill", "label": "前の値で埋める"},
                {"id": "remove", "label": "このレコードを削除"}
            ])
        
        if "out_of_range" in problem_types:
            # 範囲外の値の詳細
            out_of_range_cols = []
            for col in self.data.columns:
                if pd.api.types.is_numeric_dtype(self.data[col]):
                    value = record[col]
                    if not pd.isna(value):
                        mean = self.data[col].mean()
                        std = self.data[col].std()
                        z_score = abs((value - mean) / std) if std > 0 else 0
                        
                        if z_score > 3:
                            out_of_range_cols.append({
                                "column": col,
                                "value": value,
                                "mean": mean,
                                "std": std,
                                "z_score": z_score
                            })
            
            popup_data["details"]["out_of_range_columns"] = out_of_range_cols
            
            # 修正オプション
            popup_data["fix_options"].extend([
                {"id": "clip", "label": "値を範囲内に制限"},
                {"id": "remove", "label": "このレコードを削除"}
            ])
        
        if "duplicates" in problem_types:
            # 重複の詳細
            if "timestamp" in record:
                ts = record["timestamp"]
                # 同じタイムスタンプを持つレコードを検索
                same_ts_records = self.data[self.data["timestamp"] == ts]
                
                popup_data["details"]["duplicates"] = {
                    "timestamp": ts,
                    "count": len(same_ts_records),
                    "indices": same_ts_records.index.tolist()
                }
            
            # 修正オプション
            popup_data["fix_options"].extend([
                {"id": "offset", "label": "タイムスタンプをずらす"},
                {"id": "remove", "label": "このレコードを削除"}
            ])
        
        if "spatial_anomalies" in problem_types:
            # 空間的異常の詳細
            if "latitude" in record and "longitude" in record:
                lat = record["latitude"]
                lon = record["longitude"]
                
                # 前後の位置データで異常を検出
                if idx > 0 and idx < len(self.data) - 1:
                    prev_lat = self.data.iloc[idx-1]["latitude"]
                    prev_lon = self.data.iloc[idx-1]["longitude"]
                    next_lat = self.data.iloc[idx+1]["latitude"]
                    next_lon = self.data.iloc[idx+1]["longitude"]
                    
                    # 簡易的な異常度計算（実際のシステムではより複雑なロジックがあるはず）
                    from math import sqrt
                    
                    def distance(lat1, lon1, lat2, lon2):
                        return sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
                    
                    dist_prev = distance(lat, lon, prev_lat, prev_lon)
                    dist_next = distance(lat, lon, next_lat, next_lon)
                    dist_prev_next = distance(prev_lat, prev_lon, next_lat, next_lon)
                    
                    # 前後のポイントを結ぶ直線からの逸脱度
                    deviation = dist_prev + dist_next - dist_prev_next
                    
                    popup_data["details"]["spatial_anomaly"] = {
                        "lat": lat,
                        "lon": lon,
                        "dist_prev": dist_prev,
                        "dist_next": dist_next,
                        "deviation": deviation
                    }
            
            # 修正オプション
            popup_data["fix_options"].extend([
                {"id": "interpolate", "label": "位置を補間"},
                {"id": "remove", "label": "このレコードを削除"}
            ])
        
        if "temporal_anomalies" in problem_types:
            # 時間的異常の詳細
            if "timestamp" in record:
                ts = record["timestamp"]
                
                # 前後のタイムスタンプと比較
                if idx > 0 and idx < len(self.data) - 1:
                    prev_ts = self.data.iloc[idx-1]["timestamp"]
                    next_ts = self.data.iloc[idx+1]["timestamp"]
                    
                    # タイムスタンプの異常を検出
                    if prev_ts > ts:  # 時間逆行
                        anomaly_type = "reverse"
                        time_diff_seconds = (prev_ts - ts).total_seconds()
                    elif next_ts < ts:  # 時間逆行（次レコードとの比較）
                        anomaly_type = "reverse"
                        time_diff_seconds = (ts - next_ts).total_seconds()
                    else:  # 大きな時間ギャップ
                        anomaly_type = "gap"
                        time_diff_prev = (ts - prev_ts).total_seconds()
                        time_diff_next = (next_ts - ts).total_seconds()
                        
                        # 平均タイムスタンプ間隔（簡易計算）
                        if len(self.data) > 2:
                            avg_time_diff = ((self.data.iloc[-1]["timestamp"] - self.data.iloc[0]["timestamp"]).total_seconds() / (len(self.data) - 1))
                            
                            # 異常な時間ギャップかチェック
                            is_abnormal_gap_prev = time_diff_prev > 3 * avg_time_diff
                            is_abnormal_gap_next = time_diff_next > 3 * avg_time_diff
                            
                            popup_data["details"]["temporal_anomaly"] = {
                                "type": anomaly_type,
                                "timestamp": ts,
                                "prev_timestamp": prev_ts,
                                "next_timestamp": next_ts,
                                "time_diff_prev": time_diff_prev,
                                "time_diff_next": time_diff_next,
                                "avg_time_diff": avg_time_diff,
                                "is_abnormal_gap_prev": is_abnormal_gap_prev,
                                "is_abnormal_gap_next": is_abnormal_gap_next
                            }
                    
                    # 時間逆行の場合の詳細
                    if anomaly_type == "reverse":
                        popup_data["details"]["temporal_anomaly"] = {
                            "type": "reverse",
                            "timestamp": ts,
                            "prev_timestamp": prev_ts,
                            "time_diff_seconds": time_diff_seconds,
                        }
            
            # 修正オプション
            popup_data["fix_options"].extend([
                {"id": "adjust", "label": "タイムスタンプを調整"},
                {"id": "remove", "label": "このレコードを削除"}
            ])
        
        # 前後のコンテキスト（前後3ポイント）を取得
        context_size = 3
        start_idx = max(0, idx - context_size)
        end_idx = min(len(self.data), idx + context_size + 1)
        
        # 前のポイント
        for i in range(start_idx, idx):
            popup_data["context"]["prev_points"].append(self.data.iloc[i].to_dict())
        
        # 次のポイント
        for i in range(idx + 1, end_idx):
            popup_data["context"]["next_points"].append(self.data.iloc[i].to_dict())
        
        return popup_data
    
    def render_quick_navigation(self) -> None:
        """
        クイックナビゲーション機能を表示
        """
        st.subheader("問題箇所へのクイックナビゲーション")
        
        # フィルタリングされた問題インデックスを取得
        filtered_indices = self._get_filtered_indices()
        
        if not filtered_indices:
            st.info("条件に一致する問題はありません。")
            return
        
        # 問題タイプごとのカウント
        problem_type_counts = {}
        
        for pt, indices in self.problem_indices.items():
            if pt != "all":
                # フィルタリングとの交差
                matched_indices = set(indices) & set(filtered_indices)
                if matched_indices:
                    problem_type_counts[pt] = len(matched_indices)
        
        # 重要度ごとのカウント
        severity_counts = {"error": 0, "warning": 0, "info": 0}
        
        for idx in filtered_indices:
            severity = self._get_issue_severity(idx)
            severity_counts[severity] += 1
        
        # 問題タイプごとのナビゲーションボタン
        if problem_type_counts:
            st.write("**問題タイプ別:**")
            
            # 3列でボタンを表示
            cols = st.columns(3)
            
            for i, (pt, count) in enumerate(problem_type_counts.items()):
                pt_name = self.problem_type_names.get(pt, pt)
                with cols[i % 3]:
                    if st.button(f"{pt_name} ({count})", key=f"{self.key}_nav_{pt}"):
                        # 問題タイプで絞り込み
                        st.session_state[f"{self.key}_filtered_problem_type"] = pt
                        
                        # 絞り込み後の最初の問題を選択
                        if pt in self.problem_indices and self.problem_indices[pt]:
                            st.session_state[f"{self.key}_selected_indices"] = [self.problem_indices[pt][0]]
                        
                        # 再レンダリング
                        st.experimental_rerun()
        
        # 重要度ごとのナビゲーションボタン
        if any(severity_counts.values()):
            st.write("**重要度別:**")
            
            cols = st.columns(3)
            
            severity_labels = {"error": "エラー", "warning": "警告", "info": "情報"}
            severity_colors = {"error": "#f44336", "warning": "#ff9800", "info": "#2196f3"}
            
            for i, (severity, count) in enumerate(severity_counts.items()):
                if count > 0:
                    label = severity_labels.get(severity, severity)
                    color = severity_colors.get(severity, "#000000")
                    
                    with cols[i]:
                        if st.button(f"{label} ({count})", key=f"{self.key}_nav_sev_{severity}"):
                            # 重要度で絞り込み
                            st.session_state[f"{self.key}_severity_filter"] = [severity]
                            
                            # 絞り込み後の最初の問題を選択
                            severity_indices = [idx for idx in filtered_indices if self._get_issue_severity(idx) == severity]
                            if severity_indices:
                                st.session_state[f"{self.key}_selected_indices"] = [severity_indices[0]]
                            
                            # 再レンダリング
                            st.experimental_rerun()
        
        # ナビゲーションコントロール
        st.write("**ナビゲーション:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 前の問題へのナビゲーション
            if st.button("← 前の問題", key=f"{self.key}_nav_prev"):
                selected = st.session_state.get(f"{self.key}_selected_indices", [])
                if selected and selected[0] in filtered_indices:
                    # 現在の問題のインデックスを取得
                    current_idx = filtered_indices.index(selected[0])
                    
                    # 前の問題を取得
                    if current_idx > 0:
                        prev_idx = filtered_indices[current_idx - 1]
                        st.session_state[f"{self.key}_selected_indices"] = [prev_idx]
                        st.experimental_rerun()
        
        with col2:
            # 次の問題へのナビゲーション
            if st.button("次の問題 →", key=f"{self.key}_nav_next"):
                selected = st.session_state.get(f"{self.key}_selected_indices", [])
                if selected and selected[0] in filtered_indices:
                    # 現在の問題のインデックスを取得
                    current_idx = filtered_indices.index(selected[0])
                    
                    # 次の問題を取得
                    if current_idx < len(filtered_indices) - 1:
                        next_idx = filtered_indices[current_idx + 1]
                        st.session_state[f"{self.key}_selected_indices"] = [next_idx]
                        st.experimental_rerun()
    
    def render_comparison_view(self, idx: int) -> None:
        """
        問題の比較ビューを表示
        
        Parameters
        ----------
        idx : int
            問題のインデックス
        """
        if idx < 0 or idx >= len(self.data):
            st.warning(f"インデックス {idx} は有効なレコードではありません。")
            return
        
        st.subheader("問題データ比較")
        
        # 問題タイプを取得
        problem_types = []
        for pt, indices in self.problem_indices.items():
            if pt != "all" and idx in indices:
                problem_types.append(pt)
        
        if not problem_types:
            st.info(f"レコード {idx} に問題は見つかりませんでした。")
            return
        
        # 問題に応じた比較ビューを表示
        record = self.data.iloc[idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**<div style='text-align: center;'>現在のデータ</div>**", unsafe_allow_html=True)
            
            # 問題のあるレコードの表示
            problem_df = pd.DataFrame([record])
            st.dataframe(problem_df.T, use_container_width=True)
        
        with col2:
            st.markdown("**<div style='text-align: center;'>修正後の予測データ</div>**", unsafe_allow_html=True)
            
            # 問題タイプに応じた修正後のデータを予測
            fixed_record = record.copy()
            
            if "missing_data" in problem_types:
                # 欠損値の補間
                for col in self.data.columns:
                    if pd.isna(fixed_record[col]):
                        # 簡易的な補間（前後の値の平均など）
                        if pd.api.types.is_numeric_dtype(self.data[col]):
                            col_mean = self.data[col].mean()
                            fixed_record[col] = col_mean
                            st.caption(f"{col}: 欠損値を平均値 {col_mean:.2f} で補間")
                        else:
                            # 非数値型の場合は最頻値など
                            most_common = self.data[col].mode().iloc[0] if not self.data[col].mode().empty else None
                            if most_common is not None:
                                fixed_record[col] = most_common
                                st.caption(f"{col}: 欠損値を最頻値で補間")
            
            elif "out_of_range" in problem_types:
                # 範囲外の値の修正
                for col in self.data.columns:
                    if pd.api.types.is_numeric_dtype(self.data[col]):
                        value = fixed_record[col]
                        if not pd.isna(value):
                            mean = self.data[col].mean()
                            std = self.data[col].std()
                            z_score = abs((value - mean) / std) if std > 0 else 0
                            
                            if z_score > 3:
                                # 3標準偏差に制限
                                clipped_value = mean + 3 * std if value > mean else mean - 3 * std
                                fixed_record[col] = clipped_value
                                st.caption(f"{col}: 範囲外の値 {value:.2f} を {clipped_value:.2f} に制限")
            
            elif "duplicates" in problem_types:
                # 重複タイムスタンプの調整
                if "timestamp" in fixed_record:
                    ts = fixed_record["timestamp"]
                    fixed_record["timestamp"] = ts + pd.Timedelta(milliseconds=100)
                    st.caption(f"タイムスタンプを 100ms ずらす: {ts} → {fixed_record['timestamp']}")
            
            elif "spatial_anomalies" in problem_types:
                # 空間的異常の修正
                if "latitude" in fixed_record and "longitude" in fixed_record and idx > 0 and idx < len(self.data) - 1:
                    prev_lat = self.data.iloc[idx-1]["latitude"]
                    prev_lon = self.data.iloc[idx-1]["longitude"]
                    next_lat = self.data.iloc[idx+1]["latitude"]
                    next_lon = self.data.iloc[idx+1]["longitude"]
                    
                    # 前後のポイントから補間
                    fixed_record["latitude"] = (prev_lat + next_lat) / 2
                    fixed_record["longitude"] = (prev_lon + next_lon) / 2
                    
                    st.caption(f"位置を前後のポイントから補間:")
                    st.caption(f"緯度: {record['latitude']:.6f} → {fixed_record['latitude']:.6f}")
                    st.caption(f"経度: {record['longitude']:.6f} → {fixed_record['longitude']:.6f}")
            
            elif "temporal_anomalies" in problem_types:
                # 時間的異常の修正
                if "timestamp" in fixed_record and idx > 0 and idx < len(self.data) - 1:
                    prev_ts = self.data.iloc[idx-1]["timestamp"]
                    next_ts = self.data.iloc[idx+1]["timestamp"]
                    
                    if prev_ts > fixed_record["timestamp"]:  # 時間逆行
                        # 前のタイムスタンプの少し後に設定
                        fixed_record["timestamp"] = prev_ts + pd.Timedelta(seconds=1)
                        st.caption(f"時間逆行を修正: {record['timestamp']} → {fixed_record['timestamp']}")
                    elif next_ts < fixed_record["timestamp"]:  # 時間逆行（次レコードとの比較）
                        # 次のタイムスタンプの少し前に設定
                        fixed_record["timestamp"] = next_ts - pd.Timedelta(seconds=1)
                        st.caption(f"時間逆行を修正: {record['timestamp']} → {fixed_record['timestamp']}")
                    else:  # 大きな時間ギャップ
                        # 前後の中間に設定
                        mid_ts = prev_ts + (next_ts - prev_ts) / 2
                        fixed_record["timestamp"] = mid_ts
                        st.caption(f"時間ギャップを修正: {record['timestamp']} → {fixed_record['timestamp']}")
            
            # 修正後のデータ表示
            fixed_df = pd.DataFrame([fixed_record])
            st.dataframe(fixed_df.T, use_container_width=True)
        
        # 修正適用ボタン
        st.write("**修正の適用:**")
        
        # 問題タイプ別の修正オプション
        fix_options = []
        
        if "missing_data" in problem_types:
            fix_options.append(("interpolate", "欠損値を補間"))
        
        if "out_of_range" in problem_types:
            fix_options.append(("clip", "範囲内に制限"))
        
        if "duplicates" in problem_types:
            fix_options.append(("offset", "タイムスタンプをずらす"))
        
        if "spatial_anomalies" in problem_types:
            fix_options.append(("smooth", "位置を補間"))
        
        if "temporal_anomalies" in problem_types:
            fix_options.append(("adjust", "時間を調整"))
        
        # 共通オプション
        fix_options.append(("remove", "このレコードを削除"))
        
        # 修正オプションの選択
        selected_fix = st.selectbox(
            "修正方法を選択:",
            options=[opt[0] for opt in fix_options],
            format_func=lambda x: next((opt[1] for opt in fix_options if opt[0] == x), x),
            key=f"{self.key}_fix_method"
        )
        
        # 修正ボタン
        if st.button("選択した修正を適用", key=f"{self.key}_apply_fix"):
            st.success(f"修正 '{selected_fix}' を適用しました。実際の処理はバックエンドで行われます。")
            
            # 選択した問題インデックスをクリア
            st.session_state[f"{self.key}_selected_indices"] = []
            st.experimental_rerun()


def problem_highlighter(data: pd.DataFrame, 
                       problem_indices: Dict[str, List[int]],
                       key: str = "problem_highlighter") -> ProblemHighlighter:
    """
    問題箇所をハイライトするコンポーネントを作成
    
    Parameters
    ----------
    data : pd.DataFrame
        ハイライト対象のデータフレーム
    problem_indices : Dict[str, List[int]]
        問題タイプごとのインデックスリスト
    key : str, optional
        コンポーネントのキー, by default "problem_highlighter"
    
    Returns
    -------
    ProblemHighlighter
        問題ハイライトコンポーネント
    """
    return ProblemHighlighter(data, problem_indices, key)
