# -*- coding: utf-8 -*-
"""
ui.components.forms.data_cleaning_enhanced

拡張データクリーニングフォームを提供するモジュール
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
import json
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.visualization import ValidationVisualization
from sailing_data_processor.validation.data_cleaner import DataCleaner, FixProposal

def data_cleaning_form(validator: DataValidator, container: GPSDataContainer, on_clean_callback: Optional[Callable] = None):
    """
    データクリーニングフォームを表示
    
    Parameters
    ----------
    validator : DataValidator
        データ検証器
    container : GPSDataContainer
        GPSデータコンテナ
    on_clean_callback : Optional[Callable], optional
        クリーニング後のコールバック関数, by default None
    """
    if not container or not validator:
        st.warning("データが読み込まれていません。まずデータをインポートしてください。")
        return
    
    # データクリーナーを初期化
    cleaner = DataCleaner(validator, container)
    
    # セッション状態を初期化
    if 'fix_proposals' not in st.session_state:
        st.session_state.fix_proposals = cleaner.fix_proposals
    
    if 'cleaned_container' not in st.session_state:
        st.session_state.cleaned_container = container
    
    if 'selected_fixes' not in st.session_state:
        st.session_state.selected_fixes = []
    
    st.write("## データクリーニング")
    
    # データ品質情報の表示
    visualization = ValidationVisualization(validator, container)
    quality_score = visualization.quality_score
    
    # スコアをゲージチャートで表示
    gauge_fig, cat_fig = visualization.get_quality_score_visualization()
    st.plotly_chart(gauge_fig)
    
    # タブでコンテンツを整理
    tabs = st.tabs(["品質概要", "問題詳細", "修正提案", "マップ表示", "履歴"])
    
    # 品質概要タブ
    with tabs[0]:
        st.plotly_chart(cat_fig)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 問題の概要を表示
            severity_fig, type_fig, _ = visualization.get_issues_summary_visualization()
            st.plotly_chart(severity_fig)
        
        with col2:
            st.plotly_chart(type_fig)
        
        # データ品質サマリー
        st.write("### データ品質サマリー")
        quality_summary = visualization.quality_summary
        
        col1, col2, col3 = st.columns(3)
        col1.metric("総レコード数", quality_summary["issue_counts"]["total_records"])
        col2.metric("問題のあるレコード数", quality_summary["issue_counts"]["problematic_records"])
        col3.metric("問題レコード割合", f"{quality_summary['issue_counts']['problematic_percentage']:.2f}%")
        
        # 修正可能性
        st.write("### 修正可能性")
        
        fix_counts = quality_summary.get("fixable_counts", {})
        auto_fix = fix_counts.get("auto_fixable", 0)
        semi_auto = fix_counts.get("semi_auto_fixable", 0)
        manual = fix_counts.get("manual_fix_required", 0)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("自動修正可能", auto_fix)
        col2.metric("半自動修正可能", semi_auto)
        col3.metric("手動修正必要", manual)
    
    # 問題詳細タブ
    with tabs[1]:
        # 問題カテゴリ別のフィルター
        st.write("### 問題カテゴリ")
        problem_type = st.selectbox(
            "表示する問題タイプを選択",
            ["すべて", "欠損値", "範囲外の値", "重複", "空間的異常", "時間的異常"],
            index=0
        )
        
        # 問題の詳細テーブル
        st.write("### 問題の詳細")
        
        # 問題タイプのマッピング
        problem_type_mapping = {
            "すべて": None,
            "欠損値": "missing_data",
            "範囲外の値": "out_of_range",
            "重複": "duplicates",
            "空間的異常": "spatial_anomalies",
            "時間的異常": "temporal_anomalies"
        }
        
        # フィルタリングされた問題インデックス
        if problem_type == "すべて":
            problem_indices = visualization.problematic_indices["all"]
        else:
            problem_indices = visualization.problematic_indices[problem_type_mapping[problem_type]]
        
        if problem_indices:
            # 問題レコードのみを表示
            problem_records = []
            
            for idx in problem_indices:
                if idx in visualization.record_issues:
                    issue = visualization.record_issues[idx]
                    record = {
                        "インデックス": idx,
                        "タイムスタンプ": issue.get("timestamp"),
                        "緯度": issue.get("latitude"),
                        "経度": issue.get("longitude"),
                        "問題タイプ": ", ".join(issue.get("issues", [])),
                        "重要度": issue.get("severity")
                    }
                    problem_records.append(record)
            
            if problem_records:
                problem_df = pd.DataFrame(problem_records)
                st.dataframe(problem_df, use_container_width=True)
            else:
                st.info("表示する問題レコードがありません。")
        else:
            st.info("表示する問題レコードがありません。")
    
    # 修正提案タブ
    with tabs[2]:
        st.write("### 修正提案")
        
        # 修正タイプによるフィルタリング
        fix_types = ["すべて", "interpolate (補間)", "remove (削除)", "adjust (調整)", "replace (置換)"]
        fix_type_filter = st.selectbox("修正タイプでフィルター", fix_types, index=0)
        
        # 重要度によるフィルタリング
        severity_types = ["すべて", "high (高)", "medium (中)", "low (低)"]
        severity_filter = st.selectbox("重要度でフィルター", severity_types, index=0)
        
        # 自動修正可能なもののみ表示するオプション
        auto_fixable_only = st.checkbox("自動修正可能なもののみ表示", value=False)
        
        # フィルタリング条件を適用
        filtered_proposals = cleaner.fix_proposals
        
        if fix_type_filter != "すべて":
            fix_type = fix_type_filter.split(" ")[0]
            filtered_proposals = [p for p in filtered_proposals if p.fix_type == fix_type]
        
        if severity_filter != "すべて":
            severity = severity_filter.split(" ")[0]
            filtered_proposals = [p for p in filtered_proposals if p.severity == severity]
        
        if auto_fixable_only:
            filtered_proposals = [p for p in filtered_proposals if p.auto_fixable]
        
        # 修正提案を表示
        if filtered_proposals:
            st.write(f"{len(filtered_proposals)}件の修正提案が見つかりました")
            
            # 修正提案のグループ化（同じタイプの提案をグループ化）
            proposals_by_description = {}
            
            for prop in filtered_proposals:
                key = (prop.fix_type, prop.description)
                if key not in proposals_by_description:
                    proposals_by_description[key] = []
                proposals_by_description[key].append(prop)
            
            # グループごとに表示
            for (fix_type, description), props in proposals_by_description.items():
                with st.expander(f"{description} ({len(props)}件)"):
                    # 提案の詳細を表示
                    sample_prop = props[0]
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    col1.write(f"**修正タイプ:** {fix_type}")
                    col2.write(f"**重要度:** {sample_prop.severity}")
                    col3.write(f"**自動修正:** {'可能' if sample_prop.auto_fixable else '不可'}")
                    
                    # 対象データの表示
                    if len(props) > 0:
                        # すべての影響を受けるインデックスを収集
                        all_indices = []
                        for p in props:
                            all_indices.extend(p.target_indices)
                        all_indices = sorted(list(set(all_indices)))
                        
                        st.write(f"**影響する行数:** {len(all_indices)}行")
                        
                        # サンプルデータを表示
                        sample_size = min(5, len(all_indices))
                        sample_indices = all_indices[:sample_size]
                        
                        if sample_indices:
                            sample_data = container.data.loc[sample_indices]
                            st.write("**サンプルデータ:**")
                            st.dataframe(sample_data, use_container_width=True)
                    
                    # 修正を選択するチェックボックス
                    selected = st.checkbox(
                        "この修正を適用する",
                        key=f"fix_{sample_prop.fix_id}",
                        value=sample_prop.fix_id in st.session_state.selected_fixes
                    )
                    
                    if selected and sample_prop.fix_id not in st.session_state.selected_fixes:
                        st.session_state.selected_fixes.append(sample_prop.fix_id)
                    elif not selected and sample_prop.fix_id in st.session_state.selected_fixes:
                        st.session_state.selected_fixes.remove(sample_prop.fix_id)
            
            # 修正の適用ボタン
            if st.session_state.selected_fixes:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{len(st.session_state.selected_fixes)}件の修正を選択中**")
                
                with col2:
                    if st.button("選択した修正を適用", type="primary"):
                        with st.spinner("修正を適用中..."):
                            try:
                                # 選択された修正を適用
                                fixed_container = cleaner.apply_batch_fixes(st.session_state.selected_fixes)
                                
                                # 結果を保存
                                st.session_state.cleaned_container = fixed_container
                                
                                # コールバックを呼び出し
                                if on_clean_callback:
                                    on_clean_callback(fixed_container)
                                
                                # 修正提案とセッション状態をリセット
                                cleaner = DataCleaner(validator, fixed_container)
                                st.session_state.fix_proposals = cleaner.fix_proposals
                                st.session_state.selected_fixes = []
                                
                                st.success("修正が正常に適用されました！")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"修正の適用中にエラーが発生しました: {e}")
        else:
            st.info("現在の条件に一致する修正提案はありません。")
    
    # マップ表示タブ
    with tabs[3]:
        st.write("### 問題箇所のマップ表示")
        
        # 空間的な問題の地図表示
        map_fig = visualization.get_spatial_issues_map()
        st.plotly_chart(map_fig, use_container_width=True)
        
        # 時間的な問題のグラフ表示
        st.write("### 時間的問題の可視化")
        time_fig = visualization.get_temporal_issues_visualization()
        st.plotly_chart(time_fig, use_container_width=True)
    
    # 履歴タブ
    with tabs[4]:
        st.write("### 修正履歴")
        
        # 適用された修正の履歴を表示
        fix_history = cleaner.get_fix_history()
        
        if fix_history:
            history_items = []
            
            for fix in fix_history:
                item = {
                    "修正タイプ": fix.get("fix_type", ""),
                    "説明": fix.get("description", ""),
                    "適用日時": fix.get("applied_at", ""),
                    "影響行数": len(fix.get("target_indices", [])),
                    "重要度": fix.get("severity", "")
                }
                history_items.append(item)
            
            history_df = pd.DataFrame(history_items)
            st.dataframe(history_df, use_container_width=True)
            
            # 修正サマリー
            fix_summary = cleaner.get_fix_summary()
            
            st.write("### 修正サマリー")
            col1, col2 = st.columns(2)
            
            col1.metric("合計修正数", fix_summary.get("total_fixes", 0))
            
            # 修正タイプごとの内訳
            st.write("#### 修正タイプの内訳")
            fix_type_counts = fix_summary.get("fix_type_counts", {})
            
            if fix_type_counts:
                type_df = pd.DataFrame({
                    "修正タイプ": list(fix_type_counts.keys()),
                    "件数": list(fix_type_counts.values())
                })
                
                fig = px.bar(
                    type_df,
                    x="修正タイプ",
                    y="件数",
                    title="修正タイプの内訳",
                    color="修正タイプ"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("修正履歴はまだありません。")

def data_cleaning_demo():
    """
    データクリーニングのデモ画面
    """
    st.title("データクリーニングデモ")
    
    # サンプルデータの生成
    if 'demo_data' not in st.session_state:
        # サンプルデータを作成（わざと問題を含める）
        import numpy as np
        from datetime import datetime, timedelta
        
        # 基本データの作成
        n = 100
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        times = [start_time + timedelta(seconds=i*10) for i in range(n)]
        
        # 緯度・経度の基本的な動き
        base_lat = 35.6580
        base_lon = 139.7510
        
        # ランダムウォーク
        np.random.seed(42)
        lat_steps = np.random.normal(0, 0.0001, n).cumsum()
        lon_steps = np.random.normal(0, 0.0001, n).cumsum()
        
        latitudes = base_lat + lat_steps
        longitudes = base_lon + lon_steps
        
        # わざと問題を含める
        # 欠損値
        latitudes[10:15] = np.nan
        
        # 範囲外の値
        latitudes[30] = 200.0  # 緯度の範囲は-90〜90
        
        # 重複タイムスタンプ
        times[50] = times[49]
        
        # 時間の逆行
        times[70] = times[68] - timedelta(seconds=30)
        
        # 空間的ジャンプ
        latitudes[80] = latitudes[79] + 0.1
        longitudes[80] = longitudes[79] + 0.1
        
        # DataFrameの作成
        data = {
            'timestamp': times,
            'latitude': latitudes,
            'longitude': longitudes,
            'speed': np.random.uniform(5, 15, n)
        }
        
        df = pd.DataFrame(data)
        container = GPSDataContainer(df)
        
        # 検証器の作成
        validator = DataValidator()
        validator.validate(container)
        
        st.session_state.demo_data = container
        st.session_state.demo_validator = validator
    
    # デモの実行
    data_cleaning_form(st.session_state.demo_validator, st.session_state.demo_data)

if __name__ == "__main__":
    data_cleaning_demo()
