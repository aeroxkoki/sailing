# -*- coding: utf-8 -*-
"""
sailing_data_processor.filters.filter_system

データフィルタリングシステムを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set, Callable, TypeVar, Generic
from datetime import datetime, timedelta
import re
import json

# フィルタリング対象の型
T = TypeVar('T')


class FilterCondition(Generic[T]):
    """
    フィルタ条件クラス
    
    データをフィルタリングするための条件を表現します。
    """
    
    def __init__(self, name: str, field: str, operator: str, value: Any):
        """
        フィルタ条件の初期化
        
        Parameters
        ----------
        name : str
            条件の名前
        field : str
            フィルタの対象フィールド
        operator : str
            演算子（'eq', 'contains', 'gt', 'lt', 'in', 'between'など）
        value : Any
            フィルタ値
        """
        self.name = name
        self.field = field
        self.operator = operator
        self.value = value
    
    def matches(self, item: T) -> bool:
        """
        アイテムがフィルタ条件にマッチするかをチェック
        
        Parameters
        ----------
        item : T
            チェック対象のアイテム
            
        Returns
        -------
        bool
            条件にマッチする場合True
        """
        # フィールド値の取得
        field_value = self._get_field_value(item, self.field)
        
        # 値が取得できない場合はマッチしない
        if field_value is None:
            return False
        
        # 演算子に基づいてマッチングを実行
        if self.operator == 'eq':  # 等しい
            return field_value == self.value
        
        elif self.operator == 'neq':  # 等しくない
            return field_value != self.value
        
        elif self.operator == 'contains':  # 含む
            if isinstance(field_value, str) and isinstance(self.value, str):
                return self.value.lower() in field_value.lower()
            return False
        
        elif self.operator == 'starts_with':  # で始まる
            if isinstance(field_value, str) and isinstance(self.value, str):
                return field_value.lower().startswith(self.value.lower())
            return False
        
        elif self.operator == 'ends_with':  # で終わる
            if isinstance(field_value, str) and isinstance(self.value, str):
                return field_value.lower().endswith(self.value.lower())
            return False
        
        elif self.operator == 'matches':  # 正規表現にマッチ
            if isinstance(field_value, str) and isinstance(self.value, str):
                try:
                    return bool(re.search(self.value, field_value))
                except:
                    return False
            return False
        
        elif self.operator == 'gt':  # より大きい
            return field_value > self.value
        
        elif self.operator == 'gte':  # 以上
            return field_value >= self.value
        
        elif self.operator == 'lt':  # より小さい
            return field_value < self.value
        
        elif self.operator == 'lte':  # 以下
            return field_value <= self.value
        
        elif self.operator == 'in':  # リストに含まれる
            if isinstance(self.value, list):
                return field_value in self.value
            return False
        
        elif self.operator == 'not_in':  # リストに含まれない
            if isinstance(self.value, list):
                return field_value not in self.value
            return False
        
        elif self.operator == 'between':  # 範囲内
            if isinstance(self.value, list) and len(self.value) == 2:
                return self.value[0] <= field_value <= self.value[1]
            return False
        
        elif self.operator == 'exists':  # 存在する
            return field_value is not None
        
        elif self.operator == 'not_exists':  # 存在しない
            return field_value is None
        
        # 日付関連の演算子
        elif self.operator == 'date_eq':  # 日付が等しい
            if isinstance(field_value, str):
                try:
                    date1 = datetime.fromisoformat(field_value).date()
                    date2 = datetime.fromisoformat(self.value).date()
                    return date1 == date2
                except:
                    return False
            return False
        
        elif self.operator == 'date_gt':  # 日付がより後
            if isinstance(field_value, str):
                try:
                    date1 = datetime.fromisoformat(field_value)
                    date2 = datetime.fromisoformat(self.value)
                    return date1 > date2
                except:
                    return False
            return False
        
        elif self.operator == 'date_lt':  # 日付がより前
            if isinstance(field_value, str):
                try:
                    date1 = datetime.fromisoformat(field_value)
                    date2 = datetime.fromisoformat(self.value)
                    return date1 < date2
                except:
                    return False
            return False
        
        elif self.operator == 'date_between':  # 日付が範囲内
            if isinstance(field_value, str) and isinstance(self.value, list) and len(self.value) == 2:
                try:
                    date = datetime.fromisoformat(field_value)
                    start = datetime.fromisoformat(self.value[0])
                    end = datetime.fromisoformat(self.value[1])
                    return start <= date <= end
                except:
                    return False
            return False
        
        elif self.operator == 'has_tag':  # タグを持つ
            if hasattr(item, 'tags'):
                return self.value in item.tags
            return False
        
        elif self.operator == 'has_any_tag':  # いずれかのタグを持つ
            if hasattr(item, 'tags') and isinstance(self.value, list):
                return any(tag in item.tags for tag in self.value)
            return False
        
        elif self.operator == 'has_all_tags':  # すべてのタグを持つ
            if hasattr(item, 'tags') and isinstance(self.value, list):
                return all(tag in item.tags for tag in self.value)
            return False
        
        # サポートされていない演算子の場合
        return False
    
    def _get_field_value(self, item: T, field: str) -> Any:
        """
        アイテムから指定されたフィールドの値を取得
        
        Parameters
        ----------
        item : T
            値を取得するアイテム
        field : str
            フィールド名（ドット区切りでネストされたフィールドも可能）
            
        Returns
        -------
        Any
            フィールドの値、取得できない場合はNone
        """
        # ドット区切りのフィールド名を処理
        fields = field.split('.')
        value = item
        
        try:
            for f in fields:
                if hasattr(value, f):
                    value = getattr(value, f)
                elif isinstance(value, dict) and f in value:
                    value = value[f]
                else:
                    return None
            return value
        except:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        フィルタ条件を辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            フィルタ条件の辞書表現
        """
        return {
            'name': self.name,
            'field': self.field,
            'operator': self.operator,
            'value': self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterCondition':
        """
        辞書からフィルタ条件を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            フィルタ条件の辞書表現
            
        Returns
        -------
        FilterCondition
            作成されたフィルタ条件
        """
        return cls(
            name=data.get('name', ''),
            field=data.get('field', ''),
            operator=data.get('operator', 'eq'),
            value=data.get('value')
        )


class FilterGroup(Generic[T]):
    """
    フィルタグループクラス
    
    複数のフィルタ条件をグループ化します。
    """
    
    def __init__(self, name: str, conditions: List[FilterCondition[T]] = None, operator: str = 'and'):
        """
        フィルタグループの初期化
        
        Parameters
        ----------
        name : str
            グループの名前
        conditions : List[FilterCondition[T]], optional
            フィルタ条件のリスト, by default None
        operator : str, optional
            グループ内の条件の結合演算子（'and'または'or'）, by default 'and'
        """
        self.name = name
        self.conditions = conditions or []
        self.operator = operator  # 'and' または 'or'
    
    def add_condition(self, condition: FilterCondition[T]) -> None:
        """
        フィルタ条件を追加
        
        Parameters
        ----------
        condition : FilterCondition[T]
            追加するフィルタ条件
        """
        self.conditions.append(condition)
    
    def remove_condition(self, index: int) -> Optional[FilterCondition[T]]:
        """
        フィルタ条件を削除
        
        Parameters
        ----------
        index : int
            削除する条件のインデックス
            
        Returns
        -------
        Optional[FilterCondition[T]]
            削除された条件、存在しない場合はNone
        """
        if 0 <= index < len(self.conditions):
            return self.conditions.pop(index)
        return None
    
    def matches(self, item: T) -> bool:
        """
        アイテムがフィルタグループの条件にマッチするかをチェック
        
        Parameters
        ----------
        item : T
            チェック対象のアイテム
            
        Returns
        -------
        bool
            条件にマッチする場合True
        """
        if not self.conditions:
            return True  # 条件がない場合は常にマッチ
        
        if self.operator == 'and':
            return all(condition.matches(item) for condition in self.conditions)
        else:  # 'or'
            return any(condition.matches(item) for condition in self.conditions)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        フィルタグループを辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            フィルタグループの辞書表現
        """
        return {
            'name': self.name,
            'operator': self.operator,
            'conditions': [condition.to_dict() for condition in self.conditions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterGroup':
        """
        辞書からフィルタグループを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            フィルタグループの辞書表現
            
        Returns
        -------
        FilterGroup
            作成されたフィルタグループ
        """
        group = cls(
            name=data.get('name', ''),
            operator=data.get('operator', 'and')
        )
        
        for condition_data in data.get('conditions', []):
            group.add_condition(FilterCondition.from_dict(condition_data))
        
        return group


class FilterSet(Generic[T]):
    """
    フィルタセットクラス
    
    複数のフィルタグループを組み合わせたフィルタセットを表現します。
    """
    
    def __init__(self, name: str, groups: List[FilterGroup[T]] = None, operator: str = 'and'):
        """
        フィルタセットの初期化
        
        Parameters
        ----------
        name : str
            フィルタセットの名前
        groups : List[FilterGroup[T]], optional
            フィルタグループのリスト, by default None
        operator : str, optional
            グループ間の結合演算子（'and'または'or'）, by default 'and'
        """
        self.name = name
        self.groups = groups or []
        self.operator = operator  # 'and' または 'or'
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def add_group(self, group: FilterGroup[T]) -> None:
        """
        フィルタグループを追加
        
        Parameters
        ----------
        group : FilterGroup[T]
            追加するフィルタグループ
        """
        self.groups.append(group)
        self.updated_at = datetime.now().isoformat()
    
    def remove_group(self, index: int) -> Optional[FilterGroup[T]]:
        """
        フィルタグループを削除
        
        Parameters
        ----------
        index : int
            削除するグループのインデックス
            
        Returns
        -------
        Optional[FilterGroup[T]]
            削除されたグループ、存在しない場合はNone
        """
        if 0 <= index < len(self.groups):
            self.updated_at = datetime.now().isoformat()
            return self.groups.pop(index)
        return None
    
    def matches(self, item: T) -> bool:
        """
        アイテムがフィルタセットの条件にマッチするかをチェック
        
        Parameters
        ----------
        item : T
            チェック対象のアイテム
            
        Returns
        -------
        bool
            条件にマッチする場合True
        """
        if not self.groups:
            return True  # グループがない場合は常にマッチ
        
        if self.operator == 'and':
            return all(group.matches(item) for group in self.groups)
        else:  # 'or'
            return any(group.matches(item) for group in self.groups)
    
    def filter_items(self, items: List[T]) -> List[T]:
        """
        アイテムリストをフィルタリング
        
        Parameters
        ----------
        items : List[T]
            フィルタリング対象のアイテムリスト
            
        Returns
        -------
        List[T]
            フィルタ条件にマッチするアイテムのリスト
        """
        return [item for item in items if self.matches(item)]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        フィルタセットを辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            フィルタセットの辞書表現
        """
        return {
            'name': self.name,
            'operator': self.operator,
            'groups': [group.to_dict() for group in self.groups],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def to_json(self) -> str:
        """
        フィルタセットをJSON文字列に変換
        
        Returns
        -------
        str
            JSON文字列
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterSet':
        """
        辞書からフィルタセットを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            フィルタセットの辞書表現
            
        Returns
        -------
        FilterSet
            作成されたフィルタセット
        """
        filter_set = cls(
            name=data.get('name', ''),
            operator=data.get('operator', 'and')
        )
        
        for group_data in data.get('groups', []):
            filter_set.add_group(FilterGroup.from_dict(group_data))
        
        filter_set.created_at = data.get('created_at', filter_set.created_at)
        filter_set.updated_at = data.get('updated_at', filter_set.updated_at)
        
        return filter_set
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FilterSet':
        """
        JSON文字列からフィルタセットを作成
        
        Parameters
        ----------
        json_str : str
            フィルタセットのJSON文字列
            
        Returns
        -------
        FilterSet
            作成されたフィルタセット
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class FilterManager:
    """
    フィルタ管理クラス
    
    フィルタセットの保存と読み込みを管理します。
    """
    
    def __init__(self, storage_path: str = "filters"):
        """
        フィルタ管理クラスの初期化
        
        Parameters
        ----------
        storage_path : str, optional
            フィルタの保存パス, by default "filters"
        """
        self.storage_path = storage_path
        self.filter_sets: Dict[str, FilterSet] = {}
        
        # ここで実際のファイルシステムからフィルタを読み込む処理を追加できる
    
    def add_filter_set(self, filter_set: FilterSet) -> None:
        """
        フィルタセットを追加
        
        Parameters
        ----------
        filter_set : FilterSet
            追加するフィルタセット
        """
        self.filter_sets[filter_set.name] = filter_set
        # 保存処理を追加できる
    
    def get_filter_set(self, name: str) -> Optional[FilterSet]:
        """
        名前でフィルタセットを取得
        
        Parameters
        ----------
        name : str
            フィルタセット名
            
        Returns
        -------
        Optional[FilterSet]
            フィルタセット、存在しない場合はNone
        """
        return self.filter_sets.get(name)
    
    def remove_filter_set(self, name: str) -> bool:
        """
        フィルタセットを削除
        
        Parameters
        ----------
        name : str
            削除するフィルタセット名
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if name in self.filter_sets:
            del self.filter_sets[name]
            # 削除処理を追加できる
            return True
        return False
    
    def get_all_filter_sets(self) -> List[FilterSet]:
        """
        すべてのフィルタセットを取得
        
        Returns
        -------
        List[FilterSet]
            フィルタセットのリスト
        """
        return list(self.filter_sets.values())


# プリセットフィルタの作成ヘルパー関数
def create_date_range_filter(name: str, field: str, start_date: str, end_date: str) -> FilterSet:
    """
    日付範囲フィルタを作成
    
    Parameters
    ----------
    name : str
        フィルタ名
    field : str
        日付フィールド名
    start_date : str
        開始日（ISO形式）
    end_date : str
        終了日（ISO形式）
        
    Returns
    -------
    FilterSet
        作成されたフィルタセット
    """
    condition = FilterCondition(
        name=f"{start_date}から{end_date}まで",
        field=field,
        operator="date_between",
        value=[start_date, end_date]
    )
    
    group = FilterGroup(name=f"{field}の日付範囲")
    group.add_condition(condition)
    
    filter_set = FilterSet(name=name)
    filter_set.add_group(group)
    
    return filter_set


def create_tag_filter(name: str, tags: List[str], match_all: bool = False) -> FilterSet:
    """
    タグフィルタを作成
    
    Parameters
    ----------
    name : str
        フィルタ名
    tags : List[str]
        フィルタするタグのリスト
    match_all : bool, optional
        すべてのタグにマッチさせるかどうか, by default False
        
    Returns
    -------
    FilterSet
        作成されたフィルタセット
    """
    operator = "has_all_tags" if match_all else "has_any_tag"
    
    condition = FilterCondition(
        name=f"タグ: {', '.join(tags)}",
        field="tags",
        operator=operator,
        value=tags
    )
    
    group = FilterGroup(name="タグフィルタ")
    group.add_condition(condition)
    
    filter_set = FilterSet(name=name)
    filter_set.add_group(group)
    
    return filter_set


def create_text_search_filter(name: str, field: str, query: str) -> FilterSet:
    """
    テキスト検索フィルタを作成
    
    Parameters
    ----------
    name : str
        フィルタ名
    field : str
        検索対象フィールド
    query : str
        検索クエリ
        
    Returns
    -------
    FilterSet
        作成されたフィルタセット
    """
    condition = FilterCondition(
        name=f"{field}に「{query}」を含む",
        field=field,
        operator="contains",
        value=query
    )
    
    group = FilterGroup(name="テキスト検索")
    group.add_condition(condition)
    
    filter_set = FilterSet(name=name)
    filter_set.add_group(group)
    
    return filter_set
