# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.templates.template_model

レポートテンプレートのデータモデルを定義するモジュールです。
"""

from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime
from enum import Enum
import uuid
import json
from pathlib import Path


class TemplateOutputFormat(str, Enum):
    """
    テンプレートの出力形式を表す列挙型
    """
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    DOCX = "docx"
    PPTX = "pptx"


class SectionType(str, Enum):
    """
    テンプレートセクションのタイプを表す列挙型
    """
    HEADER = "header"
    CONTENT = "content"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    COVER = "cover"


class ElementType(str, Enum):
    """
    テンプレート要素のタイプを表す列挙型
    """
    # コンテンツ要素
    TEXT = "text"
    TABLE = "table"
    LIST = "list"
    KEY_VALUE = "key_value"
    
    # 視覚化要素
    CHART = "chart"
    MAP = "map"
    DIAGRAM = "diagram"
    
    # メディア要素
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    
    # レイアウト要素
    SECTION = "section"
    COLUMN = "column"
    GRID = "grid"
    TAB = "tab"
    
    # 装飾要素
    DIVIDER = "divider"
    BOX = "box"
    BACKGROUND = "background"
    ICON = "icon"
    
    # インタラクティブ要素
    BUTTON = "button"
    FILTER = "filter"
    SLIDER = "slider"
    DROPDOWN = "dropdown"


class ConditionOperator(str, Enum):
    """
    条件式の演算子を表す列挙型
    """
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUALS = "greater_than_or_equals"
    LESS_THAN_OR_EQUALS = "less_than_or_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    EMPTY = "empty"
    NOT_EMPTY = "not_empty"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class Condition:
    """
    条件式を表すクラス
    
    表示条件や動的な振る舞いを制御するための条件式を定義します。
    """
    
    def __init__(self, 
                 field: str, 
                 operator: Union[ConditionOperator, str], 
                 value: Any = None):
        """
        初期化
        
        Parameters
        ----------
        field : str
            条件の対象フィールド
        operator : Union[ConditionOperator, str]
            条件演算子
        value : Any, optional
            比較値, by default None
        """
        self.field = field
        
        if isinstance(operator, str):
            try:
                self.operator = ConditionOperator(operator)
            except ValueError:
                raise ValueError(f"Invalid operator: {operator}")
        else:
            self.operator = operator
            
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns
        -------
        Dict[str, Any]
            条件式を表す辞書
        """
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """
        辞書からConditionオブジェクトを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            条件式を表す辞書
            
        Returns
        -------
        Condition
            作成されたConditionオブジェクト
        """
        field = data.get("field", "")
        operator = data.get("operator", "")
        value = data.get("value")
        
        return cls(field, operator, value)


class Element:
    """
    テンプレート要素の基底クラス
    
    レポートを構成する個々の要素（テキスト、テーブル、グラフなど）の
    基本的な属性と振る舞いを定義します。
    """
    
    def __init__(self, 
                 element_id: Optional[str] = None,
                 element_type: Union[ElementType, str] = None,
                 name: str = "",
                 properties: Optional[Dict[str, Any]] = None,
                 styles: Optional[Dict[str, Any]] = None,
                 conditions: Optional[List[Dict[str, Any]]] = None,
                 children: Optional[List[Dict[str, Any]]] = None):
        """
        初期化
        
        Parameters
        ----------
        element_id : Optional[str], optional
            要素ID, by default None（自動生成）
        element_type : Union[ElementType, str], optional
            要素タイプ, by default None
        name : str, optional
            要素名, by default ""
        properties : Optional[Dict[str, Any]], optional
            要素のプロパティ, by default None
        styles : Optional[Dict[str, Any]], optional
            要素のスタイル, by default None
        conditions : Optional[List[Dict[str, Any]]], optional
            表示条件, by default None
        children : Optional[List[Dict[str, Any]]], optional
            子要素, by default None
        """
        self.element_id = element_id or str(uuid.uuid4())
        
        if isinstance(element_type, str):
            try:
                self.element_type = ElementType(element_type)
            except ValueError:
                raise ValueError(f"Invalid element type: {element_type}")
        else:
            self.element_type = element_type
        
        self.name = name
        self.properties = properties or {}
        self.styles = styles or {}
        self.conditions = [Condition.from_dict(c) for c in (conditions or [])]
        self.children = [Element.from_dict(c) for c in (children or [])]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns
        -------
        Dict[str, Any]
            要素を表す辞書
        """
        return {
            "element_id": self.element_id,
            "element_type": self.element_type.value if self.element_type else None,
            "name": self.name,
            "properties": self.properties,
            "styles": self.styles,
            "conditions": [c.to_dict() for c in self.conditions],
            "children": [c.to_dict() for c in self.children] if self.children else []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Element':
        """
        辞書からElementオブジェクトを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            要素を表す辞書
            
        Returns
        -------
        Element
            作成されたElementオブジェクト
        """
        return cls(
            element_id=data.get("element_id"),
            element_type=data.get("element_type"),
            name=data.get("name", ""),
            properties=data.get("properties", {}),
            styles=data.get("styles", {}),
            conditions=data.get("conditions", []),
            children=data.get("children", [])
        )


class Section:
    """
    テンプレートセクションクラス
    
    レポートを構成するセクション（ヘッダー、コンテンツ、フッターなど）の
    属性と振る舞いを定義します。
    """
    
    def __init__(self, 
                 section_id: Optional[str] = None,
                 section_type: Union[SectionType, str] = SectionType.CONTENT,
                 name: str = "",
                 title: str = "",
                 description: str = "",
                 order: int = 0,
                 layout: Optional[Dict[str, Any]] = None,
                 styles: Optional[Dict[str, Any]] = None,
                 conditions: Optional[List[Dict[str, Any]]] = None,
                 elements: Optional[List[Dict[str, Any]]] = None):
        """
        初期化
        
        Parameters
        ----------
        section_id : Optional[str], optional
            セクションID, by default None（自動生成）
        section_type : Union[SectionType, str], optional
            セクションタイプ, by default SectionType.CONTENT
        name : str, optional
            セクション内部名, by default ""
        title : str, optional
            セクション表示名, by default ""
        description : str, optional
            セクション説明, by default ""
        order : int, optional
            セクション順序, by default 0
        layout : Optional[Dict[str, Any]], optional
            レイアウト設定, by default None
        styles : Optional[Dict[str, Any]], optional
            スタイル設定, by default None
        conditions : Optional[List[Dict[str, Any]]], optional
            表示条件, by default None
        elements : Optional[List[Dict[str, Any]]], optional
            セクション内の要素, by default None
        """
        self.section_id = section_id or str(uuid.uuid4())
        
        if isinstance(section_type, str):
            try:
                self.section_type = SectionType(section_type)
            except ValueError:
                raise ValueError(f"Invalid section type: {section_type}")
        else:
            self.section_type = section_type
        
        self.name = name
        self.title = title
        self.description = description
        self.order = order
        self.layout = layout or {"columns": 1, "margin": {"top": 20, "right": 20, "bottom": 20, "left": 20}}
        self.styles = styles or {}
        self.conditions = [Condition.from_dict(c) for c in (conditions or [])]
        self.elements = [Element.from_dict(e) for e in (elements or [])]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns
        -------
        Dict[str, Any]
            セクションを表す辞書
        """
        return {
            "section_id": self.section_id,
            "section_type": self.section_type.value,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "layout": self.layout,
            "styles": self.styles,
            "conditions": [c.to_dict() for c in self.conditions],
            "elements": [e.to_dict() for e in self.elements]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Section':
        """
        辞書からSectionオブジェクトを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            セクションを表す辞書
            
        Returns
        -------
        Section
            作成されたSectionオブジェクト
        """
        return cls(
            section_id=data.get("section_id"),
            section_type=data.get("section_type", SectionType.CONTENT),
            name=data.get("name", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            order=data.get("order", 0),
            layout=data.get("layout", {}),
            styles=data.get("styles", {}),
            conditions=data.get("conditions", []),
            elements=data.get("elements", [])
        )


class Template:
    """
    レポートテンプレートクラス
    
    レポートテンプレート全体の構造と振る舞いを定義します。
    """
    
    def __init__(self, 
                 template_id: Optional[str] = None,
                 name: str = "",
                 description: str = "",
                 author: str = "",
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 version: str = "1.0",
                 tags: Optional[List[str]] = None,
                 category: str = "",
                 output_format: Union[TemplateOutputFormat, str] = TemplateOutputFormat.HTML,
                 metadata: Optional[Dict[str, Any]] = None,
                 global_styles: Optional[Dict[str, Any]] = None,
                 sections: Optional[List[Dict[str, Any]]] = None):
        """
        初期化
        
        Parameters
        ----------
        template_id : Optional[str], optional
            テンプレートID, by default None（自動生成）
        name : str, optional
            テンプレート名, by default ""
        description : str, optional
            テンプレート説明, by default ""
        author : str, optional
            作成者, by default ""
        created_at : Optional[datetime], optional
            作成日時, by default None（現在時刻）
        updated_at : Optional[datetime], optional
            更新日時, by default None（現在時刻）
        version : str, optional
            バージョン, by default "1.0"
        tags : Optional[List[str]], optional
            タグ, by default None
        category : str, optional
            カテゴリ, by default ""
        output_format : Union[TemplateOutputFormat, str], optional
            出力形式, by default TemplateOutputFormat.HTML
        metadata : Optional[Dict[str, Any]], optional
            メタデータ, by default None
        global_styles : Optional[Dict[str, Any]], optional
            グローバルスタイル, by default None
        sections : Optional[List[Dict[str, Any]]], optional
            セクションリスト, by default None
        """
        now = datetime.now()
        
        self.template_id = template_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.author = author
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.version = version
        self.tags = tags or []
        self.category = category
        
        if isinstance(output_format, str):
            try:
                self.output_format = TemplateOutputFormat(output_format)
            except ValueError:
                raise ValueError(f"Invalid output format: {output_format}")
        else:
            self.output_format = output_format
        
        self.metadata = metadata or {}
        self.global_styles = global_styles or {
            "font_family": "Arial, sans-serif",
            "base_font_size": 12,
            "color_primary": "#3498db",
            "color_secondary": "#2c3e50",
            "color_accent": "#e74c3c",
            "color_background": "#ffffff",
            "color_text": "#333333"
        }
        
        self.sections = [Section.from_dict(s) for s in (sections or [])]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns
        -------
        Dict[str, Any]
            テンプレートを表す辞書
        """
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "tags": self.tags,
            "category": self.category,
            "output_format": self.output_format.value,
            "metadata": self.metadata,
            "global_styles": self.global_styles,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """
        辞書からTemplateオブジェクトを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            テンプレートを表す辞書
            
        Returns
        -------
        Template
            作成されたTemplateオブジェクト
        """
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            template_id=data.get("template_id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", "1.0"),
            tags=data.get("tags", []),
            category=data.get("category", ""),
            output_format=data.get("output_format", TemplateOutputFormat.HTML),
            metadata=data.get("metadata", {}),
            global_styles=data.get("global_styles", {}),
            sections=data.get("sections", [])
        )
    
    def to_json(self, indent: int = 2) -> str:
        """
        JSON文字列に変換
        
        Parameters
        ----------
        indent : int, optional
            インデント数, by default 2
            
        Returns
        -------
        str
            JSON文字列
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Template':
        """
        JSON文字列からTemplateオブジェクトを作成
        
        Parameters
        ----------
        json_str : str
            JSON文字列
            
        Returns
        -------
        Template
            作成されたTemplateオブジェクト
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Union[str, Path], indent: int = 2) -> None:
        """
        テンプレートをファイルに保存
        
        Parameters
        ----------
        file_path : Union[str, Path]
            保存先ファイルパス
        indent : int, optional
            インデント数, by default 2
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent))
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'Template':
        """
        ファイルからTemplateオブジェクトを作成
        
        Parameters
        ----------
        file_path : Union[str, Path]
            ファイルパス
            
        Returns
        -------
        Template
            作成されたTemplateオブジェクト
        """
        file_path = Path(file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            json_str = f.read()
        
        return cls.from_json(json_str)
    
    def add_section(self, section: Section) -> None:
        """
        セクションを追加
        
        Parameters
        ----------
        section : Section
            追加するセクション
        """
        self.sections.append(section)
        self.updated_at = datetime.now()
    
    def add_section_from_dict(self, section_data: Dict[str, Any]) -> None:
        """
        辞書からセクションを追加
        
        Parameters
        ----------
        section_data : Dict[str, Any]
            セクションデータ
        """
        section = Section.from_dict(section_data)
        self.add_section(section)
    
    def get_section_by_id(self, section_id: str) -> Optional[Section]:
        """
        IDでセクションを取得
        
        Parameters
        ----------
        section_id : str
            セクションID
            
        Returns
        -------
        Optional[Section]
            見つかったセクション、なければNone
        """
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None
    
    def get_section_by_name(self, name: str) -> Optional[Section]:
        """
        名前でセクションを取得
        
        Parameters
        ----------
        name : str
            セクション名
            
        Returns
        -------
        Optional[Section]
            見つかったセクション、なければNone
        """
        for section in self.sections:
            if section.name == name:
                return section
        return None
    
    def remove_section(self, section_id: str) -> bool:
        """
        セクションを削除
        
        Parameters
        ----------
        section_id : str
            削除するセクションID
            
        Returns
        -------
        bool
            削除成功したらTrue
        """
        for i, section in enumerate(self.sections):
            if section.section_id == section_id:
                self.sections.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_all_element_ids(self) -> Set[str]:
        """
        テンプレート内のすべての要素IDを取得
        
        Returns
        -------
        Set[str]
            要素IDのセット
        """
        element_ids = set()
        
        def collect_element_ids(elements):
            for element in elements:
                element_ids.add(element.element_id)
                if element.children:
                    collect_element_ids(element.children)
        
        for section in self.sections:
            if section.elements:
                collect_element_ids(section.elements)
        
        return element_ids
    
    def get_element_by_id(self, element_id: str) -> Optional[Element]:
        """
        IDで要素を取得
        
        Parameters
        ----------
        element_id : str
            要素ID
            
        Returns
        -------
        Optional[Element]
            見つかった要素、なければNone
        """
        result = [None]  # 可変オブジェクトを使って結果を保存
        
        def find_element(elements):
            for element in elements:
                if element.element_id == element_id:
                    result[0] = element
                    return True
                if element.children and find_element(element.children):
                    return True
            return False
        
        for section in self.sections:
            if section.elements and find_element(section.elements):
                break
        
        return result[0]
    
    def sort_sections(self) -> None:
        """
        セクションを順序でソート
        """
        self.sections.sort(key=lambda x: x.order)
        self.updated_at = datetime.now()



class ElementModel:
    """要素モデルクラス"""
    
    def __init__(self, element_type: ElementType = ElementType.TEXT, properties: Dict[str, Any] = None):
        """初期化"""
        self.element_type = element_type
        self.properties = properties or {}
        self.element_id = str(uuid.uuid4())
        self.name = ""
        self.styles = {}
        self.conditions = []
        self.children = []
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """プロパティを取得"""
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value: Any) -> None:
        """プロパティを設定"""
        self.properties[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書表現を取得"""
        return {
            "element_id": self.element_id,
            "element_type": self.element_type.name,
            "name": self.name,
            "properties": self.properties.copy(),
            "styles": self.styles.copy(),
            "conditions": self.conditions,
            "children": self.children
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ElementModel":
        """辞書から生成"""
        element_type = ElementType[data.get("element_type", "TEXT")]
        properties = data.get("properties", {})
        model = cls(element_type=element_type, properties=properties)
        model.element_id = data.get("element_id", str(uuid.uuid4()))
        model.name = data.get("name", "")
        model.styles = data.get("styles", {})
        model.conditions = data.get("conditions", [])
        model.children = data.get("children", [])
        return model
