"""
ui.components.export.json_preview

JSONデータのプレビュー表示コンポーネント
"""

import streamlit as st
import json
import io
from typing import Dict, List, Any, Optional, Union, Callable


class JSONPreviewComponent:
    """
    JSONデータのプレビュー表示コンポーネント
    
    エクスポート対象のJSONデータをプレビュー表示するためのUIコンポーネント。
    折りたたみ表示、検索機能、シンタックスハイライトを提供。
    """
    
    def __init__(self, key: str = "json_preview"):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "json_preview"
        """
        self.key = key
        
        # ステート管理
        if f"{key}_data" not in st.session_state:
            st.session_state[f"{key}_data"] = None
        if f"{key}_search_term" not in st.session_state:
            st.session_state[f"{key}_search_term"] = ""
        if f"{key}_display_mode" not in st.session_state:
            st.session_state[f"{key}_display_mode"] = "pretty"
        if f"{key}_path_filter" not in st.session_state:
            st.session_state[f"{key}_path_filter"] = ""
    
    def load_data(self, data: Union[Dict, List, str, bytes, io.TextIOBase], encoding: str = "utf-8") -> None:
        """
        データを読み込む
        
        Parameters
        ----------
        data : Union[Dict, List, str, bytes, io.TextIOBase]
            JSON互換オブジェクトまたはJSON文字列
        encoding : str, optional
            エンコーディング, by default "utf-8"
        """
        try:
            if isinstance(data, (dict, list)):
                # すでにJSONオブジェクトの場合はそのまま使用
                json_data = data
            elif isinstance(data, bytes):
                # バイト列の場合は文字列に変換
                json_data = json.loads(data.decode(encoding))
            elif isinstance(data, str):
                # JSON文字列の場合
                json_data = json.loads(data)
            elif hasattr(data, 'read'):
                # ファイルオブジェクトの場合
                json_data = json.load(data)
            else:
                raise ValueError("サポートされていない入力形式です")
            
            # データを保存
            st.session_state[f"{self.key}_data"] = json_data
            
        except Exception as e:
            st.error(f"JSONデータの読み込みに失敗しました: {str(e)}")
    
    def render(self):
        """コンポーネントを表示"""
        # データの取得
        data = st.session_state.get(f"{self.key}_data")
        
        if data is None:
            st.warning("プレビューするデータがありません。")
            return
        
        # 検索機能
        search_term = st.text_input(
            "JSONデータを検索", 
            value=st.session_state[f"{self.key}_search_term"],
            key=f"{self.key}_search_input"
        )
        st.session_state[f"{self.key}_search_term"] = search_term
        
        # 表示モード切り替え
        display_mode = st.radio(
            "表示モード",
            options=["整形表示", "ツリー表示", "生データ"],
            index=["pretty", "tree", "raw"].index(st.session_state[f"{self.key}_display_mode"]),
            horizontal=True,
            key=f"{self.key}_display_mode_select"
        )
        st.session_state[f"{self.key}_display_mode"] = {
            "整形表示": "pretty",
            "ツリー表示": "tree",
            "生データ": "raw"
        }[display_mode]
        
        # パスフィルタ（特定のJSONパスのみ表示）
        path_filter = st.text_input(
            "JSONパスフィルタ (例: results[0].data)",
            value=st.session_state[f"{self.key}_path_filter"],
            key=f"{self.key}_path_filter_input",
            help="特定のJSONパスのみを表示します。空白の場合は全てのデータを表示します。"
        )
        st.session_state[f"{self.key}_path_filter"] = path_filter
        
        # フィルタリングの適用
        filtered_data = self._apply_path_filter(data, path_filter)
        
        # 選択した表示モードでデータを表示
        if st.session_state[f"{self.key}_display_mode"] == "pretty":
            self._render_pretty_json(filtered_data, search_term)
        elif st.session_state[f"{self.key}_display_mode"] == "tree":
            self._render_tree_json(filtered_data)
        else:  # "raw"
            self._render_raw_json(filtered_data)
    
    def _apply_path_filter(self, data, path_filter):
        """
        JSONパスフィルタを適用
        
        Parameters
        ----------
        data : Union[Dict, List]
            JSON互換オブジェクト
        path_filter : str
            JSONパスフィルタ文字列
            
        Returns
        -------
        Any
            フィルタリングされたデータ
        """
        if not path_filter:
            return data
            
        try:
            # パスの解析
            path_parts = []
            current_part = ""
            in_brackets = False
            
            for char in path_filter:
                if char == '.' and not in_brackets:
                    if current_part:
                        path_parts.append(current_part)
                        current_part = ""
                elif char == '[':
                    if current_part:
                        path_parts.append(current_part)
                        current_part = ""
                    in_brackets = True
                elif char == ']' and in_brackets:
                    if current_part:
                        try:
                            # 数値であれば整数として解析
                            idx = int(current_part)
                            path_parts.append(idx)
                        except ValueError:
                            # 数値でなければ文字列として使用
                            path_parts.append(current_part)
                        current_part = ""
                    in_brackets = False
                else:
                    current_part += char
            
            if current_part:
                path_parts.append(current_part)
            
            # パスに沿ってデータを取得
            current = data
            for part in path_parts:
                if isinstance(current, dict):
                    if part in current:
                        current = current[part]
                    else:
                        return None  # パスが存在しない
                elif isinstance(current, list):
                    if isinstance(part, int) and 0 <= part < len(current):
                        current = current[part]
                    else:
                        return None  # インデックスが範囲外
                else:
                    return None  # パスが存在しない
            
            return current
            
        except Exception as e:
            st.error(f"JSONパスフィルタの適用に失敗しました: {str(e)}")
            return data
    
    def _render_pretty_json(self, data, search_term=None):
        """
        整形されたJSONデータを表示
        
        Parameters
        ----------
        data : Any
            表示するJSONデータ
        search_term : str, optional
            検索文字列, by default None
        """
        # JSON文字列に変換
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        # 検索語のハイライト
        if search_term:
            # 検索ヒットの数をカウント
            hit_count = json_str.lower().count(search_term.lower())
            if hit_count > 0:
                st.info(f"検索語 '{search_term}' が {hit_count} 件見つかりました")
            else:
                st.warning(f"検索語 '{search_term}' は見つかりませんでした")
        
        # コードブロックとしてJSONを表示
        st.code(json_str, language="json")
    
    def _render_tree_json(self, data):
        """
        ツリー形式でJSONデータを表示
        
        Parameters
        ----------
        data : Any
            表示するJSONデータ
        """
        # 再帰的にツリー表示するカスタム関数
        self._render_json_tree("root", data, 0)
    
    def _render_json_tree(self, key, value, depth=0):
        """
        JSONデータをツリー形式で再帰的に表示
        
        Parameters
        ----------
        key : str
            表示する項目のキー
        value : Any
            表示する値
        depth : int, optional
            現在の深さ, by default 0
        """
        # 特定の深さまでデフォルトで展開
        default_expanded = (depth < 2)
        
        if isinstance(value, dict):
            # 辞書の場合
            if len(value) == 0:
                st.write(f"**{key}**: " + "{}")
            else:
                with st.expander(f"**{key}**" + f" (オブジェクト, {len(value)}プロパティ)", expanded=default_expanded):
                    for k, v in value.items():
                        self._render_json_tree(k, v, depth + 1)
                        
        elif isinstance(value, list):
            # リストの場合
            if len(value) == 0:
                st.write(f"**{key}**: " + "[]")
            else:
                with st.expander(f"**{key}**" + f" (配列, {len(value)}項目)", expanded=default_expanded):
                    for i, item in enumerate(value):
                        self._render_json_tree(f"[{i}]", item, depth + 1)
        else:
            # プリミティブ値の場合
            if isinstance(value, str):
                # 文字列ならクォートを付ける
                display_value = f'"{value}"'
            elif value is None:
                # Noneならnullと表示
                display_value = "null"
            else:
                # それ以外はそのまま表示
                display_value = str(value)
                
            st.write(f"**{key}**: {display_value}")
    
    def _render_raw_json(self, data):
        """
        生のJSONデータを表示
        
        Parameters
        ----------
        data : Any
            表示するJSONデータ
        """
        # 一行のJSON文字列に変換
        json_str = json.dumps(data, ensure_ascii=False)
        st.code(json_str, language="json")
        
        # コピーボタンの模擬
        st.button("JSONをコピー", key=f"{self.key}_copy_button")
    
    def reset(self):
        """設定をリセット"""
        st.session_state[f"{self.key}_search_term"] = ""
        st.session_state[f"{self.key}_display_mode"] = "pretty"
        st.session_state[f"{self.key}_path_filter"] = ""
