"""
sailing_data_processor.reporting.elements.element_factory

要素の作成を担当する工場モジュールです。
要素タイプに応じた適切な要素クラスのインスタンスを作成します。
"""

from typing import Dict, Optional, Type, Union

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


# 要素クラスのインポート
from sailing_data_processor.reporting.elements.content_elements import (
    TextElement, TableElement, ListElement, KeyValueElement,
    ChartElement, MapElement, DiagramElement, ImageElement
)

from sailing_data_processor.reporting.elements.layout_elements import (
    SectionElement, ColumnElement, GridElement, TabElement,
    DividerElement, BoxElement, BackgroundElement
)


# 要素タイプと要素クラスのマッピング
_ELEMENT_CLASSES: Dict[ElementType, Type[BaseElement]] = {
    # コンテンツ要素
    ElementType.TEXT: TextElement,
    ElementType.TABLE: TableElement,
    ElementType.LIST: ListElement,
    ElementType.KEY_VALUE: KeyValueElement,
    ElementType.CHART: ChartElement,
    ElementType.MAP: MapElement,
    ElementType.DIAGRAM: DiagramElement,
    ElementType.IMAGE: ImageElement,
    
    # レイアウト要素
    ElementType.SECTION: SectionElement,
    ElementType.COLUMN: ColumnElement,
    ElementType.GRID: GridElement,
    ElementType.TAB: TabElement,
    ElementType.DIVIDER: DividerElement,
    ElementType.BOX: BoxElement,
    ElementType.BACKGROUND: BackgroundElement,


def create_element(model_or_type: Union[ElementModel, ElementType, str], **kwargs) -> Optional[BaseElement]:
    """
    要素を作成
    
    Parameters
    ----------
    model_or_type : Union[ElementModel, ElementType, str]
        要素モデルまたは要素タイプ
    **kwargs : dict
        要素モデルが提供されない場合に使用されるプロパティ
    
    Returns
    -------
    Optional[BaseElement]
        作成された要素、作成できない場合はNone
    """
    if isinstance(model_or_type, ElementModel):
        # 要素モデルが提供された場合
        model = model_or_type
        element_type = model.element_type
    else:
        # 要素タイプが提供された場合
        model = None
        if isinstance(model_or_type, str):
            try:
                element_type = ElementType(model_or_type)
            except ValueError:
                return None
        else:
            element_type = model_or_type
    
    # 要素タイプに対応するクラスを取得
    element_class = _ELEMENT_CLASSES.get(element_type)
    
    if element_class is None:
        return None
    
    # 要素インスタンスを作成して返す
    if model:
        return element_class(model=model)
    else:
        return element_class(element_type=element_type, **kwargs)


def register_element_class(element_type: ElementType, element_class: Type[BaseElement]) -> None:
    """
    要素クラスを登録
    
    Parameters
    ----------
    element_type : ElementType
        要素タイプ
    element_class : Type[BaseElement]
        要素クラス
    """
    _ELEMENT_CLASSES[element_type] = element_class
