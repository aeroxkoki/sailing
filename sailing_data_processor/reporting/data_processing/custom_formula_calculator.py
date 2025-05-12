# -*- coding: utf-8 -*-
"""
Custom Formula Calculator Module - Provides functionality for custom formula calculations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np
import math
import re

from sailing_data_processor.reporting.data_processing.base_calculator import BaseCalculator


class CustomFormulaCalculator(BaseCalculator):
    """
    カスタム計算式計算
    
    ユーザー定義の計算式を評価して新しい値を計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
            
            formulas: Dict[str, str]
                列名と計算式のマッピング
            safe_mode: bool
                安全モード（危険な関数の使用を制限）
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'formulas' not in self.params:
            self.params['formulas'] = {}
        
        if 'safe_mode' not in self.params:
            self.params['safe_mode'] = True
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameにカスタム計算式を適用
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            計算結果のDataFrame
        """
        # 結果用のDataFrameを作成（元のデータをコピー）
        result_df = df.copy()
        
        # カスタム計算式ごとに処理
        formulas = self.params['formulas']
        safe_mode = self.params['safe_mode']
        
        for col_name, formula in formulas.items():
            try:
                # 数式内の列名をDataFrameの列へのアクセスに置換
                processed_formula = self._preprocess_formula(formula, df.columns, safe_mode)
                
                # 数式を評価
                result_df[col_name] = eval(processed_formula, {"df": result_df, "np": np, "math": math})
            
            except Exception as e:
                print(f"Error evaluating formula for column {col_name}: {e}")
                result_df[col_name] = np.nan
        
        return result_df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストにカスタム計算式を適用
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            計算対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            計算結果の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._calculate_dataframe(df)
        
        # 再度リストに変換
        return result_df.to_dict('records')
    
    def _calculate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        辞書にカスタム計算式を適用
        
        Parameters
        ----------
        data : Dict[str, Any]
            計算対象の辞書
            
        Returns
        -------
        Dict[str, Any]
            計算結果の辞書
        """
        # 結果用の辞書を作成（元のデータをコピー）
        result = data.copy()
        
        # カスタム計算式ごとに処理
        formulas = self.params['formulas']
        safe_mode = self.params['safe_mode']
        
        for key, formula in formulas.items():
            try:
                # 数式内の変数名を辞書のキーへのアクセスに置換
                processed_formula = self._preprocess_dict_formula(formula, data.keys(), safe_mode)
                
                # 数式を評価するためのローカル変数を設定
                local_vars = {"data": result, "np": np, "math": math}
                local_vars.update(result)  # 辞書の値を変数として利用可能に
                
                # 数式を評価
                result[key] = eval(processed_formula, {}, local_vars)
            
            except Exception as e:
                print(f"Error evaluating formula for key {key}: {e}")
                result[key] = None
        
        return result
    
    def _preprocess_formula(self, formula: str, columns: List[str], safe_mode: bool) -> str:
        """
        数式を前処理して列名をDataFrameの列へのアクセスに置換
        
        Parameters
        ----------
        formula : str
            計算式
        columns : List[str]
            列名のリスト
        safe_mode : bool
            安全モード
            
        Returns
        -------
        str
            処理後の数式
        """
        # 安全モードが有効な場合、危険な関数呼び出しをチェック
        if safe_mode:
            # 禁止する関数や属性のパターン
            forbidden_patterns = [
                r'__\w+__',         # 特殊メソッド
                r'eval\s*\(',        # eval
                r'exec\s*\(',        # exec
                r'import\s+',        # import
                r'open\s*\(',        # ファイルアクセス
                r'os\.',             # OSモジュール
                r'sys\.',            # sysモジュール
                r'subprocess\.',     # サブプロセス
                r'shutil\.',         # ファイル操作
                r'globals\(\)',      # グローバル変数
                r'locals\(\)'        # ローカル変数
            ]
            
            for pattern in forbidden_patterns:
                if re.search(pattern, formula):
                    raise ValueError(f"Formula contains forbidden pattern: {pattern}")
        
        # 列名を抽出（最長一致を優先）
        sorted_columns = sorted(columns, key=len, reverse=True)
        
        # 列名をDataFrameへのアクセスに置換
        processed_formula = formula
        for col in sorted_columns:
            # 列名が他の列名の部分文字列である場合の問題を回避
            pattern = r'\b' + re.escape(col) + r'\b'
            processed_formula = re.sub(pattern, f"df['{col}']", processed_formula)
        
        return processed_formula
    
    def _preprocess_dict_formula(self, formula: str, keys: List[str], safe_mode: bool) -> str:
        """
        数式を前処理して変数名を辞書のキーへのアクセスに置換
        
        Parameters
        ----------
        formula : str
            計算式
        keys : List[str]
            辞書のキーのリスト
        safe_mode : bool
            安全モード
            
        Returns
        -------
        str
            処理後の数式
        """
        # 安全モードが有効な場合、危険な関数呼び出しをチェック
        if safe_mode:
            # 禁止する関数や属性のパターン
            forbidden_patterns = [
                r'__\w+__',         # 特殊メソッド
                r'eval\s*\(',        # eval
                r'exec\s*\(',        # exec
                r'import\s+',        # import
                r'open\s*\(',        # ファイルアクセス
                r'os\.',             # OSモジュール
                r'sys\.',            # sysモジュール
                r'subprocess\.',     # サブプロセス
                r'shutil\.',         # ファイル操作
                r'globals\(\)',      # グローバル変数
                r'locals\(\)'        # ローカル変数
            ]
            
            for pattern in forbidden_patterns:
                if re.search(pattern, formula):
                    raise ValueError(f"Formula contains forbidden pattern: {pattern}")
        
        # キーを抽出（最長一致を優先）
        sorted_keys = sorted(keys, key=len, reverse=True)
        
        # キーを辞書へのアクセスに置換
        processed_formula = formula
        for key in sorted_keys:
            # キーが他のキーの部分文字列である場合の問題を回避
            pattern = r'\b' + re.escape(key) + r'\b'
            processed_formula = re.sub(pattern, f"data['{key}']", processed_formula)
        
        return processed_formula
