"""
sailing_data_processor.preprocessing.gps_processors

GPS位置データ用の前処理プロセッサの実装
"""

from typing import Dict, List, Any, Optional, Callable, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

from sailing_data_processor.data_model.container import GPSDataContainer
from .base_processor import GPSProcessor


class OutlierRemovalProcessor(GPSProcessor):
    """
    外れ値を削除するプロセッサ
    
    Parameters
    ----------
    config : Dict[str, Any], optional
        設定パラメータ
        - method: 外れ値検出方法 ('speed', 'distance', 'quartile', 'iqr')
        - threshold: しきい値
        - window_size: 移動ウィンドウサイズ (秒)
        - replace: 外れ値を補間するかどうか (True/False)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="OutlierRemoval",
            description="GPSデータから外れ値を検出して削除または補間します",
            config=config
        )
        
        # デフォルト設定
        if 'method' not in self.config:
            self.config['method'] = 'speed'
        if 'threshold' not in self.config:
            self.config['threshold'] = 30.0  # ノット
        if 'window_size' not in self.config:
            self.config['window_size'] = 60  # 秒
        if 'replace' not in self.config:
            self.config['replace'] = True
    
    def _process_gps(self, container: GPSDataContainer) -> GPSDataContainer:
        """
        GPS位置データから外れ値を検出して削除または補間
        
        Parameters
        ----------
        container : GPSDataContainer
            処理するGPSデータコンテナ
            
        Returns
        -------
        GPSDataContainer
            処理後のGPSデータコンテナ
        """
        method = self.config['method']
        threshold = self.config['threshold']
        window_size = self.config['window_size']
        replace = self.config['replace']
        
        # データフレームを取得
        df = container.data.copy()
        
        # 初期の行数を記録
        initial_rows = len(df)
        
        # 方法に応じて外れ値を検出
        if method == 'speed':
            outliers = self._detect_by_speed(df, threshold)
        elif method == 'distance':
            outliers = self._detect_by_distance(df, threshold, window_size)
        elif method == 'quartile' or method == 'iqr':
            outliers = self._detect_by_iqr(df, threshold)
        else:
            self.errors.append(f"未知の外れ値検出方法: {method}")
            return container
        
        # 外れ値の数を記録
        outlier_count = outliers.sum()
        
        # 外れ値がない場合はそのまま返す
        if outlier_count == 0:
            self.info.append("外れ値は検出されませんでした")
            return container
        
        # 外れ値を処理
        if replace:
            # 外れ値を補間
            processed_df = self._interpolate_outliers(df, outliers)
            self.info.append(f"{outlier_count}行の外れ値を検出し、補間しました")
        else:
            # 外れ値を削除
            processed_df = df[~outliers].reset_index(drop=True)
            self.info.append(f"{outlier_count}行の外れ値を検出し、削除しました")
        
        # 結果の行数を記録
        result_rows = len(processed_df)
        
        # 処理結果をメタデータに記録
        processing_metadata = {
            'method': method,
            'threshold': threshold,
            'window_size': window_size,
            'replace': replace,
            'initial_rows': initial_rows,
            'outlier_count': int(outlier_count),
            'result_rows': result_rows
        }
        
        # 新しいコンテナを作成
        new_metadata = container.metadata.copy()
        new_metadata['outlier_removal'] = processing_metadata
        
        return GPSDataContainer(processed_df, new_metadata)
    
    def _detect_by_speed(self, df: pd.DataFrame, threshold: float) -> pd.Series:
        """
        速度に基づいて外れ値を検出
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        threshold : float
            速度のしきい値（ノット）
            
        Returns
        -------
        pd.Series
            外れ値を示すブールシリーズ（True=外れ値）
        """
        # 速度カラムがあれば使用
        if 'speed' in df.columns:
            return df['speed'] > threshold
        
        # なければ計算
        outliers = pd.Series(False, index=df.index)
        
        if len(df) < 2:
            return outliers
        
        # 速度計算
        earth_radius = 6371000  # 地球の半径（メートル）
        
        for i in range(1, len(df)):
            lat1, lon1 = df.iloc[i-1]['latitude'], df.iloc[i-1]['longitude']
            lat2, lon2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
            
            # 地球上の距離を計算（メートル）
            dlat = np.radians(lat2 - lat1)
            dlon = np.radians(lon2 - lon1)
            a = (np.sin(dlat/2) * np.sin(dlat/2) + 
                 np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
                 np.sin(dlon/2) * np.sin(dlon/2))
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            distance = earth_radius * c  # メートル
            
            # 時間差（秒）
            time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds()
            
            if time_diff > 0:
                # 速度計算（m/s）
                speed_mps = distance / time_diff
                
                # m/sからノットに変換（1ノット = 0.514444 m/s）
                speed_knots = speed_mps / 0.514444
                
                # しきい値を超えた場合は外れ値とする
                if speed_knots > threshold:
                    outliers.iloc[i] = True
        
        return outliers
    
    def _detect_by_distance(self, df: pd.DataFrame, threshold: float, window_size: int) -> pd.Series:
        """
        距離に基づいて外れ値を検出
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        threshold : float
            距離のしきい値（メートル）
        window_size : int
            時間ウィンドウサイズ（秒）
            
        Returns
        -------
        pd.Series
            外れ値を示すブールシリーズ（True=外れ値）
        """
        outliers = pd.Series(False, index=df.index)
        
        if len(df) < 2:
            return outliers
        
        earth_radius = 6371000  # 地球の半径（メートル）
        
        for i in range(1, len(df)):
            # 現在の点とウィンドウ内の点を比較
            current_time = df.iloc[i]['timestamp']
            lat2, lon2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
            
            # ウィンドウ内の点を探す
            window_points = []
            
            # 前方の点を探索
            for j in range(i-1, -1, -1):
                time_diff = (current_time - df.iloc[j]['timestamp']).total_seconds()
                if time_diff > window_size:
                    break
                window_points.append(j)
            
            if not window_points:
                continue
            
            # 各ウィンドウポイントとの距離を計算
            distances = []
            for j in window_points:
                lat1, lon1 = df.iloc[j]['latitude'], df.iloc[j]['longitude']
                
                dlat = np.radians(lat2 - lat1)
                dlon = np.radians(lon2 - lon1)
                a = (np.sin(dlat/2) * np.sin(dlat/2) + 
                     np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
                     np.sin(dlon/2) * np.sin(dlon/2))
                c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                distance = earth_radius * c  # メートル
                
                distances.append(distance)
            
            # 最小距離がしきい値を超えるか
            if min(distances) > threshold:
                outliers.iloc[i] = True
        
        return outliers
    
    def _detect_by_iqr(self, df: pd.DataFrame, threshold: float) -> pd.Series:
        """
        四分位範囲（IQR）に基づいて外れ値を検出
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        threshold : float
            IQRの倍数（通常は1.5や3）
            
        Returns
        -------
        pd.Series
            外れ値を示すブールシリーズ（True=外れ値）
        """
        outliers = pd.Series(False, index=df.index)
        
        # 速度や距離などの数値カラムに対して検出
        numeric_columns = ['speed'] if 'speed' in df.columns else []
        
        if not numeric_columns:
            # 速度がなければ緯度・経度の移動距離を計算
            if len(df) >= 2:
                # 後処理用の速度を計算
                speeds = []
                speeds.append(0)  # 最初のポイントは0
                
                for i in range(1, len(df)):
                    lat1, lon1 = df.iloc[i-1]['latitude'], df.iloc[i-1]['longitude']
                    lat2, lon2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
                    time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds()
                    
                    if time_diff > 0:
                        # 地球上の距離を計算（メートル）
                        dlat = np.radians(lat2 - lat1)
                        dlon = np.radians(lon2 - lon1)
                        a = (np.sin(dlat/2) * np.sin(dlat/2) + 
                             np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
                             np.sin(dlon/2) * np.sin(dlon/2))
                        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                        distance = 6371000 * c  # メートル
                        
                        # 速度計算（m/s）
                        speed_mps = distance / time_diff
                        speeds.append(speed_mps)
                    else:
                        speeds.append(0)
                
                temp_df = df.copy()
                temp_df['calc_speed'] = speeds
                numeric_columns = ['calc_speed']
            else:
                return outliers
        
        # 各数値カラムに対してIQRを使用して外れ値を検出
        for col in numeric_columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outliers = outliers | col_outliers
        
        return outliers
    
    def _interpolate_outliers(self, df: pd.DataFrame, outliers: pd.Series) -> pd.DataFrame:
        """
        外れ値を補間
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        outliers : pd.Series
            外れ値を示すブールシリーズ（True=外れ値）
            
        Returns
        -------
        pd.DataFrame
            補間後のデータフレーム
        """
        # 結果用のコピーを作成
        result_df = df.copy()
        
        # 外れ値のインデックス
        outlier_indices = outliers[outliers].index
        
        # 各外れ値を処理
        for idx in outlier_indices:
            # 前後のデータポイントを取得
            prev_indices = df.index[df.index < idx]
            next_indices = df.index[df.index > idx]
            
            prev_idx = prev_indices[-1] if len(prev_indices) > 0 else None
            next_idx = next_indices[0] if len(next_indices) > 0 else None
            
            # 前後のデータポイントが両方存在する場合のみ補間
            if prev_idx is not None and next_idx is not None:
                # 時間比率を計算
                total_time = (df.loc[next_idx, 'timestamp'] - df.loc[prev_idx, 'timestamp']).total_seconds()
                time_ratio = (df.loc[idx, 'timestamp'] - df.loc[prev_idx, 'timestamp']).total_seconds() / total_time
                
                # 緯度・経度を線形補間
                result_df.loc[idx, 'latitude'] = (
                    df.loc[prev_idx, 'latitude'] + 
                    (df.loc[next_idx, 'latitude'] - df.loc[prev_idx, 'latitude']) * time_ratio
                )
                
                result_df.loc[idx, 'longitude'] = (
                    df.loc[prev_idx, 'longitude'] + 
                    (df.loc[next_idx, 'longitude'] - df.loc[prev_idx, 'longitude']) * time_ratio
                )
                
                # 他の数値カラムも補間
                for col in df.columns:
                    if col not in ['timestamp', 'latitude', 'longitude'] and pd.api.types.is_numeric_dtype(df[col]):
                        result_df.loc[idx, col] = (
                            df.loc[prev_idx, col] + 
                            (df.loc[next_idx, col] - df.loc[prev_idx, col]) * time_ratio
                        )
        
        return result_df


class ResamplingSmoothingProcessor(GPSProcessor):
    """
    データのリサンプリングとスムージングを行うプロセッサ
    
    Parameters
    ----------
    config : Dict[str, Any], optional
        設定パラメータ
        - method: スムージング方法 ('resample', 'moving_average', 'savgol', 'spline')
        - freq: リサンプル間隔 ('1S', '5S', '10S' など)
        - window_size: 移動平均窓サイズ
        - polynomial_order: 多項式次数（Savitzky-Golayフィルタ用）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="ResamplingSmoothingProcessor",
            description="GPSデータをリサンプリングおよびスムージングします",
            config=config
        )
        
        # デフォルト設定
        if 'method' not in self.config:
            self.config['method'] = 'resample'
        if 'freq' not in self.config:
            self.config['freq'] = '1S'  # 1秒ごと
        if 'window_size' not in self.config:
            self.config['window_size'] = 5
        if 'polynomial_order' not in self.config:
            self.config['polynomial_order'] = 2
    
    def _process_gps(self, container: GPSDataContainer) -> GPSDataContainer:
        """
        GPS位置データを処理
        
        Parameters
        ----------
        container : GPSDataContainer
            処理するGPSデータコンテナ
            
        Returns
        -------
        GPSDataContainer
            処理後のGPSデータコンテナ
        """
        method = self.config['method']
        
        # データフレームを取得
        df = container.data.copy()
        
        # 初期の行数を記録
        initial_rows = len(df)
        
        # 方法に応じて処理
        if method == 'resample':
            processed_df = self._resample_data(df, self.config['freq'])
        elif method == 'moving_average':
            processed_df = self._apply_moving_average(df, self.config['window_size'])
        elif method == 'savgol':
            from scipy.signal import savgol_filter
            processed_df = self._apply_savgol(df, self.config['window_size'], self.config['polynomial_order'])
        elif method == 'spline':
            from scipy.interpolate import UnivariateSpline
            processed_df = self._apply_spline(df)
        else:
            self.errors.append(f"未知の処理方法: {method}")
            return container
        
        # 結果の行数を記録
        result_rows = len(processed_df)
        
        # 処理結果をメタデータに記録
        processing_metadata = {
            'method': method,
            'initial_rows': initial_rows,
            'result_rows': result_rows
        }
        
        if method == 'resample':
            processing_metadata['freq'] = self.config['freq']
        elif method in ['moving_average', 'savgol']:
            processing_metadata['window_size'] = self.config['window_size']
        
        if method == 'savgol':
            processing_metadata['polynomial_order'] = self.config['polynomial_order']
        
        # 新しいコンテナを作成
        new_metadata = container.metadata.copy()
        new_metadata['smoothing'] = processing_metadata
        
        self.info.append(f"{method}法によりデータを処理しました（{initial_rows}行→{result_rows}行）")
        
        return GPSDataContainer(processed_df, new_metadata)
    
    def _resample_data(self, df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """
        データを一定間隔でリサンプリング
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        freq : str
            リサンプル間隔（'1S', '5S' など）
            
        Returns
        -------
        pd.DataFrame
            リサンプル後のデータフレーム
        """
        # timestampをインデックスに設定
        df_indexed = df.set_index('timestamp')
        
        # リサンプルして線形補間
        resampled = df_indexed.resample(freq).asfreq()
        
        # 数値カラムを補間
        numeric_cols = [col for col in df.columns if col != 'timestamp' and pd.api.types.is_numeric_dtype(df[col])]
        resampled[numeric_cols] = resampled[numeric_cols].interpolate(method='linear')
        
        # インデックスをカラムに戻す
        result = resampled.reset_index()
        
        return result
    
    def _apply_moving_average(self, df: pd.DataFrame, window_size: int) -> pd.DataFrame:
        """
        移動平均を適用
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        window_size : int
            移動平均の窓サイズ
            
        Returns
        -------
        pd.DataFrame
            処理後のデータフレーム
        """
        result = df.copy()
        
        # 数値カラムに移動平均を適用
        numeric_cols = [col for col in df.columns if col != 'timestamp' and pd.api.types.is_numeric_dtype(df[col])]
        
        for col in numeric_cols:
            result[col] = df[col].rolling(window=window_size, center=True, min_periods=1).mean()
        
        return result
    
    def _apply_savgol(self, df: pd.DataFrame, window_size: int, poly_order: int) -> pd.DataFrame:
        """
        Savitzky-Golayフィルタを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
        window_size : int
            フィルタの窓サイズ
        poly_order : int
            多項式次数
            
        Returns
        -------
        pd.DataFrame
            処理後のデータフレーム
        """
        from scipy.signal import savgol_filter
        
        result = df.copy()
        
        # 数値カラムにSavitzky-Golayフィルタを適用
        numeric_cols = [col for col in df.columns if col != 'timestamp' and pd.api.types.is_numeric_dtype(df[col])]
        
        # 窓サイズは奇数である必要がある
        if window_size % 2 == 0:
            window_size += 1
        
        for col in numeric_cols:
            if len(df) > window_size:
                result[col] = savgol_filter(df[col], window_size, poly_order)
        
        return result
    
    def _apply_spline(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        スプライン補間を適用
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns
        -------
        pd.DataFrame
            処理後のデータフレーム
        """
        from scipy.interpolate import UnivariateSpline
        
        result = df.copy()
        
        # 数値カラムにスプライン補間を適用
        numeric_cols = [col for col in df.columns if col != 'timestamp' and pd.api.types.is_numeric_dtype(df[col])]
        
        # 時間を数値に変換
        times = [(t - df['timestamp'].min()).total_seconds() for t in df['timestamp']]
        
        for col in numeric_cols:
            if len(df) > 3:  # スプラインには少なくとも4点必要
                try:
                    # スプライン補間を適用
                    spline = UnivariateSpline(times, df[col], s=len(df))
                    result[col] = spline(times)
                except Exception as e:
                    self.warnings.append(f"カラム {col} のスプライン補間に失敗しました: {str(e)}")
        
        return result


class DerivedColumnsProcessor(GPSProcessor):
    """
    派生的な情報を計算して追加するプロセッサ
    
    Parameters
    ----------
    config : Dict[str, Any], optional
        設定パラメータ
        - calculate_speed: 速度を計算するかどうか (True/False)
        - calculate_course: 進行方向を計算するかどうか (True/False)
        - calculate_acceleration: 加速度を計算するかどうか (True/False)
        - calculate_distance: 累積距離を計算するかどうか (True/False)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="DerivedColumnsProcessor",
            description="GPSデータから派生的な情報を計算して追加します",
            config=config
        )
        
        # デフォルト設定
        if 'calculate_speed' not in self.config:
            self.config['calculate_speed'] = True
        if 'calculate_course' not in self.config:
            self.config['calculate_course'] = True
        if 'calculate_acceleration' not in self.config:
            self.config['calculate_acceleration'] = False
        if 'calculate_distance' not in self.config:
            self.config['calculate_distance'] = True
    
    def _process_gps(self, container: GPSDataContainer) -> GPSDataContainer:
        """
        GPS位置データを処理
        
        Parameters
        ----------
        container : GPSDataContainer
            処理するGPSデータコンテナ
            
        Returns
        -------
        GPSDataContainer
            処理後のGPSデータコンテナ
        """
        # データフレームを取得
        df = container.data.copy()
        
        # データポイントが2つ未満の場合は計算しない
        if len(df) < 2:
            self.warnings.append("データポイントが不足しているため派生情報を計算できません")
            return container
        
        # 設定に応じて派生情報を計算
        added_columns = []
        
        # 速度計算
        if self.config['calculate_speed'] and 'speed' not in df.columns:
            df = self._calculate_speed(df)
            added_columns.append('speed')
        
        # 進行方向計算
        if self.config['calculate_course'] and 'course' not in df.columns:
            df = self._calculate_course(df)
            added_columns.append('course')
        
        # 加速度計算
        if self.config['calculate_acceleration'] and 'acceleration' not in df.columns and 'speed' in df.columns:
            df = self._calculate_acceleration(df)
            added_columns.append('acceleration')
        
        # 累積距離計算
        if self.config['calculate_distance'] and 'cum_distance' not in df.columns:
            df = self._calculate_cumulative_distance(df)
            added_columns.append('cum_distance')
        
        # 処理結果をメタデータに記録
        processing_metadata = {
            'added_columns': added_columns
        }
        
        # 新しいコンテナを作成
        new_metadata = container.metadata.copy()
        new_metadata['derived_columns'] = processing_metadata
        
        self.info.append(f"派生カラムを追加しました: {', '.join(added_columns)}")
        
        return GPSDataContainer(df, new_metadata)
    
    def _calculate_speed(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        速度を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns
        -------
        pd.DataFrame
            速度カラムを追加したデータフレーム
        """
        # 結果用のコピーを作成
        result = df.copy()
        
        # 速度カラムを初期化
        speeds = np.zeros(len(df))
        
        # 各ポイント間の速度を計算
        for i in range(1, len(df)):
            lat1, lon1 = df.iloc[i-1]['latitude'], df.iloc[i-1]['longitude']
            lat2, lon2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
            time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds()
            
            if time_diff > 0:
                # 地球上の距離を計算（メートル）
                dlat = np.radians(lat2 - lat1)
                dlon = np.radians(lon2 - lon1)
                a = (np.sin(dlat/2) * np.sin(dlat/2) + 
                     np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
                     np.sin(dlon/2) * np.sin(dlon/2))
                c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                distance = 6371000 * c  # メートル
                
                # 速度計算（m/s）
                speed_mps = distance / time_diff
                
                # m/sからノットに変換（1ノット = 0.514444 m/s）
                speed_knots = speed_mps / 0.514444
                
                speeds[i] = speed_knots
        
        # 前のポイントの速度をコピー（最初のポイントは0のまま）
        for i in range(1, len(speeds)):
            if speeds[i] == 0:
                speeds[i] = speeds[i-1]
        
        result['speed'] = speeds
        
        return result
    
    def _calculate_course(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        進行方向（コース）を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns
        -------
        pd.DataFrame
            コースカラムを追加したデータフレーム
        """
        # 結果用のコピーを作成
        result = df.copy()
        
        # コースカラムを初期化
        courses = np.zeros(len(df))
        
        # 各ポイント間のコースを計算
        for i in range(1, len(df)):
            lat1, lon1 = df.iloc[i-1]['latitude'], df.iloc[i-1]['longitude']
            lat2, lon2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
            
            # ラジアンに変換
            lat1_rad = np.radians(lat1)
            lon1_rad = np.radians(lon1)
            lat2_rad = np.radians(lat2)
            lon2_rad = np.radians(lon2)
            
            # 方位角計算
            y = np.sin(lon2_rad - lon1_rad) * np.cos(lat2_rad)
            x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(lon2_rad - lon1_rad)
            bearing = np.arctan2(y, x)
            
            # ラジアンから度に変換して正規化（0-360度）
            course = (np.degrees(bearing) + 360) % 360
            
            courses[i] = course
        
        # 前のポイントのコースをコピー（最初のポイントは0のまま）
        for i in range(1, len(courses)):
            if courses[i] == 0 and i > 1:
                courses[i] = courses[i-1]
        
        result['course'] = courses
        
        return result
    
    def _calculate_acceleration(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        加速度を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム（speedカラムが必要）
            
        Returns
        -------
        pd.DataFrame
            加速度カラムを追加したデータフレーム
        """
        # 結果用のコピーを作成
        result = df.copy()
        
        # 加速度カラムを初期化
        accels = np.zeros(len(df))
        
        # 各ポイント間の加速度を計算
        for i in range(1, len(df)):
            speed1 = df.iloc[i-1]['speed']
            speed2 = df.iloc[i]['speed']
            time_diff = (df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds()
            
            if time_diff > 0:
                # 加速度計算（ノット/秒）
                accels[i] = (speed2 - speed1) / time_diff
        
        result['acceleration'] = accels
        
        return result
    
    def _calculate_cumulative_distance(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        累積距離を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns
        -------
        pd.DataFrame
            累積距離カラムを追加したデータフレーム
        """
        # 結果用のコピーを作成
        result = df.copy()
        
        # 累積距離カラムを初期化
        cum_distances = np.zeros(len(df))
        
        # 地球半径（メートル）
        earth_radius = 6371000
        
        # 累積距離を計算
        total_distance = 0.0
        
        for i in range(1, len(df)):
            lat1, lon1 = df.iloc[i-1]['latitude'], df.iloc[i-1]['longitude']
            lat2, lon2 = df.iloc[i]['latitude'], df.iloc[i]['longitude']
            
            # 地球上の距離を計算（メートル）
            dlat = np.radians(lat2 - lat1)
            dlon = np.radians(lon2 - lon1)
            a = (np.sin(dlat/2) * np.sin(dlat/2) + 
                 np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
                 np.sin(dlon/2) * np.sin(dlon/2))
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            distance = earth_radius * c  # メートル
            
            total_distance += distance
            cum_distances[i] = total_distance
        
        # メートルから海里に変換（1海里 = 1852メートル）
        cum_distances = cum_distances / 1852.0
        
        result['cum_distance'] = cum_distances
        
        return result
