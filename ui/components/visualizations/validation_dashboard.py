# -*- coding: utf-8 -*-
"""
ui.components.visualizations.validation_dashboard

データ検証ダッシュボードコンポーネント
修正フィードバック機能と連携強化版
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from ui.components.visualizations.validation_dashboard_base import ValidationDashboardBase


class ValidationDashboard(ValidationDashboardBase):
    """
    データ検証ダッシュボードコンポーネント
    修正フィードバック機能と連携強化版
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : Optional[DataValidator], optional
        データ検証器, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "validation_dashboard"
    on_fix_proposal : Optional[Callable], optional
        修正提案適用時のコールバック関数, by default None
    on_export : Optional[Callable], optional
        エクスポート時のコールバック関数, by default None
    on_data_update : Optional[Callable], optional
        データ更新時のコールバック関数, by default None
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                validator: Optional[DataValidator] = None,
                key_prefix: str = "validation_dashboard",
                on_fix_proposal: Optional[Callable[[str, str], Dict[str, Any]]] = None,
                on_export: Optional[Callable[[str], None]] = None,
                on_data_update: Optional[Callable[[GPSDataContainer], None]] = None):
        """
        初期化（拡張版）
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        validator : Optional[DataValidator], optional
            データ検証器, by default None
        key_prefix : str, optional
            Streamlitのキープレフィックス, by default "validation_dashboard"
        on_fix_proposal : Optional[Callable[[str, str], Dict[str, Any]]], optional
            修正提案適用時のコールバック関数, by default None
            (proposal_id, method_type) -> Dict[str, Any]
        on_export : Optional[Callable[[str], None]], optional
            エクスポート時のコールバック関数, by default None
        on_data_update : Optional[Callable[[GPSDataContainer], None]], optional
            データ更新時のコールバック関数, by default None
        """
        # 親クラスの初期化
        super().__init__(container, validator, key_prefix)
        
        # 拡張機能のコールバック設定
        self.on_fix_proposal = on_fix_proposal
        self.on_export = on_export
        self.on_data_update = on_data_update
    
    def _safely_render_visualization(self, render_func: Callable, fallback_message: str) -> None:
        """
        可視化の安全なレンダリング
        
        Parameters
        ----------
        render_func : Callable
            レンダリング関数
        fallback_message : str
            失敗時のフォールバックメッセージ
        """
        try:
            # 進行状況表示の準備
            progress_placeholder = st.empty()
            
            # プログレスバーの表示（必要に応じて）
            with progress_placeholder.container():
                st.info("可視化データを準備中...")
                render_func()
            
            # 成功したら進捗表示をクリア
            progress_placeholder.empty()
            
        except Exception as e:
            import traceback
            
            # エラーメッセージと対処法の表示
            st.error(f"{fallback_message}: {str(e)}")
            st.info("データの検証と前処理を確認してください。問題が解決しない場合は、サンプル数を減らすか、データをクリーニングしてください。")
            
            # 詳細なエラー情報（開発用）
            with st.expander("詳細なエラー情報", expanded=False):
                st.code(traceback.format_exc())
    
    def _render_report_tab(self) -> None:
        """レポートタブをレンダリング"""
        st.header("データ品質レポート")
        
        # 大規模データセットの場合は最適化処理
        try:
            data = self._optimize_data_processing(self.container.data)
            
            # レポートデータがセッションに保存されているか確認
            if f"{self.key}_report_data" not in st.session_state:
                # レポートデータがない場合は生成
                with st.spinner("レポートデータを生成中..."):
                    report_data = self.visualization.generate_full_report(data=data)
                    st.session_state[f"{self.key}_report_data"] = report_data
            else:
                # セッションからレポートデータを取得
                report_data = st.session_state[f"{self.key}_report_data"]
                
            # データのない場合またはエラーの場合の処理
            if report_data is None:
                st.error("レポートデータが生成できませんでした。データを確認してください。")
                return
                
            if "error" in report_data:
                st.error("レポートデータの生成中にエラーが発生しました。データを確認してください。")
                st.error(f"エラー詳細: {report_data['error']}")
                return
        except Exception as e:
            st.error(f"レポートの準備中にエラーが発生しました: {str(e)}")
            st.info("もう一度試すか、データサイズを小さくしてみてください。")
            return
        
        # レポートの表示 - 安全なレンダリングで各セクションを表示
        
        # 概要セクションの表示
        def render_summary_section():
            st.subheader("概要")
            st.write(report_data["summary"])
            
            st.subheader("データ品質スコア")
            st.write(f"**総合スコア:** {report_data['overall_score']:.1f}/10.0")
            
            # カテゴリ別スコアの表示
            category_scores = report_data["category_scores"]
            category_df = pd.DataFrame({
                "カテゴリ": list(category_scores.keys()),
                "スコア": list(category_scores.values())
            })
            
            st.bar_chart(category_df.set_index("カテゴリ"))
            
        self._safely_render_visualization(render_summary_section, "概要セクションの表示中にエラーが発生しました")
        
        # 詳細な問題リストセクションを表示
        def render_issues_section():
            st.subheader("検出された問題の詳細")
            
            issues_df = pd.DataFrame(report_data["issues"]) if "issues" in report_data else pd.DataFrame()
            if not issues_df.empty:
                # 表示するカラムを選択
                display_cols = ['index', 'problem_type', 'column', 'severity', 'description', 'value']
                display_cols = [col for col in display_cols if col in issues_df.columns]
                
                # 日本語表示名に変換
                display_name_map = {
                    'index': 'インデックス',
                    'problem_type': '問題タイプ',
                    'column': 'カラム',
                    'severity': '重要度',
                    'description': '説明',
                    'value': '値'
                }
                
                # カラム名を日本語に変換
                renamed_df = issues_df[display_cols].rename(columns=display_name_map)
                
                # 問題タイプを日本語表示に変換
                if '問題タイプ' in renamed_df.columns:
                    renamed_df['問題タイプ'] = renamed_df['問題タイプ'].apply(self._get_problem_type_display)
                
                # 結果を表示
                st.dataframe(renamed_df, use_container_width=True)
                
                # ダウンロードボタン
                csv = renamed_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="問題リストをCSVダウンロード",
                    data=csv,
                    file_name="validation_issues.csv",
                    mime="text/csv",
                    key=f"{self.key}_download_issues"
                )
            else:
                st.success("検出された問題はありません。")
        
        self._safely_render_visualization(render_issues_section, "問題リストの表示中にエラーが発生しました")
                
        # カテゴリ別の問題統計セクションを表示
        def render_category_stats_section():
            st.subheader("カテゴリ別の問題統計")
            
            if "problem_category_stats" in report_data:
                category_stats = report_data["problem_category_stats"]
                stats_df = pd.DataFrame(category_stats)
                st.dataframe(stats_df, use_container_width=True)
                
                # グラフ表示
                if not stats_df.empty and "カテゴリ" in stats_df.columns and "問題数" in stats_df.columns:
                    st.bar_chart(stats_df.set_index("カテゴリ")["問題数"])
            else:
                st.info("カテゴリ別統計情報はありません。")
        
        self._safely_render_visualization(render_category_stats_section, "カテゴリ統計の表示中にエラーが発生しました")
        
        # 修正提案の概要セクションを安全にレンダリング
        def render_fix_proposals_section():
            st.subheader("修正提案の概要")
            
            if "fix_proposals" in report_data and report_data["fix_proposals"]:
                proposals = report_data["fix_proposals"]
                st.write(f"**合計 {len(proposals)} 件の修正提案があります**")
                
                # 表形式で表示
                proposal_data = []
                for i, proposal in enumerate(proposals):
                    proposal_data.append({
                        "No.": i+1,
                        "提案タイプ": self._get_problem_type_display(proposal.get("issue_type", "")),
                        "説明": proposal.get("description", ""),
                        "影響レコード数": len(proposal.get("affected_indices", [])),
                        "推奨方法": proposal.get("recommended_method", "")
                    })
                
                proposal_df = pd.DataFrame(proposal_data)
                st.dataframe(proposal_df, use_container_width=True)
                
                # 修正提案の適用ボタンを表示
                if self.on_fix_proposal:
                    with st.expander("修正提案の適用", expanded=False):
                        selected_proposal = st.selectbox(
                            "適用する提案を選択:",
                            options=range(len(proposal_data)),
                            format_func=lambda i: f"{proposal_data[i]['No']}. {proposal_data[i]['提案タイプ']} - {proposal_data[i]['説明']}",
                            key=f"{self.key}_selected_proposal"
                        )
                        
                        if st.button("この提案を適用", key=f"{self.key}_apply_proposal"):
                            if 0 <= selected_proposal < len(proposals):
                                proposal_id = proposals[selected_proposal].get("id", "")
                                recommended_method = proposals[selected_proposal].get("recommended_method", "")
                                
                                if proposal_id and recommended_method:
                                    try:
                                        # コールバック関数を呼び出して提案を適用
                                        fix_result = self.on_fix_proposal(proposal_id, recommended_method)
                                        
                                        if fix_result and "success" in fix_result and fix_result["success"]:
                                            st.success(f"修正が適用されました: {fix_result.get('message', '')}")
                                            # 修正適用後の状態更新を処理
                                            self._handle_fix_application(fix_result)
                                        else:
                                            st.error(f"修正の適用に失敗しました: {fix_result.get('error', '不明なエラー')}")
                                    except Exception as e:
                                        st.error(f"修正適用処理中にエラーが発生しました: {str(e)}")
                                        st.info("再試行するか、データの状態を確認してください。")
            else:
                st.info("自動修正提案はありません。")
        
        self._safely_render_visualization(render_fix_proposals_section, "修正提案の表示中にエラーが発生しました")
        
        # エクスポートオプションセクションを安全にレンダリング
        def render_export_section():
            st.subheader("レポートのエクスポート")
            
            export_format = st.selectbox(
                "エクスポート形式",
                options=["PDF", "HTML", "CSV", "Excel"],
                key=f"{self.key}_export_format"
            )
            
            if st.button("レポートをエクスポート", key=f"{self.key}_export_report"):
                # エクスポートコールバックがある場合は実行
                if self.on_export:
                    try:
                        self.on_export(export_format.lower())
                        st.success(f"レポートを{export_format}形式でエクスポートしました。")
                    except Exception as e:
                        st.error(f"エクスポート処理中にエラーが発生しました: {str(e)}")
                else:
                    # エクスポートコールバックがなければ、基本的なJSONエクスポートを提供
                    try:
                        if export_format.lower() == "csv":
                            # CSVエクスポート
                            issues_df = pd.DataFrame(report_data.get("issues", []))
                            if not issues_df.empty:
                                csv = issues_df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label=f"{export_format}形式でダウンロード",
                                    data=csv,
                                    file_name="validation_report.csv",
                                    mime="text/csv",
                                    key=f"{self.key}_download_csv"
                                )
                            else:
                                st.warning("エクスポートするデータがありません。")
                        else:
                            # JSON形式でエクスポート
                            json_data = json.dumps(report_data, default=str, indent=2)
                            st.download_button(
                                label=f"JSON形式でダウンロード (すべてのデータ)",
                                data=json_data,
                                file_name="validation_report.json",
                                mime="application/json",
                                key=f"{self.key}_download_json"
                            )
                            st.info(f"{export_format}形式のエクスポートはまだ実装されていません。代わりにJSON形式でダウンロードできます。")
                    except Exception as e:
                        st.error(f"データエクスポート中にエラーが発生しました: {str(e)}")
        
        self._safely_render_visualization(render_export_section, "エクスポートオプションの表示中にエラーが発生しました")
                    
    def _optimize_data_processing(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        大規模データセット処理の最適化（改良版）
        
        Parameters
        ----------
        data : pd.DataFrame
            処理対象のデータ
            
        Returns
        -------
        pd.DataFrame
            最適化されたデータ
        """
        # データがない場合は空のDataFrameを返す
        if data is None or data.empty:
            return pd.DataFrame()
            
        # キャッシュを使用（同じデータに対して最適化を繰り返さない）
        # データのハッシュ値を計算（サイズ、カラム構成、先頭行を使用）
        try:
            # 先頭/末尾行のハッシュとカラム情報をベースにハッシュ値を計算
            data_hash = f"{len(data)}_{hash(tuple(data.columns))}"
            if not data.empty:
                data_hash += f"_{hash(str(data.iloc[0].values))}"
                if len(data) > 1:
                    data_hash += f"_{hash(str(data.iloc[-1].values))}"
        except Exception:
            # ハッシュ計算に失敗した場合は、サイズとタイムスタンプでキャッシュキーを作成
            import time
            data_hash = f"{len(data)}_{int(time.time())}"
            
        cache_key = f"{self.key_prefix}_optimized_data_{data_hash}"
        
        # キャッシュがある場合はそれを返す
        if cache_key in st.session_state:
            # キャッシュを使用する際に進捗メッセージを表示
            if len(data) >= 10000:
                st.info(f"キャッシュされた最適化データを使用しています（{len(st.session_state[cache_key])}行）")
            return st.session_state[cache_key]
        
        # データが少なければ、そのまま返す（10,000行未満）
        if len(data) < 10000:
            st.session_state[cache_key] = data
            return data
        
        # 大規模データセットの場合、進捗状況を表示
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            st.info(f"大規模データセット（{len(data):,}行）を最適化しています...")
            progress_bar = st.progress(0.0)
        
        # 大規模データセットの場合は、スマートサンプリングを行う
        try:
            # データサイズに応じて目標サンプルサイズを調整
            if len(data) > 100000:
                target_sample_size = 10000
            elif len(data) > 50000:
                target_sample_size = 7500
            else:
                target_sample_size = 5000
                
            # 進捗を更新
            progress_bar.progress(0.1)
                
            # 基本サンプリング（均等に抽出）- メモリ効率の良い方法
            step = max(1, len(data) // (target_sample_size // 2))
            indices = range(0, len(data), step)
            base_sample = data.iloc[list(indices)[:target_sample_size // 2]].copy()
            
            # 進捗を更新
            progress_bar.progress(0.3)
            
            # 問題のある箇所を抽出（検証結果に基づく）
            problem_indices = set()
            if hasattr(self, 'metrics_calculator') and hasattr(self.metrics_calculator, 'problematic_indices'):
                problematic_indices = self.metrics_calculator.problematic_indices
                
                # 各カテゴリの問題インデックスを追加（重要度に応じて制限）
                for category, indices in problematic_indices.items():
                    if category == 'all':
                        continue
                        
                    # カテゴリごとに最大数を設定（重要な問題カテゴリは多めに含める）
                    if category in ['missing_data', 'temporal_anomalies', 'spatial_anomalies']:
                        max_per_category = 1500  # 重要な問題は多めに含める
                    else:
                        max_per_category = 750
                        
                    if isinstance(indices, (list, set)):
                        # 制限数に抑える
                        problem_indices.update(list(indices)[:max_per_category])
            
            # 進捗を更新
            progress_bar.progress(0.5)
            
            # 重要なポイントを検出（先頭、末尾、極値など）
            important_indices = self._identify_important_points(data)
            problem_indices.update(important_indices)
            
            # 進捗を更新
            progress_bar.progress(0.6)
            
            # 問題のある行をサンプルに追加（メモリ効率を考慮）
            if problem_indices:
                # 大量の問題インデックスがある場合、ランダムサンプリング
                if len(problem_indices) > 3000:
                    import random
                    sampled_problem_indices = random.sample(list(problem_indices), 3000)
                else:
                    sampled_problem_indices = list(problem_indices)
                    
                # インデックスが有効範囲内にあることを確認
                valid_indices = [idx for idx in sampled_problem_indices if 0 <= idx < len(data)]
                
                # チャンクに分けて処理（メモリ効率化）
                chunk_size = 500
                problem_chunks = [valid_indices[i:i + chunk_size] 
                                for i in range(0, len(valid_indices), chunk_size)]
                
                problem_rows_list = []
                for i, chunk in enumerate(problem_chunks):
                    # 進捗を更新（チャンク処理の進捗を60%～80%で表示）
                    progress_value = 0.6 + (0.2 * (i / max(1, len(problem_chunks))))
                    progress_bar.progress(progress_value)
                    
                    try:
                        chunk_rows = data.loc[chunk].copy()
                        problem_rows_list.append(chunk_rows)
                    except Exception as chunk_error:
                        # チャンク処理中のエラーを記録し、続行
                        st.warning(f"チャンク {i+1}/{len(problem_chunks)} の処理中にエラーが発生しましたが、処理を続行します: {chunk_error}")
                        continue
                
                problem_rows = pd.concat(problem_rows_list) if problem_rows_list else pd.DataFrame()
            else:
                problem_rows = pd.DataFrame()
            
            # 進捗を更新
            progress_bar.progress(0.8)
            
            # サンプルと問題行をマージ（重複を除去）
            optimized_data = pd.concat([base_sample, problem_rows]).drop_duplicates()
            
            # データ量の上限を設定
            if len(optimized_data) > target_sample_size:
                if 'timestamp' in optimized_data.columns:
                    # 時系列データの場合、時間的に均等になるようにサンプリング
                    try:
                        optimized_data = optimized_data.sort_values('timestamp')
                        step = max(1, len(optimized_data) // target_sample_size)
                        optimized_data = optimized_data.iloc[::step].head(target_sample_size)
                    except Exception as sort_error:
                        # ソート失敗時は通常のサンプリング
                        st.warning(f"時間ソート中にエラーが発生: {sort_error}。標準サンプリングを適用します。")
                        optimized_data = optimized_data.sample(min(len(optimized_data), target_sample_size))
                else:
                    # 時系列データでない場合は標準サンプリング
                    optimized_data = optimized_data.sample(min(len(optimized_data), target_sample_size))
            
            # 進捗を更新
            progress_bar.progress(0.9)
            
            # ソート（必要に応じて）
            if 'timestamp' in optimized_data.columns:
                try:
                    optimized_data = optimized_data.sort_values('timestamp')
                except Exception as sort_error:
                    st.warning(f"最終時間ソート中にエラーが発生: {sort_error}")
            
            # 結果をキャッシュに保存
            st.session_state[cache_key] = optimized_data
            
            # 進捗を完了表示
            progress_bar.progress(1.0)
            progress_placeholder.empty()  # 進捗表示をクリア
            
            # 結果の情報表示
            st.success(f"データ最適化完了: {len(data):,}行 → {len(optimized_data):,}行（{len(optimized_data)/len(data)*100:.1f}%）")
            
            return optimized_data
            
        except Exception as e:
            # エラーが発生した場合は安全策としてシンプルな方法でサンプリング
            progress_placeholder.warning(f"最適化処理中にエラーが発生しました: {e}。シンプルなサンプリングを適用します。")
            
            try:
                # データサイズに基づいてサンプリングサイズを決定
                sample_size = min(5000, max(len(data) // 10, 1000))
                
                # インデックスのランダムサンプリング（フォールバック）
                sample_indices = np.linspace(0, len(data)-1, sample_size).astype(int)
                sample = data.iloc[sample_indices].copy()
                
                # ソート（可能であれば）
                if 'timestamp' in sample.columns:
                    try:
                        sample = sample.sort_values('timestamp')
                    except Exception:
                        pass  # ソートに失敗してもそのまま続行
                
                # 結果をキャッシュに保存（エラー時のフォールバックも）
                st.session_state[cache_key] = sample
                
                return sample
                
            except Exception as fallback_error:
                # 最終的なフォールバック - 極めて少量のデータを返す
                progress_placeholder.error(f"フォールバックサンプリングでもエラーが発生: {fallback_error}。最小データセットを返します。")
                
                # 最初の1000行だけを返す
                minimal_sample = data.head(1000).copy() if len(data) > 1000 else data.copy()
                
                # キャッシュには保存しない（エラー状態のため）
                return minimal_sample
                
    def _identify_important_points(self, data: pd.DataFrame) -> List[int]:
        """
        データ内の重要なポイントを特定
        
        Parameters
        ----------
        data : pd.DataFrame
            対象データ
            
        Returns
        -------
        List[int]
            重要なポイントのインデックスリスト
        """
        important_indices = []
        
        # データが少なすぎる場合は空リストを返す
        if len(data) < 10:
            return important_indices
        
        try:
            # 数値カラムに対して処理
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            
            # 主要なカラム（GPS固有のもの）に対して優先的に処理
            priority_cols = [col for col in ['latitude', 'longitude', 'speed', 'course', 'heading'] 
                            if col in numeric_cols]
            
            # その他の数値カラムも処理
            other_numeric_cols = [col for col in numeric_cols if col not in priority_cols]
            
            # すべての処理対象カラム
            target_cols = priority_cols + other_numeric_cols
            
            for col in target_cols:
                # NaNを無視
                series = data[col].dropna()
                
                if len(series) < 10:
                    continue
                
                try:
                    # 極値（最大・最小）のインデックスを追加
                    important_indices.extend(series.nlargest(3).index.tolist())
                    important_indices.extend(series.nsmallest(3).index.tolist())
                    
                    # 変化率の大きいポイントを特定
                    diff_series = series.diff().abs()
                    if not diff_series.empty:
                        important_indices.extend(diff_series.nlargest(5).index.tolist())
                except Exception:
                    # カラム処理中のエラーを無視して次へ
                    continue
            
            # 時系列データの場合、等間隔のサンプルポイントも追加
            if 'timestamp' in data.columns and len(data) > 20:
                try:
                    # 先頭、末尾、および等間隔の10ポイントを追加
                    sample_indices = np.linspace(0, len(data)-1, 10).astype(int)
                    important_indices.extend(sample_indices)
                    important_indices.extend([0, len(data)-1])  # 先頭と末尾を明示的に追加
                except Exception:
                    pass  # エラー時は無視
        
        except Exception as e:
            # エラーが発生しても処理を継続
            print(f"重要ポイント特定中のエラー: {e}")
        
        # 重複を除去して返す（ソートはしない）
        return list(set(important_indices))
    
    def _implement_caching(self, operation: str, key: str, compute_func: Callable) -> Any:
        """
        計算結果のキャッシュ実装
        
        Parameters
        ----------
        operation : str
            操作の種類
        key : str
            キャッシュキー
        compute_func : Callable
            計算関数
            
        Returns
        -------
        Any
            計算結果またはキャッシュ値
        """
        cache_key = f"{self.key_prefix}_{operation}_{key}"
        
        # キャッシュにあればそれを返す
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
        # なければ計算して結果をキャッシュに保存
        result = compute_func()
        st.session_state[cache_key] = result
        
        return result
    
    def integrate_with_correction_controls(self, correction_controls_key: str = "correction_controls") -> int:
        """
        CorrectionControlsとの統合
        
        修正提案コントロールから提案を取得し、品質レポートに統合します。
        修正提案のカテゴリ化と重要度に基づくソートを行います。
        
        Parameters
        ----------
        correction_controls_key : str, optional
            CorrectionControlsのキー, by default "correction_controls"
            
        Returns
        -------
        int
            統合された提案の合計数
        """
        # キャッシュキーの生成（コントロールのIDを考慮）
        cache_key = f"{self.key_prefix}_proposal_integration_{correction_controls_key}"
        
        # 最近統合された場合はキャッシュから返す（UIの再レンダリング時の重複実行防止）
        if cache_key in st.session_state and 'last_update_time' in st.session_state[cache_key]:
            # 最後の更新から10秒以内なら再統合をスキップ
            import time
            last_update = st.session_state[cache_key]['last_update_time']
            if time.time() - last_update < 10:
                return st.session_state[cache_key]['count']
        
        # CorrectionControlsから修正提案を取得
        if correction_controls_key in st.session_state:
            correction_controls = st.session_state[correction_controls_key]
            if hasattr(correction_controls, 'get_proposals'):
                try:
                    # 提案を取得
                    proposals = correction_controls.get_proposals()
                    
                    # 提案がない場合は処理をスキップ
                    if not proposals:
                        # 統合結果なしとしてキャッシュ
                        import time
                        st.session_state[cache_key] = {
                            'count': 0,
                            'added': 0,
                            'last_update_time': time.time()
                        }
                        return 0
                    
                    # 提案を品質レポートに統合
                    if f"{self.key}_report_data" in st.session_state:
                        report_data = st.session_state[f"{self.key}_report_data"]
                        if report_data:
                            # 既存の提案数を確認
                            existing_proposals = report_data.get("fix_proposals", [])
                            
                            # 提案IDを抽出
                            existing_ids = set(p.get("id", "") for p in existing_proposals)
                            
                            # 新しい提案を追加（重複を避ける）
                            added_count = 0
                            for proposal in proposals:
                                # IDが存在しない場合はIDを生成
                                if "id" not in proposal or not proposal["id"]:
                                    import uuid
                                    proposal["id"] = str(uuid.uuid4())
                                    
                                if proposal.get("id", "") not in existing_ids:
                                    # 重要度を確認（デフォルトはinfo）
                                    if "severity" not in proposal or not proposal["severity"]:
                                        proposal["severity"] = "info"
                                    
                                    # タイムスタンプを追加（存在しない場合）
                                    if "timestamp" not in proposal:
                                        from datetime import datetime
                                        proposal["timestamp"] = datetime.now().isoformat()
                                        
                                    existing_proposals.append(proposal)
                                    existing_ids.add(proposal.get("id", ""))
                                    added_count += 1
                            
                            # 重要度と適用範囲でソート
                            def sort_key(p):
                                # 重要度によるプライオリティ（エラー > 警告 > 情報）
                                severity_priority = {"error": 0, "warning": 1, "info": 2, "batch": 0}
                                # 影響を受けるレコード数
                                affected_count = len(p.get("affected_indices", []))
                                # バッチ処理は優先度を高くする
                                is_batch = p.get("severity", "") == "batch"
                                # タイムスタンプ（新しいものを優先）
                                timestamp = p.get("timestamp", "")
                                
                                return (
                                    severity_priority.get(p.get("severity", "info"), 3),
                                    -affected_count,  # 影響範囲が大きい順（マイナスにする）
                                    0 if is_batch else 1,  # バッチ処理を優先
                                    -len(timestamp)  # 新しいタイムスタンプを優先（長さの逆順）
                                )
                            
                            # 提案をソート
                            sorted_proposals = sorted(existing_proposals, key=sort_key)
                            
                            # エラー状態の場合は個数制限（最大100件）
                            if len(sorted_proposals) > 100:
                                sorted_proposals = sorted_proposals[:100]
                                st.warning(f"提案数が多すぎるため、最も重要な100件のみを表示します。（{len(existing_proposals)}件中）")
                            
                            # 更新した提案をレポートデータに設定
                            report_data["fix_proposals"] = sorted_proposals
                            st.session_state[f"{self.key}_report_data"] = report_data
                            
                            # 統合結果をキャッシュ
                            import time
                            st.session_state[cache_key] = {
                                'count': len(sorted_proposals),
                                'added': added_count,
                                'last_update_time': time.time()
                            }
                            
                            # 提案が統合されたことを通知（新しい提案があった場合のみ）
                            if added_count > 0:
                                st.info(f"{added_count}件の新しい修正提案が追加されました。")
                            
                            return len(sorted_proposals)
                        else:
                            # レポートデータがない場合は新しく作成
                            self._create_report_data_with_proposals(proposals)
                            return len(proposals)
                    else:
                        # レポートデータがない場合は新しく作成
                        self._create_report_data_with_proposals(proposals)
                        return len(proposals)
                        
                except Exception as e:
                    # 提案統合中のエラーをキャッチして表示
                    import traceback
                    st.warning(f"修正提案の統合中にエラーが発生しました: {str(e)}")
                    print(f"提案統合エラー: {e}")
                    print(traceback.format_exc())
        
        # 統合結果なしとしてキャッシュ
        import time
        st.session_state[cache_key] = {
            'count': 0,
            'added': 0,
            'last_update_time': time.time()
        }
        return 0
        
    def _create_report_data_with_proposals(self, proposals: List[Dict[str, Any]]) -> None:
        """
        提案を含む新しいレポートデータを作成
        
        Parameters
        ----------
        proposals : List[Dict[str, Any]]
            修正提案のリスト
        """
        # 基本的なレポートデータの構造を作成
        report_data = {
            "summary": "データ検証レポート",
            "overall_score": 0.0,
            "category_scores": {},
            "issues": [],
            "fix_proposals": proposals,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 現在の品質スコアを取得（可能であれば）
            if hasattr(self, 'metrics_calculator'):
                quality_scores = self.metrics_calculator.quality_scores
                if quality_scores:
                    # 10点満点に変換
                    report_data["overall_score"] = quality_scores.get("total", 0) / 10.0
                    # カテゴリ別スコアを保存
                    for category in ["completeness", "accuracy", "consistency"]:
                        if category in quality_scores:
                            report_data["category_scores"][category] = quality_scores[category] / 10.0
        except Exception as e:
            print(f"スコア取得エラー: {e}")
        
        # セッションに保存
        st.session_state[f"{self.key}_report_data"] = report_data
    
    def handle_interactive_fix_result(self, fix_result: Dict[str, Any]) -> bool:
        """
        インタラクティブな修正結果を処理
        
        修正の適用結果を処理し、必要に応じてデータを更新して検証を再実行します。
        フィードバックを表示し、コンテナの更新時はコールバックを呼び出します。
        
        Parameters
        ----------
        fix_result : Dict[str, Any]
            修正結果
            
        Returns
        -------
        bool
            修正が成功したかどうか
        """
        # 結果がNoneまたは空の場合はエラー
        if not fix_result:
            st.error("修正結果が空です。処理を中止します。")
            return False
            
        # 成功ステータスのチェック
        success = fix_result.get("status") == "success" or fix_result.get("success", False)
        
        if success:
            try:
                # 更新されたコンテナがある場合
                if "container" in fix_result:
                    # 更新前のデータサイズを記録
                    before_size = len(self.container.data) if hasattr(self.container, 'data') and self.container.data is not None else 0
                    
                    # 更新後のデータサイズを取得
                    after_size = len(fix_result["container"].data) if hasattr(fix_result["container"], 'data') and fix_result["container"].data is not None else 0
                    
                    # データサイズの変更を確認（削除操作の場合など）
                    size_change = after_size - before_size
                    
                    # 変更された列の情報を抽出
                    changed_columns = []
                    if "changed_columns" in fix_result:
                        changed_columns = fix_result["changed_columns"]
                    elif "fix_details" in fix_result and "changed_columns" in fix_result["fix_details"]:
                        changed_columns = fix_result["fix_details"]["changed_columns"]
                    
                    # 影響を受けたインデックスを抽出
                    affected_indices = []
                    if "affected_indices" in fix_result:
                        affected_indices = fix_result["affected_indices"]
                    elif "fix_details" in fix_result and "affected_indices" in fix_result["fix_details"]:
                        affected_indices = fix_result["fix_details"]["affected_indices"]
                    
                    # 修正詳細情報を構築
                    fix_details = {
                        "type": fix_result.get("fix_type", "unknown"),
                        "affected_indices": affected_indices,
                        "changed_columns": changed_columns,
                        "affected_count": fix_result.get("affected_count", len(affected_indices)),
                        "data_size_change": size_change,
                        "before_values": fix_result.get("before_values", {}),
                        "after_values": fix_result.get("after_values", {})
                    }
                    
                    # 修正適用後の状態更新を処理
                    self._handle_fix_application({
                        "success": True,
                        "container": fix_result["container"],
                        "fix_details": fix_details
                    })
                    
                    # 成功メッセージを表示（既に表示されている場合があるので、オプション）
                    if not fix_result.get("message_displayed", False):
                        affected_count = fix_result.get("affected_count", len(affected_indices))
                        st.success(f"修正が適用されました: {affected_count}件のレコードが更新されました。")
                        
                        # データサイズに変更がある場合は追加メッセージ
                        if size_change != 0:
                            if size_change < 0:
                                st.info(f"データサイズが変更されました: {abs(size_change)}件のレコードが削除されました。")
                            else:
                                st.info(f"データサイズが変更されました: {size_change}件のレコードが追加されました。")
                    
                    return True
                else:
                    # コンテナがない場合は警告
                    st.warning("修正は成功しましたが、更新されたデータが提供されていません。データは更新されていません。")
                    return True
                    
            except Exception as e:
                # エラーが発生した場合
                import traceback
                st.error(f"修正結果の処理中にエラーが発生しました: {str(e)}")
                with st.expander("詳細なエラー情報", expanded=False):
                    st.code(traceback.format_exc())
                return False
        else:
            # 失敗した場合はエラーメッセージを表示
            error_msg = fix_result.get("error", "不明なエラー")
            st.error(f"修正の適用に失敗しました: {error_msg}")
            return False
    
    def handle_large_dataset(self, data: pd.DataFrame, max_size: int = 10000) -> pd.DataFrame:
        """
        大規模データセットの処理
        
        大量のデータポイントを含むデータセットを効率的に処理するため、
        サンプリングやフィルタリングを実施し、適切なサイズに最適化します。
        
        Parameters
        ----------
        data : pd.DataFrame
            処理対象のデータ
        max_size : int, optional
            最大処理サイズ, by default 10000
            
        Returns
        -------
        pd.DataFrame
            処理後のデータ
        """
        # データが空または少ない場合はそのまま返す
        if data is None or data.empty:
            return pd.DataFrame()
        elif len(data) <= max_size:
            return data
        
        # 大規模データセットの警告と情報を表示
        # キャッシュキー（このデータを既に処理済みかどうかを確認）
        try:
            # ハッシュキーを生成
            cache_key = f"{self.key_prefix}_handled_large_data_{len(data)}_{hash(tuple(data.columns))}"
            
            # キャッシュがある場合はそれを返す
            if cache_key in st.session_state:
                # 情報メッセージを表示（キャッシュを使用）
                st.info(f"前回の最適化結果を使用します（{len(st.session_state[cache_key])}行、元データの{len(st.session_state[cache_key])/len(data)*100:.1f}%）")
                return st.session_state[cache_key]
        except:
            # ハッシュ生成に失敗した場合はキャッシュを使用しない
            cache_key = None
            
        # 大規模データセットの警告表示
        dataset_size = len(data)
        if dataset_size > 100000:
            size_category = "非常に大規模"
            estimated_time = "数分以上"
        elif dataset_size > 50000:
            size_category = "大規模"
            estimated_time = "1〜2分程度"
        else:
            size_category = "中規模"
            estimated_time = "30秒〜1分程度"
            
        st.warning(f"{size_category}なデータセット（{dataset_size:,}行）を最適化します。完全な分析には{estimated_time}かかる場合があります。")
        
        # 進捗状態を表示
        with st.status("大規模データセットを最適化中...", expanded=True) as status:
            # データの基本情報を表示
            st.write(f"**データサイズ:** {len(data):,}行 × {len(data.columns)}列")
            
            # メモリ使用量の推定
            estimated_memory = len(data) * len(data.columns) * 8 / (1024 * 1024)  # MB単位で概算
            st.write(f"**推定メモリ使用量:** 約 {estimated_memory:.1f} MB")
            
            # データタイプの分析
            data_types = data.dtypes.value_counts().to_dict()
            type_info = ", ".join([f"{v}個の{k}" for k, v in data_types.items()])
            st.write(f"**データ型の分布:** {type_info}")
            
            # 最適化アプローチの選択とプレビュー
            st.write("**最適化方法の選択:**")
            
            # 時系列データかどうかを確認
            has_timestamp = 'timestamp' in data.columns
            
            # データの種類に応じて最適化方法を選択（自動）
            if has_timestamp:
                st.write("📊 時系列データを検出しました - 時間ベースのサンプリングを使用します")
                optimization_method = "時間ベース"
            else:
                st.write("📊 一般データとして均等サンプリングを使用します")
                optimization_method = "均等サンプリング"
            
            # 進捗メッセージを表示
            st.write(f"サンプリング方法: **{optimization_method}**")
            st.write("データをサンプリングしています...")
            
            # プログレスバーを表示
            progress_bar = st.progress(0.0)
            progress_bar.progress(0.2, text="データを分析中...")
            
            # 最適化処理を実行
            optimized_data = self._optimize_data_processing(data)
            
            # 最終進捗を更新
            progress_bar.progress(1.0, text="最適化完了")
            
            # 結果の統計情報
            reduction_pct = (1 - len(optimized_data) / len(data)) * 100
            st.write(f"**処理結果:** {len(data):,}行 → {len(optimized_data):,}行 (縮小率: {reduction_pct:.1f}%)")
            
            # 列統計
            if len(optimized_data) > 0:
                # NaN値の割合を計算
                nan_pct = optimized_data.isna().mean() * 100
                # 上位3つの列とそのNaN割合を取得
                top_nan_cols = nan_pct.nlargest(3)
                if not top_nan_cols.empty:
                    nan_info = ", ".join([f"{col}: {pct:.1f}%" for col, pct in top_nan_cols.items() if pct > 0])
                    if nan_info:
                        st.write(f"**欠損値の多い列:** {nan_info}")
            
            # 最適化完了メッセージ
            result_detail = f"元データの{len(optimized_data)/len(data)*100:.1f}%にサンプリングされました"
            status.update(label=f"データ最適化完了: {len(optimized_data):,}行を分析に使用", state="complete")
            
            # 結果をキャッシュに保存（キーが生成できた場合のみ）
            if cache_key:
                st.session_state[cache_key] = optimized_data
            
        return optimized_data
    
    def _handle_fix_application(self, fix_result: Dict[str, Any]) -> None:
        """
        修正適用後の状態更新処理
        
        Parameters
        ----------
        fix_result : Dict[str, Any]
            修正適用結果
        """
        # 修正が適用された場合、キャッシュを更新する
        if fix_result.get("success", False):
            # 更新されたコンテナがある場合
            if "container" in fix_result:
                self.container = fix_result["container"]
                
                # バリデーションを再実行
                self.validator.validate(self.container)
                
                # メトリクス計算を更新
                self.metrics_calculator = QualityMetricsCalculator(
                    self.validator.validation_results,
                    self.container.data
                )
                
                self.visualizer = ValidationVisualizer(
                    self.metrics_calculator,
                    self.container.data
                )
                
                # キャッシュを初期化
                for key in list(st.session_state.keys()):
                    if key.startswith(f"{self.key_prefix}_"):
                        del st.session_state[key]
                
                # 成功メッセージを表示
                st.success("データが更新され、検証が再実行されました。")
                
                # 問題修正結果の詳細を表示
                if "fix_details" in fix_result:
                    self._show_fix_details(fix_result["fix_details"])
                
                # 更新イベントを通知（コールバックがあれば）
                if hasattr(self, 'on_data_update') and self.on_data_update:
                    self.on_data_update(self.container)
    
    def _show_fix_details(self, fix_details: Dict[str, Any]) -> None:
        """
        修正詳細情報を表示
        
        Parameters
        ----------
        fix_details : Dict[str, Any]
            修正詳細情報
        """
        # 拡張可能なコンテナで詳細情報を表示
        with st.expander("修正詳細", expanded=False):
            # 修正タイプ
            fix_type = fix_details.get("type", "不明")
            st.write(f"**修正タイプ:** {self._get_fix_type_display(fix_type)}")
            
            # 影響を受けたレコード数
            affected_count = len(fix_details.get("affected_indices", []))
            st.write(f"**影響を受けたレコード:** {affected_count}件")
            
            # 変更されたカラム
            if "changed_columns" in fix_details:
                st.write(f"**変更されたカラム:** {', '.join(fix_details['changed_columns'])}")
            
            # 修正前後の値を表示（サンプル）
            if "before_values" in fix_details and "after_values" in fix_details:
                st.subheader("変更内容サンプル")
                
                # サンプルとして最大5件表示
                indices = list(fix_details["before_values"].keys())[:5]
                
                for idx in indices:
                    before = fix_details["before_values"].get(str(idx), {})
                    after = fix_details["after_values"].get(str(idx), {})
                    
                    if before and after:
                        st.write(f"**レコード {idx}**")
                        
                        # 変更内容を表形式で表示
                        changes = []
                        for col in before.keys():
                            changes.append({
                                "カラム": col,
                                "修正前": before[col],
                                "修正後": after.get(col, "")
                            })
                        
                        st.table(pd.DataFrame(changes))
    
    def _get_fix_type_display(self, fix_type: str) -> str:
        """
        修正タイプの表示名を取得
        
        Parameters
        ----------
        fix_type : str
            修正タイプ
            
        Returns
        -------
        str
            表示名
        """
        type_map = {
            "interpolate": "補間",
            "replace": "置換",
            "remove": "削除",
            "fill": "埋め込み",
            "adjust": "調整",
            "auto": "自動修正",
            "direct_edit": "直接編集",
            "batch": "一括処理"
        }
        return type_map.get(fix_type, fix_type)
