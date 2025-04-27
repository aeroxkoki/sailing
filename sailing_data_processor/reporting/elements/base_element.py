# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.base_element

レポート要素の基底クラスを提供するモジュールです。
このモジュールは、すべての要素タイプに共通する機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Set
from abc import ABC, abstractmethod
import uuid
import json
import copy

from sailing_data_processor.reporting.templates.template_model import (
    Element as ElementModel, ElementType, Condition
)


class BaseElement(ABC):
    """
    レポート要素の基底クラス
    
    すべての要素タイプに共通する機能を提供します。モデルクラスとは異なり、
    実際のレンダリングや振る舞いを実装します。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        if model:
            self.model = model
        else:
            self.model = ElementModel(**kwargs)
    
    @property
    def element_id(self) -> str:
        """
        要素ID
        
        Returns
        -------
        str
            要素ID
        """
        return self.model.element_id
    
    @property
    def element_type(self) -> ElementType:
        """
        要素タイプ
        
        Returns
        -------
        ElementType
            要素タイプ
        """
        return self.model.element_type
    
    @property
    def name(self) -> str:
        """
        要素名
        
        Returns
        -------
        str
            要素名
        """
        return self.model.name
    
    @property
    def properties(self) -> Dict[str, Any]:
        """
        要素プロパティ
        
        Returns
        -------
        Dict[str, Any]
            プロパティ辞書
        """
        return self.model.properties
    
    @property
    def styles(self) -> Dict[str, Any]:
        """
        要素スタイル
        
        Returns
        -------
        Dict[str, Any]
            スタイル辞書
        """
        return self.model.styles
    
    @property
    def conditions(self) -> List[Condition]:
        """
        要素の表示条件
        
        Returns
        -------
        List[Condition]
            条件リスト
        """
        return self.model.conditions
    
    @property
    def children(self) -> List[ElementModel]:
        """
        子要素
        
        Returns
        -------
        List[ElementModel]
            子要素のリスト
        """
        return self.model.children
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """
        プロパティ値を取得
        
        Parameters
        ----------
        name : str
            プロパティ名
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            プロパティ値
        """
        return self.properties.get(name, default)
    
    def set_property(self, name: str, value: Any) -> None:
        """
        プロパティ値を設定
        
        Parameters
        ----------
        name : str
            プロパティ名
        value : Any
            プロパティ値
        """
        self.model.properties[name] = value
    
    def get_style(self, name: str, default: Any = None) -> Any:
        """
        スタイル値を取得
        
        Parameters
        ----------
        name : str
            スタイル名
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            スタイル値
        """
        return self.styles.get(name, default)
    
    def set_style(self, name: str, value: Any) -> None:
        """
        スタイル値を設定
        
        Parameters
        ----------
        name : str
            スタイル名
        value : Any
            スタイル値
        """
        self.model.styles[name] = value
    
    def add_condition(self, field: str, operator: str, value: Any = None) -> None:
        """
        表示条件を追加
        
        Parameters
        ----------
        field : str
            条件の対象フィールド
        operator : str
            条件演算子
        value : Any, optional
            比較値, by default None
        """
        condition = Condition(field, operator, value)
        self.model.conditions.append(condition)
    
    def remove_condition(self, index: int) -> None:
        """
        表示条件を削除
        
        Parameters
        ----------
        index : int
            削除する条件のインデックス
        """
        if 0 <= index < len(self.model.conditions):
            self.model.conditions.pop(index)
    
    def add_child(self, child: Union[ElementModel, 'BaseElement']) -> None:
        """
        子要素を追加
        
        Parameters
        ----------
        child : Union[ElementModel, BaseElement]
            追加する子要素
        """
        if isinstance(child, BaseElement):
            self.model.children.append(child.model)
        else:
            self.model.children.append(child)
    
    def remove_child(self, index: int) -> None:
        """
        子要素を削除
        
        Parameters
        ----------
        index : int
            削除する子要素のインデックス
        """
        if 0 <= index < len(self.model.children):
            self.model.children.pop(index)
    
    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """
        条件を評価
        
        Parameters
        ----------
        context : Dict[str, Any]
            評価コンテキスト
            
        Returns
        -------
        bool
            すべての条件が満たされている場合はTrue
        """
        if not self.conditions:
            return True
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """
        単一の条件を評価
        
        Parameters
        ----------
        condition : Condition
            評価する条件
        context : Dict[str, Any]
            評価コンテキスト
            
        Returns
        -------
        bool
            条件が満たされている場合はTrue
        """
        field_value = self._get_field_value(condition.field, context)
        
        # 存在チェック
        if condition.operator == "exists":
            return field_value is not None
        
        if condition.operator == "not_exists":
            return field_value is None
        
        # フィールドが存在しない場合
        if field_value is None:
            return False
        
        # 空チェック
        if condition.operator == "empty":
            if isinstance(field_value, (str, list, dict)):
                return len(field_value) == 0
            return field_value is None
        
        if condition.operator == "not_empty":
            if isinstance(field_value, (str, list, dict)):
                return len(field_value) > 0
            return field_value is not None
        
        # 比較演算子
        if condition.operator == "equals":
            return field_value == condition.value
        
        if condition.operator == "not_equals":
            return field_value != condition.value
        
        # 大小比較（数値のみ）
        if isinstance(field_value, (int, float)) and isinstance(condition.value, (int, float)):
            if condition.operator == "greater_than":
                return field_value > condition.value
            
            if condition.operator == "less_than":
                return field_value < condition.value
            
            if condition.operator == "greater_than_or_equals":
                return field_value >= condition.value
            
            if condition.operator == "less_than_or_equals":
                return field_value <= condition.value
        
        # 文字列操作（文字列のみ）
        if isinstance(field_value, str) and isinstance(condition.value, str):
            if condition.operator == "contains":
                return condition.value in field_value
            
            if condition.operator == "not_contains":
                return condition.value not in field_value
            
            if condition.operator == "starts_with":
                return field_value.startswith(condition.value)
            
            if condition.operator == "ends_with":
                return field_value.endswith(condition.value)
        
        # デフォルト
        return False
    
    def _get_field_value(self, field: str, context: Dict[str, Any]) -> Any:
        """
        コンテキストからフィールド値を取得
        
        Parameters
        ----------
        field : str
            フィールド名（ドット区切りのパスをサポート）
        context : Dict[str, Any]
            評価コンテキスト
            
        Returns
        -------
        Any
            フィールド値
        """
        if not field:
            return None
        
        # ドット区切りのパスをサポート
        parts = field.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        
        return value
    
    def get_css_styles(self) -> str:
        """
        CSSスタイル文字列を取得
        
        Returns
        -------
        str
            インラインCSSスタイル
        """
        style_parts = []
        
        # スタイル辞書をCSSプロパティに変換
        for key, value in self.styles.items():
            # camelCaseをkebab-caseに変換（例：fontSize -> font-size）
            css_key = ''
            for i, char in enumerate(key):
                if char.isupper():
                    css_key += '-' + char.lower()
                else:
                    css_key += char
            
            style_parts.append(f"{css_key}: {value}")
        
        return '; '.join(style_parts)
    
    def replace_variables(self, text: str, context: Dict[str, Any]) -> str:
        """
        テキスト内の変数を置換
        
        Parameters
        ----------
        text : str
            変数を含むテキスト
        context : Dict[str, Any]
            変数値を含むコンテキスト
            
        Returns
        -------
        str
            変数が置換されたテキスト
        """
        if not text or "{{" not in text:
            return text
        
        result = text
        
        # 簡易的な変数置換（{variable}}形式）
        start_pos = 0
        while True:
            start_pos = result.find("{", start_pos)
            if start_pos == -1:
                break
                
            end_pos = result.find("}}", start_pos)
            if end_pos == -1:
                break
                
            var_name = result[start_pos + 2:end_pos].strip()
            var_value = self._get_field_value(var_name, context)
            
            if var_value is not None:
                # 変数値を文字列に変換
                if not isinstance(var_value, str):
                    var_value = str(var_value)
                
                # 置換
                result = result[:start_pos] + var_value + result[end_pos + 2:]
                
                # 開始位置を更新
                start_pos = start_pos + len(var_value)
            else:
                # 変数が見つからない場合はそのまま残す
                start_pos = end_pos + 2
        
        return result
    
    def clone(self) -> 'BaseElement':
        """
        要素のコピーを作成
        
        Returns
        -------
        BaseElement
            コピーされた要素
        """
        model_copy = copy.deepcopy(self.model)
        return self.__class__(model=model_copy)
    
    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        pass
