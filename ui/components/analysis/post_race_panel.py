# -*- coding: utf-8 -*-
"""
ui.components.analysis.post_race_panel モジュール

レース後戦略分析のためのStreamlit UIコンポーネントを提供します。
戦略評価、重要ポイント、改善提案などの分析結果を表示するパネルを実装しています。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import json
import base64
from io import BytesIO
from typing import Dict, List, Tuple, Optional, Union, Any

# 内部モジュールのインポート
from sailing_data_processor.analysis.post_race_analyzer import PostRaceAnalyzer
from sailing_data_processor.visualization.strategy_visualization import StrategyVisualizer

def post_race_analysis_panel(analyzer: PostRaceAnalyzer = None, 
                           data_manager=None, 
                           on_change=None, 
                           key_prefix=""):
    """
    レース後分析パネルを表示
    
    Parameters
    ----------
    analyzer : PostRaceAnalyzer, optional
        レース後分析エンジン, by default None
    data_manager : DataManager, optional
        データ管理オブジェクト, by default None
    on_change : callable, optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""
        
    Returns
    -------
    dict
        コンポーネント状態
    """
    changes = {}
    
    # 分析エンジンがない場合は新規作成
    if analyzer is None:
        analyzer = PostRaceAnalyzer()
    
    # セーラープロファイルの設定（最初に必要な情報を取得）
    st.markdown("### セーラー情報設定")
    with st.expander("セーラープロファイル", expanded=False):
        sailor_profile = _sailor_profile_settings(key_prefix)
        
        # 分析エンジンのプロファイル更新
        if sailor_profile != analyzer.sailor_profile:
            analyzer.sailor_profile = sailor_profile
            analyzer.skill_level = analyzer._determine_skill_level()
            changes["sailor_profile"] = sailor_profile
    
    # タブレイアウト
    tabs = st.tabs(["分析設定", "戦略評価", "重要ポイント", "改善提案", "レポート"])
    
    # 分析設定タブ
    with tabs[0]:
        analysis_settings, is_settings_changed = _analysis_settings_tab(analyzer, data_manager, key_prefix)
        
        # データ選択
        selected_data, is_data_changed = _data_selection_panel(data_manager, key_prefix)
        
        if is_settings_changed:
            changes["analysis_settings"] = analysis_settings
        
        if is_data_changed:
            changes["selected_data"] = selected_data
        
        # 分析実行ボタン
        if st.button("分析実行", key=f"{key_prefix}_run_analysis_button"):
            if selected_data:
                with st.spinner("分析を実行中..."):
                    # 選択されたデータを取得
                    track_data = selected_data.get("track_data")
                    wind_data = selected_data.get("wind_data")
                    competitor_data = selected_data.get("competitor_data")
                    course_data = selected_data.get("course_data")
                    
                    # 分析の実行
                    try:
                        analysis_result = analyzer.analyze_race(
                            track_data, wind_data, competitor_data, course_data
                        )
                        st.session_state[f"{key_prefix}_analysis_result"] = analysis_result
                        st.success("分析が完了しました。各タブで結果を確認してください。")
                        changes["analysis_result"] = analysis_result
                    except Exception as e:
                        st.error(f"分析中にエラーが発生しました: {str(e)}")
            else:
                st.warning("分析に必要なデータが選択されていません。")
    
    # 分析結果の取得
    analysis_result = st.session_state.get(f"{key_prefix}_analysis_result", None)
    
    # 分析結果が存在する場合のみ、他のタブを表示
    if analysis_result:
        # 戦略評価タブ
        with tabs[1]:
            _strategy_evaluation_tab(analysis_result, key_prefix)
        
        # 重要ポイントタブ
        with tabs[2]:
            _decision_points_tab(analysis_result, selected_data, key_prefix)
        
        # 改善提案タブ
        with tabs[3]:
            _improvement_suggestions_tab(analysis_result, key_prefix)
        
        # レポートタブ
        with tabs[4]:
            _report_generation_tab(analyzer, analysis_result, key_prefix)
    else:
        # 分析結果がない場合のメッセージ
        for tab in tabs[1:]:
            with tab:
                st.info("分析結果がありません。「分析設定」タブで分析を実行してください。")
    
    # コールバックの呼び出し
    if changes and on_change:
        on_change(changes)
    
    return changes

def _sailor_profile_settings(key_prefix):
    """セーラープロファイル設定コンポーネント"""
    # 既存のプロファイルを取得（ない場合はデフォルト値）
    default_profile = {
        "name": "",
        "skill_level": "intermediate",
        "experience_years": 3,
        "competition_level": "club",
        "preferred_boat_class": "",
        "goals": ""
    }
    
    profile = st.session_state.get(f"{key_prefix}_sailor_profile", default_profile)
    
    # プロファイル設定UIを表示
    col1, col2 = st.columns(2)
    
    with col1:
        profile["name"] = st.text_input("名前", profile["name"], key=f"{key_prefix}_sailor_name")
        profile["experience_years"] = st.number_input(
            "経験年数", min_value=0, max_value=50, value=profile.get("experience_years", 3),
            key=f"{key_prefix}_experience_years"
        )
        profile["preferred_boat_class"] = st.text_input(
            "主な使用艇種", profile.get("preferred_boat_class", ""),
            key=f"{key_prefix}_boat_class"
        )
    
    with col2:
        profile["skill_level"] = st.selectbox(
            "スキルレベル",
            options=["beginner", "intermediate", "advanced", "expert", "professional"],
            format_func=lambda x: {
                "beginner": "初心者", 
                "intermediate": "中級者", 
                "advanced": "上級者",
                "expert": "エキスパート", 
                "professional": "プロフェッショナル"
            }.get(x, x),
            index=["beginner", "intermediate", "advanced", "expert", "professional"].index(
                profile.get("skill_level", "intermediate")
            ),
            key=f"{key_prefix}_skill_level"
        )
        
        profile["competition_level"] = st.selectbox(
            "競技レベル",
            options=["recreational", "club", "regional", "national", "international", "olympic"],
            format_func=lambda x: {
                "recreational": "レクリエーション", 
                "club": "クラブ", 
                "regional": "地域",
                "national": "国内", 
                "international": "国際", 
                "olympic": "オリンピック"
            }.get(x, x),
            index=["recreational", "club", "regional", "national", "international", "olympic"].index(
                profile.get("competition_level", "club")
            ),
            key=f"{key_prefix}_competition_level"
        )
    
    profile["goals"] = st.text_area(
        "目標", profile.get("goals", ""),
        key=f"{key_prefix}_goals", height=100
    )
    
    # セッションステートに保存
    st.session_state[f"{key_prefix}_sailor_profile"] = profile
    
    return profile

def _analysis_settings_tab(analyzer, data_manager, key_prefix):
    """分析設定タブのUI"""
    st.markdown("#### 分析設定")
    
    # 現在の設定を取得
    current_settings = st.session_state.get(f"{key_prefix}_analysis_settings", {
        "analysis_level": analyzer.analysis_level,
        "include_wind_analysis": True,
        "include_competitor_analysis": True,
        "detail_level": "comprehensive"
    })
    
    # 設定変更フラグ
    is_changed = False
    
    # 設定UI
    col1, col2 = st.columns(2)
    
    with col1:
        # 分析レベル設定
        new_analysis_level = st.selectbox(
            "分析レベル",
            options=["basic", "intermediate", "advanced", "professional"],
            format_func=lambda x: {
                "basic": "基本", 
                "intermediate": "中級", 
                "advanced": "高度", 
                "professional": "プロフェッショナル"
            }.get(x, x),
            index=["basic", "intermediate", "advanced", "professional"].index(
                current_settings.get("analysis_level", "advanced")
            ),
            key=f"{key_prefix}_analysis_level",
            help="分析の詳細度と複雑さを指定します。セーラーのスキルレベルに合わせて選択してください。"
        )
        
        # 設定が変更されたかチェック
        if new_analysis_level != current_settings.get("analysis_level"):
            current_settings["analysis_level"] = new_analysis_level
            analyzer.analysis_level = new_analysis_level  # 分析器の設定も更新
            is_changed = True
        
        # 詳細レベル設定
        new_detail_level = st.selectbox(
            "詳細度",
            options=["brief", "standard", "comprehensive"],
            format_func=lambda x: {
                "brief": "簡潔", 
                "standard": "標準", 
                "comprehensive": "詳細"
            }.get(x, x),
            index=["brief", "standard", "comprehensive"].index(
                current_settings.get("detail_level", "comprehensive")
            ),
            key=f"{key_prefix}_detail_level",
            help="分析結果の詳細度を指定します。「簡潔」は主要なポイントのみ、「詳細」はすべての情報を含みます。"
        )
        
        if new_detail_level != current_settings.get("detail_level"):
            current_settings["detail_level"] = new_detail_level
            is_changed = True
    
    with col2:
        # 風分析の有無
        new_include_wind = st.checkbox(
            "風向分析を含める", 
            value=current_settings.get("include_wind_analysis", True),
            key=f"{key_prefix}_include_wind",
            help="風向風速データがある場合、風向変化とその影響の分析を含めます。"
        )
        
        if new_include_wind != current_settings.get("include_wind_analysis"):
            current_settings["include_wind_analysis"] = new_include_wind
            is_changed = True
        
        # 競合艇分析の有無
        new_include_competitor = st.checkbox(
            "競合艇分析を含める", 
            value=current_settings.get("include_competitor_analysis", True),
            key=f"{key_prefix}_include_competitor",
            help="競合艇データがある場合、相対的なパフォーマンスとポジショニングの分析を含めます。"
        )
        
        if new_include_competitor != current_settings.get("include_competitor_analysis"):
            current_settings["include_competitor_analysis"] = new_include_competitor
            is_changed = True
    
    # 高度な設定（折りたたみ可能）
    with st.expander("高度な分析設定", expanded=False):
        # 分析パラメータの詳細設定
        col1, col2 = st.columns(2)
        
        with col1:
            # 戦略ポイント感度
            new_sensitivity = st.slider(
                "戦略ポイント感度", 
                min_value=0.1, 
                max_value=1.0, 
                value=current_settings.get("strategy_sensitivity", 0.7),
                step=0.1,
                key=f"{key_prefix}_strategy_sensitivity",
                help="値が高いほど、より多くの戦略的判断ポイントが検出されます。"
            )
            
            if "strategy_sensitivity" not in current_settings or new_sensitivity != current_settings["strategy_sensitivity"]:
                current_settings["strategy_sensitivity"] = new_sensitivity
                is_changed = True
            
            # 最大戦略ポイント数
            new_max_points = st.slider(
                "最大戦略ポイント数", 
                min_value=5, 
                max_value=30, 
                value=current_settings.get("max_strategy_points", 15),
                step=5,
                key=f"{key_prefix}_max_points",
                help="分析結果に含める戦略的判断ポイントの最大数です。"
            )
            
            if "max_strategy_points" not in current_settings or new_max_points != current_settings["max_strategy_points"]:
                current_settings["max_strategy_points"] = new_max_points
                is_changed = True
        
        with col2:
            # 風向変化検出の閾値
            new_wind_threshold = st.slider(
                "風向変化検出閾値", 
                min_value=5, 
                max_value=30, 
                value=current_settings.get("wind_shift_threshold", 10),
                step=5,
                key=f"{key_prefix}_wind_threshold",
                help="検出する風向変化の最小角度（度）です。値が小さいほど、小さな変化も検出します。"
            )
            
            if "wind_shift_threshold" not in current_settings or new_wind_threshold != current_settings["wind_shift_threshold"]:
                current_settings["wind_shift_threshold"] = new_wind_threshold
                is_changed = True
            
            # 改善提案レベル
            new_suggestion_level = st.selectbox(
                "改善提案レベル",
                options=["basic", "intermediate", "advanced"],
                format_func=lambda x: {
                    "basic": "基本的な提案", 
                    "intermediate": "中級者向け提案", 
                    "advanced": "詳細な専門的提案"
                }.get(x, x),
                index=["basic", "intermediate", "advanced"].index(
                    current_settings.get("suggestion_level", "intermediate")
                ),
                key=f"{key_prefix}_suggestion_level",
                help="セーラーのレベルに合わせた改善提案の詳細度です。"
            )
            
            if "suggestion_level" not in current_settings or new_suggestion_level != current_settings["suggestion_level"]:
                current_settings["suggestion_level"] = new_suggestion_level
                is_changed = True
    
    # セッションステートに保存
    st.session_state[f"{key_prefix}_analysis_settings"] = current_settings
    
    return current_settings, is_changed

def _data_selection_panel(data_manager, key_prefix):
    """データ選択パネル"""
    st.markdown("#### データ選択")
    
    # 現在の選択を取得
    current_selection = st.session_state.get(f"{key_prefix}_selected_data", {})
    
    # データ選択用の辞書（本来はデータマネージャーから取得）
    available_data = {}
    if data_manager:
        # データマネージャーからデータリストを取得
        available_data = data_manager.get_available_data()
    else:
        # ダミーデータ（デモ用）
        available_data = {
            "tracks": ["デモトラック1", "デモトラック2", "サンプルレース"],
            "wind_data": ["推定風データ1", "推定風データ2", "なし"],
            "competitors": ["競合艇データ1", "なし"],
            "courses": ["コースA", "コースB", "なし"]
        }
    
    # 選択変更フラグ
    is_changed = False
    
    # データ選択UI
    col1, col2 = st.columns(2)
    
    with col1:
        # トラックデータ選択（必須）
        tracks = available_data.get("tracks", [])
        selected_track = st.selectbox(
            "GPSトラックデータ (必須)",
            options=tracks,
            index=0 if not tracks else tracks.index(current_selection.get("track_name", tracks[0])) if current_selection.get("track_name") in tracks else 0,
            key=f"{key_prefix}_track_selection"
        )
        
        if selected_track != current_selection.get("track_name"):
            current_selection["track_name"] = selected_track
            # 実際のデータの取得（ここではダミーデータを設定）
            if data_manager:
                current_selection["track_data"] = data_manager.get_track_data(selected_track)
            else:
                # ダミーデータ生成（デモ用）
                current_selection["track_data"] = _generate_dummy_track_data()
            is_changed = True
        
        # 競合艇データ選択（オプション）
        competitors = available_data.get("competitors", ["なし"])
        selected_competitor = st.selectbox(
            "競合艇データ (オプション)",
            options=competitors,
            index=0 if not competitors else competitors.index(current_selection.get("competitor_name", "なし")) if current_selection.get("competitor_name") in competitors else 0,
            key=f"{key_prefix}_competitor_selection"
        )
        
        if selected_competitor != current_selection.get("competitor_name"):
            current_selection["competitor_name"] = selected_competitor
            # 実際のデータの取得
            if selected_competitor != "なし" and data_manager:
                current_selection["competitor_data"] = data_manager.get_competitor_data(selected_competitor)
            else:
                current_selection["competitor_data"] = None
            is_changed = True
    
    with col2:
        # 風データ選択（オプション）
        wind_data = available_data.get("wind_data", ["なし"])
        selected_wind = st.selectbox(
            "風データ (オプション)",
            options=wind_data,
            index=0 if not wind_data else wind_data.index(current_selection.get("wind_name", "なし")) if current_selection.get("wind_name") in wind_data else 0,
            key=f"{key_prefix}_wind_selection"
        )
        
        if selected_wind != current_selection.get("wind_name"):
            current_selection["wind_name"] = selected_wind
            # 実際のデータの取得
            if selected_wind != "なし" and data_manager:
                current_selection["wind_data"] = data_manager.get_wind_data(selected_wind)
            else:
                # ダミーデータ生成（デモ用）
                current_selection["wind_data"] = _generate_dummy_wind_data()
            is_changed = True
        
        # コースデータ選択（オプション）
        courses = available_data.get("courses", ["なし"])
        selected_course = st.selectbox(
            "コースデータ (オプション)",
            options=courses,
            index=0 if not courses else courses.index(current_selection.get("course_name", "なし")) if current_selection.get("course_name") in courses else 0,
            key=f"{key_prefix}_course_selection"
        )
        
        if selected_course != current_selection.get("course_name"):
            current_selection["course_name"] = selected_course
            # 実際のデータの取得
            if selected_course != "なし" and data_manager:
                current_selection["course_data"] = data_manager.get_course_data(selected_course)
            else:
                current_selection["course_data"] = None
            is_changed = True
    
    # データプレビュー
    with st.expander("選択データのプレビュー", expanded=False):
        if "track_data" in current_selection and current_selection["track_data"] is not None:
            st.subheader("GPSトラックデータ")
            st.dataframe(current_selection["track_data"].head())
        
        if "wind_data" in current_selection and current_selection["wind_data"] is not None:
            st.subheader("風データ")
            st.dataframe(current_selection["wind_data"].head())
        
        if "competitor_data" in current_selection and current_selection["competitor_data"] is not None:
            st.subheader("競合艇データ")
            st.dataframe(current_selection["competitor_data"].head())
        
        if "course_data" in current_selection and current_selection["course_data"] is not None:
            st.subheader("コースデータ")
            st.json(current_selection["course_data"])
    
    # セッションステートに保存
    st.session_state[f"{key_prefix}_selected_data"] = current_selection
    
    return current_selection, is_changed

def _strategy_evaluation_tab(analysis_result, key_prefix):
    """戦略評価タブのUI"""
    st.markdown("### 戦略評価")
    
    # 戦略評価データの取得
    strategy_evaluation = analysis_result.get("strategy_evaluation", {})
    
    if not strategy_evaluation:
        st.warning("戦略評価データがありません。")
        return
    
    # 分析結果サマリー
    st.markdown("#### 総合評価")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 総合評価スコア
        overall_rating = strategy_evaluation.get("overall_rating", 0)
        st.metric("総合評価スコア", f"{overall_rating:.1f}/10")
        
        # 評価コメント
        if "overall_assessment" in strategy_evaluation:
            st.markdown(f"**評価コメント:** {strategy_evaluation['overall_assessment']}")
        
        # 風の評価
        if "wind_assessment" in analysis_result.get("summary", {}):
            st.markdown(f"**風況:** {analysis_result['summary']['wind_assessment']}")
        
        # ポジショニング評価
        if "positioning_assessment" in analysis_result.get("summary", {}):
            st.markdown(f"**ポジショニング:** {analysis_result['summary']['positioning_assessment']}")
    
    with col2:
        # 実行品質
        execution_quality = strategy_evaluation.get("execution_quality", 0)
        
        # ゲージ表示（簡易的なものをここで実装）
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 評価に基づいた色
        if overall_rating >= 7.5:
            color = 'green'
        elif overall_rating >= 5.0:
            color = 'orange'
        else:
            color = 'red'
        
        # 円弧の描画
        ax.add_patch(plt.Circle((0.5, 0.5), 0.4, color='lightgray', fill=True))
        ax.add_patch(plt.matplotlib.patches.Wedge(
            (0.5, 0.5), 0.4, 90, 90 + 360 * (overall_rating / 10), width=0.1, color=color
        ))
        
        # 実行品質の円弧
        ax.add_patch(plt.matplotlib.patches.Wedge(
            (0.5, 0.5), 0.28, 90, 90 + 360 * (execution_quality / 10), width=0.1, color='blue'
        ))
        
        # テキスト
        ax.text(0.5, 0.5, f'{overall_rating:.1f}', ha='center', va='center', fontsize=24, fontweight='bold')
        ax.text(0.5, 0.3, f'実行品質: {execution_quality:.1f}', ha='center', va='center', fontsize=10)
        
        st.pyplot(fig)
    
    # カテゴリ別評価
    st.markdown("#### カテゴリ別評価")
    
    # カテゴリとスコアの取得
    categories = {
        'upwind_strategy': '風上戦略',
        'downwind_strategy': '風下戦略',
        'start_execution': 'スタート実行',
        'mark_rounding': 'マーク回航',
        'tactical_decisions': '戦術判断'
    }
    
    scores = []
    for key, label in categories.items():
        if key in strategy_evaluation and 'score' in strategy_evaluation[key]:
            scores.append((label, strategy_evaluation[key]['score']))
    
    # スコアを表示
    if scores:
        # 横棒グラフでスコアを表示
        labels = [s[0] for s in scores]
        values = [s[1] for s in scores]
        
        fig, ax = plt.subplots(figsize=(10, 4))
        bars = ax.barh(labels, values, color=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd'])
        
        # スコア値の表示
        for i, v in enumerate(values):
            ax.text(v + 0.1, i, f'{v:.1f}', va='center')
        
        ax.set_xlim(0, 10.5)
        ax.set_xlabel('評価点')
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        
        st.pyplot(fig)
    else:
        st.info("カテゴリ別評価データがありません。")
    
    # 強みと弱みの表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 強み")
        strengths = strategy_evaluation.get("strengths", [])
        if strengths:
            for strength in strengths:
                st.markdown(f"- **{strength.get('display_name', strength.get('area', ''))}**: {strength.get('description', '')}")
        else:
            st.info("強みのデータがありません。")
    
    with col2:
        st.markdown("#### 改善点")
        weaknesses = strategy_evaluation.get("weaknesses", [])
        if weaknesses:
            for weakness in weaknesses:
                st.markdown(f"- **{weakness.get('display_name', weakness.get('area', ''))}**: {weakness.get('description', '')}")
        else:
            st.info("改善点のデータがありません。")
    
    # 詳細な評価結果を折りたたみ表示
    with st.expander("詳細な評価結果", expanded=False):
        # カテゴリごとの詳細表示
        for key, label in categories.items():
            if key in strategy_evaluation:
                cat_data = strategy_evaluation[key]
                st.markdown(f"#### {label}")
                
                # スコアと主要なコメント
                st.markdown(f"**スコア:** {cat_data.get('score', 0):.1f}/10")
                
                # コメントの表示
                if 'comments' in cat_data:
                    st.markdown("**評価コメント:**")
                    for comment in cat_data['comments']:
                        st.markdown(f"- {comment}")
                
                # メトリクスの表示
                if 'metrics' in cat_data:
                    st.markdown("**評価指標:**")
                    metrics = cat_data['metrics']
                    metrics_df = pd.DataFrame([metrics])
                    st.dataframe(metrics_df)
                
                st.markdown("---")

def _decision_points_tab(analysis_result, selected_data, key_prefix):
    """重要ポイントタブのUI"""
    st.markdown("### 重要判断ポイント")
    
    # 決断ポイントデータの取得
    decision_points = analysis_result.get("decision_points", {})
    
    if not decision_points:
        st.warning("重要判断ポイントのデータがありません。")
        return
    
    # サマリー情報
    if "summary" in decision_points:
        st.markdown(f"**分析サマリー:** {decision_points['summary']}")
    
    # 高影響ポイントの取得
    high_impact_points = decision_points.get("high_impact_points", [])
    
    if not high_impact_points:
        st.info("高影響度の判断ポイントが検出されませんでした。")
        return
    
    # 地図表示（トラックデータと判断ポイントの位置）
    if "track_data" in selected_data and selected_data["track_data"] is not None:
        st.markdown("#### 戦略ポイントの地理的分布")
        
        # 可視化オブジェクトの作成
        visualizer = StrategyVisualizer()
        
        # 位置情報のあるポイントのみ抽出
        geo_points = [p for p in high_impact_points if 'position' in p and p['position']]
        
        if geo_points:
            try:
                # 地図プロット作成
                fig = visualizer.plot_strategic_points_map(
                    selected_data["track_data"],
                    geo_points,
                    selected_data.get("course_data"),
                    "戦略的判断ポイントの分布"
                )
                
                # 図の表示
                st.pyplot(fig)
            except Exception as e:
                st.error(f"地図表示中にエラーが発生しました: {str(e)}")
        else:
            st.info("位置情報のある判断ポイントがありません。")
    
    # ポイントのリスト表示
    st.markdown("#### 主要な判断ポイント")
    
    # フィルタリングオプション
    col1, col2 = st.columns(2)
    
    with col1:
        # タイプによるフィルター
        point_types = list(set(p.get("type", "unknown") for p in high_impact_points))
        selected_types = st.multiselect(
            "ポイント種類でフィルタ",
            options=point_types,
            default=point_types,
            format_func=lambda x: {
                "tack": "タック",
                "gybe": "ジャイブ",
                "layline": "レイライン",
                "wind_shift": "風向変化",
                "cross_point": "クロスポイント",
                "vmg_change": "VMG変化",
                "start": "スタート",
                "mark_rounding": "マーク回航"
            }.get(x, x),
            key=f"{key_prefix}_point_type_filter"
        )
    
    with col2:
        # 影響度によるフィルター
        min_impact = st.slider(
            "最小影響度",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.5,
            key=f"{key_prefix}_min_impact"
        )
    
    # フィルタリングされたポイント
    filtered_points = [
        p for p in high_impact_points 
        if p.get("type", "unknown") in selected_types and p.get("impact_score", 0) >= min_impact
    ]
    
    # ポイントリストの表示
    if filtered_points:
        # テーブル形式でポイントを表示
        point_data = []
        for p in filtered_points:
            point_type = p.get("type", "unknown")
            type_display = {
                "tack": "タック",
                "gybe": "ジャイブ",
                "layline": "レイライン",
                "wind_shift": "風向変化",
                "cross_point": "クロスポイント",
                "vmg_change": "VMG変化",
                "start": "スタート",
                "mark_rounding": "マーク回航"
            }.get(point_type, point_type)
            
            time_str = ""
            point_time = p.get("time", "")
            if point_time:
                if isinstance(point_time, datetime):
                    time_str = point_time.strftime("%H:%M:%S")
                else:
                    time_str = str(point_time)
            
            point_data.append({
                "時刻": time_str,
                "種類": type_display,
                "影響度": f"{p.get('impact_score', 0):.1f}",
                "説明": p.get("description", ""),
                "詳細": "詳細を表示"
            })
        
        # データフレームの作成と表示
        df = pd.DataFrame(point_data)
        
        # インタラクティブな詳細表示のための設定
        st.session_state[f"{key_prefix}_point_data"] = filtered_points
        
        # テーブル表示とクリックイベント
        selected_indices = st.dataframe(
            df,
            column_config={
                "詳細": st.column_config.CheckboxColumn(
                    "詳細を表示",
                    help="クリックすると詳細情報を表示します",
                    default=False
                )
            },
            hide_index=True,
            key=f"{key_prefix}_points_table"
        )
        
        # 選択された行の詳細表示
        if selected_indices and "edited_rows" in selected_indices:
            for idx, value in selected_indices["edited_rows"].items():
                if value.get("詳細") is True:
                    # 選択されたポイントの詳細を取得
                    point = filtered_points[int(idx)]
                    
                    # セッションステートに保存
                    st.session_state[f"{key_prefix}_selected_point"] = point
                    
                    # 詳細表示ダイアログを表示
                    _show_point_details_dialog(point, selected_data, key_prefix)
    else:
        st.info("フィルタ条件に一致する判断ポイントがありません。")

def _show_point_details_dialog(point, selected_data, key_prefix):
    """判断ポイントの詳細ダイアログを表示"""
    # ダイアログ用の列
    st.markdown("#### 判断ポイント詳細分析")
    
    # ポイントの基本情報
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 基本情報
        point_type = point.get("type", "unknown")
        type_display = {
            "tack": "タック",
            "gybe": "ジャイブ",
            "layline": "レイライン",
            "wind_shift": "風向変化",
            "cross_point": "クロスポイント",
            "vmg_change": "VMG変化",
            "start": "スタート",
            "mark_rounding": "マーク回航"
        }.get(point_type, point_type)
        
        st.markdown(f"**種類:** {type_display}")
        
        # 時刻表示
        point_time = point.get("time", "")
        if point_time:
            if isinstance(point_time, datetime):
                time_str = point_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = str(point_time)
            st.markdown(f"**時刻:** {time_str}")
        
        # 影響度
        impact_score = point.get("impact_score", 0)
        st.markdown(f"**影響度:** {impact_score:.1f}/10")
        
        # 説明
        st.markdown(f"**説明:** {point.get('description', '')}")
        
        # その他の詳細情報
        for key, value in point.items():
            if key not in ["type", "time", "impact_score", "description", "position", "alternatives"]:
                # 詳細情報の表示（フォーマットに注意）
                if isinstance(value, (int, float)):
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value:.2f}")
                elif not isinstance(value, (list, dict)):
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
    
    with col2:
        # 代替シナリオの表示
        alternatives = point.get("alternatives", [])
        if alternatives:
            st.markdown("**代替シナリオ:**")
            for i, alt in enumerate(alternatives):
                with st.expander(f"シナリオ {i+1}: {alt.get('scenario', '')}", expanded=i == 0):
                    st.markdown(f"**予想結果:** {alt.get('outcome', '')}")
                    st.markdown(f"**影響度:** {alt.get('impact', 0):.2f}")
                    
                    # その他の詳細情報
                    for key, value in alt.items():
                        if key not in ["scenario", "outcome", "impact"]:
                            if isinstance(value, (int, float)):
                                st.markdown(f"**{key.replace('_', ' ').title()}:** {value:.2f}")
                            elif not isinstance(value, (list, dict)):
                                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.info("代替シナリオのデータがありません。")
    
    # マップ表示（位置情報がある場合）
    if "position" in point and point["position"] and "track_data" in selected_data and selected_data["track_data"] is not None:
        st.markdown("#### 位置情報")
        
        # 位置周辺のトラックデータを抽出
        track_data = selected_data["track_data"]
        
        # 可視化オブジェクトの作成
        visualizer = StrategyVisualizer()
        
        try:
            # 詳細マップの作成
            fig = visualizer.plot_decision_point_details(
                point,
                alternatives if alternatives else None,
                track_data
            )
            
            # 図の表示
            st.pyplot(fig)
        except Exception as e:
            st.error(f"詳細マップ表示中にエラーが発生しました: {str(e)}")

def _improvement_suggestions_tab(analysis_result, key_prefix):
    """改善提案タブのUI"""
    st.markdown("### 改善提案")
    
    # 改善提案データの取得
    improvement_suggestions = analysis_result.get("improvement_suggestions", {})
    
    if not improvement_suggestions:
        st.warning("改善提案データがありません。")
        return
    
    # サマリー情報
    if "summary" in improvement_suggestions:
        st.markdown(f"**提案サマリー:** {improvement_suggestions['summary']}")
    
    # 優先改善領域
    priority_areas = improvement_suggestions.get("priority_areas", [])
    
    if priority_areas:
        st.markdown("#### 優先改善領域")
        
        # 可視化オブジェクトの作成
        visualizer = StrategyVisualizer()
        
        try:
            # 優先領域のバブルチャート作成
            fig = visualizer.plot_improvement_recommendations(
                improvement_suggestions,
                "改善提案と重点領域"
            )
            
            # 図の表示
            st.pyplot(fig)
        except Exception as e:
            st.error(f"改善提案の可視化中にエラーが発生しました: {str(e)}")
        
        # 優先領域のリスト表示
        for i, area in enumerate(priority_areas[:5]):  # 上位5つのみ表示
            with st.expander(
                f"{i+1}. {area.get('display_name', area.get('area', ''))} (優先度: {area.get('priority', 0):.1f})",
                expanded=i == 0
            ):
                st.markdown(f"**カテゴリ:** {area.get('category_name', area.get('category', ''))}")
                st.markdown(f"**改善点:** {area.get('weakness_description', '')}")
                st.markdown(f"**推奨アクション:** {area.get('suggested_action', '')}")
    else:
        st.info("優先改善領域のデータがありません。")
    
    # 練習課題の表示
    practice_tasks = improvement_suggestions.get("practice_tasks", [])
    
    if practice_tasks:
        st.markdown("#### 推奨練習課題")
        
        for i, task in enumerate(practice_tasks):
            with st.expander(
                f"{task.get('name', f'練習課題 {i+1}')}",
                expanded=i == 0
            ):
                st.markdown(f"**領域:** {task.get('area_name', task.get('area', ''))}")
                st.markdown(f"**説明:** {task.get('description', '')}")
                
                # 優先度が提供されている場合
                if 'priority' in task:
                    st.markdown(f"**優先度:** {task.get('priority', 0):.1f}/10")
    else:
        st.info("推奨練習課題のデータがありません。")
    
    # 成長パスの表示
    development_path = improvement_suggestions.get("development_path", [])
    
    if development_path:
        st.markdown("#### 成長パス")
        
        for i, path in enumerate(development_path):
            with st.expander(
                f"{path.get('area_name', path.get('area', ''))}の成長ステップ",
                expanded=i == 0
            ):
                st.markdown(f"**現在のレベル:** {path.get('current_status', '')}")
                st.markdown(f"**次の目標:** {path.get('next_goal', '')}")
                
                # 優先度が提供されている場合
                if 'priority' in path:
                    st.markdown(f"**優先度:** {path.get('priority', 0):.1f}/10")
    else:
        st.info("成長パス情報がありません。")
    
    # スキルベンチマークの表示
    skill_benchmarks = improvement_suggestions.get("skill_benchmarks", {})
    
    if skill_benchmarks and "current_benchmarks" in skill_benchmarks:
        st.markdown("#### スキルベンチマーク評価")
        
        # 現在のレベルと次のレベル
        current_level = skill_benchmarks.get("current_level", "")
        next_level = skill_benchmarks.get("next_level", "")
        
        if current_level and next_level:
            st.markdown(f"**現在のレベル:** {current_level}")
            st.markdown(f"**次のレベル目標:** {next_level}")
        
        # ベンチマークデータの表示
        current_benchmarks = skill_benchmarks.get("current_benchmarks", {})
        next_benchmarks = skill_benchmarks.get("next_benchmarks", {})
        actual_performance = skill_benchmarks.get("actual_performance", {})
        
        # データフレームの作成
        bench_data = []
        
        for metric in ['upwind_vmg_efficiency', 'downwind_vmg_efficiency', 'tack_efficiency', 
                      'gybe_efficiency', 'start_timing_accuracy', 'mark_rounding_efficiency',
                      'tactical_decision_quality']:
            metric_name = {
                'upwind_vmg_efficiency': '風上VMG効率',
                'downwind_vmg_efficiency': '風下VMG効率',
                'tack_efficiency': 'タック効率',
                'gybe_efficiency': 'ジャイブ効率',
                'start_timing_accuracy': 'スタート精度',
                'mark_rounding_efficiency': 'マーク回航効率',
                'tactical_decision_quality': '戦術判断品質'
            }.get(metric, metric)
            
            bench_data.append({
                "メトリクス": metric_name,
                "現在のレベル基準値": current_benchmarks.get(metric, 0),
                "実際のパフォーマンス": actual_performance.get(metric, "-"),
                "次のレベル基準値": next_benchmarks.get(metric, 0)
            })
        
        # データフレームの表示
        st.dataframe(pd.DataFrame(bench_data), hide_index=True)
    else:
        st.info("スキルベンチマーク情報がありません。")

def _report_generation_tab(analyzer, analysis_result, key_prefix):
    """レポート生成タブのUI"""
    st.markdown("### レポート生成")
    
    # フォーマット選択
    report_format = st.selectbox(
        "レポート形式",
        options=["HTML", "JSON", "PDF"],
        index=0,
        key=f"{key_prefix}_report_format",
        help="生成するレポートの形式を選択します。PDF形式は現在実装中です。"
    )
    
    # テンプレート選択（折りたたみ可能）
    with st.expander("レポートテンプレート設定", expanded=False):
        template_type = st.radio(
            "テンプレートタイプ",
            options=["デフォルト", "カスタム"],
            index=0,
            key=f"{key_prefix}_template_type",
            help="カスタムテンプレートを使用する場合は、テンプレートファイルを選択してください。"
        )
        
        template_file = None
        if template_type == "カスタム":
            template_file = st.file_uploader(
                "テンプレートファイルを選択",
                type=["html", "json", "txt"],
                key=f"{key_prefix}_template_file",
                help="HTMLまたはJSON形式のテンプレートファイルをアップロードしてください。"
            )
    
    # レポート生成ボタン
    if st.button("レポート生成", key=f"{key_prefix}_generate_report_button"):
        if analysis_result:
            with st.spinner("レポートを生成中..."):
                try:
                    # フォーマットに合わせてレポートを生成
                    format_str = report_format.lower()
                    
                    if template_file and template_type == "カスタム":
                        # テンプレートファイルの読み込み
                        template_content = template_file.read().decode("utf-8")
                        report_content = analyzer.export_analysis_report(
                            None, format=format_str, template=template_content
                        )
                    else:
                        # デフォルトテンプレートでレポート生成
                        report_content = analyzer.export_analysis_report(
                            None, format=format_str
                        )
                    
                    if report_content:
                        # レポートのプレビュー表示
                        if format_str == "html":
                            st.markdown("#### HTMLレポートプレビュー")
                            st.components.v1.html(report_content, height=500, scrolling=True)
                            
                            # ダウンロードボタン
                            st.download_button(
                                "HTMLレポートをダウンロード",
                                report_content,
                                file_name=f"sailing_strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                mime="text/html",
                                key=f"{key_prefix}_download_html"
                            )
                        elif format_str == "json":
                            st.markdown("#### JSONレポートプレビュー")
                            st.json(json.loads(report_content))
                            
                            # ダウンロードボタン
                            st.download_button(
                                "JSONレポートをダウンロード",
                                report_content,
                                file_name=f"sailing_strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                key=f"{key_prefix}_download_json"
                            )
                        elif format_str == "pdf":
                            st.warning("PDF形式のレポートは現在実装中です。")
                    else:
                        st.error("レポートの生成に失敗しました。")
                except Exception as e:
                    st.error(f"レポート生成中にエラーが発生しました: {str(e)}")
        else:
            st.warning("レポート生成に必要な分析結果がありません。")

def _generate_dummy_track_data():
    """デモ用のダミートラックデータを生成"""
    # 開始時刻（現在時刻の1時間前）
    start_time = datetime.now() - timedelta(hours=1)
    
    # データポイント数
    n_points = 500
    
    # タイムスタンプの生成（1秒間隔）
    timestamps = [start_time + timedelta(seconds=i) for i in range(n_points)]
    
    # 緯度経度の生成（シンプルな円形コース）
    center_lat, center_lon = 35.6, 139.7  # 東京付近
    radius = 0.01  # 約1km
    angles = np.linspace(0, 2 * np.pi, n_points)
    
    latitudes = center_lat + radius * np.sin(angles)
    longitudes = center_lon + radius * np.cos(angles)
    
    # 速度の生成（5〜8ノット、風向によって変動）
    base_speed = 6.5
    speed_variation = 1.5
    speeds = base_speed + speed_variation * np.sin(angles * 2)
    
    # VMGの生成（速度の60〜90%）
    vmg = speeds * (0.6 + 0.3 * np.abs(np.sin(angles)))
    
    # データフレームの作成
    data = {
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'vmg': vmg,
        'heading': (angles * 180 / np.pi) % 360
    }
    
    return pd.DataFrame(data)

def _generate_dummy_wind_data():
    """デモ用のダミー風データを生成"""
    # 開始時刻（現在時刻の1時間前）
    start_time = datetime.now() - timedelta(hours=1)
    
    # データポイント数
    n_points = 500
    
    # タイムスタンプの生成（1秒間隔）
    timestamps = [start_time + timedelta(seconds=i) for i in range(n_points)]
    
    # 風向の生成（徐々に変化する、225度を中心に±30度）
    base_direction = 225
    direction_variation = 30
    directions = base_direction + direction_variation * np.sin(np.linspace(0, 4 * np.pi, n_points))
    
    # 風速の生成（8〜12ノット）
    base_speed = 10
    speed_variation = 2
    speeds = base_speed + speed_variation * np.sin(np.linspace(0, 8 * np.pi, n_points))
    
    # データフレームの作成
    data = {
        'timestamp': timestamps,
        'wind_direction': directions,
        'wind_speed': speeds
    }
    
    return pd.DataFrame(data)
