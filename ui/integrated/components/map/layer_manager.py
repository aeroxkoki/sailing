# -*- coding: utf-8 -*-
"""
ui.integrated.components.map.layer_manager

インタラクティブマップのレイヤーを管理するクラス
"""

import streamlit as st
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class LayerManager:
    """マップレイヤーを管理するクラス"""
    
    def __init__(self):
        """レイヤーマネージャーを初期化"""
        # セッション状態の初期化
        if 'map_layer_registry' not in st.session_state:
            st.session_state.map_layer_registry = {}
        
        if 'map_layer_configs' not in st.session_state:
            st.session_state.map_layer_configs = {
                'default': {
                    'name': 'デフォルト',
                    'description': '標準的なマップレイヤー設定',
                    'created_at': datetime.now().isoformat(),
                    'layers': {
                        'gps_track': {
                            'visible': True, 
                            'opacity': 0.8, 
                            'z_index': 1,
                            'color': '#FF5733',
                            'weight': 3
                        },
                        'wind_direction': {
                            'visible': True, 
                            'opacity': 0.7, 
                            'z_index': 2,
                            'color': 'blue',
                            'arrow_size': 5
                        },
                        'strategy_points': {
                            'visible': True, 
                            'opacity': 1.0, 
                            'z_index': 3,
                            'cluster': True
                        },
                        'wind_field': {
                            'visible': False, 
                            'opacity': 0.5, 
                            'z_index': 0,
                            'style': 'heatmap'
                        },
                        'tack_points': {
                            'visible': False, 
                            'opacity': 0.8, 
                            'z_index': 2,
                            'color': 'green',
                            'radius': 8
                        },
                        'laylines': {
                            'visible': False, 
                            'opacity': 0.7, 
                            'z_index': 1,
                            'starboard_color': 'purple',
                            'port_color': 'blue',
                            'weight': 2
                        },
                        'vmg_heatmap': {
                            'visible': False, 
                            'opacity': 0.6, 
                            'z_index': 0,
                            'radius': 12
                        },
                        'speed_heatmap': {
                            'visible': False, 
                            'opacity': 0.6, 
                            'z_index': 0,
                            'radius': 12
                        }
                    }
                },
                'wind_analysis': {
                    'name': '風向分析',
                    'description': '風向と風速の分析に特化した設定',
                    'created_at': datetime.now().isoformat(),
                    'layers': {
                        'gps_track': {
                            'visible': True, 
                            'opacity': 0.4, 
                            'z_index': 0,
                            'color': '#FF5733',
                            'weight': 2
                        },
                        'wind_direction': {
                            'visible': True, 
                            'opacity': 0.9, 
                            'z_index': 2,
                            'color': 'blue',
                            'arrow_size': 7
                        },
                        'strategy_points': {
                            'visible': False, 
                            'opacity': 1.0, 
                            'z_index': 3,
                            'cluster': False
                        },
                        'wind_field': {
                            'visible': True, 
                            'opacity': 0.7, 
                            'z_index': 1,
                            'style': 'heatmap'
                        },
                        'tack_points': {
                            'visible': False, 
                            'opacity': 0.8, 
                            'z_index': 2,
                            'color': 'green',
                            'radius': 8
                        },
                        'laylines': {
                            'visible': False, 
                            'opacity': 0.7, 
                            'z_index': 1,
                            'starboard_color': 'purple',
                            'port_color': 'blue',
                            'weight': 2
                        },
                        'vmg_heatmap': {
                            'visible': False, 
                            'opacity': 0.6, 
                            'z_index': 0,
                            'radius': 12
                        },
                        'speed_heatmap': {
                            'visible': False, 
                            'opacity': 0.6, 
                            'z_index': 0,
                            'radius': 12
                        }
                    }
                },
                'strategy_focus': {
                    'name': '戦略ポイント分析',
                    'description': '戦略的判断ポイントに焦点を当てた設定',
                    'created_at': datetime.now().isoformat(),
                    'layers': {
                        'gps_track': {
                            'visible': True, 
                            'opacity': 0.7, 
                            'z_index': 1,
                            'color': '#FF5733',
                            'weight': 3
                        },
                        'wind_direction': {
                            'visible': False, 
                            'opacity': 0.5, 
                            'z_index': 0,
                            'color': 'blue',
                            'arrow_size': 4
                        },
                        'strategy_points': {
                            'visible': True, 
                            'opacity': 1.0, 
                            'z_index': 3,
                            'cluster': True
                        },
                        'wind_field': {
                            'visible': False, 
                            'opacity': 0.4, 
                            'z_index': 0,
                            'style': 'heatmap'
                        },
                        'tack_points': {
                            'visible': True, 
                            'opacity': 0.9, 
                            'z_index': 2,
                            'color': 'green',
                            'radius': 8
                        },
                        'laylines': {
                            'visible': True, 
                            'opacity': 0.8, 
                            'z_index': 1,
                            'starboard_color': 'purple',
                            'port_color': 'blue',
                            'weight': 2
                        },
                        'vmg_heatmap': {
                            'visible': False, 
                            'opacity': 0.6, 
                            'z_index': 0,
                            'radius': 12
                        },
                        'speed_heatmap': {
                            'visible': False, 
                            'opacity': 0.6, 
                            'z_index': 0,
                            'radius': 12
                        }
                    }
                },
                'performance_analysis': {
                    'name': 'パフォーマンス分析',
                    'description': '速度とVMGの分析に特化した設定',
                    'created_at': datetime.now().isoformat(),
                    'layers': {
                        'gps_track': {
                            'visible': True, 
                            'opacity': 0.8, 
                            'z_index': 1,
                            'color': '#FF5733',
                            'weight': 3
                        },
                        'wind_direction': {
                            'visible': True, 
                            'opacity': 0.6, 
                            'z_index': 1,
                            'color': 'blue',
                            'arrow_size': 5
                        },
                        'strategy_points': {
                            'visible': False, 
                            'opacity': 0.7, 
                            'z_index': 2,
                            'cluster': True
                        },
                        'wind_field': {
                            'visible': False, 
                            'opacity': 0.4, 
                            'z_index': 0,
                            'style': 'heatmap'
                        },
                        'tack_points': {
                            'visible': True, 
                            'opacity': 0.8, 
                            'z_index': 2,
                            'color': 'orange',
                            'radius': 8
                        },
                        'laylines': {
                            'visible': False, 
                            'opacity': 0.7, 
                            'z_index': 1,
                            'starboard_color': 'purple',
                            'port_color': 'blue',
                            'weight': 2
                        },
                        'vmg_heatmap': {
                            'visible': True, 
                            'opacity': 0.7, 
                            'z_index': 0,
                            'radius': 15
                        },
                        'speed_heatmap': {
                            'visible': True, 
                            'opacity': 0.7, 
                            'z_index': 0,
                            'radius': 15
                        }
                    }
                }
            }
        
        # レイヤータイプの登録
        self._register_layer_types()
    
    def _register_layer_types(self):
        """利用可能なレイヤータイプを登録"""
        layer_types = {
            'gps_track': {
                'name': 'GPSトラック',
                'description': 'GPSトラックの表示',
                'properties': [
                    {'name': 'color', 'type': 'color', 'default': '#FF5733', 'label': '色'},
                    {'name': 'weight', 'type': 'slider', 'min': 1, 'max': 10, 'default': 3, 'label': '太さ'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.8, 'label': '透明度'},
                    {'name': 'dash_array', 'type': 'text', 'default': '', 'label': '破線パターン'}
                ]
            },
            'wind_direction': {
                'name': '風向ベクトル',
                'description': '風向と風速を矢印で表示',
                'properties': [
                    {'name': 'color', 'type': 'color', 'default': 'blue', 'label': '色'},
                    {'name': 'arrow_size', 'type': 'slider', 'min': 3, 'max': 15, 'default': 5, 'label': '矢印サイズ'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.7, 'label': '透明度'},
                    {'name': 'resolution', 'type': 'select', 'options': ['低', '中', '高'], 'default': '中', 'label': '解像度'}
                ]
            },
            'wind_field': {
                'name': '風向場',
                'description': '風向場をヒートマップで表示',
                'properties': [
                    {'name': 'style', 'type': 'select', 'options': ['heatmap', 'vector', 'contour'], 'default': 'heatmap', 'label': '表示スタイル'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.6, 'label': '透明度'},
                    {'name': 'resolution', 'type': 'select', 'options': ['低', '中', '高'], 'default': '中', 'label': '解像度'},
                    {'name': 'color_scale', 'type': 'select', 'options': ['青-赤', '緑-赤', 'モノクロ'], 'default': '青-赤', 'label': 'カラースケール'}
                ]
            },
            'strategy_points': {
                'name': '戦略ポイント',
                'description': '重要な戦略的判断ポイントを表示',
                'properties': [
                    {'name': 'cluster', 'type': 'checkbox', 'default': True, 'label': 'クラスタリング'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 1.0, 'label': '透明度'},
                    {'name': 'filter_types', 'type': 'multiselect', 'options': ['タック', 'ジャイブ', '風向シフト', 'レイライン', '障害物回避', 'コース変更'], 'default': [], 'label': 'タイプフィルター'},
                    {'name': 'filter_importance', 'type': 'select', 'options': ['すべて', '低', '中', '高', '最高'], 'default': 'すべて', 'label': '重要度フィルター'}
                ]
            },
            'tack_points': {
                'name': 'タックポイント',
                'description': 'タックとジャイブのポイントを表示',
                'properties': [
                    {'name': 'color', 'type': 'color', 'default': 'green', 'label': '色'},
                    {'name': 'radius', 'type': 'slider', 'min': 3, 'max': 15, 'default': 8, 'label': 'サイズ'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.8, 'label': '透明度'},
                    {'name': 'show_labels', 'type': 'checkbox', 'default': False, 'label': 'ラベル表示'}
                ]
            },
            'laylines': {
                'name': 'レイライン',
                'description': 'レイラインを表示',
                'properties': [
                    {'name': 'starboard_color', 'type': 'color', 'default': 'purple', 'label': 'スターボード色'},
                    {'name': 'port_color', 'type': 'color', 'default': 'blue', 'label': 'ポート色'},
                    {'name': 'weight', 'type': 'slider', 'min': 1, 'max': 5, 'default': 2, 'label': '太さ'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.7, 'label': '透明度'},
                    {'name': 'dash_array', 'type': 'text', 'default': '5, 10', 'label': '破線パターン'}
                ]
            },
            'vmg_heatmap': {
                'name': 'VMGヒートマップ',
                'description': 'VMG（対風速度）の分布をヒートマップで表示',
                'properties': [
                    {'name': 'radius', 'type': 'slider', 'min': 5, 'max': 30, 'default': 12, 'label': '半径'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.6, 'label': '透明度'},
                    {'name': 'blur', 'type': 'slider', 'min': 0, 'max': 20, 'default': 10, 'label': 'ぼかし'},
                    {'name': 'gradient', 'type': 'select', 'options': ['青-赤', '緑-赤', 'モノクロ'], 'default': '青-赤', 'label': 'グラデーション'}
                ]
            },
            'speed_heatmap': {
                'name': '速度ヒートマップ',
                'description': '速度の分布をヒートマップで表示',
                'properties': [
                    {'name': 'radius', 'type': 'slider', 'min': 5, 'max': 30, 'default': 12, 'label': '半径'},
                    {'name': 'opacity', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 0.6, 'label': '透明度'},
                    {'name': 'blur', 'type': 'slider', 'min': 0, 'max': 20, 'default': 10, 'label': 'ぼかし'},
                    {'name': 'gradient', 'type': 'select', 'options': ['青-赤', '緑-赤', 'モノクロ'], 'default': '青-赤', 'label': 'グラデーション'}
                ]
            }
        }
        
        # セッション状態に登録
        st.session_state.map_layer_registry = layer_types
    
    def get_available_layer_types(self) -> Dict[str, Dict[str, Any]]:
        """利用可能なレイヤータイプを取得
        
        Returns:
            レイヤータイプの辞書
        """
        return st.session_state.map_layer_registry
    
    def get_layer_config(self, config_name: str = 'default') -> Dict[str, Any]:
        """指定された名前のレイヤー設定を取得
        
        Args:
            config_name: 設定名
            
        Returns:
            レイヤー設定の辞書
        """
        # 指定された設定が存在しない場合はデフォルトを返す
        if config_name not in st.session_state.map_layer_configs:
            return st.session_state.map_layer_configs.get('default', {})
        return st.session_state.map_layer_configs[config_name]
    
    def save_layer_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """レイヤー設定を保存
        
        Args:
            config_name: 設定名
            config: レイヤー設定の辞書
            
        Returns:
            保存が成功したかどうか
        """
        try:
            # 設定名が既に存在する場合は上書き
            st.session_state.map_layer_configs[config_name] = config
            return True
        except Exception as e:
            st.error(f"レイヤー設定の保存に失敗しました: {str(e)}")
            return False
    
    def delete_layer_config(self, config_name: str) -> bool:
        """レイヤー設定を削除
        
        Args:
            config_name: 削除する設定名
            
        Returns:
            削除が成功したかどうか
        """
        # デフォルト設定は削除不可
        if config_name == 'default':
            st.error("デフォルト設定は削除できません。")
            return False
        
        if config_name in st.session_state.map_layer_configs:
            del st.session_state.map_layer_configs[config_name]
            return True
        return False
    
    def get_visible_layers(self, config_name: str = 'default') -> List[str]:
        """指定された設定で表示されるレイヤーのリストを取得
        
        Args:
            config_name: 設定名
            
        Returns:
            表示レイヤーのIDリスト
        """
        config = self.get_layer_config(config_name)
        visible_layers = []
        
        for layer_id, layer_config in config.get('layers', {}).items():
            if layer_config.get('visible', False):
                visible_layers.append(layer_id)
        
        return visible_layers
    
    def get_layer_property(self, config_name: str, layer_id: str, property_name: str) -> Any:
        """特定のレイヤープロパティの値を取得
        
        Args:
            config_name: 設定名
            layer_id: レイヤーID
            property_name: プロパティ名
            
        Returns:
            プロパティ値
        """
        config = self.get_layer_config(config_name)
        layer_config = config.get('layers', {}).get(layer_id, {})
        
        # プロパティが存在しない場合はNoneを返す
        return layer_config.get(property_name, None)
    
    def set_layer_property(self, config_name: str, layer_id: str, property_name: str, value: Any) -> bool:
        """レイヤープロパティの値を設定
        
        Args:
            config_name: 設定名
            layer_id: レイヤーID
            property_name: プロパティ名
            value: 設定する値
            
        Returns:
            設定が成功したかどうか
        """
        if config_name not in st.session_state.map_layer_configs:
            st.error(f"設定 '{config_name}' が見つかりません。")
            return False
        
        config = st.session_state.map_layer_configs[config_name]
        
        if layer_id not in config.get('layers', {}):
            st.error(f"レイヤー '{layer_id}' が見つかりません。")
            return False
        
        try:
            # プロパティ値を更新
            st.session_state.map_layer_configs[config_name]['layers'][layer_id][property_name] = value
            return True
        except Exception as e:
            st.error(f"プロパティの設定に失敗しました: {str(e)}")
            return False
    
    def set_layer_visibility(self, config_name: str, layer_id: str, visible: bool) -> bool:
        """レイヤーの表示/非表示を設定
        
        Args:
            config_name: 設定名
            layer_id: レイヤーID
            visible: 表示するかどうか
            
        Returns:
            設定が成功したかどうか
        """
        return self.set_layer_property(config_name, layer_id, 'visible', visible)
    
    def render_layer_controls(self, config_name: str = 'default') -> None:
        """レイヤー設定コントロールを表示
        
        Args:
            config_name: 設定名
        """
        config = self.get_layer_config(config_name)
        layer_registry = self.get_available_layer_types()
        
        st.subheader("レイヤー管理")
        
        # レイヤーの表示/非表示選択
        st.markdown("### 表示レイヤー")
        
        for layer_id, layer_info in layer_registry.items():
            layer_config = config.get('layers', {}).get(layer_id, {})
            visible = layer_config.get('visible', False)
            
            if st.checkbox(layer_info['name'], value=visible, key=f"layer_visible_{layer_id}"):
                if not visible:  # 状態が変わった場合のみ更新
                    self.set_layer_visibility(config_name, layer_id, True)
            else:
                if visible:  # 状態が変わった場合のみ更新
                    self.set_layer_visibility(config_name, layer_id, False)
        
        # レイヤーの詳細設定
        st.markdown("### レイヤー設定")
        
        # 設定するレイヤーの選択
        layer_options = [(layer_id, info['name']) for layer_id, info in layer_registry.items()]
        selected_layer = st.selectbox(
            "設定するレイヤー",
            options=[opt[0] for opt in layer_options],
            format_func=lambda x: next((name for id, name in layer_options if id == x), x)
        )
        
        if selected_layer:
            # 選択されたレイヤーのプロパティを表示
            self._render_layer_properties(config_name, selected_layer)
    
    def _render_layer_properties(self, config_name: str, layer_id: str) -> None:
        """レイヤープロパティの設定コントロールを表示
        
        Args:
            config_name: 設定名
            layer_id: レイヤーID
        """
        layer_registry = self.get_available_layer_types()
        layer_info = layer_registry.get(layer_id, {})
        properties = layer_info.get('properties', [])
        
        config = self.get_layer_config(config_name)
        layer_config = config.get('layers', {}).get(layer_id, {})
        
        st.markdown(f"#### {layer_info.get('name', layer_id)}の設定")
        
        for prop in properties:
            prop_name = prop['name']
            prop_type = prop['type']
            prop_label = prop.get('label', prop_name)
            current_value = layer_config.get(prop_name, prop.get('default'))
            
            # プロパティタイプに応じて適切なコントロールを表示
            if prop_type == 'slider':
                new_value = st.slider(
                    prop_label,
                    min_value=prop.get('min', 0),
                    max_value=prop.get('max', 100),
                    value=float(current_value) if isinstance(current_value, (int, float)) else prop.get('default'),
                    step=prop.get('step', None),
                    key=f"prop_{layer_id}_{prop_name}"
                )
            elif prop_type == 'color':
                new_value = st.color_picker(
                    prop_label,
                    value=current_value if isinstance(current_value, str) else prop.get('default'),
                    key=f"prop_{layer_id}_{prop_name}"
                )
            elif prop_type == 'checkbox':
                new_value = st.checkbox(
                    prop_label,
                    value=bool(current_value) if isinstance(current_value, bool) else prop.get('default'),
                    key=f"prop_{layer_id}_{prop_name}"
                )
            elif prop_type == 'text':
                new_value = st.text_input(
                    prop_label,
                    value=current_value if isinstance(current_value, str) else prop.get('default'),
                    key=f"prop_{layer_id}_{prop_name}"
                )
            elif prop_type == 'select':
                new_value = st.selectbox(
                    prop_label,
                    options=prop.get('options', []),
                    index=prop.get('options', []).index(current_value) if current_value in prop.get('options', []) else 0,
                    key=f"prop_{layer_id}_{prop_name}"
                )
            elif prop_type == 'multiselect':
                new_value = st.multiselect(
                    prop_label,
                    options=prop.get('options', []),
                    default=current_value if isinstance(current_value, list) else prop.get('default', []),
                    key=f"prop_{layer_id}_{prop_name}"
                )
            else:
                # 未対応のプロパティタイプの場合は現在の値を維持
                new_value = current_value
            
            # 値が変わった場合のみ更新
            if new_value != current_value:
                self.set_layer_property(config_name, layer_id, prop_name, new_value)
        
        # レイヤー設定のリセットボタン
        if st.button("設定をリセット", key=f"reset_{layer_id}"):
            # レイヤーのデフォルト設定を適用
            default_config = st.session_state.map_layer_configs.get('default', {})
            default_layer_config = default_config.get('layers', {}).get(layer_id, {})
            
            for prop in properties:
                prop_name = prop['name']
                default_value = default_layer_config.get(prop_name, prop.get('default'))
                self.set_layer_property(config_name, layer_id, prop_name, default_value)
            
            st.experimental_rerun()
    
    def render_config_manager(self) -> None:
        """レイヤー設定の管理インターフェースを表示"""
        st.subheader("レイヤー設定の管理")
        
        # 現在の設定一覧
        st.markdown("### 保存された設定")
        
        for config_name, config in st.session_state.map_layer_configs.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{config.get('name', config_name)}**")
                st.caption(config.get('description', ''))
            
            with col2:
                if st.button("適用", key=f"apply_{config_name}"):
                    st.session_state.current_map_config = config_name
                    st.experimental_rerun()
            
            with col3:
                if config_name != 'default' and st.button("削除", key=f"delete_{config_name}"):
                    if self.delete_layer_config(config_name):
                        st.success(f"設定 '{config.get('name', config_name)}' を削除しました。")
                        st.experimental_rerun()
        
        # 新しい設定の作成
        st.markdown("### 新しい設定を作成")
        
        with st.form("new_config_form"):
            new_config_name = st.text_input("設定名")
            new_config_description = st.text_area("説明")
            base_config = st.selectbox(
                "ベース設定",
                options=list(st.session_state.map_layer_configs.keys()),
                format_func=lambda x: st.session_state.map_layer_configs[x].get('name', x)
            )
            
            submit = st.form_submit_button("作成")
            
            if submit and new_config_name:
                # ベース設定をコピーして新しい設定を作成
                config_id = new_config_name.lower().replace(" ", "_")
                
                if config_id in st.session_state.map_layer_configs:
                    st.error(f"この名前の設定は既に存在します。")
                else:
                    base = self.get_layer_config(base_config)
                    new_config = base.copy()
                    new_config['name'] = new_config_name
                    new_config['description'] = new_config_description
                    new_config['created_at'] = datetime.now().isoformat()
                    
                    if self.save_layer_config(config_id, new_config):
                        st.success(f"新しい設定 '{new_config_name}' を作成しました。")
                        st.experimental_rerun()
    
    def export_configs(self) -> str:
        """レイヤー設定をJSONとしてエクスポート
        
        Returns:
            JSON形式のレイヤー設定
        """
        try:
            return json.dumps(st.session_state.map_layer_configs, indent=2)
        except Exception as e:
            st.error(f"レイヤー設定のエクスポートに失敗しました: {str(e)}")
            return "{}"
    
    def import_configs(self, configs_json: str) -> bool:
        """JSONからレイヤー設定をインポート
        
        Args:
            configs_json: インポートするJSON形式のレイヤー設定
            
        Returns:
            インポートが成功したかどうか
        """
        try:
            configs = json.loads(configs_json)
            # デフォルト設定は上書きしない
            if 'default' in configs:
                default_backup = st.session_state.map_layer_configs.get('default', {})
                
            st.session_state.map_layer_configs.update(configs)
            
            # デフォルト設定を復元
            if 'default' in configs:
                st.session_state.map_layer_configs['default'] = default_backup
                
            return True
        except json.JSONDecodeError:
            st.error("無効なJSON形式です。")
            return False
        except Exception as e:
            st.error(f"レイヤー設定のインポートに失敗しました: {str(e)}")
            return False
