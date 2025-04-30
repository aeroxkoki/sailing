# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.visualization import ValidationVisualization

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


class DataCleaner:
    """
    データクリーニングクラス
    
    データ検証結果に基づいて修正提案を生成し、選択された修正を適用します。
    """
    
    def __init__(self, validator: DataValidator = None, container: GPSDataContainer = None):
        """
        初期化
        
        Parameters
        ----------
        validator : DataValidator, optional
            データ検証器, by default None
        container : GPSDataContainer, optional
            GPSデータコンテナ, by default None
        """
        self.validator = validator
        self.container = container
        self.fix_proposals = []
        self.applied_fixes = []
        self.fix_history = []
        
        # 検証器とコンテナが与えられた場合、修正提案を生成
        if validator and container:
            self.generate_fix_proposals()
    
    def set_data(self, validator: DataValidator, container: GPSDataContainer) -> None:
        """
        データを設定
        
        Parameters
        ----------
        validator : DataValidator
            データ検証器
        container : GPSDataContainer
            GPSデータコンテナ
        """
        self.validator = validator
        self.container = container
        self.fix_proposals = []
        self.applied_fixes = []
        
        # 修正提案を生成
        self.generate_fix_proposals()
    
    def generate_fix_proposals(self) -> List[FixProposal]:
        """
        検証結果に基づいて修正提案を生成
        
        Returns
        -------
        List[FixProposal]
            生成された修正提案リスト
        """
        if not self.validator or not self.container:
            return []
        
        # 検証が実行されていない場合は実行
        if not self.validator.validation_results:
            self.validator.validate(self.container)
        
        proposals = []
        data = self.container.data
        
        # 各検証結果から修正提案を生成
        for result in self.validator.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                details = result["details"]
                severity = "high" if result["severity"] == "error" else "medium" if result["severity"] == "warning" else "low"
                
                # 重複タイムスタンプの修正提案
                if "No Duplicate Timestamps" in rule_name:
                    if "duplicate_indices" in details:
                        for ts, indices in details["duplicate_indices"].items():
                            if len(indices) > 1:
                                # タイムスタンプをずらす修正提案
                                proposal = FixProposal(
                                    fix_type="adjust",
                                    target_indices=indices[1:],  # 最初のものを除く
                                    columns=["timestamp"],
                                    description=f"重複しているタイムスタンプ '{ts}' を1ミリ秒ずつずらす",
                                    severity=severity,
                                    auto_fixable=True,
                                    metadata={
                                        "adjustment": 0.001,  # 1ミリ秒
                                        "timestamp": ts
                                    })
                                proposals.append(proposal)
                                
                                # 重複を削除する修正提案
                                proposal = FixProposal(
                                    fix_type="remove",
                                    target_indices=indices[1:],  # 最初のものを除く
                                    columns=[],
                                    description=f"重複しているタイムスタンプ '{ts}' の行を削除",
                                    severity=severity,
                                    auto_fixable=True,
                                    metadata={
                                        "timestamp": ts
                                    }
                                )
                                proposals.append(proposal)
                
                # 欠損値の修正提案
                elif "No Null Values Check" in rule_name:
                    if "null_indices" in details:
                        for col, indices in details["null_indices"].items():
                            if indices:
                                # 線形補間による修正提案
                                proposal = FixProposal(
                                    fix_type="interpolate",
                                    target_indices=indices,
                                    columns=[col],
                                    description=f"カラム '{col}' の欠損値を線形補間で修正",
                                    severity=severity,
                                    auto_fixable=True,
                                    metadata={
                                        "method": "linear"
                                    }
                                )
                                proposals.append(proposal)
                                
                                # 削除による修正提案
                                proposal = FixProposal(
                                    fix_type="remove",
                                    target_indices=indices,
                                    columns=[],
                                    description=f"カラム '{col}' に欠損値を含む行を削除",
                                    severity=severity,
                                    auto_fixable=True
                                )
                                proposals.append(proposal)
                
                # 値範囲外の修正提案
                elif "Value Range Check" in rule_name:
                    if "out_of_range_indices" in details:
                        col = details.get("column", "")
                        min_val = details.get("min_value")
                        max_val = details.get("max_value")
                        indices = details["out_of_range_indices"]
                        
                        if indices and col:
                            # 範囲内に収める修正提案
                            description = f"カラム '{col}' の範囲外の値を"
                            replacement = None
                            
                            if min_val is not None and max_val is not None:
                                description += f"{min_val}～{max_val}の範囲内に収める"
                                # 範囲外の値をクリップ
                                def clip_values(df, idx_list, cols, meta):
                                    min_v = meta.get('min_value')
                                    max_v = meta.get('max_value')
                                    col_name = cols[0]
                                    
                                    df_copy = df.copy()
                                    for idx in idx_list:
                                        if idx in df_copy.index:
                                            val = df_copy.loc[idx, col_name]
                                            if val < min_v:
                                                df_copy.loc[idx, col_name] = min_v
                                            elif val > max_v:
                                                df_copy.loc[idx, col_name] = max_v
                                    
                                    return df_copy
                                
                                proposal = FixProposal(
                                    fix_type="replace",
                                    target_indices=indices,
                                    columns=[col],
                                    description=description,
                                    severity=severity,
                                    auto_fixable=True,
                                    fix_function=clip_values,
                                    metadata={
                                        "min_value": min_val,
                                        "max_value": max_val
                                    }
                                )
                                proposals.append(proposal)
                            
                            # 削除による修正提案
                            proposal = FixProposal(
                                fix_type="remove",
                                target_indices=indices,
                                columns=[],
                                description=f"カラム '{col}' に範囲外の値を含む行を削除",
                                severity=severity,
                                auto_fixable=True
                            )
                            proposals.append(proposal)
                
                # 空間的整合性問題の修正提案
                elif "Spatial Consistency Check" in rule_name:
                    if "anomaly_indices" in details:
                        indices = details["anomaly_indices"]
                        
                        if indices:
                            # 異常な空間的ジャンプを削除
                            proposal = FixProposal(
                                fix_type="remove",
                                target_indices=indices,
                                columns=[],
                                description="異常な空間的ジャンプのあるデータポイントを削除",
                                severity=severity,
                                auto_fixable=True
                            )
                            proposals.append(proposal)
                            
                            # 線形補間で修正
                            proposal = FixProposal(
                                fix_type="interpolate",
                                target_indices=indices,
                                columns=["latitude", "longitude"],
                                description="異常な空間的ジャンプのあるデータポイントの位置を線形補間",
                                severity=severity,
                                auto_fixable=True,
                                metadata={
                                    "method": "linear"
                                }
                            )
                            proposals.append(proposal)
                
                # 時間的整合性問題の修正提案
                elif "Temporal Consistency Check" in rule_name:
                    # 時間の逆行
                    if "reverse_indices" in details and details["reverse_indices"]:
                        indices = details["reverse_indices"]
                        
                        # 逆行するタイムスタンプを削除
                        proposal = FixProposal(
                            fix_type="remove",
                            target_indices=indices,
                            columns=[],
                            description="時間的に逆行しているデータポイントを削除",
                            severity=severity,
                            auto_fixable=True
                        )
                        proposals.append(proposal)
                        
                        # 逆行するタイムスタンプを修正
                        if "reverse_details" in details:
                            for detail in details["reverse_details"]:
                                idx = detail.get("original_index")
                                prev_ts = detail.get("prev_timestamp")
                                curr_ts = detail.get("curr_timestamp")
                                
                                if idx is not None and prev_ts and curr_ts:
                                    # 前のタイムスタンプの1秒後に設定
                                    if isinstance(prev_ts, str):
                                        prev_ts = pd.to_datetime(prev_ts)
                                    
                                    new_ts = prev_ts + timedelta(seconds=1)
                                    
                                    proposal = FixProposal(
                                        fix_type="replace",
                                        target_indices=[idx],
                                        columns=["timestamp"],
                                        description=f"逆行しているタイムスタンプを修正（{curr_ts} → {new_ts}）",
                                        severity=severity,
                                        auto_fixable=True,
                                        metadata={
                                            "replacement": new_ts
                                        }
                                    )
                                    proposals.append(proposal)
                    
                    # 時間ギャップ
                    if "gap_indices" in details and details["gap_indices"]:
                        # タイムギャップの場合は通常は修正の必要はないので、提案は生成しない
                        # または、必要に応じてログをとるなどの軽い提案を生成
                        pass
        
        # 修正提案を保存
        self.fix_proposals = proposals
        
        return proposals
    
    def apply_fix(self, fix_proposal: Union[FixProposal, str]) -> GPSDataContainer:
        """
        修正提案を適用
        
        Parameters
        ----------
        fix_proposal : Union[FixProposal, str]
            適用する修正提案またはfix_id
            
        Returns
        -------
        GPSDataContainer
            修正後のデータコンテナ
        """
        if not self.container:
            raise ValueError("データコンテナが設定されていません")
        
        # fix_idの場合は対応する修正提案を取得
        if isinstance(fix_proposal, str):
            fix_id = fix_proposal
            fix_proposal = next((f for f in self.fix_proposals if f.fix_id == fix_id), None)
            
            if not fix_proposal:
                raise ValueError(f"修正提案 ID '{fix_id}' が見つかりません")
        
        # 修正を適用
        fixed_data = fix_proposal.apply(self.container.data)
        
        # 修正履歴に追加
        fix_info = fix_proposal.to_dict()
        fix_info['applied_at'] = datetime.now().isoformat()
        self.applied_fixes.append(fix_info)
        self.fix_history.append(fix_info)
        
        # 新しいコンテナを作成
        new_metadata = self.container.metadata.copy()
        
        # 修正履歴をメタデータに追加
        if 'fix_history' not in new_metadata:
            new_metadata['fix_history'] = []
        
        new_metadata['fix_history'].append(fix_info)
        new_metadata['last_fixed_at'] = datetime.now().isoformat()
        
        # 修正されたデータコンテナを返す
        return GPSDataContainer(fixed_data, new_metadata)
    
    def apply_batch_fixes(self, fix_ids: List[str]) -> GPSDataContainer:
        """
        複数の修正提案をバッチで適用
        
        Parameters
        ----------
        fix_ids : List[str]
            適用する修正提案IDのリスト
            
        Returns
        -------
        GPSDataContainer
            修正後のデータコンテナ
        """
        if not self.container:
            raise ValueError("データコンテナが設定されていません")
        
        # 修正するコンテナを初期化
        container = self.container
        
        # 各修正を順番に適用
        for fix_id in fix_ids:
            container = self.apply_fix(fix_id)
            
            # コンテナを更新
            self.container = container
            
            # 修正提案を再生成（前の修正によって問題が解決されている可能性があるため）
            self.generate_fix_proposals()
        
        return container
    
    def get_fixes_by_problem_type(self, problem_type: str) -> List[FixProposal]:
        """
        問題タイプ別の修正提案を取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
            
        Returns
        -------
        List[FixProposal]
            該当する修正提案のリスト
        """
        type_mapping = {
            "missing_data": ["No Null Values Check"],
            "out_of_range": ["Value Range Check"],
            "duplicates": ["No Duplicate Timestamps"],
            "spatial_anomalies": ["Spatial Consistency Check"],
            "temporal_anomalies": ["Temporal Consistency Check"]
        }
        if problem_type in type_mapping:
            rule_prefixes = type_mapping[problem_type]
            
            return [fix for fix in self.fix_proposals 
                   if any(fix.metadata.get('rule_name', '').startswith(prefix) 
                          for prefix in rule_prefixes)]
        
        return []
    
    def get_auto_fixable_proposals(self) -> List[FixProposal]:
        """
        自動修正可能な提案を取得
        
        Returns
        -------
        List[FixProposal]
            自動修正可能な提案のリスト
        """
        return [fix for fix in self.fix_proposals if fix.auto_fixable]
    
    def get_fix_by_id(self, fix_id: str) -> Optional[FixProposal]:
        """
        ID指定で修正提案を取得
        
        Parameters
        ----------
        fix_id : str
            修正提案ID
            
        Returns
        -------
        Optional[FixProposal]
            該当する修正提案（見つからない場合はNone）
        """
        return next((fix for fix in self.fix_proposals if fix.fix_id == fix_id), None)
    
    def undo_last_fix(self) -> Optional[GPSDataContainer]:
        """
        最後に適用した修正を元に戻す
        
        Returns
        -------
        Optional[GPSDataContainer]
            修正前のデータコンテナ（戻せない場合はNone）
        """
        if not self.container or 'fix_history' not in self.container.metadata:
            return None
        
        fix_history = self.container.metadata['fix_history']
        
        if not fix_history:
            return None
        
        # 最後の修正を取り除く
        fix_history.pop()
        
        # 元のデータがメタデータに保存されている場合は復元
        if 'original_data_hash' in self.container.metadata:
            # ここでは元のデータの復元方法が必要
            # 例えば、元のデータをファイルから読み込むなど
            pass
        
        # 適用済み修正リストからも削除
        if self.applied_fixes:
            self.applied_fixes.pop()
        
        # 履歴からも削除
        if self.fix_history:
            self.fix_history.pop()
        
        # 現在は簡易的な実装で、本当の元に戻す機能は追加の実装が必要
        return None
    
    def get_fix_history(self) -> List[Dict[str, Any]]:
        """
        修正履歴を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            修正履歴
        """
        # コンテナからも履歴を取得
        if self.container and 'fix_history' in self.container.metadata:
            return self.container.metadata['fix_history']
        
        return self.fix_history
    
    def get_fix_summary(self) -> Dict[str, Any]:
        """
        修正サマリーを取得
        
        Returns
        -------
        Dict[str, Any]
            修正サマリー
        """
        history = self.get_fix_history()
        
        # 修正タイプごとのカウント
        fix_type_counts = {}
        for fix in history:
            fix_type = fix.get('fix_type', '')
            fix_type_counts[fix_type] = fix_type_counts.get(fix_type, 0) + 1
        
        # 対象カラムごとのカウント
        column_counts = {}
        for fix in history:
            for col in fix.get('columns', []):
                column_counts[col] = column_counts.get(col, 0) + 1
        
        return {
            'total_fixes': len(history),
            'fix_type_counts': fix_type_counts,
            'column_counts': column_counts,
            'first_fixed_at': history[0]['applied_at'] if history else None,
            'last_fixed_at': history[-1]['applied_at'] if history else None
