"""
ui.components.reporting.map.layer_data_connector_panel

マップレイヤーのデータ連携機能を制御するUIパネルを提供するモジュールです。
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer
from sailing_data_processor.reporting.elements.map.layers.enhanced_layer_manager import EnhancedLayerManager


def layer_data_connector_panel(layer_manager: EnhancedLayerManager, 
                             on_change: Optional[Callable[[str], None]] = None,
                             key_prefix: str = "") -> Dict[str, Any]:
    """
    レイヤーデータ連携パネルを表示

    Parameters
    ----------
    layer_manager : EnhancedLayerManager
        拡張レイヤーマネージャー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更された設定情報
    """
    st.markdown("### データ連携管理")
    
    changes = {}
    
    # レイヤー一覧の取得
    ordered_layers = layer_manager.get_ordered_layers()
    
    if not ordered_layers:
        st.info("レイヤーがありません。レイヤーを追加してください。")
        return changes
    
    # データソース管理
    with st.expander("データソース管理", expanded=True):
        st.markdown("#### 登録されているデータソース")
        
        # データソース情報の表示
        sources = list(layer_manager.get_context().keys())
        if sources:
            source_data = []
            for source_id in sources:
                data = layer_manager.get_context_data(source_id)
                data_type = type(data).__name__
                data_size = "N/A"
                
                if isinstance(data, list):
                    data_size = f"{len(data)} items"
                elif isinstance(data, dict):
                    data_size = f"{len(data)} keys"
                
                source_data.append({
                    "データソースID": source_id,
                    "データ型": data_type,
                    "サイズ": data_size
                })
            
            source_df = pd.DataFrame(source_data)
            st.dataframe(source_df, hide_index=True)
        else:
            st.info("登録されているデータソースがありません。")
        
        # データソースのクリア
        if sources:
            # データソース選択
            selected_source = st.selectbox(
                "クリアするデータソース",
                options=sources,
                key=f"{key_prefix}_clear_source_select"
            )
            
            if st.button("選択したソースをクリア", key=f"{key_prefix}_clear_source"):
                if st.session_state.get(f"{key_prefix}_confirm_clear_source", False):
                    layer_manager.clear_context_data(selected_source)
                    changes[f"source_{selected_source}_cleared"] = True
                    st.session_state[f"{key_prefix}_confirm_clear_source"] = False
                    if on_change:
                        on_change("data_source_cleared")
                    st.rerun()
                else:
                    st.session_state[f"{key_prefix}_confirm_clear_source"] = True
                    st.warning(f"データソース '{selected_source}' をクリアします。もう一度ボタンをクリックして確認してください。")
            
            if st.button("すべてのソースをクリア", key=f"{key_prefix}_clear_all_sources"):
                if st.session_state.get(f"{key_prefix}_confirm_clear_all_sources", False):
                    layer_manager.clear_context_data()
                    changes["all_sources_cleared"] = True
                    st.session_state[f"{key_prefix}_confirm_clear_all_sources"] = False
                    if on_change:
                        on_change("all_data_sources_cleared")
                    st.rerun()
                else:
                    st.session_state[f"{key_prefix}_confirm_clear_all_sources"] = True
                    st.warning("すべてのデータソースをクリアします。もう一度ボタンをクリックして確認してください。")
    
    # レイヤーバインディング管理
    with st.expander("レイヤーバインディング管理", expanded=True):
        st.markdown("#### レイヤーとデータソースのバインド")
        
        # レイヤー選択
        selected_layer_id = st.selectbox(
            "レイヤーを選択",
            options=[layer.layer_id for layer in ordered_layers],
            format_func=lambda x: next((layer.name for layer in ordered_layers if layer.layer_id == x), x),
            key=f"{key_prefix}_binding_layer_select"
        )
        
        selected_layer = None
        if selected_layer_id:
            selected_layer = layer_manager.get_layer(selected_layer_id)
        
        if selected_layer:
            # 現在のバインディング情報を表示
            binding = layer_manager.data_connector.get_binding(selected_layer)
            
            if binding:
                st.markdown("**現在のバインディング**")
                st.write(f"データソース: {binding['source_id']}")
                
                if binding['field_mappings']:
                    st.markdown("フィールドマッピング:")
                    for target, source in binding['field_mappings'].items():
                        st.write(f"・ {target} ← {source}")
                
                if binding['transform']:
                    if callable(binding['transform']):
                        st.write("変換関数: カスタム関数")
                    else:
                        st.write(f"変換関数: {binding['transform']}")
                
                # バインディング解除ボタン
                if st.button("バインディングを解除", key=f"{key_prefix}_unbind_layer"):
                    if layer_manager.unbind_layer(selected_layer):
                        changes[f"{selected_layer_id}_unbound"] = True
                        if on_change:
                            on_change("layer_unbound")
                        st.rerun()
            else:
                # 新規バインディング設定
                st.markdown("**新規バインディング**")
                
                # データソース選択
                sources = list(layer_manager.get_context().keys())
                source_id = None
                
                if sources:
                    source_id = st.selectbox(
                        "データソース",
                        options=sources,
                        key=f"{key_prefix}_binding_source_select"
                    )
                else:
                    st.info("バインド可能なデータソースがありません。")
                
                if source_id:
                    # 簡易フィールドマッピング
                    st.markdown("**フィールドマッピング**")
                    st.info("フィールドマッピングは、データソースの特定フィールドをレイヤーフィールドにマッピングします。")
                    
                    use_mapping = st.checkbox(
                        "フィールドマッピングを使用",
                        value=False,
                        key=f"{key_prefix}_use_field_mapping"
                    )
                    
                    field_mappings = {}
                    
                    if use_mapping:
                        # データの最初の要素からフィールドを取得
                        sample_data = layer_manager.get_context_data(source_id)
                        source_fields = []
                        
                        if isinstance(sample_data, list) and sample_data:
                            if isinstance(sample_data[0], dict):
                                source_fields = list(sample_data[0].keys())
                        elif isinstance(sample_data, dict):
                            source_fields = list(sample_data.keys())
                        
                        if source_fields:
                            # マッピング設定
                            st.markdown("以下のフィールドに対応するソースフィールドを選択してください：")
                            
                            # レイヤータイプに応じた一般的なフィールド
                            target_fields = ["lat", "lng", "value", "speed", "wind_speed", "wind_direction", "heading", "timestamp"]
                            
                            for target_field in target_fields:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    use_field = st.checkbox(
                                        f"{target_field}を使用",
                                        value=False,
                                        key=f"{key_prefix}_use_{target_field}"
                                    )
                                
                                if use_field:
                                    with col2:
                                        source_field = st.selectbox(
                                            f"{target_field}のソースフィールド",
                                            options=source_fields,
                                            key=f"{key_prefix}_map_{target_field}"
                                        )
                                        field_mappings[target_field] = source_field
                        else:
                            st.warning("データソースからフィールド情報を取得できません。")
                    
                    # 変換関数選択
                    st.markdown("**データ変換**")
                    
                    transform_options = [
                        "なし",
                        "identity",
                        "to_float",
                        "to_int",
                        "to_str",
                        "scale",
                        "offset",
                        "min_max_normalize"
                    ]
                    
                    transform_selection = st.selectbox(
                        "変換関数",
                        options=transform_options,
                        format_func=lambda x: {
                            "なし": "変換なし",
                            "identity": "恒等変換",
                            "to_float": "浮動小数点に変換",
                            "to_int": "整数に変換",
                            "to_str": "文字列に変換",
                            "scale": "スケーリング",
                            "offset": "オフセット追加",
                            "min_max_normalize": "最小・最大正規化"
                        }.get(x, x),
                        key=f"{key_prefix}_transform_select"
                    )
                    
                    transform = None
                    if transform_selection != "なし":
                        transform = transform_selection
                    
                    # バインドボタン
                    if st.button("レイヤーをバインド", key=f"{key_prefix}_bind_layer"):
                        # バインディングを実行
                        layer_manager.bind_layer_to_source(
                            selected_layer, 
                            source_id, 
                            field_mappings if use_mapping else None,
                            transform
                        )
                        
                        changes[f"{selected_layer_id}_bound"] = {
                            "source_id": source_id,
                            "field_mappings": field_mappings if use_mapping else None,
                            "transform": transform
                        }
                        
                        if on_change:
                            on_change("layer_bound")
                        
                        st.rerun()
    
    # レイヤー間同期の管理
    with st.expander("レイヤー間同期の管理", expanded=False):
        st.markdown("#### レイヤー間の同期設定")
        
        # ソースレイヤー選択
        source_layer_id = st.selectbox(
            "ソースレイヤー",
            options=[layer.layer_id for layer in ordered_layers],
            format_func=lambda x: next((layer.name for layer in ordered_layers if layer.layer_id == x), x),
            key=f"{key_prefix}_sync_source_layer"
        )
        
        # ターゲットレイヤー選択
        target_layer_options = [layer.layer_id for layer in ordered_layers if layer.layer_id != source_layer_id]
        target_layer_id = st.selectbox(
            "ターゲットレイヤー",
            options=target_layer_options if target_layer_options else [""],
            format_func=lambda x: next((layer.name for layer in ordered_layers if layer.layer_id == x), x) if x else "（なし）",
            key=f"{key_prefix}_sync_target_layer"
        )
        
        if source_layer_id and target_layer_id:
            source_layer = layer_manager.get_layer(source_layer_id)
            target_layer = layer_manager.get_layer(target_layer_id)
            
            if source_layer and target_layer:
                # 同期設定
                st.markdown("**同期設定**")
                
                # 双方向同期
                bidirectional = st.checkbox(
                    "双方向同期",
                    value=False,
                    key=f"{key_prefix}_bidirectional_sync"
                )
                
                # 同期追加ボタン
                if st.button("同期ペアを追加", key=f"{key_prefix}_add_sync_pair"):
                    layer_manager.add_sync_pair(
                        source_layer,
                        target_layer,
                        bidirectional=bidirectional
                    )
                    
                    changes["sync_pair_added"] = {
                        "source_id": source_layer_id,
                        "target_id": target_layer_id,
                        "bidirectional": bidirectional
                    }
                    
                    if on_change:
                        on_change("sync_pair_added")
                    
                    st.rerun()
                
                # 同期削除ボタン
                if st.button("同期ペアを削除", key=f"{key_prefix}_remove_sync_pair"):
                    layer_manager.remove_sync_pair(source_layer, target_layer)
                    
                    changes["sync_pair_removed"] = {
                        "source_id": source_layer_id,
                        "target_id": target_layer_id
                    }
                    
                    if on_change:
                        on_change("sync_pair_removed")
                    
                    st.rerun()
                
                # 同期実行ボタン
                if st.button("同期を実行", key=f"{key_prefix}_sync_layers"):
                    results = layer_manager.sync_layers()
                    
                    changes["sync_results"] = results
                    
                    if on_change:
                        on_change("layers_synced")
                    
                    st.rerun()
    
    # レイヤーイベント管理
    with st.expander("レイヤーイベント管理", expanded=False):
        st.markdown("#### レイヤーイベント設定")
        st.info("この機能はプログラムによる設定が必要です。UI上での設定は現在サポートされていません。")
    
    return changes


def data_source_editor_panel(layer_manager: EnhancedLayerManager,
                           on_change: Optional[Callable[[str], None]] = None,
                           key_prefix: str = "") -> Dict[str, Any]:
    """
    データソース編集パネルを表示

    Parameters
    ----------
    layer_manager : EnhancedLayerManager
        拡張レイヤーマネージャー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたデータソース情報
    """
    st.markdown("### データソース編集")
    
    changes = {}
    
    # データソース選択
    sources = list(layer_manager.get_context().keys())
    
    if not sources:
        st.info("登録されているデータソースがありません。")
        
        # 新規データソース作成
        with st.expander("新規データソース作成", expanded=True):
            new_source_id = st.text_input(
                "データソースID",
                value="",
                key=f"{key_prefix}_new_source_id"
            )
            
            data_type = st.selectbox(
                "データ型",
                options=["list", "dict"],
                format_func=lambda x: {"list": "リスト", "dict": "辞書"}.get(x, x),
                key=f"{key_prefix}_new_source_type"
            )
            
            if st.button("空のデータソースを作成", key=f"{key_prefix}_create_empty_source"):
                if new_source_id:
                    # 空のデータソースを作成
                    if data_type == "list":
                        layer_manager.set_context_data(new_source_id, [])
                    else:
                        layer_manager.set_context_data(new_source_id, {})
                    
                    changes["new_source_created"] = {
                        "source_id": new_source_id,
                        "type": data_type
                    }
                    
                    if on_change:
                        on_change("data_source_created")
                    
                    st.rerun()
                else:
                    st.warning("データソースIDを入力してください。")
        
        return changes
    
    # 既存データソース編集
    selected_source = st.selectbox(
        "編集するデータソース",
        options=sources,
        key=f"{key_prefix}_edit_source_select"
    )
    
    if selected_source:
        data = layer_manager.get_context_data(selected_source)
        
        # データ型に応じた編集UI
        if isinstance(data, list):
            # リスト型データの編集
            st.markdown(f"**リスト型データ ({len(data)} アイテム)**")
            
            if data:
                # サンプルデータの表示
                sample_size = min(5, len(data))
                st.markdown(f"サンプルデータ (最初の{sample_size}アイテム):")
                
                if isinstance(data[0], dict):
                    # 辞書のリストの場合、DataFrameとして表示
                    df = pd.DataFrame(data[:sample_size])
                    st.dataframe(df, hide_index=False)
                else:
                    # プリミティブ型のリストの場合
                    for i, item in enumerate(data[:sample_size]):
                        st.write(f"{i}: {item}")
            else:
                st.info("データが空です。")
            
            # リストに新しいアイテムを追加（辞書型アイテムのみ）
            with st.expander("新しいアイテムを追加", expanded=False):
                if data and isinstance(data[0], dict):
                    # フィールドの取得
                    fields = list(data[0].keys())
                    
                    # フィールド値の入力
                    new_item = {}
                    for field in fields:
                        field_type = type(data[0][field]).__name__
                        
                        if field_type == 'int':
                            new_item[field] = st.number_input(
                                f"{field} (整数)",
                                value=0,
                                step=1,
                                key=f"{key_prefix}_new_item_{field}"
                            )
                        elif field_type == 'float':
                            new_item[field] = st.number_input(
                                f"{field} (浮動小数点)",
                                value=0.0,
                                key=f"{key_prefix}_new_item_{field}"
                            )
                        elif field_type == 'bool':
                            new_item[field] = st.checkbox(
                                f"{field} (真偽値)",
                                value=False,
                                key=f"{key_prefix}_new_item_{field}"
                            )
                        else:
                            new_item[field] = st.text_input(
                                f"{field} (文字列)",
                                value="",
                                key=f"{key_prefix}_new_item_{field}"
                            )
                    
                    if st.button("アイテムを追加", key=f"{key_prefix}_add_item"):
                        # 新しいリストを作成して追加
                        new_data = data.copy()
                        new_data.append(new_item)
                        
                        # データソースを更新
                        layer_manager.set_context_data(selected_source, new_data)
                        
                        changes["item_added"] = {
                            "source_id": selected_source,
                            "item": new_item
                        }
                        
                        if on_change:
                            on_change("data_source_updated")
                        
                        st.rerun()
                else:
                    st.info("このデータ形式では新しいアイテムの追加はサポートされていません。")
            
            # リストからアイテムを削除
            with st.expander("アイテムを削除", expanded=False):
                if data:
                    # インデックス範囲の入力
                    st.warning("削除するアイテムのインデックス範囲を指定してください。")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        start_index = st.number_input(
                            "開始インデックス",
                            min_value=0,
                            max_value=len(data) - 1,
                            value=0,
                            step=1,
                            key=f"{key_prefix}_delete_start_index"
                        )
                    
                    with col2:
                        end_index = st.number_input(
                            "終了インデックス",
                            min_value=0,
                            max_value=len(data) - 1,
                            value=min(5, len(data) - 1),
                            step=1,
                            key=f"{key_prefix}_delete_end_index"
                        )
                    
                    if start_index > end_index:
                        st.error("開始インデックスは終了インデックス以下にしてください。")
                    else:
                        num_items = end_index - start_index + 1
                        if st.button(f"{num_items}アイテムを削除", key=f"{key_prefix}_delete_items"):
                            if st.session_state.get(f"{key_prefix}_confirm_delete_items", False):
                                # 新しいリストを作成して削除
                                new_data = data.copy()
                                del new_data[start_index:end_index + 1]
                                
                                # データソースを更新
                                layer_manager.set_context_data(selected_source, new_data)
                                
                                changes["items_deleted"] = {
                                    "source_id": selected_source,
                                    "start_index": start_index,
                                    "end_index": end_index
                                }
                                
                                st.session_state[f"{key_prefix}_confirm_delete_items"] = False
                                
                                if on_change:
                                    on_change("data_source_updated")
                                
                                st.rerun()
                            else:
                                st.session_state[f"{key_prefix}_confirm_delete_items"] = True
                                st.warning(f"{num_items}アイテムを削除します。もう一度ボタンをクリックして確認してください。")
                else:
                    st.info("データが空のため、削除するアイテムがありません。")
        
        elif isinstance(data, dict):
            # 辞書型データの編集
            st.markdown(f"**辞書型データ ({len(data)} キー)**")
            
            if data:
                # データの表示
                st.markdown("現在のデータ:")
                
                # キーと値を表形式で表示
                items = [{"キー": key, "値": str(value), "型": type(value).__name__} for key, value in data.items()]
                df = pd.DataFrame(items)
                st.dataframe(df, hide_index=True)
            else:
                st.info("データが空です。")
            
            # 辞書に新しいキー・値を追加
            with st.expander("新しいキー・値を追加", expanded=False):
                new_key = st.text_input(
                    "キー",
                    value="",
                    key=f"{key_prefix}_new_dict_key"
                )
                
                value_type = st.selectbox(
                    "値の型",
                    options=["str", "int", "float", "bool", "list", "dict"],
                    format_func=lambda x: {
                        "str": "文字列",
                        "int": "整数",
                        "float": "浮動小数点",
                        "bool": "真偽値",
                        "list": "リスト",
                        "dict": "辞書"
                    }.get(x, x),
                    key=f"{key_prefix}_new_value_type"
                )
                
                new_value = None
                
                if value_type == "str":
                    new_value = st.text_input(
                        "値（文字列）",
                        value="",
                        key=f"{key_prefix}_new_str_value"
                    )
                elif value_type == "int":
                    new_value = st.number_input(
                        "値（整数）",
                        value=0,
                        step=1,
                        key=f"{key_prefix}_new_int_value"
                    )
                elif value_type == "float":
                    new_value = st.number_input(
                        "値（浮動小数点）",
                        value=0.0,
                        key=f"{key_prefix}_new_float_value"
                    )
                elif value_type == "bool":
                    new_value = st.checkbox(
                        "値（真偽値）",
                        value=False,
                        key=f"{key_prefix}_new_bool_value"
                    )
                elif value_type == "list":
                    new_value = []
                    st.info("空のリストが作成されます。")
                elif value_type == "dict":
                    new_value = {}
                    st.info("空の辞書が作成されます。")
                
                if st.button("追加", key=f"{key_prefix}_add_dict_item"):
                    if new_key:
                        # 新しい辞書を作成して追加
                        new_data = data.copy()
                        new_data[new_key] = new_value
                        
                        # データソースを更新
                        layer_manager.set_context_data(selected_source, new_data)
                        
                        changes["dict_item_added"] = {
                            "source_id": selected_source,
                            "key": new_key,
                            "value": new_value
                        }
                        
                        if on_change:
                            on_change("data_source_updated")
                        
                        st.rerun()
                    else:
                        st.warning("キーを入力してください。")
            
            # 辞書からキーを削除
            with st.expander("キーを削除", expanded=False):
                if data:
                    # 削除するキーの選択
                    keys_to_delete = st.multiselect(
                        "削除するキー",
                        options=list(data.keys()),
                        key=f"{key_prefix}_keys_to_delete"
                    )
                    
                    if keys_to_delete:
                        if st.button(f"{len(keys_to_delete)}キーを削除", key=f"{key_prefix}_delete_keys"):
                            if st.session_state.get(f"{key_prefix}_confirm_delete_keys", False):
                                # 新しい辞書を作成して削除
                                new_data = data.copy()
                                for key in keys_to_delete:
                                    if key in new_data:
                                        del new_data[key]
                                
                                # データソースを更新
                                layer_manager.set_context_data(selected_source, new_data)
                                
                                changes["dict_keys_deleted"] = {
                                    "source_id": selected_source,
                                    "keys": keys_to_delete
                                }
                                
                                st.session_state[f"{key_prefix}_confirm_delete_keys"] = False
                                
                                if on_change:
                                    on_change("data_source_updated")
                                
                                st.rerun()
                            else:
                                st.session_state[f"{key_prefix}_confirm_delete_keys"] = True
                                st.warning(f"{len(keys_to_delete)}キーを削除します。もう一度ボタンをクリックして確認してください。")
                else:
                    st.info("データが空のため、削除するキーがありません。")
        
        else:
            # その他のデータ型
            st.markdown(f"**{type(data).__name__}型データ**")
            st.write(data)
            st.warning("このデータ型は現在編集をサポートしていません。")
    
    return changes
