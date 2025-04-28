# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np
import math
import re


class BaseCalculator:
    """
    計算処理の基底クラス
    
    様々な計算処理の基底となるクラスを提供します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
        """
        self.params = params or {}
    
    def calculate(self, data: Any) -> Any:
        """
        データを計算
        
        Parameters
        ----------
        data : Any
            計算対象データ
            
        Returns
        -------
        Any
            計算結果
        """
        # 特定のデータ型に対応した計算処理を呼び出す
        if isinstance(data, pd.DataFrame):
            return self._calculate_dataframe(data)
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return self._calculate_dict_list(data)
            else:
                return self._calculate_list(data)
        elif isinstance(data, dict):
            return self._calculate_dict(data)
        else:
            return data
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameの計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            計算結果のDataFrame
        """
        # 具体的な計算はサブクラスで実装
        return df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストの計算
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            計算対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            計算結果の辞書リスト
        """
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._calculate_dataframe(df)
        return result_df.to_dict('records')
    
    def _calculate_list(self, data: List[Any]) -> List[Any]:
        """
        リストの計算
        
        Parameters
        ----------
        data : List[Any]
            計算対象のリスト
            
        Returns
        -------
        List[Any]
            計算結果のリスト
        """
        # 具体的な計算はサブクラスで実装
        return data
    
    def _calculate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        辞書の計算
        
        Parameters
        ----------
        data : Dict[str, Any]
            計算対象の辞書
            
        Returns
        -------
        Dict[str, Any]
            計算結果の辞書
        """
        # 具体的な計算はサブクラスで実装
        return data


class PerformanceCalculator(BaseCalculator):
    """
    パフォーマンス指標計算
    
    セーリングのパフォーマンス指標を計算します。
    VMG（風上/風下方向の有効速度）、対ターゲット速度比率、タッキング効率などを計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
            
            speed_column: str
                速度の列名
            direction_column: str
                方向の列名
            wind_direction_column: str
                風向の列名
            wind_speed_column: str
                風速の列名
            target_speeds: Dict[float, float]
                風速に対するターゲット速度の辞書
            metrics: List[str]
                計算する指標のリスト ('vmg', 'target_ratio', 'tacking_efficiency')
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'speed_column' not in self.params:
            self.params['speed_column'] = 'speed'
        
        if 'direction_column' not in self.params:
            self.params['direction_column'] = 'direction'
        
        if 'wind_direction_column' not in self.params:
            self.params['wind_direction_column'] = 'wind_direction'
        
        if 'wind_speed_column' not in self.params:
            self.params['wind_speed_column'] = 'wind_speed'
        
        if 'metrics' not in self.params:
            self.params['metrics'] = ['vmg', 'target_ratio']
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameのパフォーマンス指標を計算
        
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
        
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column'],
            self.params['wind_direction_column']
        ]
        
        # VMGの計算には風向と艇の進行方向が必要
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 欠損列がある場合は、その指標の計算をスキップ
            if 'vmg' in self.params['metrics']:
                print(f"Warning: Cannot calculate VMG due to missing columns: {missing_columns}")
            required_for_vmg = False
        else:
            required_for_vmg = True
        
        # ターゲット速度比の計算には風速と艇速が必要
        if (self.params['speed_column'] not in df.columns or 
            self.params['wind_speed_column'] not in df.columns):
            if 'target_ratio' in self.params['metrics']:
                print(f"Warning: Cannot calculate target ratio due to missing columns: {self.params['speed_column']} or {self.params['wind_speed_column']}")
            required_for_target = False
        else:
            required_for_target = True
        
        # 指標の計算
        metrics = self.params['metrics']
        
        # VMG（Velocity Made Good）の計算
        if 'vmg' in metrics and required_for_vmg:
            speed_col = self.params['speed_column']
            direction_col = self.params['direction_column']
            wind_direction_col = self.params['wind_direction_column']
            
            # 風向と艇の進行方向の差（角度）を計算
            result_df['wind_angle'] = (result_df[wind_direction_col] - result_df[direction_col]) % 360
            
            # 180度を超える角度は反対側からの角度として調整
            result_df.loc[result_df['wind_angle'] > 180, 'wind_angle'] = 360 - result_df.loc[result_df['wind_angle'] > 180, 'wind_angle']
            
            # VMGの計算
            # 風上方向のVMG: speed * cos(wind_angle)
            # 風下方向のVMG: speed * cos(180 - wind_angle)
            result_df['vmg_upwind'] = result_df[speed_col] * np.cos(np.radians(result_df['wind_angle']))
            result_df['vmg_downwind'] = result_df[speed_col] * np.cos(np.radians(180 - result_df['wind_angle']))
            
            # 正のVMG値は風上方向、負のVMG値は風下方向の効率を表す
            result_df['vmg'] = result_df['vmg_upwind']
            
            # VMG効率（実際のVMGと理論上の最大VMGの比率）
            # 風上と風下の区別
            upwind_mask = result_df['wind_angle'] <= 90
            downwind_mask = ~upwind_mask
            
            # 理論上の最大VMG（仮の値、実際はボートの極曲線から導出）
            # 風上：45度で最大VMG、風下：135度で最大VMG
            optimal_upwind_angle = 45  # 実際のボートによって異なる
            optimal_downwind_angle = 135  # 実際のボートによって異なる
            
            # VMG効率の計算
            # 風上の場合
            if 'vmg_efficiency' not in result_df.columns:
                result_df['vmg_efficiency'] = np.nan
                
            upwind_optimal_vmg = result_df.loc[upwind_mask, speed_col] * np.cos(np.radians(optimal_upwind_angle))
            result_df.loc[upwind_mask, 'vmg_efficiency'] = (
                result_df.loc[upwind_mask, 'vmg_upwind'] / upwind_optimal_vmg
            )
            
            # 風下の場合
            downwind_optimal_vmg = result_df.loc[downwind_mask, speed_col] * np.cos(np.radians(180 - optimal_downwind_angle))
            result_df.loc[downwind_mask, 'vmg_efficiency'] = (
                result_df.loc[downwind_mask, 'vmg_downwind'] / downwind_optimal_vmg
            )
        
        # ターゲット速度比の計算
        if 'target_ratio' in metrics and required_for_target:
            speed_col = self.params['speed_column']
            wind_speed_col = self.params['wind_speed_column']
            target_speeds = self.params.get('target_speeds', {})
            
            # ターゲット速度を計算
            result_df['target_speed'] = np.nan
            
            # ターゲット速度が指定されている場合
            if target_speeds:
                # 風速ごとのターゲット速度を設定
                for wind_speed, target_speed in target_speeds.items():
                    result_df.loc[result_df[wind_speed_col] == wind_speed, 'target_speed'] = target_speed
                
                # 未設定の風速に対して補間
                # ソートされた風速のリスト
                wind_speeds = sorted(target_speeds.keys())
                
                for i, row in result_df.iterrows():
                    wind_speed = row[wind_speed_col]
                    if np.isnan(row['target_speed']):
                        # 補間
                        if wind_speed < wind_speeds[0]:
                            # 最小風速以下の場合
                            ratio = wind_speed / wind_speeds[0]
                            result_df.loc[i, 'target_speed'] = target_speeds[wind_speeds[0]] * ratio
                        elif wind_speed > wind_speeds[-1]:
                            # 最大風速以上の場合
                            result_df.loc[i, 'target_speed'] = target_speeds[wind_speeds[-1]]
                        else:
                            # 中間の風速の場合、線形補間
                            lower_idx = next(j for j, ws in enumerate(wind_speeds) if ws > wind_speed) - 1
                            upper_idx = lower_idx + 1
                            
                            lower_wind = wind_speeds[lower_idx]
                            upper_wind = wind_speeds[upper_idx]
                            
                            # 線形補間
                            ratio = (wind_speed - lower_wind) / (upper_wind - lower_wind)
                            lower_target = target_speeds[lower_wind]
                            upper_target = target_speeds[upper_wind]
                            
                            result_df.loc[i, 'target_speed'] = lower_target + ratio * (upper_target - lower_target)
            
            # ターゲット速度が指定されていない場合は、風速の一定割合をターゲットとして設定
            else:
                # 仮のターゲット速度として風速の70%を設定
                result_df['target_speed'] = result_df[wind_speed_col] * 0.7
            
            # ターゲット速度比の計算
            result_df['target_ratio'] = result_df[speed_col] / result_df['target_speed']
        
        # タッキング効率の計算
        if 'tacking_efficiency' in metrics:
            # タッキングの検出とその効率計算は複雑なため、別途実装
            # ここでは簡略的な実装として、方向の変化が大きい箇所をタッキングとして検出
            
            # direction_colが存在する場合のみ計算
            if self.params['direction_column'] in df.columns:
                direction_col = self.params['direction_column']
                speed_col = self.params['speed_column']
                
                # 方向の変化を計算
                result_df['direction_diff'] = result_df[direction_col].diff().abs()
                
                # 方向の変化が大きい箇所（例：60度以上）をタッキングとして検出
                tacking_threshold = self.params.get('tacking_threshold', 60)
                result_df['is_tacking'] = result_df['direction_diff'] > tacking_threshold
                
                # タッキング前後の速度の比率を計算
                result_df['speed_after_tack'] = np.nan
                result_df['tacking_efficiency'] = np.nan
                
                # タッキング位置を特定
                tack_indices = result_df.index[result_df['is_tacking']]
                
                # 各タッキングの効率を計算
                for tack_idx in tack_indices:
                    if tack_idx > 0 and tack_idx < len(result_df) - 1:
                        # タッキング前の速度（数ポイントの平均）
                        pre_indices = range(max(0, tack_idx - 5), tack_idx)
                        speed_before = result_df.loc[pre_indices, speed_col].mean()
                        
                        # タッキング後の速度（数ポイントの平均）
                        post_indices = range(tack_idx + 1, min(len(result_df), tack_idx + 6))
                        speed_after = result_df.loc[post_indices, speed_col].mean()
                        
                        # タッキング後の速度を記録
                        result_df.loc[tack_idx, 'speed_after_tack'] = speed_after
                        
                        # タッキング効率を計算（タッキング後の速度 / タッキング前の速度）
                        if speed_before > 0:
                            result_df.loc[tack_idx, 'tacking_efficiency'] = speed_after / speed_before
        
        return result_df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストのパフォーマンス指標を計算
        
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


class StatisticalCalculator(BaseCalculator):
    """
    統計値計算
    
    データの統計値を計算します。
    平均、中央値、標準偏差、パーセンタイル、トレンドなどを計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
            
            columns: List[str]
                計算対象の列リスト
            metrics: List[str]
                計算する統計指標のリスト ('mean', 'median', 'std', 'min', 'max', 'percentile', 'trend')
            percentiles: List[float]
                計算するパーセンタイル値のリスト (0-100)
            window_size: int
                移動統計値の窓サイズ
            trend_method: str
                トレンド計算方法 ('linear', 'polynomial')
            trend_degree: int
                多項式トレンドの次数
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'metrics' not in self.params:
            self.params['metrics'] = ['mean', 'median', 'std', 'min', 'max']
        
        if 'percentiles' not in self.params:
            self.params['percentiles'] = [25, 50, 75]
        
        if 'window_size' not in self.params:
            self.params['window_size'] = 10
        
        if 'trend_method' not in self.params:
            self.params['trend_method'] = 'linear'
        
        if 'trend_degree' not in self.params:
            self.params['trend_degree'] = 1
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameの統計値を計算
        
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
        
        # 計算対象の列を決定
        columns = self.params.get('columns', None)
        if columns is None:
            # 数値列のみを計算対象にする
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            # 存在する列のみを対象に
            columns = [col for col in columns if col in df.columns]
        
        # 統計指標ごとの計算
        metrics = self.params['metrics']
        
        for col in columns:
            # 平均値
            if 'mean' in metrics:
                result_df[f'{col}_mean'] = df[col].mean()
                
                # 移動平均
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_mean'] = df[col].rolling(window=window_size, center=True).mean()
            
            # 中央値
            if 'median' in metrics:
                result_df[f'{col}_median'] = df[col].median()
                
                # 移動中央値
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_median'] = df[col].rolling(window=window_size, center=True).median()
            
            # 標準偏差
            if 'std' in metrics:
                result_df[f'{col}_std'] = df[col].std()
                
                # 移動標準偏差
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_std'] = df[col].rolling(window=window_size, center=True).std()
            
            # 最小値
            if 'min' in metrics:
                result_df[f'{col}_min'] = df[col].min()
                
                # 移動最小値
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_min'] = df[col].rolling(window=window_size, center=True).min()
            
            # 最大値
            if 'max' in metrics:
                result_df[f'{col}_max'] = df[col].max()
                
                # 移動最大値
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_max'] = df[col].rolling(window=window_size, center=True).max()
            
            # パーセンタイル
            if 'percentile' in metrics:
                percentiles = self.params['percentiles']
                for p in percentiles:
                    result_df[f'{col}_p{p}'] = df[col].quantile(p / 100)
                    
                    # 移動パーセンタイル
                    if 'moving' in metrics:
                        window_size = self.params['window_size']
                        result_df[f'{col}_moving_p{p}'] = df[col].rolling(window=window_size, center=True).quantile(p / 100)
            
            # トレンド
            if 'trend' in metrics:
                trend_method = self.params['trend_method']
                
                # インデックスを数値に変換
                x = np.arange(len(df))
                y = df[col].values
                
                # 欠損値を除外
                mask = ~np.isnan(y)
                x_valid = x[mask]
                y_valid = y[mask]
                
                if len(x_valid) > 1:  # 有効なデータが2点以上ある場合
                    if trend_method == 'linear':
                        # 線形トレンド
                        slope, intercept = np.polyfit(x_valid, y_valid, 1)
                        trend_line = slope * x + intercept
                        result_df[f'{col}_trend'] = trend_line
                        result_df[f'{col}_trend_slope'] = slope
                    
                    elif trend_method == 'polynomial':
                        # 多項式トレンド
                        degree = self.params['trend_degree']
                        coeffs = np.polyfit(x_valid, y_valid, degree)
                        trend_line = np.zeros_like(x, dtype=float)
                        for i, coef in enumerate(coeffs):
                            trend_line += coef * (x ** (degree - i))
                        result_df[f'{col}_trend'] = trend_line
                        result_df[f'{col}_trend_coeffs'] = str(coeffs)
        
        return result_df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストの統計値を計算
        
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
    
    def _calculate_list(self, data: List[Any]) -> Dict[str, Any]:
        """
        数値リストの統計値を計算
        
        Parameters
        ----------
        data : List[Any]
            計算対象のリスト
            
        Returns
        -------
        Dict[str, Any]
            統計値の辞書
        """
        if not data or not all(isinstance(x, (int, float)) for x in data if x is not None):
            return {}
        
        # None値をNaNに置換
        cleaned_data = np.array([np.nan if x is None else x for x in data])
        
        # 統計指標ごとの計算
        metrics = self.params['metrics']
        result = {}
        
        # 平均値
        if 'mean' in metrics:
            result['mean'] = np.nanmean(cleaned_data)
        
        # 中央値
        if 'median' in metrics:
            result['median'] = np.nanmedian(cleaned_data)
        
        # 標準偏差
        if 'std' in metrics:
            result['std'] = np.nanstd(cleaned_data)
        
        # 最小値
        if 'min' in metrics:
            result['min'] = np.nanmin(cleaned_data)
        
        # 最大値
        if 'max' in metrics:
            result['max'] = np.nanmax(cleaned_data)
        
        # パーセンタイル
        if 'percentile' in metrics:
            percentiles = self.params['percentiles']
            for p in percentiles:
                result[f'p{p}'] = np.nanpercentile(cleaned_data, p)
        
        # トレンド
        if 'trend' in metrics:
            trend_method = self.params['trend_method']
            
            # インデックスを数値に変換
            x = np.arange(len(cleaned_data))
            y = cleaned_data
            
            # 欠損値を除外
            mask = ~np.isnan(y)
            x_valid = x[mask]
            y_valid = y[mask]
            
            if len(x_valid) > 1:  # 有効なデータが2点以上ある場合
                if trend_method == 'linear':
                    # 線形トレンド
                    slope, intercept = np.polyfit(x_valid, y_valid, 1)
                    result['trend_slope'] = slope
                    result['trend_intercept'] = intercept
                
                elif trend_method == 'polynomial':
                    # 多項式トレンド
                    degree = self.params['trend_degree']
                    coeffs = np.polyfit(x_valid, y_valid, degree)
                    result['trend_coeffs'] = coeffs.tolist()
        
        return result


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
