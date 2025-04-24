# -*- coding: utf-8 -*-
"""
ui.integrated.components.dashboard.widget_manager

ダッシュボードウィジェットの管理システム
ウィジェットの登録、配置、設定保存などを担当
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from typing import Dict, Any, List, Optional, Type, Tuple
from datetime import datetime
import importlib
import inspect
import uuid

# ウィジェットのインポート
from .widgets.base_widget import BaseWidget
from .widgets.wind_summary_widget import WindSummaryWidget
from .widgets.performance_widget import PerformanceWidget
from .widgets.strategy_points_widget import StrategyPointsWidget
from .widgets.data_quality_widget import DataQualityWidget


class WidgetManager:
    """
    ダッシュボードウィジェットの管理クラス
    
    ウィジェットの追加、削除、レイアウト管理、設定保存などを担当します。
    """
    
    def __init__(self):
        """
        ウィジェットマネージャーの初期化
        """
        # セッション状態の初期化
        if 'dashboard_widgets' not in st.session_state:
            st.session_state.dashboard_widgets = {}
            
        if 'dashboard_layouts' not in st.session_state:
            st.session_state.dashboard_layouts = {}
            
        if 'active_layout' not in st.session_state:
            st.session_state.active_layout = 'default'
        
        # 利用可能なウィジェットクラスの登録
        self.widget_classes = {
            'WindSummaryWidget': WindSummaryWidget,
            'PerformanceWidget': PerformanceWidget,
            'StrategyPointsWidget': StrategyPointsWidget,
            'DataQualityWidget': DataQualityWidget
        }
        
        # デフォルトレイアウトの初期化
        self._initialize_default_layouts()
    
    def _initialize_default_layouts(self) -> None:
        """
        デフォルトレイアウトの初期化
        """
        if 'default' not in st.session_state.dashboard_layouts:
            default_layout = {
                'name': 'デフォルト',
                'description': '標準ダッシュボードレイアウト',
                'grid_cols': 3,
                'grid_rows': 3,
                'widgets': {
                    'wind_summary': {
                        'type': 'WindSummaryWidget',
                        'position': {'col': 0, 'row': 0},
                        'size': {'width': 2, 'height': 2},
                        'config': {}
                    },
                    'performance': {
                        'type': 'PerformanceWidget',
                        'position': {'col': 2, 'row': 0},
                        'size': {'width': 1, 'height': 1},
                        'config': {}
                    },
                    'strategy_points': {
                        'type': 'StrategyPointsWidget',
                        'position': {'col': 2, 'row': 1},
                        'size': {'width': 1, 'height': 1},
                        'config': {}
                    },
                    'data_quality': {
                        'type': 'DataQualityWidget',
                        'position': {'col': 0, 'row': 2},
                        'size': {'width': 3, 'height': 1},
                        'config': {}
                    }
                }
            }
            st.session_state.dashboard_layouts['default'] = default_layout
        
        if 'wind_focus' not in st.session_state.dashboard_layouts:
            wind_focus_layout = {
                'name': '風向分析フォーカス',
                'description': '風向・風速分析に特化したレイアウト',
                'grid_cols': 3,
                'grid_rows': 3,
                'widgets': {
                    'wind_summary_1': {
                        'type': 'WindSummaryWidget',
                        'position': {'col': 0, 'row': 0},
                        'size': {'width': 3, 'height': 2},
                        'config': {'plot_type': 'polar'}
                    },
                    'wind_summary_2': {
                        'type': 'WindSummaryWidget',
                        'position': {'col': 0, 'row': 2},
                        'size': {'width': 3, 'height': 1},
                        'config': {'plot_type': 'time_series'}
                    }
                }
            }
            st.session_state.dashboard_layouts['wind_focus'] = wind_focus_layout
        
        if 'performance_focus' not in st.session_state.dashboard_layouts:
            performance_focus_layout = {
                'name': 'パフォーマンスフォーカス',
                'description': 'パフォーマンス分析に特化したレイアウト',
                'grid_cols': 3,
                'grid_rows': 3,
                'widgets': {
                    'performance_1': {
                        'type': 'PerformanceWidget',
                        'position': {'col': 0, 'row': 0},
                        'size': {'width': 2, 'height': 2},
                        'config': {}
                    },
                    'wind_summary': {
                        'type': 'WindSummaryWidget',
                        'position': {'col': 2, 'row': 0},
                        'size': {'width': 1, 'height': 1},
                        'config': {'plot_type': 'polar'}
                    },
                    'strategy_points': {
                        'type': 'StrategyPointsWidget',
                        'position': {'col': 2, 'row': 1},
                        'size': {'width': 1, 'height': 1},
                        'config': {}
                    },
                    'data_quality': {
                        'type': 'DataQualityWidget',
                        'position': {'col': 0, 'row': 2},
                        'size': {'width': 3, 'height': 1},
                        'config': {}
                    }
                }
            }
            st.session_state.dashboard_layouts['performance_focus'] = performance_focus_layout
    
    def get_available_widgets(self) -> List[Dict[str, Any]]:
        """
        利用可能なウィジェットのリストを取得
        
        Returns:
            利用可能なウィジェットのリスト
        """
        widgets = []
        for widget_class in self.widget_classes.values():
            widget_info = widget_class.get_widget_info()
            widgets.append(widget_info)
        return widgets
    
    def get_available_layouts(self) -> List[Dict[str, Any]]:
        """
        利用可能なレイアウトのリストを取得
        
        Returns:
            利用可能なレイアウトのリスト
        """
        layouts = []
        for layout_id, layout in st.session_state.dashboard_layouts.items():
            layouts.append({
                'id': layout_id,
                'name': layout['name'],
                'description': layout['description']
            })
        return layouts
    
    def create_widget(self, widget_type: str, widget_id: str = None, title: str = None, 
                     description: str = None, config: Dict[str, Any] = None) -> Optional[BaseWidget]:
        """
        新しいウィジェットを作成
        
        Args:
            widget_type: ウィジェットのタイプ
            widget_id: ウィジェットID（省略時は自動生成）
            title: ウィジェットのタイトル（省略時はデフォルト）
            description: ウィジェットの説明（省略時はデフォルト）
            config: ウィジェットの構成（省略時はデフォルト）
        
        Returns:
            作成されたウィジェットオブジェクト、または失敗時はNone
        """
        if widget_type not in self.widget_classes:
            st.error(f"不明なウィジェットタイプ: {widget_type}")
            return None
        
        # ウィジェットIDを生成または検証
        if widget_id is None:
            widget_id = f"{widget_type.lower()}_{uuid.uuid4().hex[:8]}"
        elif widget_id in st.session_state.dashboard_widgets:
            st.warning(f"ウィジェットID '{widget_id}' は既に使用されています。別のIDを生成します。")
            widget_id = f"{widget_type.lower()}_{uuid.uuid4().hex[:8]}"
        
        # ウィジェットインスタンスを作成
        try:
            widget_class = self.widget_classes[widget_type]
            widget = widget_class(
                widget_id=widget_id,
                title=title or f"新規 {widget_type}",
                description=description or "",
                config=config or {}
            )
            
            # セッションに保存
            st.session_state.dashboard_widgets[widget_id] = widget
            return widget
        
        except Exception as e:
            st.error(f"ウィジェットの作成に失敗しました: {str(e)}")
            return None
    
    def add_widget_to_layout(self, layout_id: str, widget_id: str, 
                           position: Dict[str, int], size: Dict[str, int]) -> bool:
        """
        ウィジェットをレイアウトに追加
        
        Args:
            layout_id: レイアウトID
            widget_id: ウィジェットID
            position: ウィジェットの位置 {'col': x, 'row': y}
            size: ウィジェットのサイズ {'width': w, 'height': h}
        
        Returns:
            成功したかどうか
        """
        if layout_id not in st.session_state.dashboard_layouts:
            st.error(f"不明なレイアウトID: {layout_id}")
            return False
        
        if widget_id not in st.session_state.dashboard_widgets:
            st.error(f"不明なウィジェットID: {widget_id}")
            return False
        
        # ウィジェットの情報を取得
        widget = st.session_state.dashboard_widgets[widget_id]
        
        # レイアウトにウィジェットを追加
        layout = st.session_state.dashboard_layouts[layout_id]
        layout['widgets'][widget_id] = {
            'type': widget.__class__.__name__,
            'position': position,
            'size': size,
            'config': widget.config
        }
        
        return True
    
    def remove_widget_from_layout(self, layout_id: str, widget_id: str) -> bool:
        """
        レイアウトからウィジェットを削除
        
        Args:
            layout_id: レイアウトID
            widget_id: ウィジェットID
        
        Returns:
            成功したかどうか
        """
        if layout_id not in st.session_state.dashboard_layouts:
            st.error(f"不明なレイアウトID: {layout_id}")
            return False
        
        layout = st.session_state.dashboard_layouts[layout_id]
        
        if widget_id in layout['widgets']:
            del layout['widgets'][widget_id]
            return True
        else:
            st.warning(f"ウィジェット '{widget_id}' はレイアウト '{layout_id}' に存在しません")
            return False
    
    def delete_widget(self, widget_id: str) -> bool:
        """
        ウィジェットを完全に削除
        
        Args:
            widget_id: ウィジェットID
        
        Returns:
            成功したかどうか
        """
        if widget_id not in st.session_state.dashboard_widgets:
            st.warning(f"ウィジェット '{widget_id}' は存在しません")
            return False
        
        # 関連するレイアウトからウィジェットを削除
        for layout_id in st.session_state.dashboard_layouts:
            layout = st.session_state.dashboard_layouts[layout_id]
            if widget_id in layout['widgets']:
                del layout['widgets'][widget_id]
        
        # ウィジェット自体を削除
        del st.session_state.dashboard_widgets[widget_id]
        return True
    
    def create_layout(self, name: str, description: str = "", 
                    grid_cols: int = 3, grid_rows: int = 3) -> str:
        """
        新しいレイアウトを作成
        
        Args:
            name: レイアウト名
            description: レイアウトの説明
            grid_cols: グリッドの列数
            grid_rows: グリッドの行数
        
        Returns:
            作成されたレイアウトのID
        """
        layout_id = name.lower().replace(" ", "_")
        
        # IDが既に存在する場合、ユニークなIDを生成
        if layout_id in st.session_state.dashboard_layouts:
            layout_id = f"{layout_id}_{uuid.uuid4().hex[:8]}"
        
        # 新しいレイアウトを作成
        layout = {
            'name': name,
            'description': description,
            'grid_cols': grid_cols,
            'grid_rows': grid_rows,
            'widgets': {}
        }
        
        # レイアウトを保存
        st.session_state.dashboard_layouts[layout_id] = layout
        
        return layout_id
    
    def delete_layout(self, layout_id: str) -> bool:
        """
        レイアウトを削除
        
        Args:
            layout_id: レイアウトID
        
        Returns:
            成功したかどうか
        """
        if layout_id not in st.session_state.dashboard_layouts:
            st.warning(f"レイアウト '{layout_id}' は存在しません")
            return False
        
        # デフォルトレイアウトは削除不可
        if layout_id == 'default':
            st.error("デフォルトレイアウトは削除できません")
            return False
        
        # アクティブレイアウトの場合は別のレイアウトに切り替え
        if st.session_state.active_layout == layout_id:
            st.session_state.active_layout = 'default'
        
        # レイアウトを削除
        del st.session_state.dashboard_layouts[layout_id]
        
        return True
    
    def load_layout(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """
        レイアウトを読み込む
        
        Args:
            layout_id: レイアウトID
        
        Returns:
            レイアウト定義、または失敗時はNone
        """
        if layout_id not in st.session_state.dashboard_layouts:
            st.error(f"不明なレイアウトID: {layout_id}")
            return None
        
        return st.session_state.dashboard_layouts[layout_id]
    
    def set_active_layout(self, layout_id: str) -> bool:
        """
        アクティブなレイアウトを設定
        
        Args:
            layout_id: レイアウトID
        
        Returns:
            成功したかどうか
        """
        if layout_id not in st.session_state.dashboard_layouts:
            st.error(f"不明なレイアウトID: {layout_id}")
            return False
        
        st.session_state.active_layout = layout_id
        return True
    
    def get_active_layout(self) -> Optional[Dict[str, Any]]:
        """
        現在アクティブなレイアウトを取得
        
        Returns:
            アクティブなレイアウト定義、または失敗時はNone
        """
        layout_id = st.session_state.active_layout
        if layout_id not in st.session_state.dashboard_layouts:
            st.session_state.active_layout = 'default'
            layout_id = 'default'
        
        return st.session_state.dashboard_layouts[layout_id]
    
    def render_dashboard(self, session_data: Dict[str, Any] = None) -> None:
        """
        ダッシュボードを描画
        
        Args:
            session_data: 分析セッションのデータ
        """
        # アクティブなレイアウトを取得
        layout = self.get_active_layout()
        if not layout:
            st.error("ダッシュボードレイアウトが読み込めませんでした。")
            return
        
        # 編集モードの確認
        edit_mode = st.session_state.get('dashboard_edit_mode', False)
        
        # グリッド設定
        grid_cols = layout.get('grid_cols', 3)
        grid_rows = layout.get('grid_rows', 3)
        
        # 編集モード時のコントロールを表示
        if edit_mode:
            st.markdown("""
            <style>
            .widget-container {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
                position: relative;
            }
            .widget-controls {
                position: absolute;
                top: 5px;
                right: 5px;
                background: rgba(255, 255, 255, 0.8);
                padding: 3px;
                border-radius: 3px;
                font-size: 0.8em;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("#### ダッシュボード編集モード")
            st.markdown("ウィジェットの配置を編集できます。ウィジェットをドラッグ＆ドロップで移動するか、各ウィジェットの編集ボタンを使用してください。")
        
        # グリッドごとにウィジェットを配置
        for row in range(grid_rows):
            cols = st.columns(grid_cols)
            
            for col in range(grid_cols):
                # 配置位置に対応するウィジェットを検索
                widget_id = None
                widget_config = None
                
                for w_id, w_info in layout['widgets'].items():
                    if w_info['position']['row'] == row and w_info['position']['col'] == col:
                        widget_id = w_id
                        widget_config = w_info
                        break
                
                if widget_id and widget_config:
                    # ウィジェットのサイズを取得
                    widget_width = min(widget_config['size']['width'], grid_cols - col)
                    
                    # 複数列にまたがるウィジェットの場合、最初の列にのみ描画
                    if widget_width > 1:
                        with st.container():
                            # 編集モードの場合、ウィジェットコンテナにスタイルを適用
                            if edit_mode:
                                st.markdown(f'<div class="widget-container" id="widget-{widget_id}">', unsafe_allow_html=True)
                                # 編集用コントロールを表示
                                self._render_widget_controls(widget_id, row, col)
                            
                            # 実際のウィジェットを描画
                            self._render_widget(widget_id, widget_config, session_data)
                            
                            if edit_mode:
                                st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        with cols[col]:
                            # 編集モードの場合、ウィジェットコンテナにスタイルを適用
                            if edit_mode:
                                st.markdown(f'<div class="widget-container" id="widget-{widget_id}">', unsafe_allow_html=True)
                                # 編集用コントロールを表示
                                self._render_widget_controls(widget_id, row, col)
                            
                            # 実際のウィジェットを描画
                            self._render_widget(widget_id, widget_config, session_data)
                            
                            if edit_mode:
                                st.markdown('</div>', unsafe_allow_html=True)
                # 空のセルには、編集モード時にプレースホルダーを表示
                elif edit_mode:
                    with cols[col]:
                        st.markdown(
                            f'<div class="widget-container" style="min-height: 100px; display: flex; align-items: center; justify-content: center;">'
                            f'<div style="color: #aaaaaa;">ここにウィジェットをドロップ</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        # 空セルへのウィジェット追加ボタン
                        if st.button(f"追加 ({row},{col})", key=f"add_{row}_{col}"):
                            st.session_state.add_widget_position = (row, col)
                            st.session_state.show_widget_selector = True
                            st.experimental_rerun()
    
    def _render_widget_controls(self, widget_id: str, row: int, col: int) -> None:
        """
        ウィジェット編集用コントロールを描画
        
        Args:
            widget_id: ウィジェットID
            row: 行位置
            col: 列位置
        """
        # コントロールスタイルをHTML/CSSで表現
        st.markdown(
            f'<div class="widget-controls">'
            f'<span title="移動" style="cursor: pointer; margin-right: 5px;">⬍</span>'
            f'<span title="編集" style="cursor: pointer; margin-right: 5px;">✏️</span>'
            f'<span title="削除" style="cursor: pointer; color: #ff0000;">✕</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # 実際の実装では、JavaScriptのイベントハンドラを追加してドラッグ＆ドロップを実現
        # Streamlitでは直接JavaScriptは実行できないため、ボタンでエミュレート
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("移動", key=f"move_{widget_id}"):
                st.session_state.move_widget_id = widget_id
                st.session_state.show_move_dialog = True
                
        with col2:
            if st.button("編集", key=f"edit_{widget_id}"):
                st.session_state.edit_widget_id = widget_id
                st.session_state.show_edit_dialog = True
                
        with col3:
            if st.button("削除", key=f"delete_{widget_id}"):
                # 確認ダイアログは実装の制約上省略
                self.delete_widget(widget_id)
                st.experimental_rerun()
    
    def _render_widget(self, widget_id: str, widget_config: Dict[str, Any], 
                      session_data: Dict[str, Any] = None) -> None:
        """
        個別のウィジェットを描画
        
        Args:
            widget_id: ウィジェットID
            widget_config: ウィジェット設定
            session_data: セッションデータ
        """
        # ウィジェットのタイプを取得
        widget_type = widget_config['type']
        
        # 既存のウィジェットインスタンスを取得、なければ作成
        if widget_id in st.session_state.dashboard_widgets:
            widget = st.session_state.dashboard_widgets[widget_id]
        else:
            # ウィジェットが存在しない場合、新規作成を試みる
            if widget_type in self.widget_classes:
                widget = self.create_widget(
                    widget_type=widget_type,
                    widget_id=widget_id,
                    config=widget_config.get('config', {})
                )
                if not widget:
                    st.error(f"ウィジェット '{widget_id}' の作成に失敗しました")
                    return
            else:
                st.error(f"不明なウィジェットタイプ: {widget_type}")
                return
        
        # ウィジェットを描画
        with st.container():
            widget.render(session_data)
    
    def save_layouts_to_file(self, file_path: str) -> bool:
        """
        レイアウト設定をJSONファイルに保存
        
        Args:
            file_path: 保存先ファイルパス
        
        Returns:
            成功したかどうか
        """
        try:
            # レイアウト情報をシリアライズ
            layouts_data = {}
            for layout_id, layout in st.session_state.dashboard_layouts.items():
                layouts_data[layout_id] = layout
            
            # JSONファイルに保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(layouts_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            st.error(f"レイアウト設定の保存に失敗しました: {str(e)}")
            return False
    
    def load_layouts_from_file(self, file_path: str) -> bool:
        """
        レイアウト設定をJSONファイルから読み込み
        
        Args:
            file_path: 読み込むファイルパス
        
        Returns:
            成功したかどうか
        """
        try:
            # JSONファイルから読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                layouts_data = json.load(f)
            
            # レイアウト情報を復元
            for layout_id, layout in layouts_data.items():
                st.session_state.dashboard_layouts[layout_id] = layout
            
            return True
        
        except Exception as e:
            st.error(f"レイアウト設定の読み込みに失敗しました: {str(e)}")
            return False

    def export_dashboard_config(self) -> Dict[str, Any]:
        """
        ダッシュボード設定をエクスポート
        
        Returns:
            ダッシュボード設定
        """
        return {
            'layouts': st.session_state.dashboard_layouts,
            'active_layout': st.session_state.active_layout,
        }
    
    def import_dashboard_config(self, config: Dict[str, Any]) -> bool:
        """
        ダッシュボード設定をインポート
        
        Args:
            config: ダッシュボード設定
        
        Returns:
            成功したかどうか
        """
        try:
            if 'layouts' in config:
                st.session_state.dashboard_layouts = config['layouts']
            
            if 'active_layout' in config:
                layout_id = config['active_layout']
                if layout_id in st.session_state.dashboard_layouts:
                    st.session_state.active_layout = layout_id
                else:
                    st.session_state.active_layout = 'default'
            
            return True
        
        except Exception as e:
            st.error(f"ダッシュボード設定のインポートに失敗しました: {str(e)}")
            return False
