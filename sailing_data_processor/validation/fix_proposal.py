# -*- coding: utf-8 -*-
"""
修正提案モジュール
データクリーニングのための修正提案クラスを定義します。
"""

from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FixProposal:
    """
    修正提案クラス
    
    属性
    -----
    fix_type : str
        修正タイプ（'interpolate', 'remove', 'adjust', 'replace'）
    target_indices : List[int]
        対象のインデックスリスト
    columns : List[str]
        対象のカラムリスト
    description : str
        修正内容の説明
    severity : str
        重要度（'high', 'medium', 'low'）
    auto_fixable : bool
        自動修正可能かどうか
    fix_function : Optional[Callable]
        修正を適用する関数
    metadata : Dict[str, Any]
        追加のメタデータ
    """
    
    def __init__(self, 
                 fix_type: str,
                 target_indices: List[int],
                 columns: List[str],
                 description: str,
                 severity: str = 'medium',
                 auto_fixable: bool = False,
                 fix_function: Optional[Callable] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        fix_type : str
            修正タイプ（'interpolate', 'remove', 'adjust', 'replace'）
        target_indices : List[int]
            対象のインデックスリスト
        columns : List[str]
            対象のカラムリスト
        description : str
            修正内容の説明
        severity : str, optional
            重要度（'high', 'medium', 'low'）, by default 'medium'
        auto_fixable : bool, optional
            自動修正可能かどうか, by default False
        fix_function : Optional[Callable], optional
            修正を適用する関数, by default None
        metadata : Optional[Dict[str, Any]], optional
            追加のメタデータ, by default None
        """
        self.fix_type = fix_type
        self.target_indices = target_indices
        self.columns = columns
        self.description = description
        self.severity = severity
        self.auto_fixable = auto_fixable
        self.fix_function = fix_function
        self.metadata = metadata or {}
        self.fix_id = f"{fix_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(target_indices))}"
    
    def apply(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        修正を適用
        
        Parameters
        ----------
        data : pd.DataFrame
            元のデータフレーム
            
        Returns
        -------
        pd.DataFrame
            修正後のデータフレーム
        """
        if self.fix_function:
            return self.fix_function(data, self.target_indices, self.columns, self.metadata)
        
        # 修正関数が指定されていない場合は、デフォルトの修正ロジックを使用
        fixed_data = data.copy()
        
        if self.fix_type == 'interpolate':
            # 欠損値または指定された値を補間
            for col in self.columns:
                if col in fixed_data.columns:
                    # 補間方法を決定
                    method = self.metadata.get('method', 'linear')
                    
                    # 指定されたインデックスに対して補間
                    mask = fixed_data.index.isin(self.target_indices)
                    fixed_data.loc[mask, col] = np.nan  # 一時的にNaNに設定
                    fixed_data[col] = fixed_data[col].interpolate(method=method)
        
        elif self.fix_type == 'remove':
            # 指定されたインデックスの行を削除
            fixed_data = fixed_data.drop(self.target_indices)
            
            # インデックスをリセット
            if self.metadata.get('reset_index', True):
                fixed_data = fixed_data.reset_index(drop=True)
        
        elif self.fix_type == 'adjust':
            # 値を調整（時間ずらしなど）
            adjustment = self.metadata.get('adjustment', 0)
            
            for col in self.columns:
                if col in fixed_data.columns:
                    for idx in self.target_indices:
                        if idx in fixed_data.index:
                            # 時間カラムの場合
                            if col == 'timestamp' and isinstance(adjustment, (int, float)):
                                fixed_data.loc[idx, col] += timedelta(seconds=adjustment)
                            # 数値カラムの場合
                            elif pd.api.types.is_numeric_dtype(fixed_data[col]):
                                fixed_data.loc[idx, col] += adjustment
        
        elif self.fix_type == 'replace':
            # 値を置換
            replacement = self.metadata.get('replacement')
            
            if replacement is not None:
                for col in self.columns:
                    if col in fixed_data.columns:
                        fixed_data.loc[self.target_indices, col] = replacement
        
        return fixed_data
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            修正提案の辞書表現
        """
        return {
            'fix_id': self.fix_id,
            'fix_type': self.fix_type,
            'target_indices': self.target_indices,
            'columns': self.columns,
            'description': self.description,
            'severity': self.severity,
            'auto_fixable': self.auto_fixable,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FixProposal':
        """
        辞書から修正提案を作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            修正提案の辞書表現
            
        Returns
        -------
        FixProposal
            作成された修正提案
        """
        fix = cls(
            fix_type=data['fix_type'],
            target_indices=data['target_indices'],
            columns=data['columns'],
            description=data['description'],
            severity=data['severity'],
            auto_fixable=data['auto_fixable'],
            metadata=data.get('metadata', {})
        )
        
        if 'fix_id' in data:
            fix.fix_id = data['fix_id']
        
        return fix
