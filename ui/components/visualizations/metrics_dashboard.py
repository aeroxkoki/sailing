"""
ui.components.visualizations.metrics_dashboard

メトリクスダッシュボードコンポーネント - パフォーマンス指標をカード形式で表示するコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
from sailing_data_processor.data_model.container import GPSDataContainer, WindDataContainer
from ui.data_binding import DataBindingManager, UIStateManager
from ui.components.common.card import Card

class MetricsDashboardComponent:
    """
    メトリクスダッシュボード用のコンポーネント
    
    セーリングデータのパフォーマンス指標をカード形式で表示するためのコンポーネントです。
    """
    
    def __init__(self, data_binding: DataBindingManager, ui_state: UIStateManager):
        """
        初期化
        
        Parameters
        ----------
        data_binding : DataBindingManager
            データバインディング管理オブジェクト
        ui_state : UIStateManager
            UI状態管理オブジェクト
        """
        self.data_binding = data_binding
        self.ui_state = ui_state
    
    def render_speed_metrics(self, container: GPSDataContainer, name: str = '', key_prefix: str = '') -> None:
        """
        速度関連のメトリクスを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # データフレームを取得
        df = container.data
        
        # 速度列が存在するか確認
        if 'speed' not in df.columns:
            st.warning("速度データがありません")
            return
        
        # 速度をノットに変換（もし必要なら）
        speed_col = 'speed'
        if df[speed_col].mean() < 10:  # おそらくm/s表記
            speed_values = df[speed_col] * 1.94384  # m/s からノットに変換
        else:
            speed_values = df[speed_col]
        
        # 速度メトリクスの計算
        avg_speed = speed_values.mean()
        max_speed = speed_values.max()
        min_speed = speed_values.min()
        std_speed = speed_values.std()
        
        # カードを3列で表示
        cols = st.columns(3)
        
        # 平均速度
        with cols[0]:
            Card(
                title="平均速度",
                content=f"{avg_speed:.2f} ノット",
                description=f"標準偏差: ±{std_speed:.2f} ノット",
                key=f"{key_prefix}avg_speed"
            )
        
        # 最高速度
        with cols[1]:
            Card(
                title="最高速度",
                content=f"{max_speed:.2f} ノット",
                description=f"平均を{(max_speed/avg_speed - 1)*100:.1f}%上回る",
                key=f"{key_prefix}max_speed"
            )
        
        # 最低速度
        with cols[2]:
            Card(
                title="最低速度",
                content=f"{min_speed:.2f} ノット",
                description=f"平均を{(1 - min_speed/avg_speed)*100:.1f}%下回る",
                key=f"{key_prefix}min_speed"
            )
    
    def render_course_metrics(self, container: GPSDataContainer, name: str = '', key_prefix: str = '') -> None:
        """
        コース関連のメトリクスを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # データフレームを取得
        df = container.data
        
        # コース列が存在するか確認
        if 'course' not in df.columns:
            st.warning("コースデータがありません")
            return
        
        # コースに関するメトリクスの計算
        course_values = df['course']
        avg_course = self._circular_mean(course_values)
        std_course = self._circular_std(course_values)
        
        # タックの検出（コースの大きな変化）
        tack_indices = self._detect_tacks(course_values)
        tack_count = len(tack_indices)
        
        # 運航時間の計算（タイムスタンプがある場合）
        sailing_time_min = 0
        if 'timestamp' in df.columns:
            sailing_time_sec = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
            sailing_time_min = sailing_time_sec / 60
        
        # カードを3列で表示
        cols = st.columns(3)
        
        # 平均コース
        with cols[0]:
            Card(
                title="平均コース",
                content=f"{avg_course:.1f}°",
                description=f"標準偏差: ±{std_course:.1f}°",
                key=f"{key_prefix}avg_course"
            )
        
        # タック回数
        with cols[1]:
            Card(
                title="タック回数",
                content=f"{tack_count}",
                description=f"平均間隔: {sailing_time_min/max(1, tack_count):.1f}分" if sailing_time_min > 0 else "",
                key=f"{key_prefix}tack_count"
            )
        
        # コース安定性
        stability = 100 - min(100, std_course * 2)  # 標準偏差が小さいほど安定性が高い
        with cols[2]:
            Card(
                title="コース安定性",
                content=f"{stability:.1f}%",
                description="コースの一貫性を示す指標",
                key=f"{key_prefix}course_stability"
            )
    
    def render_wind_metrics(self, container: GPSDataContainer, name: str = '', key_prefix: str = '') -> None:
        """
        風関連のメトリクスを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # データフレームを取得
        df = container.data
        
        # 風向列が存在するか確認
        if 'wind_direction' not in df.columns:
            st.warning("風向データがありません")
            return
        
        # 風向に関するメトリクスの計算
        wind_values = df['wind_direction']
        avg_wind = self._circular_mean(wind_values)
        std_wind = self._circular_std(wind_values)
        
        # 風のシフト検出（風向の大きな変化）
        shift_indices = self._detect_wind_shifts(wind_values)
        shift_count = len(shift_indices)
        
        # 風のシフト幅の計算
        shift_magnitudes = []
        for i in shift_indices:
            if i > 0 and i < len(wind_values) - 1:
                before_shift = wind_values.iloc[i-1]
                after_shift = wind_values.iloc[i+1]
                magnitude = min(abs(after_shift - before_shift), 360 - abs(after_shift - before_shift))
                shift_magnitudes.append(magnitude)
        
        avg_shift_magnitude = np.mean(shift_magnitudes) if shift_magnitudes else 0
        
        # カードを3列で表示
        cols = st.columns(3)
        
        # 平均風向
        with cols[0]:
            Card(
                title="平均風向",
                content=f"{avg_wind:.1f}°",
                description=f"変動: ±{std_wind:.1f}°",
                key=f"{key_prefix}avg_wind"
            )
        
        # 風向シフト回数
        with cols[1]:
            Card(
                title="風向シフト回数",
                content=f"{shift_count}",
                description=f"平均シフト幅: {avg_shift_magnitude:.1f}°",
                key=f"{key_prefix}wind_shifts"
            )
        
        # 風の安定性
        stability = 100 - min(100, std_wind * 2)  # 標準偏差が小さいほど安定性が高い
        with cols[2]:
            Card(
                title="風向安定性",
                content=f"{stability:.1f}%",
                description="風向の一貫性を示す指標",
                key=f"{key_prefix}wind_stability"
            )
    
    def render_vmg_metrics(self, container: GPSDataContainer, name: str = '', key_prefix: str = '') -> None:
        """
        VMG（Velocity Made Good）関連のメトリクスを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # データフレームを取得
        df = container.data
        
        # 必要な列が存在するか確認
        if 'speed' not in df.columns or 'course' not in df.columns or 'wind_direction' not in df.columns:
            st.warning("VMG計算に必要なデータ（速度、コース、風向）がありません")
            return
        
        # VMGの計算
        vmg = self._calculate_vmg(df)
        
        # VMGメトリクスの計算
        avg_vmg = vmg.mean()
        max_vmg = vmg.max()
        efficiency = (avg_vmg / df['speed'].mean()) * 100 if df['speed'].mean() > 0 else 0
        
        # 風上・風下VMGの計算
        # 相対角度を計算
        relative_angle = (df['wind_direction'] - df['course']).apply(lambda x: (x + 180) % 360 - 180)
        
        # 風上データ（相対角度の絶対値が90度未満）
        upwind_mask = relative_angle.abs() < 90
        upwind_vmg = vmg[upwind_mask].mean() if upwind_mask.any() else 0
        
        # 風下データ（相対角度の絶対値が90度以上）
        downwind_mask = relative_angle.abs() >= 90
        downwind_vmg = vmg[downwind_mask].mean() if downwind_mask.any() else 0
        
        # カードを3列で表示
        cols = st.columns(3)
        
        # 平均VMG
        with cols[0]:
            Card(
                title="平均VMG",
                content=f"{avg_vmg:.2f}",
                description=f"効率: {efficiency:.1f}%",
                key=f"{key_prefix}avg_vmg"
            )
        
        # 風上VMG
        with cols[1]:
            Card(
                title="風上VMG",
                content=f"{upwind_vmg:.2f}",
                description="風に向かう際の対地速度",
                key=f"{key_prefix}upwind_vmg"
            )
        
        # 風下VMG
        with cols[2]:
            Card(
                title="風下VMG",
                content=f"{downwind_vmg:.2f}",
                description="風に背を向ける際の対地速度",
                key=f"{key_prefix}downwind_vmg"
            )
    
    def render_distance_metrics(self, container: GPSDataContainer, name: str = '', key_prefix: str = '') -> None:
        """
        距離関連のメトリクスを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # データフレームを取得
        df = container.data
        
        # 必要な列が存在するか確認
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            st.warning("距離計算に必要な位置データがありません")
            return
        
        # 累積距離の計算
        distance = self._calculate_cumulative_distance(df)
        total_distance_m = distance[-1] if len(distance) > 0 else 0
        total_distance_nm = total_distance_m / 1852  # メートルから海里に変換
        
        # 直線距離の計算
        straight_distance_m = self._calculate_straight_distance(df)
        straight_distance_nm = straight_distance_m / 1852
        
        # 効率（直線距離/実際の距離）
        efficiency = (straight_distance_m / total_distance_m) * 100 if total_distance_m > 0 else 0
        
        # 速度計算用の時間（タイムスタンプがある場合）
        avg_speed_knots = 0
        if 'timestamp' in df.columns:
            sailing_time_hours = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
            if sailing_time_hours > 0:
                avg_speed_knots = total_distance_nm / sailing_time_hours
        
        # カードを3列で表示
        cols = st.columns(3)
        
        # 走行距離
        with cols[0]:
            Card(
                title="走行距離",
                content=f"{total_distance_nm:.2f} 海里",
                description=f"平均速度: {avg_speed_knots:.2f} ノット" if avg_speed_knots > 0 else "",
                key=f"{key_prefix}total_distance"
            )
        
        # 直線距離
        with cols[1]:
            Card(
                title="直線距離",
                content=f"{straight_distance_nm:.2f} 海里",
                description="スタートからゴールまで",
                key=f"{key_prefix}straight_distance"
            )
        
        # 経路効率
        with cols[2]:
            Card(
                title="経路効率",
                content=f"{efficiency:.1f}%",
                description="直線距離/走行距離の比率",
                key=f"{key_prefix}route_efficiency"
            )
    
    def render_overall_metrics(self, container: GPSDataContainer, name: str = '', key_prefix: str = '') -> None:
        """
        総合的なメトリクスを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # データフレームを取得
        df = container.data
        
        # セッション情報を計算
        points_count = len(df)
        
        # 時間関連の情報（タイムスタンプがある場合）
        session_duration_min = 0
        sampling_freq = 0
        if 'timestamp' in df.columns:
            session_duration_sec = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
            session_duration_min = session_duration_sec / 60
            
            # サンプリング頻度
            if session_duration_sec > 0:
                sampling_freq = points_count / session_duration_sec
        
        # メタデータから追加情報を取得
        metadata = container.metadata
        boat_type = metadata.get('boat_type', '不明')
        created_at = metadata.get('created_at', '不明')
        
        # タイムスタンプをフォーマット
        if isinstance(created_at, str):
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = created_dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        # カードを横に3つ表示
        cols = st.columns(3)
        
        # セッション概要
        with cols[0]:
            Card(
                title="セッション情報",
                content=f"記録時間: {session_duration_min:.1f}分",
                description=f"データポイント: {points_count}個",
                key=f"{key_prefix}session_info"
            )
        
        # データ品質
        data_quality = min(100, sampling_freq * 10)  # サンプリング頻度が10Hzで100%
        with cols[1]:
            Card(
                title="データ品質",
                content=f"{data_quality:.1f}%",
                description=f"サンプリング頻度: {sampling_freq:.2f}Hz",
                key=f"{key_prefix}data_quality"
            )
        
        # ボート情報
        with cols[2]:
            Card(
                title="ボート情報",
                content=boat_type,
                description=f"記録日時: {created_at}",
                key=f"{key_prefix}boat_info"
            )
    
    def render_dashboard(self, container: GPSDataContainer, name: str = '') -> None:
        """
        総合的なダッシュボードを表示
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            データセット名
        """
        if name:
            st.subheader(f"{name} パフォーマンスダッシュボード")
        else:
            st.subheader("パフォーマンスダッシュボード")
        
        # セクションを分けてメトリクスを表示
        
        # セッション概要
        st.markdown("#### セッション概要")
        self.render_overall_metrics(container, name, "overall_")
        
        # 速度パフォーマンス
        st.markdown("#### 速度パフォーマンス")
        self.render_speed_metrics(container, name, "speed_")
        
        # コースと風向
        cols = st.columns(2)
        
        with cols[0]:
            st.markdown("#### コース")
            self.render_course_metrics(container, name, "course_")
        
        with cols[1]:
            st.markdown("#### 風向")
            self.render_wind_metrics(container, name, "wind_")
        
        # VMGと距離
        cols = st.columns(2)
        
        with cols[0]:
            st.markdown("#### VMG")
            self.render_vmg_metrics(container, name, "vmg_")
        
        with cols[1]:
            st.markdown("#### 距離")
            self.render_distance_metrics(container, name, "distance_")
    
    def _circular_mean(self, angles: pd.Series) -> float:
        """
        角度の円周平均を計算
        
        Parameters
        ----------
        angles : pd.Series
            角度データの系列（度数法）
            
        Returns
        -------
        float
            平均角度（度数法）
        """
        # ラジアンに変換
        rad = np.radians(angles)
        
        # 複素数表現で平均を計算
        x = np.mean(np.cos(rad))
        y = np.mean(np.sin(rad))
        
        # 平均角度を計算
        mean_rad = np.arctan2(y, x)
        
        # 度数法に戻して0-360の範囲に調整
        mean_deg = (np.degrees(mean_rad) + 360) % 360
        
        return mean_deg
    
    def _circular_std(self, angles: pd.Series) -> float:
        """
        角度の円周標準偏差を計算
        
        Parameters
        ----------
        angles : pd.Series
            角度データの系列（度数法）
            
        Returns
        -------
        float
            標準偏差（度数法）
        """
        # ラジアンに変換
        rad = np.radians(angles)
        
        # 複素数表現で分散を計算
        x = np.mean(np.cos(rad))
        y = np.mean(np.sin(rad))
        r = np.sqrt(x**2 + y**2)
        
        # 円周分散から標準偏差を計算
        std_rad = np.sqrt(-2 * np.log(r))
        
        # 度数法に変換
        std_deg = np.degrees(std_rad)
        
        return std_deg
    
    def _detect_tacks(self, course_series: pd.Series, threshold: float = 60.0) -> List[int]:
        """
        コース変化からタックを検出
        
        Parameters
        ----------
        course_series : pd.Series
            コースデータの系列
        threshold : float, optional
            タックと判定する角度変化の閾値
            
        Returns
        -------
        List[int]
            タックが検出されたインデックスのリスト
        """
        tack_indices = []
        
        if len(course_series) < 3:
            return tack_indices
        
        # 前後の値の差を計算
        diffs = course_series.diff().abs()
        
        # 角度の特殊処理（0度と360度が近い）
        diffs = diffs.apply(lambda x: min(x, 360 - x) if not pd.isna(x) else x)
        
        # 閾値以上の変化を検出
        for i in range(1, len(diffs)):
            if diffs.iloc[i] >= threshold:
                # 前後の変化が小さい場合のみタックとみなす（ノイズ除去）
                if i > 1 and i < len(diffs) - 1:
                    if diffs.iloc[i-1] < threshold / 2 and diffs.iloc[i+1] < threshold / 2:
                        tack_indices.append(i)
        
        return tack_indices
    
    def _detect_wind_shifts(self, wind_series: pd.Series, threshold: float = 15.0, window: int = 5) -> List[int]:
        """
        風向変化から風向シフトを検出
        
        Parameters
        ----------
        wind_series : pd.Series
            風向データの系列
        threshold : float, optional
            シフトと判定する角度変化の閾値
        window : int, optional
            移動平均のウィンドウサイズ
            
        Returns
        -------
        List[int]
            風向シフトが検出されたインデックスのリスト
        """
        shift_indices = []
        
        if len(wind_series) < window * 2:
            return shift_indices
        
        # 移動平均を計算して風のノイズを除去
        # 角度データなので単純平均ではなく円周平均を使用
        smoothed = []
        for i in range(len(wind_series)):
            if i < window // 2 or i >= len(wind_series) - window // 2:
                smoothed.append(wind_series.iloc[i])
            else:
                window_data = wind_series.iloc[i - window // 2:i + window // 2 + 1]
                smoothed.append(self._circular_mean(window_data))
        
        smoothed_series = pd.Series(smoothed)
        
        # 前後の値の差を計算
        diffs = smoothed_series.diff().abs()
        
        # 角度の特殊処理（0度と360度が近い）
        diffs = diffs.apply(lambda x: min(x, 360 - x) if not pd.isna(x) else x)
        
        # 閾値以上の変化を検出
        for i in range(1, len(diffs)):
            if diffs.iloc[i] >= threshold:
                # 前後にも変化がある場合のみ有意なシフトとみなす
                if i > window and i < len(diffs) - window:
                    before_avg = self._circular_mean(smoothed_series.iloc[i-window:i])
                    after_avg = self._circular_mean(smoothed_series.iloc[i:i+window])
                    diff = min(abs(after_avg - before_avg), 360 - abs(after_avg - before_avg))
                    
                    if diff >= threshold:
                        shift_indices.append(i)
        
        return shift_indices
    
    def _calculate_vmg(self, df: pd.DataFrame) -> pd.Series:
        """
        VMG（Velocity Made Good）を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算に使用するデータフレーム（speed, course, wind_directionカラムが必要）
            
        Returns
        -------
        pd.Series
            計算されたVMG
        """
        # 速度がm/sの場合はノットに変換
        speed_col = 'speed'
        if df[speed_col].mean() < 10:  # おそらくm/s表記
            speed = df[speed_col] * 1.94384  # m/s からノットに変換
        else:
            speed = df[speed_col]
        
        # 艇の進行方向と風向の相対角度を計算
        relative_angle = (df['wind_direction'] - df['course']).apply(lambda x: (x + 180) % 360 - 180).abs()
        
        # VMG = 速度 × cos(相対角度)
        vmg = speed * np.cos(np.radians(relative_angle))
        
        return vmg
    
    def _calculate_cumulative_distance(self, df: pd.DataFrame) -> np.ndarray:
        """
        累積距離を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算に使用するデータフレーム（latitude, longitudeカラムが必要）
            
        Returns
        -------
        np.ndarray
            計算された累積距離（メートル）
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # ハバーサイン公式による2点間の距離計算
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000  # 地球の半径（メートル）
            
            # 緯度経度をラジアンに変換
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # ハバーサイン公式
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            return distance
        
        # 累積距離の計算
        distances = np.zeros(len(df))
        
        for i in range(1, len(df)):
            # 2点間の距離を計算
            dist = haversine(
                df['latitude'].iloc[i-1], df['longitude'].iloc[i-1],
                df['latitude'].iloc[i], df['longitude'].iloc[i]
            )
            
            # 累積距離を更新
            distances[i] = distances[i-1] + dist
        
        return distances
    
    def _calculate_straight_distance(self, df: pd.DataFrame) -> float:
        """
        始点から終点までの直線距離を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算に使用するデータフレーム（latitude, longitudeカラムが必要）
            
        Returns
        -------
        float
            計算された直線距離（メートル）
        """
        from math import radians, sin, cos, sqrt, atan2
        
        if len(df) < 2:
            return 0.0
        
        # 始点と終点の緯度経度
        start_lat = df['latitude'].iloc[0]
        start_lon = df['longitude'].iloc[0]
        end_lat = df['latitude'].iloc[-1]
        end_lon = df['longitude'].iloc[-1]
        
        # ハバーサイン公式による距離計算
        R = 6371000  # 地球の半径（メートル）
        
        # 緯度経度をラジアンに変換
        lat1, lon1, lat2, lon2 = map(radians, [start_lat, start_lon, end_lat, end_lon])
        
        # ハバーサイン公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance
