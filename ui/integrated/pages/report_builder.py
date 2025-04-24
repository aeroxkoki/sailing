# -*- coding: utf-8 -*-
"""
ui.integrated.pages.report_builder

レポート作成および編集ページ
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# テンプレート管理システムのインポート
from ui.integrated.components.reporting.template_manager import TemplateManager

def render_page():
    """レポートビルダーページをレンダリングする関数"""
    
    st.title('レポートビルダー')
    
    # セッション状態の初期化
    if 'report_builder_initialized' not in st.session_state:
        st.session_state.report_builder_initialized = True
        st.session_state.current_report = None
        st.session_state.current_template_id = None
        st.session_state.editing_section = None
        st.session_state.selected_report_sessions = []
    
    # サイドバーのナビゲーション
    with st.sidebar:
        st.subheader("レポート作成")
        
        # テンプレートマネージャーのインスタンス化
        template_manager = TemplateManager()
        
        # テンプレート選択
        selected_template_id = template_manager.render_template_selector()
        
        if selected_template_id and selected_template_id != st.session_state.current_template_id:
            # 新しいテンプレートが選択された場合
            template = template_manager.get_template(selected_template_id)
            if template:
                st.session_state.current_template_id = selected_template_id
                
                # テンプレートからレポートの初期状態を作成
                st.session_state.current_report = {
                    'id': str(uuid.uuid4()),
                    'title': f"レポート - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    'description': '',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'template_id': selected_template_id,
                    'template_name': template['name'],
                    'sections': template['sections'],
                    'layout': template['layout'],
                    'theme': template['theme'],
                    'sessions': [],
                    'status': 'draft'
                }
                
                # 編集中のセクションをリセット
                st.session_state.editing_section = None
                
                st.success(f"テンプレート「{template['name']}」を読み込みました")
                st.experimental_rerun()
        
        # セッション選択
        if st.session_state.current_report:
            st.markdown("---")
            st.subheader("セッション選択")
            
            # 実際の実装では、プロジェクト管理システムからセッションを取得
            # サンプルとしてダミーデータを使用
            available_sessions = [
                "2025/03/27 レース練習",
                "2025/03/25 風向変化トレーニング",
                "2025/03/20 スピードテスト",
                "2025/03/15 戦術練習",
                "2025/03/10 風上風下走行"
            ]
            
            selected_sessions = st.multiselect(
                "分析対象セッション",
                available_sessions,
                default=st.session_state.selected_report_sessions
            )
            
            if selected_sessions != st.session_state.selected_report_sessions:
                st.session_state.selected_report_sessions = selected_sessions
                
                # レポートのセッション情報を更新
                if st.session_state.current_report:
                    st.session_state.current_report['sessions'] = selected_sessions
                    st.session_state.current_report['updated_at'] = datetime.now().isoformat()
            
            # テンプレート管理（エキスパート向け）
            st.markdown("---")
            with st.expander("テンプレート管理", expanded=False):
                template_manager.render_template_manager_ui()
    
    # メインコンテンツエリア
    if not st.session_state.current_report:
        # レポートが選択されていない場合
        st.info("レポートを作成するには、サイドバーからテンプレートを選択してください。")
        
        # サンプルレポートの表示
        with st.expander("利用可能なレポートタイプ", expanded=True):
            st.markdown("""
            ### レポートタイプ
            
            **基本概要レポート**
            セッションの基本情報と主要な指標を含むシンプルなレポートです。素早く概要を把握したい場合に最適です。
            
            **詳細分析レポート**
            セッションの詳細な分析結果を含む包括的なレポートです。風向風速の詳細な分析、パフォーマンス指標の詳細な内訳、
            戦略ポイントの詳細な分析と改善提案を含みます。
            
            **コーチング用レポート**
            コーチングセッション用に最適化されたレポートです。観察事項、戦略判断のレビュー、改善点と実践提案、
            次のステップを明確に示します。
            
            **セッション比較レポート**
            複数セッション間の比較分析に特化したレポートです。パフォーマンスの比較、戦略判断の比較、傾向分析と
            結論・提案を含みます。
            """)
    else:
        # レポート編集UI
        report = st.session_state.current_report
        
        # レポート基本情報
        col1, col2 = st.columns([3, 1])
        
        with col1:
            report_title = st.text_input("レポートタイトル", value=report['title'])
            if report_title != report['title']:
                report['title'] = report_title
                report['updated_at'] = datetime.now().isoformat()
        
        with col2:
            report_status = st.selectbox(
                "ステータス",
                ["下書き", "レビュー待ち", "完了"],
                index=["draft", "review", "completed"].index(report['status'])
            )
            status_map = {"下書き": "draft", "レビュー待ち": "review", "完了": "completed"}
            if status_map[report_status] != report['status']:
                report['status'] = status_map[report_status]
                report['updated_at'] = datetime.now().isoformat()
        
        report_desc = st.text_area("レポートの説明", value=report.get('description', ''))
        if report_desc != report.get('description', ''):
            report['description'] = report_desc
            report['updated_at'] = datetime.now().isoformat()
        
        # セッション情報の表示
        if report['sessions']:
            st.markdown(f"**選択セッション**: {', '.join(report['sessions'])}")
        else:
            st.warning("分析対象のセッションが選択されていません。サイドバーでセッションを選択してください。")
        
        # テーマとレイアウト設定
        with st.expander("レポート設定", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                theme_options = {
                    "default": "デフォルト",
                    "professional": "プロフェッショナル",
                    "focused": "フォーカス",
                    "analytical": "分析"
                }
                
                theme_selection = st.selectbox(
                    "テーマ",
                    list(theme_options.values()),
                    index=list(theme_options.keys()).index(report['theme'])
                )
                
                theme_key = [k for k, v in theme_options.items() if v == theme_selection][0]
                if theme_key != report['theme']:
                    report['theme'] = theme_key
                    report['updated_at'] = datetime.now().isoformat()
            
            with col2:
                layout_options = {
                    "standard": "標準",
                    "detailed": "詳細",
                    "coaching": "コーチング",
                    "comparison": "比較分析"
                }
                
                layout_selection = st.selectbox(
                    "レイアウト",
                    list(layout_options.values()),
                    index=list(layout_options.keys()).index(report['layout'])
                )
                
                layout_key = [k for k, v in layout_options.items() if v == layout_selection][0]
                if layout_key != report['layout']:
                    report['layout'] = layout_key
                    report['updated_at'] = datetime.now().isoformat()
        
        # セクション編集
        st.markdown("---")
        st.subheader("レポートセクション")
        
        # セクションの並べ替え用に順序でソート
        sections = sorted(report['sections'], key=lambda x: x.get('order', 99))
        
        # 各セクションの表示と編集UI
        for i, section in enumerate(sections):
            with st.expander(f"{i+1}. {section['title']}", expanded=st.session_state.editing_section == section['id']):
                # セクション情報の表示
                section_title = st.text_input("セクションタイトル", value=section['title'], key=f"title_{section['id']}")
                if section_title != section['title']:
                    section['title'] = section_title
                    report['updated_at'] = datetime.now().isoformat()
                
                # セクションタイプの表示（読み取り専用）
                section_type_map = {
                    'summary': 'セッション概要',
                    'wind_analysis': '風向風速分析',
                    'wind_analysis_detailed': '風向風速詳細分析',
                    'performance': 'パフォーマンス指標',
                    'performance_detailed': 'パフォーマンス詳細分析',
                    'strategy_analysis': '戦略ポイント分析',
                    'recommendations': '改善提案',
                    'key_observations': '主要な観察事項',
                    'strategy_review': '戦略判断のレビュー',
                    'improvement_suggestions': '改善点と実践提案',
                    'next_steps': '次のステップ',
                    'sessions_overview': '比較セッション概要',
                    'performance_comparison': 'パフォーマンス比較',
                    'strategy_comparison': '戦略判断の比較',
                    'trends_analysis': '傾向分析',
                    'conclusion': '結論と提案',
                    'custom': 'カスタムセクション'
                }
                
                st.text_input(
                    "セクションタイプ",
                    value=section_type_map.get(section['type'], section['type']),
                    disabled=True,
                    key=f"type_{section['id']}"
                )
                
                # カスタム内容の編集（必要に応じて）
                if section.get('editable', True):
                    section_content = st.text_area(
                        "カスタム内容（オプション）",
                        value=section.get('content', ''),
                        height=150,
                        key=f"content_{section['id']}"
                    )
                    if section_content != section.get('content', ''):
                        section['content'] = section_content
                        report['updated_at'] = datetime.now().isoformat()
                
                # セクションのプレビュー
                if section['type'] == 'summary':
                    render_summary_section(section, report['sessions'])
                elif section['type'] == 'wind_analysis' or section['type'] == 'wind_analysis_detailed':
                    render_wind_analysis_section(section, report['sessions'], detailed=(section['type'] == 'wind_analysis_detailed'))
                elif section['type'] == 'performance' or section['type'] == 'performance_detailed':
                    render_performance_section(section, report['sessions'], detailed=(section['type'] == 'performance_detailed'))
                elif section['type'] == 'strategy_analysis':
                    render_strategy_section(section, report['sessions'])
                elif section['type'] == 'recommendations':
                    render_recommendations_section(section, report['sessions'])
                else:
                    st.info(f"「{section_type_map.get(section['type'], section['type'])}」セクションのプレビューは開発中です。")
                
                # セクション操作ボタン
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if i > 0 and st.button("上へ移動", key=f"move_up_{section['id']}"):
                        # 順序の入れ替え
                        sections[i]['order'], sections[i-1]['order'] = sections[i-1]['order'], sections[i]['order']
                        report['updated_at'] = datetime.now().isoformat()
                        st.experimental_rerun()
                
                with col2:
                    if i < len(sections) - 1 and st.button("下へ移動", key=f"move_down_{section['id']}"):
                        # 順序の入れ替え
                        sections[i]['order'], sections[i+1]['order'] = sections[i+1]['order'], sections[i]['order']
                        report['updated_at'] = datetime.now().isoformat()
                        st.experimental_rerun()
                
                with col3:
                    if section.get('removable', True) and st.button("セクションを削除", key=f"delete_{section['id']}"):
                        report['sections'].remove(section)
                        report['updated_at'] = datetime.now().isoformat()
                        st.experimental_rerun()
        
        # 新規セクション追加
        st.markdown("---")
        with st.expander("新規セクション追加", expanded=False):
            new_section_title = st.text_input("セクションタイトル", key="new_section_title")
            
            section_types = {
                'summary': 'セッション概要',
                'wind_analysis': '風向風速分析',
                'wind_analysis_detailed': '風向風速詳細分析',
                'performance': 'パフォーマンス指標',
                'performance_detailed': 'パフォーマンス詳細分析',
                'strategy_analysis': '戦略ポイント分析',
                'recommendations': '改善提案',
                'custom': 'カスタムセクション'
            }
            
            new_section_type = st.selectbox(
                "セクションタイプ",
                list(section_types.values()),
                key="new_section_type"
            )
            
            type_key = [k for k, v in section_types.items() if v == new_section_type][0]
            
            new_section_content = ""
            if type_key == 'custom':
                new_section_content = st.text_area("セクション内容", key="new_section_content")
            
            if st.button("セクションを追加", key="add_section_btn"):
                if not new_section_title:
                    st.error("セクションタイトルを入力してください")
                else:
                    # 新しいセクションの作成
                    max_order = max([s.get('order', 0) for s in sections], default=0)
                    new_section = {
                        'id': str(uuid.uuid4()),
                        'title': new_section_title,
                        'type': type_key,
                        'content': new_section_content,
                        'order': max_order + 1,
                        'editable': True,
                        'removable': True
                    }
                    
                    # レポートに追加
                    report['sections'].append(new_section)
                    report['updated_at'] = datetime.now().isoformat()
                    
                    # フォームをクリア
                    st.session_state.new_section_title = ""
                    st.session_state.new_section_content = ""
                    
                    st.success(f"新しいセクション「{new_section_title}」を追加しました")
                    st.experimental_rerun()
        
        # レポート操作ボタン
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("レポートのプレビュー", use_container_width=True):
                st.info("レポートのプレビュー機能は開発中です。")
        
        with col2:
            export_format = st.selectbox(
                "エクスポート形式",
                ["PDF", "HTML", "Markdown"],
                key="export_format"
            )
        
        with col3:
            if st.button("レポートのエクスポート", use_container_width=True):
                st.success(f"レポートを{export_format}形式でエクスポートします...")
                # 実際の実装では、レポートエクスポート機能を呼び出す
        
        with col4:
            if st.button("レポートの保存", use_container_width=True):
                # 実際の実装では、レポートをデータベースやファイルに保存
                st.success("レポートを保存しました")

# セクションプレビュー用の関数

def render_summary_section(section: Dict[str, Any], session_names: List[str]):
    """セッション概要セクションのプレビューをレンダリング"""
    st.markdown("##### セクションプレビュー")
    
    if not session_names:
        st.warning("セッションが選択されていません")
        return
    
    # セッション基本情報
    st.markdown("#### セッション基本情報")
    
    # サンプルデータ
    session_info = {
        "日時": "2025年3月27日 13:00-15:30",
        "場所": "江の島沖",
        "艇種": "470級",
        "風況": "南西 8-15kt",
        "天候": "晴れ、波高0.5m",
        "総距離": "15.2 km",
        "総時間": "2時間30分"
    }
    
    # 2列で表示
    col1, col2 = st.columns(2)
    
    for i, (key, value) in enumerate(session_info.items()):
        with col1 if i < len(session_info) // 2 + len(session_info) % 2 else col2:
            st.markdown(f"**{key}**: {value}")
    
    # 主要指標
    st.markdown("#### 主要指標")
    
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.metric(label="平均VMG (風上)", value="3.2 kt", delta="0.3 kt")
    with kpi_cols[1]:
        st.metric(label="平均VMG (風下)", value="4.5 kt", delta="-0.1 kt")
    with kpi_cols[2]:
        st.metric(label="タック効率", value="92%", delta="2%")
    with kpi_cols[3]:
        st.metric(label="風向変化対応", value="85%", delta="-5%")
    
    # カスタム内容（あれば）
    if section.get('content'):
        st.markdown("#### 追加メモ")
        st.markdown(section['content'])

def render_wind_analysis_section(section: Dict[str, Any], session_names: List[str], detailed: bool = False):
    """風向風速分析セクションのプレビューをレンダリング"""
    st.markdown("##### セクションプレビュー")
    
    if not session_names:
        st.warning("セッションが選択されていません")
        return
    
    # 風向風速の概要
    st.markdown("#### 風向風速の概要")
    
    # 基本風況情報
    wind_info = {
        "平均風向": "210°（南南西）",
        "平均風速": "12.3 kt",
        "最大風速": "18.5 kt",
        "最小風速": "8.2 kt",
        "風向変動幅": "±15°",
        "検出シフト回数": "5回"
    }
    
    # 2列で表示
    col1, col2 = st.columns(2)
    
    for i, (key, value) in enumerate(wind_info.items()):
        with col1 if i < len(wind_info) // 2 + len(wind_info) % 2 else col2:
            st.markdown(f"**{key}**: {value}")
    
    # 風向の時系列データをプロット（サンプル）
    st.markdown("#### 風向の時間変化")
    
    # サンプルデータの生成
    np.random.seed(42)
    dates = pd.date_range(start='2025-03-27 13:00', periods=100, freq='1min')
    
    # 風向データを生成（徐々に変化する傾向と短期的な変動を含む）
    # 基本的な傾向 - 時間とともに右に振れる
    trend = np.linspace(180, 220, 100)
    
    # 短期的な変動
    oscillations = np.cumsum(np.random.normal(0, 1, 100))  # ランダムウォークで変動を模倣
    oscillations = oscillations * 3 / np.max(np.abs(oscillations))  # 変動幅を調整
    
    # 風向データ
    wind_dir_data = (trend + oscillations) % 360
    
    # データフレーム作成
    wind_df = pd.DataFrame({
        '時間': dates,
        '風向 (度)': wind_dir_data
    })
    
    # プロット
    st.line_chart(wind_df.set_index('時間'))
    
    # 詳細モードの場合は追加情報
    if detailed:
        # 風向シフト検出結果
        st.markdown("#### 検出された風向シフト")
        
        # サンプルデータ
        shift_data = {
            "時間": ["13:15", "13:42", "14:10", "14:35", "15:05"],
            "シフト量": ["右 15°", "左 12°", "右 8°", "右 20°", "左 10°"],
            "シフト速度": ["緩やか", "急激", "緩やか", "緩やか", "急激"],
            "対応状況": ["良好", "遅延", "良好", "見逃し", "良好"]
        }
        
        st.dataframe(pd.DataFrame(shift_data))
        
        # 風速の時系列データをプロット（サンプル）
        st.markdown("#### 風速の時間変化")
        
        # 風速データを生成
        base_wind_speed = 12.0
        wind_speed_trend = np.concatenate([
            np.linspace(base_wind_speed, base_wind_speed + 3, 40),  # 徐々に強くなる
            np.linspace(base_wind_speed + 3, base_wind_speed - 1, 60)  # 徐々に弱くなる
        ])
        
        wind_speed_oscillations = np.sin(np.linspace(0, 5*np.pi, 100)) * 1.2  # 周期的な変動
        wind_speed_noise = np.random.normal(0, 0.5, 100)  # ランダムな変動
        
        wind_speed_data = wind_speed_trend + wind_speed_oscillations + wind_speed_noise
        wind_speed_data = np.maximum(wind_speed_data, 0)  # 負の風速を除外
        
        # データフレーム作成
        wind_speed_df = pd.DataFrame({
            '時間': dates,
            '風速 (kt)': wind_speed_data
        })
        
        # プロット
        st.line_chart(wind_speed_df.set_index('時間'))
    
    # カスタム内容（あれば）
    if section.get('content'):
        st.markdown("#### 追加メモ")
        st.markdown(section['content'])

def render_performance_section(section: Dict[str, Any], session_names: List[str], detailed: bool = False):
    """パフォーマンス指標セクションのプレビューをレンダリング"""
    st.markdown("##### セクションプレビュー")
    
    if not session_names:
        st.warning("セッションが選択されていません")
        return
    
    # パフォーマンス概要
    st.markdown("#### パフォーマンス概要")
    
    # パフォーマンス指標
    perf_cols = st.columns(4)
    
    with perf_cols[0]:
        st.metric(label="平均速度", value="6.2 kt", delta="0.2 kt")
    with perf_cols[1]:
        st.metric(label="最高速度", value="8.7 kt", delta=None)
    with perf_cols[2]:
        st.metric(label="風上VMG", value="3.2 kt", delta="0.3 kt")
    with perf_cols[3]:
        st.metric(label="風下VMG", value="4.5 kt", delta="-0.1 kt")
    
    # 速度分布ヒストグラム
    st.markdown("#### 速度分布")
    
    # サンプルデータの生成
    np.random.seed(42)
    speed_data = np.random.normal(6.2, 1.2, 500)  # 平均6.2ノット、標準偏差1.2のデータ
    speed_df = pd.DataFrame({'速度 (kt)': speed_data})
    
    # ヒストグラムとして表示
    hist_values, hist_bins = np.histogram(speed_data, bins=10, range=(2, 10))
    hist_df = pd.DataFrame({
        'ビン': [f"{bin:.1f}-{hist_bins[i+1]:.1f}" for i, bin in enumerate(hist_bins[:-1])],
        '頻度': hist_values
    })
    hist_df = hist_df.set_index('ビン')
    
    st.bar_chart(hist_df)
    
    # 詳細モードの場合は追加情報
    if detailed:
        # タック/ジャイブ効率
        st.markdown("#### マニューバー効率")
        
        maneuver_cols = st.columns(2)
        
        with maneuver_cols[0]:
            st.metric(label="タック平均効率", value="92%", delta="2%")
            st.metric(label="タック平均所要時間", value="7.6秒", delta="-0.4秒")
        
        with maneuver_cols[1]:
            st.metric(label="ジャイブ平均効率", value="86%", delta="-1%")
            st.metric(label="ジャイブ平均所要時間", value="9.3秒", delta="0.2秒")
        
        # マニューバーデータの詳細
        st.markdown("#### マニューバー詳細")
        
        # サンプルデータ
        maneuver_data = {
            "種類": ["タック", "タック", "ジャイブ", "タック", "ジャイブ"],
            "時間": ["13:20", "13:55", "14:15", "14:40", "15:10"],
            "所要時間": ["8秒", "7秒", "10秒", "9秒", "8秒"],
            "速度損失": ["0.8kt", "0.5kt", "1.2kt", "0.7kt", "0.9kt"],
            "評価": ["良好", "優秀", "改善必要", "良好", "良好"]
        }
        
        st.dataframe(pd.DataFrame(maneuver_data))
        
        # 極座標パフォーマンスプロット説明
        st.markdown("#### 極座標パフォーマンス")
        st.info("極座標パフォーマンス図を表示します。（フル実装では風向別の速度データを極座標で表示します）")
    
    # カスタム内容（あれば）
    if section.get('content'):
        st.markdown("#### 追加メモ")
        st.markdown(section['content'])

def render_strategy_section(section: Dict[str, Any], session_names: List[str]):
    """戦略ポイント分析セクションのプレビューをレンダリング"""
    st.markdown("##### セクションプレビュー")
    
    if not session_names:
        st.warning("セッションが選択されていません")
        return
    
    # 戦略ポイント概要
    st.markdown("#### 戦略ポイント概要")
    
    # 戦略ポイント指標
    strategy_cols = st.columns(3)
    
    with strategy_cols[0]:
        st.metric(label="検出ポイント数", value="8個", delta=None)
    with strategy_cols[1]:
        st.metric(label="最適判断率", value="62.5%", delta="5%")
    with strategy_cols[2]:
        st.metric(label="重要度高ポイント", value="4個", delta=None)
    
    # 戦略ポイント詳細
    st.markdown("#### 検出された戦略ポイント")
    
    # サンプルデータ
    strategy_data = {
        "時間": ["13:10", "13:38", "14:05", "14:32", "15:00", "15:15", "15:30", "15:42"],
        "タイプ": ["風向シフト対応", "レイライン接近", "風向シフト対応", "障害物回避", "コース変更", "タック", "レイライン接近", "風向シフト対応"],
        "判断": ["シフト前にタック", "レイラインでタック", "様子見", "早めの回避行動", "風上へのコース変更", "早めのタック", "レイラインでタック", "シフト後にタック"],
        "結果": ["レグ短縮", "オーバースタンド", "不利なレイヤー", "ロス最小化", "有利なレイヤー獲得", "風速域改善", "コース短縮", "方位角改善"],
        "重要度": ["高", "中", "高", "低", "中", "中", "高", "高"],
        "評価": ["最適", "改善必要", "不適切", "適切", "最適", "適切", "最適", "改善必要"]
    }
    
    st.dataframe(pd.DataFrame(strategy_data))
    
    # 意思決定の効果
    st.markdown("#### 戦略判断の効果")
    
    decision_cols = st.columns(2)
    
    with decision_cols[0]:
        st.markdown("##### 風向変化への対応速度")
        # サンプルデータのバーチャート
        response_data = pd.DataFrame({'対応速度 (%)': [85, 70, 95, 60, 90]})
        st.bar_chart(response_data)
        
    with decision_cols[1]:
        st.markdown("##### 戦略効果（推定利得）")
        # サンプルデータ
        effect_data = {
            "戦略": ["早めのタック", "レイヤー選択", "周囲艇観察", "風予測に基づく展開"],
            "効果 (推定利得)": ["+45秒", "+30秒", "+15秒", "+60秒"]
        }
        st.dataframe(pd.DataFrame(effect_data))
    
    # カスタム内容（あれば）
    if section.get('content'):
        st.markdown("#### 追加メモ")
        st.markdown(section['content'])

def render_recommendations_section(section: Dict[str, Any], session_names: List[str]):
    """改善提案セクションのプレビューをレンダリング"""
    st.markdown("##### セクションプレビュー")
    
    if not session_names:
        st.warning("セッションが選択されていません")
        return
    
    # 改善提案
    st.markdown("#### 分析に基づく改善提案")
    
    # サンプルデータまたはカスタム内容
    recommendations = section.get('content', """
    1. **風向シフトの予測と対応**：右シフトパターンをより早く察知し、事前対応することで約30秒の利得が期待できます。
    
    2. **タック実行の判断**：オーバースタンドが2回観測されました。レイライン接近時の判断を改善してください。
    
    3. **風下での艇速**：風下走行時の艇速が理想値を10%下回っています。セールトリムの調整を検討してください。
    
    4. **マニューバー効率**：特にジャイブの効率が低下しています。風下帆走時のジャイブ技術の向上と練習を推奨します。
    
    5. **風予測の利用**：セーリング時に風向変化パターンの予測と活用の強化を提案します。雲の動きや波のパターンなど、風の変化を予測する視覚的手がかりに注目してください。
    """)
    
    st.markdown(recommendations)

if __name__ == "__main__":
    render_page()
