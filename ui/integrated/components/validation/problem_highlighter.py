# -*- coding: utf-8 -*-
"""
ui.integrated.components.validation.problem_highlighter

セーリング戦略分析システムのデータ問題を視覚的にハイライトするコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from typing import Dict, List, Any, Optional, Tuple

from sailing_data_processor.data_model.container import GPSDataContainer


def render_problem_highlight(
    container: GPSDataContainer,
    problem_type: str,
    affected_indices: List[int],
    affected_columns: Optional[List[str]] = None
):
    """
    データ問題を視覚的にハイライトするコンポーネント

    Parameters
    ----------
    container : GPSDataContainer
        対象のデータコンテナ
    problem_type : str
        問題の種類 ('missing', 'outlier', 'timestamp', 'coordinate')
    affected_indices : List[int]
        影響を受けるデータポイントのインデックスリスト
    affected_columns : Optional[List[str]], optional
        影響を受ける列のリスト, by default None
    """
    if not container or not hasattr(container, 'data') or container.data is None:
        st.error("データがありません。")
        return
    
    # データフレームを取得
    df = container.data
    
    # 問題タイプに応じたハイライト表示
    if problem_type == 'missing':
        render_missing_value_highlight(df, affected_indices, affected_columns)
    elif problem_type == 'outlier':
        render_outlier_highlight(df, affected_indices, affected_columns)
    elif problem_type == 'timestamp':
        render_timestamp_highlight(df, affected_indices)
    elif problem_type == 'coordinate':
        render_coordinate_highlight(df, affected_indices)
    else:
        st.warning(f"未知の問題タイプです: {problem_type}")


def render_missing_value_highlight(
    df: pd.DataFrame,
    affected_indices: List[int],
    affected_columns: Optional[List[str]] = None
):
    """
    欠損値のハイライト表示

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム
    affected_indices : List[int]
        欠損値を含む行のインデックスリスト
    affected_columns : Optional[List[str]], optional
        欠損値を含む列のリスト, by default None
    """
    st.markdown("### 欠損値のハイライト")
    
    # 欠損値を含む行を表示
    affected_data = df.loc[affected_indices]
    st.dataframe(affected_data.head(10), use_container_width=True)
    
    # 欠損値の列ごとの分布を表示
    st.markdown("#### 欠損値の分布")
    
    # 欠損値のある列を特定
    missing_columns = []
    if affected_columns:
        missing_columns = affected_columns
    else:
        for col in df.columns:
            if df.loc[affected_indices, col].isna().any():
                missing_columns.append(col)
    
    # 列ごとの欠損値の数と割合を計算
    missing_stats = {}
    for col in missing_columns:
        missing_count = df.loc[affected_indices, col].isna().sum()
        missing_pct = 100 * missing_count / len(affected_indices)
        missing_stats[col] = {"count": missing_count, "percent": missing_pct}
    
    # 統計情報の表示
    if missing_stats:
        stats_df = pd.DataFrame.from_dict(missing_stats, orient='index')
        st.bar_chart(stats_df["percent"])
        
        # 数値列の場合は時系列表示も行う
        for col in missing_columns:
            if pd.api.types.is_numeric_dtype(df[col].dtype) and "timestamp" in df.columns:
                st.markdown(f"#### 列 '{col}' の欠損値パターン")
                
                # タイムスタンプでソート
                temp_df = df.sort_values("timestamp")
                
                # 欠損値の位置にマーカー表示
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(temp_df["timestamp"], temp_df[col], 'o-', alpha=0.7, label=col)
                
                # 欠損値の位置をマーク
                for idx in affected_indices:
                    if idx in temp_df.index and pd.isna(temp_df.loc[idx, col]):
                        timestamp = temp_df.loc[idx, "timestamp"]
                        ax.axvline(x=timestamp, color='r', linestyle='--', alpha=0.3)
                
                ax.set_xlabel('時間')
                ax.set_ylabel(col)
                ax.set_title(f'{col}の欠損値パターン')
                ax.legend()
                
                st.pyplot(fig)
    else:
        st.info("欠損値のある列が見つかりませんでした。")


def render_outlier_highlight(
    df: pd.DataFrame,
    affected_indices: List[int],
    affected_columns: Optional[List[str]] = None
):
    """
    異常値のハイライト表示

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム
    affected_indices : List[int]
        異常値を含む行のインデックスリスト
    affected_columns : Optional[List[str]], optional
        異常値を含む列のリスト, by default None
    """
    st.markdown("### 異常値のハイライト")
    
    # 異常値を含む行を表示
    affected_data = df.loc[affected_indices]
    st.dataframe(affected_data.head(10), use_container_width=True)
    
    # 異常値の列ごとの分布を表示
    st.markdown("#### 異常値の分布")
    
    # 異常値のある列を特定（数値列のみ）
    outlier_columns = []
    if affected_columns:
        outlier_columns = [col for col in affected_columns if pd.api.types.is_numeric_dtype(df[col].dtype)]
    else:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col].dtype) and col not in ['timestamp']:
                # 簡易的な異常値検出（IQRベース）
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                # 異常値の判定
                outlier_mask = (df.loc[affected_indices, col] < lower_bound) | (df.loc[affected_indices, col] > upper_bound)
                if outlier_mask.any():
                    outlier_columns.append(col)
    
    # 列ごとのヒストグラムとボックスプロットを表示
    for col in outlier_columns:
        st.markdown(f"#### 列 '{col}' の異常値分布")
        
        # ヒストグラム
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # 全データのヒストグラム
        ax1.hist(df[col].dropna(), bins=30, alpha=0.7, label='全データ')
        
        # 異常値のヒストグラム
        ax1.hist(df.loc[affected_indices, col].dropna(), bins=20, alpha=0.7, color='red', label='異常値')
        
        ax1.set_xlabel(col)
        ax1.set_ylabel('頻度')
        ax1.set_title(f'{col}のヒストグラム')
        ax1.legend()
        
        # ボックスプロット
        ax2.boxplot([df[col].dropna(), df.loc[affected_indices, col].dropna()],
                   labels=['全データ', '異常値'])
        ax2.set_ylabel(col)
        ax2.set_title(f'{col}のボックスプロット')
        
        st.pyplot(fig)
        
        # 時系列表示（タイムスタンプ列がある場合）
        if "timestamp" in df.columns:
            st.markdown(f"#### 列 '{col}' の時系列パターン")
            
            # タイムスタンプでソート
            temp_df = df.sort_values("timestamp")
            
            # 時系列プロット
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(temp_df["timestamp"], temp_df[col], 'o-', alpha=0.5, label=col)
            
            # 異常値をハイライト
            for idx in affected_indices:
                if idx in temp_df.index:
                    timestamp = temp_df.loc[idx, "timestamp"]
                    value = temp_df.loc[idx, col]
                    ax.plot(timestamp, value, 'ro', markersize=8)
            
            ax.set_xlabel('時間')
            ax.set_ylabel(col)
            ax.set_title(f'{col}の異常値パターン')
            
            st.pyplot(fig)
    
    if not outlier_columns:
        st.info("異常値のある数値列が見つかりませんでした。")


def render_timestamp_highlight(
    df: pd.DataFrame,
    affected_indices: List[int]
):
    """
    タイムスタンプの問題のハイライト表示

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム
    affected_indices : List[int]
        タイムスタンプの問題を含む行のインデックスリスト
    """
    st.markdown("### タイムスタンプの問題のハイライト")
    
    # タイムスタンプ列の確認
    if "timestamp" not in df.columns:
        st.error("タイムスタンプ列がありません。")
        return
    
    # 影響を受ける行を表示
    affected_data = df.loc[affected_indices]
    st.dataframe(affected_data.head(10), use_container_width=True)
    
    # タイムスタンプ問題の種類を特定
    st.markdown("#### タイムスタンプの問題の種類")
    
    # タイムスタンプでソート
    df_sorted = df.sort_values("timestamp").copy()
    df_sorted["time_diff"] = df_sorted["timestamp"].diff().dt.total_seconds()
    
    # 重複タイムスタンプの検出
    duplicates = df_sorted[df_sorted.duplicated(subset=["timestamp"], keep=False)]
    has_duplicates = len(duplicates) > 0
    
    # ギャップの検出（中央値の5倍以上、または10秒以上の差）
    median_diff = df_sorted["time_diff"].median()
    gap_threshold = max(10.0, median_diff * 5)  # 10秒または中央値の5倍のいずれか大きい方
    gaps = df_sorted[df_sorted["time_diff"] > gap_threshold]
    has_gaps = len(gaps) > 0
    
    # 時間順の問題（ソートされていない場合）
    has_order_issues = (df_sorted["time_diff"] < 0).any()
    
    # 問題の概要表示
    if has_duplicates:
        st.info(f"重複タイムスタンプが{len(duplicates)//2}件検出されました。")
    
    if has_gaps:
        st.info(f"タイムスタンプのギャップが{len(gaps)}件検出されました（>{gap_threshold:.1f}秒）。")
    
    if has_order_issues:
        st.info("タイムスタンプの順序に問題があります。")
    
    # タイムスタンプの連続性を可視化
    st.markdown("#### タイムスタンプの連続性")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # タイムスタンプの連続性プロット
    ax1.plot(range(len(df_sorted)), df_sorted["timestamp"], 'o-', alpha=0.7)
    ax1.set_xlabel('データポイント')
    ax1.set_ylabel('タイムスタンプ')
    ax1.set_title('タイムスタンプの連続性')
    
    # 問題箇所のハイライト
    for idx in affected_indices:
        if idx in df_sorted.index:
            point_idx = df_sorted.index.get_loc(idx)
            timestamp = df_sorted.loc[idx, "timestamp"]
            ax1.plot(point_idx, timestamp, 'ro', markersize=8)
    
    # 時間差のプロット
    ax2.plot(range(len(df_sorted.dropna())), df_sorted["time_diff"].dropna(), 'o-', alpha=0.7)
    ax2.set_xlabel('データポイント')
    ax2.set_ylabel('時間差 (秒)')
    ax2.set_title('タイムスタンプの間隔')
    
    # ギャップしきい値の表示
    if has_gaps:
        ax2.axhline(y=gap_threshold, color='r', linestyle='--', label=f'ギャップしきい値 ({gap_threshold:.1f}秒)')
        ax2.legend()
    
    # 問題箇所のハイライト
    for idx in affected_indices:
        if idx in df_sorted.index and df_sorted.index.get_loc(idx) > 0:
            point_idx = df_sorted.index.get_loc(idx) - 1  # 時間差は1つ前のインデックス
            if point_idx >= 0 and point_idx < len(df_sorted["time_diff"]):
                time_diff = df_sorted["time_diff"].iloc[point_idx]
                if not pd.isna(time_diff):
                    ax2.plot(point_idx, time_diff, 'ro', markersize=8)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # 時間差のヒストグラム
    st.markdown("#### タイムスタンプ間隔の分布")
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(df_sorted["time_diff"].dropna(), bins=30, alpha=0.7)
    ax.set_xlabel('時間差 (秒)')
    ax.set_ylabel('頻度')
    ax.set_title('タイムスタンプ間隔のヒストグラム')
    
    # ギャップしきい値の表示
    if has_gaps:
        ax.axvline(x=gap_threshold, color='r', linestyle='--', label=f'ギャップしきい値 ({gap_threshold:.1f}秒)')
        ax.legend()
    
    st.pyplot(fig)


def render_coordinate_highlight(
    df: pd.DataFrame,
    affected_indices: List[int]
):
    """
    座標データの問題のハイライト表示

    Parameters
    ----------
    df : pd.DataFrame
        データフレーム
    affected_indices : List[int]
        座標データの問題を含む行のインデックスリスト
    """
    st.markdown("### 座標データの問題のハイライト")
    
    # 座標列の確認
    if "latitude" not in df.columns or "longitude" not in df.columns:
        st.error("緯度・経度データがありません。")
        return
    
    # 影響を受ける行を表示
    affected_data = df.loc[affected_indices]
    st.dataframe(affected_data.head(10), use_container_width=True)
    
    # 地図上での可視化
    st.markdown("#### 位置データの可視化")
    
    # 地図の中心座標
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    
    # foliumマップの作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 全体の軌跡をプロット
    folium.PolyLine(
        df[["latitude", "longitude"]].values.tolist(),
        color="blue",
        weight=2,
        opacity=0.7
    ).add_to(m)
    
    # 問題のある点をハイライト
    for idx in affected_indices:
        if idx in df.index:
            folium.CircleMarker(
                location=[df.loc[idx, "latitude"], df.loc[idx, "longitude"]],
                radius=8,
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.7,
                popup=f"インデックス: {idx}"
            ).add_to(m)
    
    # マップの表示
    folium_static(m)
    
    # スピード分析（タイムスタンプ列がある場合）
    if "timestamp" in df.columns:
        st.markdown("#### 速度プロファイル")
        
        # タイムスタンプでソート
        temp_df = df.sort_values("timestamp").copy()
        
        # 距離と速度を計算
        temp_df["lat_diff"] = temp_df["latitude"].diff()
        temp_df["lon_diff"] = temp_df["longitude"].diff()
        
        # 簡易的な距離計算（正確な地理的距離ではない）
        temp_df["distance"] = np.sqrt(temp_df["lat_diff"]**2 + temp_df["lon_diff"]**2) * 111000  # 緯度経度を約111kmに変換
        
        # 時間差分
        temp_df["time_diff"] = temp_df["timestamp"].diff().dt.total_seconds()
        
        # 速度計算（m/s）
        temp_df["speed_calc"] = temp_df["distance"] / temp_df["time_diff"]
        
        # 速度の可視化
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(temp_df["timestamp"], temp_df["speed_calc"], 'o-', alpha=0.7, label="計算速度")
        
        # 既存の速度列がある場合は比較
        if "speed" in temp_df.columns:
            ax.plot(temp_df["timestamp"], temp_df["speed"], 'o-', alpha=0.7, label="記録速度")
        
        # 問題点のハイライト
        for idx in affected_indices:
            if idx in temp_df.index:
                timestamp = temp_df.loc[idx, "timestamp"]
                speed = temp_df.loc[idx, "speed_calc"]
                if not pd.isna(speed):
                    ax.plot(timestamp, speed, 'ro', markersize=8)
        
        ax.set_xlabel('時間')
        ax.set_ylabel('速度 (m/s)')
        ax.set_title('速度プロファイル')
        ax.legend()
        
        st.pyplot(fig)
        
        # 速度の異常値の検出と表示
        st.markdown("#### 速度異常値分析")
        
        # 中央値と四分位範囲を使用した異常値の検出
        q1 = temp_df["speed_calc"].quantile(0.25)
        q3 = temp_df["speed_calc"].quantile(0.75)
        iqr = q3 - q1
        lower_bound = max(0, q1 - 1.5 * iqr)  # 速度は非負
        upper_bound = q3 + 1.5 * iqr
        
        # 異常値の判定
        outlier_mask = (temp_df["speed_calc"] < lower_bound) | (temp_df["speed_calc"] > upper_bound)
        outliers = temp_df[outlier_mask]
        
        # 異常値の表示
        if not outliers.empty:
            st.info(f"速度の異常値が{len(outliers)}件検出されました（<{lower_bound:.2f}m/s または >{upper_bound:.2f}m/s）。")
            
            # 速度ヒストグラム
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.hist(temp_df["speed_calc"].dropna(), bins=30, alpha=0.7)
            ax.axvline(x=lower_bound, color='r', linestyle='--', label=f'下限 ({lower_bound:.2f}m/s)')
            ax.axvline(x=upper_bound, color='r', linestyle='--', label=f'上限 ({upper_bound:.2f}m/s)')
            ax.set_xlabel('速度 (m/s)')
            ax.set_ylabel('頻度')
            ax.set_title('速度の分布')
            ax.legend()
            
            st.pyplot(fig)
