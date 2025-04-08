"""
sailing_data_processor.data_model.utils

データモデルの操作と変換のためのユーティリティ関数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from datetime import datetime
import warnings

from .container import (
    DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer
)

def convert_to_gps_container(data: pd.DataFrame, validate: bool = True) -> GPSDataContainer:
    """
    DataFrameをGPSDataContainerに変換
    
    Parameters
    ----------
    data : pd.DataFrame
        GPS位置データを含むDataFrame
    validate : bool, optional
        データ検証を行うかどうか（デフォルト: True）
    
    Returns
    -------
    GPSDataContainer
        変換されたコンテナ
    
    Raises
    ------
    ValueError
        必須カラムがない場合（validate=Trueの場合）
    """
    try:
        container = GPSDataContainer(data)
        
        if validate:
            # 検証を実行
            if not container.validate():
                warnings.warn("GPSデータの検証に失敗しました。データが不完全または不正確かもしれません。")
        
        return container
    
    except Exception as e:
        if validate:
            # validate=Trueの場合は例外を再発生
            raise
        else:
            # validate=Falseの場合は警告を表示
            warnings.warn(f"GPSコンテナ変換警告: {e}")
            # 最小限の前処理を行う
            if 'timestamp' not in data.columns:
                if 'time' in data.columns:
                    data = data.rename(columns={'time': 'timestamp'})
                else:
                    data['timestamp'] = pd.date_range(start=datetime.now(), periods=len(data), freq='1S')
            
            return GPSDataContainer(data)

def convert_to_wind_container(data: Union[Dict[str, Any], pd.Series]) -> WindDataContainer:
    """
    辞書またはSeriesをWindDataContainerに変換
    
    Parameters
    ----------
    data : Union[Dict[str, Any], pd.Series]
        風データを含む辞書またはSeries
    
    Returns
    -------
    WindDataContainer
        変換されたコンテナ
    
    Raises
    ------
    ValueError
        必須キーがない場合
    """
    if isinstance(data, pd.Series):
        data = data.to_dict()
    
    # 最低限必要なキーを確保
    if 'timestamp' not in data:
        data['timestamp'] = datetime.now()
    
    return WindDataContainer(data)

def convert_to_strategy_point_container(
        point_type: str, 
        latitude: float, 
        longitude: float, 
        timestamp: Union[datetime, str], 
        details: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StrategyPointContainer:
    """
    パラメータからStrategyPointContainerを作成
    
    Parameters
    ----------
    point_type : str
        ポイントタイプ ('tack', 'jibe', 'layline', 'wind_shift', 等)
    latitude : float
        緯度
    longitude : float
        経度
    timestamp : Union[datetime, str]
        タイムスタンプ
    details : Dict[str, Any], optional
        詳細情報
    importance : float, optional
        重要度（0-1）
    metadata : Dict[str, Any], optional
        メタデータ
    
    Returns
    -------
    StrategyPointContainer
        作成されたコンテナ
    """
    return StrategyPointContainer.from_coordinates(
        point_type, latitude, longitude, timestamp,
        importance=importance,
        details=details,
        metadata=metadata
    )

def merge_gps_data(
        containers: List[GPSDataContainer], 
        drop_duplicates: bool = True,
        sort: bool = True
    ) -> GPSDataContainer:
    """
    複数のGPSデータコンテナをマージ
    
    Parameters
    ----------
    containers : List[GPSDataContainer]
        マージするGPSデータコンテナのリスト
    drop_duplicates : bool, optional
        重複を削除するかどうか（デフォルト: True）
    sort : bool, optional
        時間順にソートするかどうか（デフォルト: True）
    
    Returns
    -------
    GPSDataContainer
        マージされたコンテナ
    """
    if not containers:
        return GPSDataContainer(pd.DataFrame())
    
    # 全てのDataFrameを連結
    dfs = [container.data for container in containers]
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # 重複を削除
    if drop_duplicates:
        merged_df = merged_df.drop_duplicates(subset=['timestamp', 'latitude', 'longitude'])
    
    # 時間順にソート
    if sort:
        merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
    
    # メタデータのマージ
    merged_metadata = {}
    for container in containers:
        merged_metadata.update(container.metadata)
    
    # 時間範囲の更新
    if len(merged_df) > 0:
        merged_metadata['time_range'] = {
            'start': merged_df['timestamp'].min().isoformat(),
            'end': merged_df['timestamp'].max().isoformat(),
            'duration_seconds': (merged_df['timestamp'].max() - merged_df['timestamp'].min()).total_seconds()
        }
    
    # 新しいコンテナを作成
    return GPSDataContainer(merged_df, merged_metadata)

def group_strategy_points(
        points: List[StrategyPointContainer], 
        by_type: bool = True,
        by_time: bool = False,
        time_window_seconds: int = 300
    ) -> Dict[str, List[StrategyPointContainer]]:
    """
    戦略ポイントをグループ化
    
    Parameters
    ----------
    points : List[StrategyPointContainer]
        グループ化する戦略ポイントのリスト
    by_type : bool, optional
        タイプでグループ化するかどうか（デフォルト: True）
    by_time : bool, optional
        時間でグループ化するかどうか（デフォルト: False）
    time_window_seconds : int, optional
        時間グループ化の窓サイズ（秒）
    
    Returns
    -------
    Dict[str, List[StrategyPointContainer]]
        グループ化された戦略ポイント
    """
    if not points:
        return {}
    
    result = {}
    
    if by_type:
        # タイプでグループ化
        for point in points:
            point_type = point.point_type
            if point_type not in result:
                result[point_type] = []
            result[point_type].append(point)
    
    elif by_time:
        # 時間でグループ化
        # 最初の基準時刻
        if points:
            base_time = points[0].timestamp
            
            current_group = 0
            result[f"group_{current_group}"] = []
            
            for point in points:
                # 前のグループの最後のポイントとの時間差
                if result[f"group_{current_group}"]:
                    last_time = result[f"group_{current_group}"][-1].timestamp
                    time_diff = (point.timestamp - last_time).total_seconds()
                    
                    # 時間差が窓サイズより大きい場合は新しいグループ
                    if time_diff > time_window_seconds:
                        current_group += 1
                        result[f"group_{current_group}"] = []
                
                result[f"group_{current_group}"].append(point)
    
    else:
        # グループ化なし
        result["all"] = points
    
    return result

def find_nearest_wind_data(
        target_lat: float, 
        target_lon: float, 
        target_time: datetime,
        wind_data_containers: List[WindDataContainer]
    ) -> Optional[WindDataContainer]:
    """
    指定位置・時刻に最も近い風データを見つける
    
    Parameters
    ----------
    target_lat : float
        目標緯度
    target_lon : float
        目標経度
    target_time : datetime
        目標時刻
    wind_data_containers : List[WindDataContainer]
        風データコンテナのリスト
    
    Returns
    -------
    Optional[WindDataContainer]
        最も近い風データコンテナ、見つからない場合はNone
    """
    if not wind_data_containers:
        return None
    
    best_container = None
    min_distance = float('inf')
    
    # Math_utils.pyのhaversine_distanceをインポートして使うべきだが、
    # このモジュールでは独立性を保つために簡略実装
    def haversine_distance(lat1, lon1, lat2, lon2):
        """2点間のヘイバーサイン距離（キロメートル）"""
        R = 6371.0  # 地球の半径（km）
        
        # ラジアンに変換
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # 差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # ヘイバーサイン公式
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    for container in wind_data_containers:
        # 位置の差
        position = container.data.get('position', {})
        wind_lat = position.get('latitude', container.latitude if hasattr(container, 'latitude') else None)
        wind_lon = position.get('longitude', container.longitude if hasattr(container, 'longitude') else None)
        
        if wind_lat is None or wind_lon is None:
            continue
        
        # 位置の距離
        space_distance = haversine_distance(target_lat, target_lon, wind_lat, wind_lon)
        
        # 時間の差（秒）
        time_diff = abs((target_time - container.timestamp).total_seconds())
        
        # 正規化（位置の重みを大きく）
        normalized_space = space_distance / 100.0  # 100kmで1.0
        normalized_time = time_diff / 3600.0       # 1時間で1.0
        
        # 距離の計算（位置と時間の加重和）
        distance = 0.8 * normalized_space + 0.2 * normalized_time
        
        if distance < min_distance:
            min_distance = distance
            best_container = container
    
    return best_container

def preprocess_gps_data(
        df: pd.DataFrame,
        fix_timestamp: bool = True,
        clean_outliers: bool = True,
        resample: bool = False,
        resample_freq: str = '1S'
    ) -> GPSDataContainer:
    """
    GPS位置データの前処理
    
    Parameters
    ----------
    df : pd.DataFrame
        GPS位置データ
    fix_timestamp : bool, optional
        タイムスタンプを修正するかどうか（デフォルト: True）
    clean_outliers : bool, optional
        外れ値を除去するかどうか（デフォルト: True）
    resample : bool, optional
        リサンプリングを行うかどうか（デフォルト: False）
    resample_freq : str, optional
        リサンプリング間隔（デフォルト: '1S'）
    
    Returns
    -------
    GPSDataContainer
        前処理されたデータコンテナ
    """
    # 必須カラムのチェック
    required_columns = ['latitude', 'longitude']
    if fix_timestamp:
        required_columns.append('timestamp')
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        # timestampがないが時間的なカラムがある場合
        if 'timestamp' in missing_columns and any(col in df.columns for col in ['time', 'datetime', 'date']):
            time_col = next(col for col in ['time', 'datetime', 'date'] if col in df.columns)
            df = df.rename(columns={time_col: 'timestamp'})
            missing_columns.remove('timestamp')
        
        # それでも不足しているカラムがある場合
        if missing_columns:
            raise ValueError(f"必須カラムがありません: {', '.join(missing_columns)}")
    
    # コピーを作成
    processed_df = df.copy()
    
    # タイムスタンプの修正
    if fix_timestamp and 'timestamp' in processed_df.columns:
        # タイムスタンプがdatetimeでない場合は変換
        if not pd.api.types.is_datetime64_any_dtype(processed_df['timestamp']):
            try:
                processed_df['timestamp'] = pd.to_datetime(processed_df['timestamp'])
            except Exception as e:
                warnings.warn(f"タイムスタンプ変換エラー: {e}")
                # 変換できない場合は現在時刻から連番で生成
                processed_df['timestamp'] = pd.date_range(
                    start=datetime.now(), 
                    periods=len(processed_df), 
                    freq='1S'
                )
    
    # 外れ値の除去
    if clean_outliers:
        # 緯度・経度の範囲チェック
        processed_df = processed_df[
            (processed_df['latitude'] >= -90) & (processed_df['latitude'] <= 90) &
            (processed_df['longitude'] >= -180) & (processed_df['longitude'] <= 180)
        ]
        
        # 距離ベースの外れ値除去
        # より高度な外れ値検出を行う場合は、AnomalyDetectorクラスを使用
        
        # 空のデータフレームにならないようにチェック
        if len(processed_df) == 0:
            warnings.warn("外れ値除去後にデータがありません")
            processed_df = df.copy()  # 元のデータを使用
    
    # GPSコンテナの作成
    container = GPSDataContainer(processed_df)
    
    # リサンプリング
    if resample:
        container = container.resample(resample_freq)
    
    return container

def extract_time_window(
        container: GPSDataContainer,
        start_time: Union[datetime, str],
        end_time: Union[datetime, str],
        include_start: bool = True,
        include_end: bool = True
    ) -> GPSDataContainer:
    """
    時間範囲のデータを抽出
    
    Parameters
    ----------
    container : GPSDataContainer
        GPS位置データコンテナ
    start_time : Union[datetime, str]
        開始時刻
    end_time : Union[datetime, str]
        終了時刻
    include_start : bool, optional
        開始時刻を含めるかどうか（デフォルト: True）
    include_end : bool, optional
        終了時刻を含めるかどうか（デフォルト: True）
    
    Returns
    -------
    GPSDataContainer
        抽出されたデータコンテナ
    """
    # 文字列の場合はdatetimeに変換
    if isinstance(start_time, str):
        start_time = pd.to_datetime(start_time)
    if isinstance(end_time, str):
        end_time = pd.to_datetime(end_time)
    
    # データフレームを取得
    df = container.data
    
    # 範囲抽出用の条件
    if include_start:
        start_condition = df['timestamp'] >= start_time
    else:
        start_condition = df['timestamp'] > start_time
    
    if include_end:
        end_condition = df['timestamp'] <= end_time
    else:
        end_condition = df['timestamp'] < end_time
    
    # 時間範囲でフィルタリング
    filtered_df = df[start_condition & end_condition].copy()
    
    # 新しいメタデータを作成
    metadata = container.metadata.copy()
    
    # 時間範囲を更新
    if len(filtered_df) > 0:
        metadata['extracted_time_range'] = {
            'original': container.get_metadata('time_range', {}),
            'start': filtered_df['timestamp'].min().isoformat(),
            'end': filtered_df['timestamp'].max().isoformat(),
            'duration_seconds': (filtered_df['timestamp'].max() - filtered_df['timestamp'].min()).total_seconds()
        }
    
    return GPSDataContainer(filtered_df, metadata)

def calculate_course_and_speed(container: GPSDataContainer, smooth: bool = True) -> GPSDataContainer:
    """
    GPSデータから進行方位と速度を計算
    
    Parameters
    ----------
    container : GPSDataContainer
        GPS位置データコンテナ
    smooth : bool, optional
        計算結果をスムージングするかどうか（デフォルト: True）
    
    Returns
    -------
    GPSDataContainer
        コースと速度が追加されたデータコンテナ
    """
    # データフレームのコピーを作成
    df = container.data.copy()
    
    # データが不足している場合
    if len(df) < 2:
        if 'course' not in df.columns:
            df['course'] = 0.0
        if 'speed' not in df.columns:
            df['speed'] = 0.0
        return GPSDataContainer(df, container.metadata.copy())
    
    # 時間順にソート
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 時間差（秒）を計算
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    
    # 最初の行はNaNになるので0秒とする
    df.loc[0, 'time_diff'] = 0
    
    # Math_utils.pyのhaversine_distanceをインポートして使うべきだが、
    # このモジュールでは独立性を保つために簡略実装
    def calculate_distance_and_bearing(lat1, lon1, lat2, lon2):
        """2点間の距離（メートル）と方位（度）"""
        R = 6371000.0  # 地球の半径（m）
        
        # ラジアンに変換
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # 差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # 距離計算
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        # 方位計算
        y = np.sin(dlon) * np.cos(lat2_rad)
        x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)
        bearing = np.degrees(np.arctan2(y, x))
        
        # 北を0度とする（0〜360度）
        bearing = (bearing + 360) % 360
        
        return distance, bearing
    
    # 距離と方位を計算
    distances = []
    bearings = []
    
    for i in range(len(df)):
        if i == 0:
            # 最初のポイントは前のポイントがないのでNaN
            distances.append(0.0)
            bearings.append(np.nan)
        else:
            # 前のポイントとの距離と方位を計算
            lat1 = df.iloc[i-1]['latitude']
            lon1 = df.iloc[i-1]['longitude']
            lat2 = df.iloc[i]['latitude']
            lon2 = df.iloc[i]['longitude']
            
            distance, bearing = calculate_distance_and_bearing(lat1, lon1, lat2, lon2)
            distances.append(distance)
            bearings.append(bearing)
    
    df['distance'] = distances
    df['bearing'] = bearings
    
    # 速度計算（m/sをノットに変換、1ノット = 0.514444m/s）
    knot_factor = 1 / 0.514444
    df['speed'] = np.where(df['time_diff'] > 0, df['distance'] / df['time_diff'] * knot_factor, 0)
    
    # 異常値をフィルタリング（例: 100ノット以上はあり得ない）
    df.loc[df['speed'] > 100, 'speed'] = np.nan
    
    # 方位（course）を計算
    # 現時点の方位が利用可能ならそれを使う、なければ次のポイントへの方位を使う
    df['course'] = df['bearing']
    
    # 最初のポイントの方位を2番目のポイントの方位で埋める
    if len(df) > 1 and np.isnan(df.iloc[0]['course']):
        df.loc[df.index[0], 'course'] = df.iloc[1]['course']
    
    # NaNをforward fillで埋める
    df['course'] = df['course'].fillna(method='ffill')
    
    # スムージング
    if smooth:
        window_size = min(5, len(df))
        
        if window_size > 1:
            # 速度のスムージング
            df['speed'] = df['speed'].rolling(window=window_size, center=True).mean()
            
            # 方位のスムージング（角度データなので単純な平均は使えない）
            # 1度目→北向きからスタートして、一周するとスムージングに問題が発生
            # 例: [359, 1] -> 平均180ではなく0（または360）になるべき
            df['sin_course'] = np.sin(np.radians(df['course']))
            df['cos_course'] = np.cos(np.radians(df['course']))
            
            df['sin_avg'] = df['sin_course'].rolling(window=window_size, center=True).mean()
            df['cos_avg'] = df['cos_course'].rolling(window=window_size, center=True).mean()
            
            # アークタンジェントで戻す
            df['course_smoothed'] = np.degrees(np.arctan2(df['sin_avg'], df['cos_avg']))
            df['course_smoothed'] = (df['course_smoothed'] + 360) % 360
            
            # スムージング結果で置き換え
            df['course'] = df['course_smoothed']
            
            # 不要な列を削除
            df = df.drop(columns=['sin_course', 'cos_course', 'sin_avg', 'cos_avg', 'course_smoothed'])
    
    # 最終的なNaNをfillna
    df['course'] = df['course'].fillna(0)
    df['speed'] = df['speed'].fillna(0)
    
    # 必要なカラムのみを残す
    result_df = df.drop(columns=['time_diff', 'distance', 'bearing'])
    
    # メタデータを更新
    metadata = container.metadata.copy()
    metadata['calculated_fields'] = ['course', 'speed']
    if smooth:
        metadata['smoothing_applied'] = True
        metadata['smoothing_window'] = window_size
    
    return GPSDataContainer(result_df, metadata)
