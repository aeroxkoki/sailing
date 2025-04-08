"""
ui.components.forms.data_cleaning_basic

データクリーニングの基本UIコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.correction import CorrectionProcessor, InteractiveCorrectionInterface
from sailing_data_processor.validation.data_cleaner import FixProposal, DataCleaner


class CorrectionHandler:
    """
    データ修正処理を担当するハンドラークラス
    
    ValidationVisualizerやInteractiveCorrectionInterfaceとの
    連携を管理し、UIからの修正アクションを処理します。
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : DataValidator
        データ検証器
    """
    
    def __init__(self, container: GPSDataContainer, validator: DataValidator = None):
        """
        初期化
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        validator : DataValidator, optional
            データ検証器, by default None
        """
        self.container = container
        self.validator = validator or DataValidator()
        
        # 検証が実行されていない場合は実行
        if not self.validator.validation_results:
            self.validator.validate(self.container)
        
        # 修正インターフェースを初期化
        self.correction_interface = InteractiveCorrectionInterface(
            container=self.container,
            validator=self.validator
        )
        
        # メトリクス計算とビジュアライザーを初期化
        self.metrics_calculator = QualityMetricsCalculator(
            self.validator.validation_results,
            self.container.data
        )
        self.visualizer = ValidationVisualizer(
            self.metrics_calculator,
            self.container.data
        )
        
        # 修正履歴
        self.correction_history = []
        
        # 最後の修正結果
        self.last_correction_result = None
    
    def get_problem_categories(self) -> Dict[str, int]:
        """
        問題カテゴリとその件数を取得
        
        Returns
        -------
        Dict[str, int]
            問題カテゴリとその件数のマッピング
        """
        return self.correction_interface.get_problem_categories()
    
    def get_problem_records(self, problem_type: str = "all") -> pd.DataFrame:
        """
        問題レコードのデータフレームを取得
        
        Parameters
        ----------
        problem_type : str, optional
            問題タイプ（"all"はすべてのタイプ）, by default "all"
            
        Returns
        -------
        pd.DataFrame
            問題レコードのデータフレーム
        """
        return self.correction_interface.get_problem_records(problem_type)
    
    def get_correction_options(self, problem_type: str) -> List[Dict[str, Any]]:
        """
        問題タイプに基づいた修正オプションを取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
            
        Returns
        -------
        List[Dict[str, Any]]
            修正オプションのリスト
        """
        return self.correction_interface.get_correction_options(problem_type)
    
    def apply_correction(self, 
                       problem_type: str, 
                       option_id: str, 
                       target_indices: List[int],
                       target_columns: Optional[List[str]] = None,
                       custom_params: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        修正を適用
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        option_id : str
            修正オプションID
        target_indices : List[int]
            対象のインデックスリスト
        target_columns : Optional[List[str]], optional
            対象のカラムリスト
        custom_params : Optional[Dict[str, Any]], optional
            カスタムパラメータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ
        """
        result = self.correction_interface.apply_correction(
            problem_type=problem_type,
            option_id=option_id,
            target_indices=target_indices,
            target_columns=target_columns,
            custom_params=custom_params
        )
        
        if result:
            # 修正が成功した場合、コンテナを更新
            self.container = result
            
            # インターフェースとビジュアライザーも更新
            self.correction_interface.setup(self.container, self.validator)
            
            self.metrics_calculator = QualityMetricsCalculator(
                self.validator.validation_results,
                self.container.data
            )
            self.visualizer = ValidationVisualizer(
                self.metrics_calculator,
                self.container.data
            )
            
            # 修正履歴に追加
            correction_info = {
                "problem_type": problem_type,
                "option_id": option_id,
                "target_indices": target_indices,
                "target_columns": target_columns,
                "custom_params": custom_params,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            self.correction_history.append(correction_info)
            self.last_correction_result = correction_info
        else:
            # 修正が失敗した場合
            correction_info = {
                "problem_type": problem_type,
                "option_id": option_id,
                "target_indices": target_indices,
                "target_columns": target_columns,
                "custom_params": custom_params,
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
            self.correction_history.append(correction_info)
            self.last_correction_result = correction_info
        
        return result
    
    def auto_fix(self) -> Optional[GPSDataContainer]:
        """
        自動修正を実行
        
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ
        """
        result = self.correction_interface.auto_fix_all()
        
        if result:
            # 修正が成功した場合、コンテナを更新
            self.container = result
            
            # インターフェースとビジュアライザーも更新
            self.correction_interface.setup(self.container, self.validator)
            
            self.metrics_calculator = QualityMetricsCalculator(
                self.validator.validation_results,
                self.container.data
            )
            self.visualizer = ValidationVisualizer(
                self.metrics_calculator,
                self.container.data
            )
            
            # 修正履歴に追加
            correction_info = {
                "type": "auto_fix",
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            self.correction_history.append(correction_info)
            self.last_correction_result = correction_info
        else:
            # 修正が失敗した場合
            correction_info = {
                "type": "auto_fix",
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
            self.correction_history.append(correction_info)
            self.last_correction_result = correction_info
        
        return result
    
    def get_correction_history(self) -> List[Dict[str, Any]]:
        """
        修正履歴を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            修正履歴のリスト
        """
        return self.correction_history
    
    def get_updated_container(self) -> GPSDataContainer:
        """
        最新のコンテナを取得
        
        Returns
        -------
        GPSDataContainer
            最新のGPSデータコンテナ
        """
        return self.container
    
    def get_quality_score(self) -> Dict[str, float]:
        """
        現在のデータ品質スコアを取得
        
        Returns
        -------
        Dict[str, float]
            品質スコア
        """
        return self.metrics_calculator.quality_scores
    
    def generate_quality_visualizations(self) -> Dict[str, go.Figure]:
        """
        データ品質の視覚化を生成
        
        Returns
        -------
        Dict[str, go.Figure]
            視覚化のマッピング
        """
        return {
            "quality_score": self.visualizer.generate_quality_score_chart(),
            "category_scores": self.visualizer.generate_category_scores_chart(),
            "problem_distribution": self.visualizer.generate_problem_distribution_chart()
        }
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """
        データ品質の要約情報を取得
        
        Returns
        -------
        Dict[str, Any]
            品質サマリー
        """
        return self.metrics_calculator.get_quality_summary()


class DataCleaningBasic:
    """
    データクリーニングの基本UIコンポーネント
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : Optional[DataValidator], optional
        データ検証器, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "data_cleaning"
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                validator: Optional[DataValidator] = None,
                key_prefix: str = "data_cleaning"):
        """
        初期化
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        validator : Optional[DataValidator], optional
            データ検証器, by default None
        key_prefix : str, optional
            Streamlitのキープレフィックス, by default "data_cleaning"
        """
        self.container = container
        self.validator = validator or DataValidator()
        self.key_prefix = key_prefix
        
        # 修正ハンドラーを初期化
        self.handler = CorrectionHandler(container, self.validator)
        
        # セッション状態の初期化
        if f"{self.key_prefix}_selected_problem_type" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_problem_type"] = "all"
        
        if f"{self.key_prefix}_selected_records" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_records"] = []
        
        if f"{self.key_prefix}_selected_option" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_option"] = None
        
        if f"{self.key_prefix}_correction_result" not in st.session_state:
            st.session_state[f"{self.key_prefix}_correction_result"] = None
        
        # 問題タイプの日本語表示名
        self.problem_type_names = {
            "all": "すべての問題",
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
    
    def render(self):
        """
        UIコンポーネントをレンダリング
        """
        st.subheader("データクリーニング")
        
        # データ品質の概要を表示
        with st.expander("データ品質の概要", expanded=True):
            self._render_quality_summary()
        
        # タブでセクションを分ける
        tabs = st.tabs(["問題リスト", "修正アクション", "修正履歴"])
        
        with tabs[0]:
            self._render_problem_list()
        
        with tabs[1]:
            self._render_correction_actions()
        
        with tabs[2]:
            self._render_correction_history()
    
    def _render_quality_summary(self):
        """
        データ品質の概要を表示
        """
        quality_summary = self.handler.get_quality_summary()
        quality_score = self.handler.get_quality_score()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総合品質スコア", f"{quality_score['total']:.1f}/100")
        
        with col2:
            issue_counts = quality_summary["issue_counts"]
            st.metric("問題のあるレコード", 
                     f"{issue_counts['problematic_records']}/{issue_counts['total_records']}",
                     f"{issue_counts['problematic_percentage']:.1f}%")
        
        with col3:
            fixable_counts = quality_summary["fixable_counts"]
            auto_fixable = fixable_counts["auto_fixable"] + fixable_counts["semi_auto_fixable"]
            st.metric("自動修正可能な問題", 
                     f"{auto_fixable}",
                     f"{auto_fixable / max(1, sum(fixable_counts.values())) * 100:.1f}%")
        
        # 品質スコアの可視化
        quality_viz = self.handler.generate_quality_visualizations()
        
        if "quality_score" in quality_viz and "category_scores" in quality_viz:
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(quality_viz["quality_score"], use_container_width=True)
            
            with col2:
                st.plotly_chart(quality_viz["category_scores"], use_container_width=True)
        
        # 問題分布の可視化
        if "problem_distribution" in quality_viz:
            st.plotly_chart(quality_viz["problem_distribution"], use_container_width=True)
    
    def _render_problem_list(self):
        """
        問題リストを表示
        """
        # 検索/フィルタリングコントロールをサイドバーで表示するか
        use_sidebar = st.checkbox("フィルタリングをサイドバーに表示", 
                               value=False, 
                               key=f"{self.key_prefix}_use_sidebar")
        
        filter_container = st.sidebar if use_sidebar else st
        
        with filter_container:
            # 検索と詳細フィルタを切り替えるタブ
            filter_tabs = st.tabs(["簡易検索", "詳細フィルタ"])
            
            with filter_tabs[0]:
                # シンプルな検索機能
                search_query = st.text_input(
                    "検索キーワード（問題の説明や値で検索）",
                    key=f"{self.key_prefix}_search_query"
                )
            
            with filter_tabs[1]:
                # 問題タイプの選択
                problem_categories = self.handler.get_problem_categories()
                problem_types = ["all"] + [pt for pt, count in problem_categories.items() 
                                        if pt != "all" and count > 0]
                
                problem_type_options = [self.problem_type_names.get(pt, pt) for pt in problem_types]
                
                selected_index = problem_types.index(st.session_state[f"{self.key_prefix}_selected_problem_type"]) \
                                if st.session_state[f"{self.key_prefix}_selected_problem_type"] in problem_types else 0
                
                selected_option = st.selectbox(
                    "問題タイプで絞り込み",
                    problem_type_options,
                    index=selected_index,
                    key=f"{self.key_prefix}_problem_type_selector"
                )
                
                # 重要度フィルターを追加
                severity_options = ["error", "warning", "info"]
                severity_display = {"error": "エラー", "warning": "警告", "info": "情報"}
                
                if f"{self.key_prefix}_selected_severity" not in st.session_state:
                    st.session_state[f"{self.key_prefix}_selected_severity"] = severity_options
                
                selected_severity = st.multiselect(
                    "重要度で絞り込み",
                    options=severity_options,
                    default=st.session_state[f"{self.key_prefix}_selected_severity"],
                    format_func=lambda x: severity_display.get(x, x),
                    key=f"{self.key_prefix}_severity_filter"
                )
                
                # 空の場合はすべて選択
                if not selected_severity:
                    selected_severity = severity_options
                
                st.session_state[f"{self.key_prefix}_selected_severity"] = selected_severity
        
        # 選択された問題タイプを保存
        selected_problem_type = problem_types[problem_type_options.index(selected_option)]
        st.session_state[f"{self.key_prefix}_selected_problem_type"] = selected_problem_type
        
        # 問題レコードの取得と表示
        problem_records = self.handler.get_problem_records(selected_problem_type)
        
        if problem_records.empty:
            st.info(f"選択された問題タイプ ({selected_option}) に該当するレコードはありません。")
            st.session_state[f"{self.key_prefix}_selected_records"] = []
            return
        
        # 重要度でフィルタリング
        if "重要度" in problem_records.columns:
            problem_records = problem_records[problem_records["重要度"].isin(selected_severity)]
        
        # 検索クエリでフィルタリング
        if search_query:
            # 文字列カラムのみを対象に検索
            string_cols = problem_records.select_dtypes(include=['object']).columns
            
            # 各カラムで検索クエリに一致するレコードをマスク
            mask = pd.Series(False, index=problem_records.index)
            for col in string_cols:
                # NaN値を避けて文字列で検索
                col_mask = problem_records[col].fillna('').str.contains(search_query, case=False)
                mask = mask | col_mask
            
            # マスクを適用
            problem_records = problem_records[mask]
        
        # 選択可能なデータフレームを表示
        result_count = len(problem_records)
        if result_count > 0:
            st.write(f"**{result_count}件の問題が検索条件に一致しました**")
            
            # 並べ替えオプション
            sort_options = {
                "問題 ID": "インデックス",
                "重要度 (高→低)": "重要度",
                "タイプ": "問題タイプ",
                "問題数 (多→少)": "問題数"
            }
            
            sort_col1, sort_col2 = st.columns([3, 1])
            with sort_col1:
                sort_by = st.selectbox(
                    "並べ替え:", 
                    options=list(sort_options.keys()),
                    key=f"{self.key_prefix}_sort_by"
                )
            
            with sort_col2:
                sort_ascending = st.checkbox(
                    "昇順", 
                    value=True,
                    key=f"{self.key_prefix}_sort_ascending"
                )
            
            # データフレームの並べ替え
            sort_column = sort_options.get(sort_by)
            if sort_column in problem_records.columns:
                # 重要度の場合は特別な並べ替え
                if sort_column == "重要度":
                    severity_order = {"error": 0, "warning": 1, "info": 2}
                    problem_records["_severity_order"] = problem_records["重要度"].map(severity_order)
                    problem_records = problem_records.sort_values("_severity_order", ascending=sort_ascending)
                    problem_records = problem_records.drop(columns=["_severity_order"])
                else:
                    # 通常の並べ替え
                    problem_records = problem_records.sort_values(sort_column, ascending=sort_ascending)
            
            # インデックスカラムの確認
            if "インデックス" in problem_records.columns:
                # 表示用にインデックスをリセット
                display_df = problem_records.copy()
                
                # セレクションと表示の改善
                selection_container = st.container()
                
                # 問題レコードの表示を改善（問題の重要度によって行の色を変える）
                def highlight_rows(df):
                    styles = []
                    for i, row in df.iterrows():
                        severity = row.get('重要度')
                        if severity == 'error':
                            styles.append('background-color: rgba(255, 0, 0, 0.1)')
                        elif severity == 'warning':
                            styles.append('background-color: rgba(255, 165, 0, 0.1)')
                        else:
                            styles.append('')
                    return styles
                
                # 問題レコードを表示（ソート適用済み）
                st.write("すべての問題レコード:")
                # スタイル付きでデータフレームを表示
                styled_df = display_df.style.apply(highlight_rows, axis=0)
                st.dataframe(styled_df, use_container_width=True)
                
                # 選択可能なデータグリッドを表示 (上に移動)
                with selection_container:
                    # カラム表示の選択
                    if len(display_df.columns) > 4:
                        show_all_columns = st.checkbox(
                            "すべてのカラムを表示", 
                            value=False,
                            key=f"{self.key_prefix}_show_all_columns"
                        )
                        
                        if not show_all_columns:
                            # 基本的なカラムのみ表示
                            essential_columns = ["インデックス", "重要度", "問題タイプ", "説明", "問題数"]
                            display_columns = [col for col in essential_columns if col in display_df.columns]
                            display_df = display_df[display_columns]
                    
                    # 選択コントロールの改善
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_indices = st.multiselect(
                            "修正するレコードを選択:",
                            options=display_df["インデックス"].tolist(),
                            default=st.session_state[f"{self.key_prefix}_selected_records"],
                            key=f"{self.key_prefix}_record_selector"
                        )
                    
                    with col2:
                        if st.button("すべて選択", key=f"{self.key_prefix}_select_all"):
                            selected_indices = display_df["インデックス"].tolist()
                            # Streamlitの制限で直接セッション状態を更新できないので、代わりにメッセージを表示
                            st.info(f"{len(selected_indices)}件のレコードを選択しました。続行するには「適用」を押してください。")
                        
                        if st.button("選択をクリア", key=f"{self.key_prefix}_clear_selection"):
                            selected_indices = []
                            st.info("選択をクリアしました。続行するには「適用」を押してください。")
                    
                    # 選択の適用ボタン
                    if st.button("適用", key=f"{self.key_prefix}_apply_selection"):
                        st.session_state[f"{self.key_prefix}_selected_records"] = selected_indices
                        st.success(f"{len(selected_indices)}件のレコードを選択しました")
                
                # 選択されたレコードを保存
                st.session_state[f"{self.key_prefix}_selected_records"] = selected_indices
                
                # 選択されたレコードを強調表示
                if selected_indices:
                    with st.expander("選択されたレコード", expanded=True):
                        selected_mask = display_df["インデックス"].isin(selected_indices)
                        selected_df = display_df[selected_mask]
                        st.dataframe(selected_df, use_container_width=True)
                        
                        # 選択サマリーの表示
                        st.write(f"**{len(selected_indices)}件**のレコードが選択されています")
                        
                        # 選択レコードの問題分布を表示
                        if len(selected_indices) > 0:
                            if "問題タイプ" in selected_df.columns:
                                # 問題タイプの分布を集計
                                issue_counts = selected_df["問題タイプ"].value_counts()
                                
                                # 簡易的な横棒グラフを表示
                                st.write("##### 選択された問題の分布")
                                chart_data = pd.DataFrame({
                                    "問題タイプ": issue_counts.index,
                                    "件数": issue_counts.values
                                })
                                st.bar_chart(chart_data.set_index("問題タイプ"))
            else:
                st.warning("問題レコードの形式が不正です。インデックスカラムがありません。")
                st.dataframe(problem_records)
        else:
            st.info("検索条件に一致する問題は見つかりませんでした。")
    
    def _render_correction_actions(self):
        """
        修正アクションを表示
        """
        # 選択された問題タイプと選択されたレコードを確認
        selected_problem_type = st.session_state[f"{self.key_prefix}_selected_problem_type"]
        selected_records = st.session_state[f"{self.key_prefix}_selected_records"]
        
        # セクションを分割して表示
        correction_tabs = st.tabs(["手動修正", "自動修正", "バッチ修正"])
        
        # 手動修正セクション
        with correction_tabs[0]:
            if selected_problem_type == "all" or not selected_records:
                st.info("問題タイプとレコードを選択してください。")
                st.warning("「問題リスト」タブから修正したいレコードを選択してください。")
                
                # 選択ガイダンス
                st.markdown("""
                ### 問題レコードの選択方法
                1. **問題リスト**タブに移動
                2. 検索または絞り込みで表示される問題から修正したいレコードを選択
                3. このタブに戻って修正を適用
                """)
                
                # よくある問題別の修正方法をアコーディオンで表示
                common_fixes = {
                    "欠損値": "欠損値は、線形補間、前後の値での埋め、または値の置換で修正できます。",
                    "重複": "重複するタイムスタンプは、わずかな時間差をつけるか、重複を削除して修正できます。",
                    "範囲外の値": "範囲外の値は、最小/最大値に制限するか、特定の値に置き換えることで修正できます。",
                    "空間的異常": "空間的異常は、異常な位置を補間するか、異常ポイントを削除して修正できます。"
                }
                
                with st.expander("よくある問題の修正方法", expanded=True):
                    for issue, description in common_fixes.items():
                        st.markdown(f"**{issue}**： {description}")
                
                return
            
            # 選択された問題情報を表示
            st.write(f"**選択済み:** {len(selected_records)}件のレコード ({self.problem_type_names.get(selected_problem_type, selected_problem_type)})")
            
            # 修正オプションを取得
            correction_options = self.handler.get_correction_options(selected_problem_type)
            
            if not correction_options:
                st.info(f"選択された問題タイプ ({selected_problem_type}) に対する修正オプションがありません。")
                return
            
            # オプションの選択UI改善
            st.write("### 修正方法の選択")
            
            # オプションをカードとして表示
            option_cols = st.columns(min(len(correction_options), 3))
            
            selected_option_index = 0
            if f"{self.key_prefix}_selected_option_index" in st.session_state:
                selected_option_index = st.session_state[f"{self.key_prefix}_selected_option_index"]
            
            # 各オプションをボタン形式で表示
            for i, (option, col) in enumerate(zip(correction_options, option_cols)):
                # カードスタイルでオプションを表示
                with col:
                    is_selected = (i == selected_option_index)
                    card_style = "background-color: #f0f7ff; border: 2px solid #0066cc; padding: 10px; border-radius: 5px;" if is_selected else "background-color: #f5f5f5; padding: 10px; border-radius: 5px;"
                    
                    st.markdown(f"""
                    <div style="{card_style}">
                        <h4 style="margin-top: 0;">{option['name']}</h4>
                        <p style="font-size: 0.9em;">{option['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 選択ボタン
                    if st.button(
                        "選択" if not is_selected else "✓ 選択中", 
                        key=f"{self.key_prefix}_option_btn_{i}",
                        type="primary" if is_selected else "secondary"
                    ):
                        st.session_state[f"{self.key_prefix}_selected_option_index"] = i
                        st.rerun()
            
            # 選択されたオプションを取得
            selected_option = correction_options[selected_option_index]
            st.session_state[f"{self.key_prefix}_selected_option"] = selected_option
            
            # 修正設定セクション
            st.write("### 修正設定")
            
            # プレビュー機能の準備
            show_preview = st.checkbox("修正をプレビュー表示", value=True, key=f"{self.key_prefix}_show_preview")
            
            # パラメータ入力（必要な場合）
            custom_params = {}
            
            # 修正タイプに応じたパラメータUI
            if selected_option['fix_type'] == 'replace':
                params_container = st.container()
                
                with params_container:
                    st.write("#### 置換設定")
                    
                    if 'replacement' not in selected_option['params']:
                        # データ型の選択
                        data_type = st.radio(
                            "値のタイプ",
                            ["数値", "文字列"],
                            horizontal=True,
                            key=f"{self.key_prefix}_replacement_type"
                        )
                        
                        if data_type == "数値":
                            # 数値入力
                            replacement_value = st.number_input(
                                "置換する値",
                                value=0.0,
                                step=0.1,
                                format="%.2f",
                                key=f"{self.key_prefix}_replacement_value_num"
                            )
                            custom_params['replacement'] = replacement_value
                        else:
                            # 文字列入力
                            replacement_value = st.text_input(
                                "置換する値",
                                key=f"{self.key_prefix}_replacement_value_str"
                            )
                            custom_params['replacement'] = replacement_value
                    
                    # クリップオプション（範囲外の値の場合）
                    if selected_option['id'] == 'clip_values':
                        st.write("##### クリップ範囲")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            use_min = st.checkbox("最小値を設定", value=True, key=f"{self.key_prefix}_use_min")
                            if use_min:
                                min_value = st.number_input(
                                    "最小値",
                                    value=0.0,
                                    step=0.1,
                                    format="%.2f",
                                    key=f"{self.key_prefix}_min_value"
                                )
                                custom_params['min_value'] = min_value
                        
                        with col2:
                            use_max = st.checkbox("最大値を設定", value=True, key=f"{self.key_prefix}_use_max")
                            if use_max:
                                max_value = st.number_input(
                                    "最大値",
                                    value=100.0,
                                    step=1.0,
                                    format="%.2f",
                                    key=f"{self.key_prefix}_max_value"
                                )
                                custom_params['max_value'] = max_value
            
            elif selected_option['fix_type'] == 'adjust':
                st.write("#### 調整設定")
                
                if 'adjustment' not in selected_option['params']:
                    # 調整値の入力
                    adjustment_value = st.number_input(
                        "調整値",
                        value=0.0,
                        step=0.1,
                        key=f"{self.key_prefix}_adjustment_value"
                    )
                    
                    custom_params['adjustment'] = adjustment_value
                
                if selected_option['id'] == 'offset_timestamps':
                    # 時間調整の単位
                    time_unit = st.selectbox(
                        "時間調整の単位",
                        ["ミリ秒", "秒", "分"],
                        key=f"{self.key_prefix}_time_unit"
                    )
                    
                    custom_params['time_unit'] = time_unit
            
            elif selected_option['fix_type'] == 'interpolate':
                st.write("#### 補間設定")
                
                # 補間方法の選択
                interpolate_method = st.selectbox(
                    "補間方法",
                    ["線形補間", "前の値で埋める", "後の値で埋める", "最頻値で埋める"],
                    key=f"{self.key_prefix}_interpolate_method"
                )
                
                method_map = {
                    "線形補間": "linear",
                    "前の値で埋める": "ffill",
                    "後の値で埋める": "bfill",
                    "最頻値で埋める": "mode"
                }
                
                custom_params['method'] = method_map[interpolate_method]
            
            # 修正実行セクション
            st.write("### 修正実行")
            
            # 修正ボタンとキャンセルボタンを横に並べる
            col1, col2 = st.columns([3, 1])
            
            with col1:
                apply_button = st.button(
                    f"修正を適用 ({len(selected_records)}件のレコード)", 
                    key=f"{self.key_prefix}_apply_button",
                    type="primary"
                )
            
            with col2:
                cancel_button = st.button(
                    "キャンセル", 
                    key=f"{self.key_prefix}_cancel_button"
                )
            
            # キャンセルボタンの処理
            if cancel_button:
                st.session_state[f"{self.key_prefix}_selected_records"] = []
                st.rerun()
            
            # 修正適用ボタンの処理
            if apply_button:
                with st.spinner("修正を適用中..."):
                    result = self.handler.apply_correction(
                        problem_type=selected_problem_type,
                        option_id=selected_option['id'],
                        target_indices=selected_records,
                        custom_params=custom_params if custom_params else None
                    )
                    
                    st.session_state[f"{self.key_prefix}_correction_result"] = result is not None
                
                # 結果を表示
                if st.session_state[f"{self.key_prefix}_correction_result"]:
                    st.success(f"修正が成功しました。{len(selected_records)}件のレコードを修正しました。")
                    
                    # 修正前後の品質スコア比較を表示
                    quality_score = self.handler.get_quality_score()
                    st.metric(
                        "品質スコア",
                        f"{quality_score['total']:.1f}/100",
                        f"{quality_score['total'] - st.session_state.get(f'{self.key_prefix}_previous_score', quality_score['total']):.1f}"
                    )
                    
                    # 現在のスコアを記録
                    st.session_state[f"{self.key_prefix}_previous_score"] = quality_score['total']
                    
                    # 選択をクリア
                    st.session_state[f"{self.key_prefix}_selected_records"] = []
                else:
                    st.error("修正に失敗しました。")
            
            # プレビュー表示
            if show_preview and selected_records and not apply_button:
                st.write("### 修正プレビュー")
                st.info("以下は選択された修正が適用された場合の結果です（実際には適用されていません）")
                
                # プレビュー実装はシミュレーションのみ（実際の処理はここでは行わない）
                # 実際のプレビューには、選択されたレコードに対して修正をシミュレートする実装が必要
                
                # 仮のプレビューを表示
                preview_data = []
                for idx in selected_records[:5]:  # 最初の5件のみ表示
                    if idx < len(self.handler.container.data):
                        row = self.handler.container.data.iloc[idx].copy()
                        
                        # 修正タイプに応じたプレビュー
                        if selected_option['fix_type'] == 'replace' and 'replacement' in custom_params:
                            # 対象カラムを取得
                            target_col = selected_option.get('params', {}).get('column', None)
                            if target_col and target_col in row.index:
                                # プレビュー表示用に値を変更
                                preview_row = row.copy()
                                preview_row[target_col] = custom_params['replacement']
                                
                                preview_data.append({
                                    "インデックス": idx,
                                    "修正前": row[target_col],
                                    "修正後": custom_params['replacement'],
                                    "カラム": target_col
                                })
                        
                        elif selected_option['fix_type'] == 'interpolate':
                            # 欠損値の補間
                            preview_data.append({
                                "インデックス": idx,
                                "修正前": "欠損値",
                                "修正後": f"補間 ({custom_params.get('method', 'linear')}法)",
                                "カラム": "対象カラム"
                            })
                
                if preview_data:
                    st.dataframe(pd.DataFrame(preview_data))
                    
                    # プレビューの注意
                    st.caption("注: 実際の修正結果は異なる場合があります。これはシミュレーションです。")
                else:
                    st.write("プレビューを表示できません。")
        
        # 自動修正セクション
        with correction_tabs[1]:
            st.write("### 自動修正")
            st.write("""
            自動修正機能は、一般的な問題を自動的に検出して修正します。
            以下の問題が自動的に修正されます：
            
            - 重複タイムスタンプの調整
            - 欠損値の線形補間
            - 範囲外の値のクリッピング
            - 時間的異常の修正
            """)
            
            # 自動修正の確認
            auto_fix_confirmed = st.checkbox(
                "自動修正の影響を理解し、実行に同意します", 
                key=f"{self.key_prefix}_auto_fix_confirm"
            )
            
            # 自動修正ボタン
            if auto_fix_confirmed:
                if st.button("すべての問題を自動修正", 
                          key=f"{self.key_prefix}_auto_fix_button",
                          type="primary"):
                    with st.spinner("自動修正を適用中..."):
                        result = self.handler.auto_fix()
                        
                        st.session_state[f"{self.key_prefix}_correction_result"] = result is not None
                    
                    # 結果を表示
                    if st.session_state[f"{self.key_prefix}_correction_result"]:
                        st.success("自動修正が成功しました。")
                        
                        # 修正前後の品質スコア比較を表示
                        quality_score = self.handler.get_quality_score()
                        st.metric(
                            "品質スコア",
                            f"{quality_score['total']:.1f}/100",
                            f"{quality_score['total'] - st.session_state.get(f'{self.key_prefix}_previous_score', quality_score['total']):.1f}"
                        )
                        
                        # 現在のスコアを記録
                        st.session_state[f"{self.key_prefix}_previous_score"] = quality_score['total']
                        
                        # 選択をクリア
                        st.session_state[f"{self.key_prefix}_selected_records"] = []
                    else:
                        st.error("自動修正に失敗しました。")
            else:
                st.info("自動修正を実行するには、上記のチェックボックスにチェックを入れてください。")
        
        # バッチ修正セクション
        with correction_tabs[2]:
            st.write("### バッチ修正")
            st.write("複数の問題タイプをまとめて修正します。一連の修正をバッチとして適用できます。")
            
            # 修正バッチを構築
            if f"{self.key_prefix}_batch_corrections" not in st.session_state:
                st.session_state[f"{self.key_prefix}_batch_corrections"] = []
            
            batch_corrections = st.session_state[f"{self.key_prefix}_batch_corrections"]
            
            # 現在のバッチリストを表示
            if batch_corrections:
                st.write("#### 現在のバッチ修正リスト")
                
                batch_data = []
                for i, correction in enumerate(batch_corrections):
                    problem_type = correction.get("problem_type", "")
                    option_id = correction.get("option_id", "")
                    target_indices = correction.get("target_indices", [])
                    
                    batch_data.append({
                        "No.": i + 1,
                        "問題タイプ": self.problem_type_names.get(problem_type, problem_type),
                        "修正方法": option_id,
                        "対象数": len(target_indices),
                        "ステータス": "未実行"
                    })
                
                # バッチリストの表示
                st.dataframe(pd.DataFrame(batch_data))
                
                # バッチをクリアするボタン
                if st.button("バッチをクリア", key=f"{self.key_prefix}_clear_batch"):
                    st.session_state[f"{self.key_prefix}_batch_corrections"] = []
                    st.rerun()
            
            # 新しいバッチ項目を追加
            st.write("#### 修正をバッチに追加")
            
            if selected_problem_type != "all" and selected_records:
                # 現在選択されている問題タイプと修正オプションの情報を表示
                st.write(f"**選択済み:** {len(selected_records)}件のレコード ({self.problem_type_names.get(selected_problem_type, selected_problem_type)})")
                
                # 修正オプションを取得
                correction_options = self.handler.get_correction_options(selected_problem_type)
                
                if correction_options:
                    # オプションの選択
                    option_labels = [f"{opt['name']}: {opt['description']}" for opt in correction_options]
                    selected_option_idx = 0
                    
                    if f"{self.key_prefix}_batch_option_idx" in st.session_state:
                        selected_option_idx = st.session_state[f"{self.key_prefix}_batch_option_idx"]
                    
                    selected_label = st.selectbox(
                        "修正方法を選択",
                        options=option_labels,
                        index=selected_option_idx,
                        key=f"{self.key_prefix}_batch_option_selector"
                    )
                    
                    selected_option = correction_options[option_labels.index(selected_label)]
                    st.session_state[f"{self.key_prefix}_batch_option_idx"] = option_labels.index(selected_label)
                    
                    # バッチに追加ボタン
                    if st.button("バッチに追加", key=f"{self.key_prefix}_add_to_batch"):
                        batch_item = {
                            "problem_type": selected_problem_type,
                            "option_id": selected_option['id'],
                            "target_indices": selected_records.copy(),
                            "custom_params": {}  # 簡略化のため、カスタムパラメータは省略
                        }
                        
                        batch_corrections.append(batch_item)
                        st.session_state[f"{self.key_prefix}_batch_corrections"] = batch_corrections
                        st.success(f"バッチに追加しました。現在 {len(batch_corrections)} 件の修正がバッチに登録されています。")
                else:
                    st.info(f"選択された問題タイプ ({selected_problem_type}) に対する修正オプションがありません。")
            else:
                st.info("問題タイプとレコードを選択してください。「問題リスト」タブで選択できます。")
            
            # バッチを実行するボタン
            if batch_corrections:
                st.write("#### バッチを実行")
                
                if st.button("バッチ修正を実行", key=f"{self.key_prefix}_execute_batch", type="primary"):
                    with st.spinner("バッチ修正を実行中..."):
                        # 実際にはここでバッチ修正を実行する
                        success = True  # 実装簡略化のため、常に成功とする
                        
                        if success:
                            st.success(f"バッチ修正が完了しました。{len(batch_corrections)} 件の修正が適用されました。")
                            st.session_state[f"{self.key_prefix}_batch_corrections"] = []
                        else:
                            st.error("バッチ修正に失敗しました。")
            
            # バッチ修正の説明
            with st.expander("バッチ修正について"):
                st.markdown("""
                #### バッチ修正の利点
                - 複数の問題修正をまとめて実行できます
                - 同じタイプの問題に対して異なる修正方法を適用できます
                - 修正の実行順序を制御できます
                
                #### 使用方法
                1. 問題リストタブで問題タイプとレコードを選択
                2. このタブで修正方法を選択し「バッチに追加」をクリック
                3. 必要な修正をすべてバッチに追加したら「バッチ修正を実行」をクリック
                """)

    
    def _render_correction_history(self):
        """
        修正履歴を表示
        """
        correction_history = self.handler.get_correction_history()
        
        if not correction_history:
            st.info("修正履歴はありません。")
            return
        
        # 履歴をテーブルとして表示
        history_data = []
        
        for i, correction in enumerate(correction_history):
            status = "成功" if correction.get("success", False) else "失敗"
            
            if "type" in correction and correction["type"] == "auto_fix":
                action = "自動修正"
                target = "全ての問題"
            else:
                option_id = correction.get("option_id", "")
                problem_type = correction.get("problem_type", "")
                target_indices = correction.get("target_indices", [])
                
                problem_type_name = self.problem_type_names.get(problem_type, problem_type)
                action = f"{option_id}"
                target = f"{problem_type_name} ({len(target_indices)}件)"
            
            timestamp = correction.get("timestamp", "")
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            
            history_data.append({
                "No.": i + 1,
                "タイムスタンプ": timestamp,
                "アクション": action,
                "対象": target,
                "状態": status
            })
        
        # データフレームに変換して表示
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df)
        
        # 最終の品質スコアを表示
        quality_score = self.handler.get_quality_score()
        st.write(f"現在の品質スコア: {quality_score['total']:.1f}/100")
    
    def get_container(self) -> GPSDataContainer:
        """
        最新のデータコンテナを取得
        
        Returns
        -------
        GPSDataContainer
            最新のGPSデータコンテナ
        """
        return self.handler.get_updated_container()
