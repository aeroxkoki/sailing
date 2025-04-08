"""
ui.integrated.components.data_explorer

セーリング戦略分析システムのデータ探索コンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from typing import Dict, List, Any, Optional

from sailing_data_processor.data_model.container import GPSDataContainer


def render_data_explorer(container: GPSDataContainer):
    """
    データエクスプローラーコンポーネントを表示

    Parameters
    ----------
    container : GPSDataContainer
        対象のデータコンテナ
    """
    if not container or not hasattr(container, 'data') or container.data is None:
        st.error("データがありません。")
        return
    
    # データフレームを取得
    df = container.data
    
    # タブで表示内容を切り替え
    tab1, tab2, tab3, tab4 = st.tabs(["データサマリー", "時系列データ", "マップビュー", "統計分析"])
    
    with tab1:
        render_data_summary(container)
    
    with tab2:
        render_time_series_view(container)
    
    with tab3:
        render_map_view(container)
    
    with tab4:
        render_statistical_analysis(container)


def render_data_summary(container: GPSDataContainer):
    """
    データサマリーを表示

    Parameters
    ----------
    container : GPSDataContainer
        対象のデータコンテナ
    """
    st.markdown("### データサマリー")
    
    # データフレームを取得
    df = container.data
    
    # 基本情報
    st.markdown("#### 基本情報")
    
    # データポイント数とカラム数
    col1, col2 = st.columns(2)
    with col1:
        st.metric("データポイント数", len(df))
    with col2:
        st.metric("カラム数", len(df.columns))
    
    # 時間範囲（存在する場合）
    if "timestamp" in df.columns:
        time_range = container.get_time_range()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**開始時刻:**", time_range["start"])
        with col2:
            st.write("**終了時刻:**", time_range["end"])
        
        # 期間と平均サンプリングレート
        duration_minutes = time_range["duration_seconds"] / 60
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("期間", f"{duration_minutes:.1f}分")
        
        if len(df) > 1:
            avg_sampling = time_range["duration_seconds"] / (len(df) - 1)
            with col2:
                st.metric("平均サンプリング間隔", f"{avg_sampling:.1f}秒")
    
    # メタデータ（存在する場合）
    if hasattr(container, 'metadata') and container.metadata:
        st.markdown("#### メタデータ")
        
        metadata = container.metadata
        metadata_df = pd.DataFrame.from_dict({k: [v] for k, v in metadata.items() if k not in ['created_at', 'updated_at']})
        
        st.dataframe(metadata_df.T, use_container_width=True)
    
    # データプレビュー
    st.markdown("#### データプレビュー")
    
    with st.expander("データプレビュー", expanded=True):
        st.dataframe(df.head(10), use_container_width=True)
    
    # 列情報
    st.markdown("#### 列情報")
    
    # 各列のデータ型と欠損値の数を表示
    col_info = []
    for col in df.columns:
        col_type = df[col].dtype
        missing_count = df[col].isna().sum()
        missing_pct = 100 * missing_count / len(df)
        
        # 基本統計量
        if pd.api.types.is_numeric_dtype(col_type):
            min_val = df[col].min()
            max_val = df[col].max()
            mean_val = df[col].mean()
            std_val = df[col].std()
            
            col_info.append({
                "列名": col,
                "データ型": col_type,
                "欠損値数": missing_count,
                "欠損率 (%)": f"{missing_pct:.2f}",
                "最小値": min_val,
                "最大値": max_val,
                "平均値": mean_val,
                "標準偏差": std_val
            })
        else:
            col_info.append({
                "列名": col,
                "データ型": col_type,
                "欠損値数": missing_count,
                "欠損率 (%)": f"{missing_pct:.2f}",
                "一意値数": df[col].nunique()
            })
    
    # 列情報をデータフレームとして表示
    col_info_df = pd.DataFrame(col_info)
    st.dataframe(col_info_df, use_container_width=True)


def render_time_series_view(container: GPSDataContainer):
    """
    時系列データビューを表示

    Parameters
    ----------
    container : GPSDataContainer
        対象のデータコンテナ
    """
    st.markdown("### 時系列データビュー")
    
    # データフレームを取得
    df = container.data
    
    # タイムスタンプ列がない場合
    if "timestamp" not in df.columns:
        st.warning("タイムスタンプ列がありません。時系列ビューは利用できません。")
        return
    
    # 表示する列を選択
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col].dtype) and col not in ["timestamp"]]
    
    if not numeric_cols:
        st.warning("表示可能な数値列がありません。")
        return
    
    selected_columns = st.multiselect(
        "表示する列を選択:",
        numeric_cols,
        default=numeric_cols[:min(3, len(numeric_cols))],  # デフォルトで最大3列を選択
        key="time_series_columns"
    )
    
    if not selected_columns:
        st.info("表示する列を選択してください。")
        return
    
    # 時間範囲の選択
    sorted_df = df.sort_values("timestamp")
    start_time = sorted_df["timestamp"].min()
    end_time = sorted_df["timestamp"].max()
    
    time_range = st.slider(
        "時間範囲を選択:",
        min_value=start_time,
        max_value=end_time,
        value=(start_time, end_time),
        key="time_range_slider"
    )
    
    # 選択した時間範囲のデータを取得
    filtered_df = sorted_df[(sorted_df["timestamp"] >= time_range[0]) & (sorted_df["timestamp"] <= time_range[1])]
    
    # プロットの種類を選択
    plot_type = st.radio(
        "プロットの種類:",
        ["線グラフ", "散布図", "マルチプロット"],
        horizontal=True,
        key="time_series_plot_type"
    )
    
    # ダウンサンプリングオプション
    if len(filtered_df) > 1000:
        st.warning(f"データポイントが多いため({len(filtered_df)}ポイント)、プロットが遅くなる可能性があります。")
        downsample = st.checkbox("ダウンサンプリング", value=True, key="downsample_checkbox")
        if downsample:
            sample_size = min(1000, len(filtered_df))
            filtered_df = filtered_df.sample(sample_size)
    
    # 選択したプロットを表示
    if plot_type == "線グラフ":
        st.markdown("#### 時系列線グラフ")
        
        plt.figure(figsize=(10, 6))
        for col in selected_columns:
            plt.plot(filtered_df["timestamp"], filtered_df[col], "-", label=col)
            
        plt.xlabel("時間")
        plt.ylabel("値")
        plt.title("時系列データ")
        plt.legend()
        plt.tight_layout()
        
        st.pyplot(plt)
    
    elif plot_type == "散布図":
        st.markdown("#### 時系列散布図")
        
        plt.figure(figsize=(10, 6))
        for col in selected_columns:
            plt.scatter(filtered_df["timestamp"], filtered_df[col], label=col, alpha=0.7)
            
        plt.xlabel("時間")
        plt.ylabel("値")
        plt.title("時系列データ")
        plt.legend()
        plt.tight_layout()
        
        st.pyplot(plt)
    
    elif plot_type == "マルチプロット":
        st.markdown("#### 複数軸プロット")
        
        # 複数のサブプロットを作成
        fig, axes = plt.subplots(len(selected_columns), 1, figsize=(10, 3 * len(selected_columns)), sharex=True)
        
        if len(selected_columns) == 1:
            # 選択が1つだけの場合、axesは配列ではなく単一のAxesオブジェクト
            axes = [axes]
        
        for i, col in enumerate(selected_columns):
            axes[i].plot(filtered_df["timestamp"], filtered_df[col], "-", label=col)
            axes[i].set_ylabel(col)
            axes[i].set_title(f"{col} vs 時間")
            axes[i].legend()
        
        # 最下部のプロットにX軸ラベルを追加
        axes[-1].set_xlabel("時間")
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # データ統計
    st.markdown("#### 選択範囲の統計")
    stats_df = filtered_df[selected_columns].describe().T
    st.dataframe(stats_df, use_container_width=True)


def render_map_view(container: GPSDataContainer):
    """
    マップビューを表示

    Parameters
    ----------
    container : GPSDataContainer
        対象のデータコンテナ
    """
    st.markdown("### マップビュー")
    
    # データフレームを取得
    df = container.data
    
    # 位置データがない場合
    if "latitude" not in df.columns or "longitude" not in df.columns:
        st.warning("緯度・経度データがありません。マップビューは利用できません。")
        return
    
    # マップ表示オプション
    map_options = st.columns(4)
    
    with map_options[0]:
        show_track = st.checkbox("航跡を表示", value=True, key="show_track_checkbox")
    
    with map_options[1]:
        show_points = st.checkbox("ポイントを表示", value=False, key="show_points_checkbox")
    
    with map_options[2]:
        if "speed" in df.columns:
            color_by_speed = st.checkbox("速度で色分け", value=True, key="color_by_speed_checkbox")
        else:
            color_by_speed = False
            st.checkbox("速度で色分け", value=False, disabled=True, key="color_by_speed_disabled")
    
    with map_options[3]:
        add_markers = st.checkbox("マーカーを追加", value=False, key="add_markers_checkbox")
    
    # 地図の中心座標
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    
    # foliumマップの作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 航跡の表示
    if show_track:
        # タイムスタンプでソート（存在する場合）
        if "timestamp" in df.columns:
            sorted_df = df.sort_values("timestamp")
        else:
            sorted_df = df
        
        # 速度で色分け
        if color_by_speed and "speed" in df.columns:
            # 速度の最小値・最大値を取得
            min_speed = sorted_df["speed"].min()
            max_speed = sorted_df["speed"].max()
            
            # 速度を正規化して色を計算
            def get_color(speed):
                norm_speed = (speed - min_speed) / (max_speed - min_speed)
                # 青(低速)から赤(高速)へのグラデーション
                r = int(255 * norm_speed)
                g = 0
                b = int(255 * (1 - norm_speed))
                return f"#{r:02x}{g:02x}{b:02x}"
            
            # 航跡を速度ごとに分割して表示
            for i in range(len(sorted_df) - 1):
                speed = sorted_df["speed"].iloc[i]
                start_point = [sorted_df["latitude"].iloc[i], sorted_df["longitude"].iloc[i]]
                end_point = [sorted_df["latitude"].iloc[i+1], sorted_df["longitude"].iloc[i+1]]
                
                folium.PolyLine(
                    [start_point, end_point],
                    color=get_color(speed),
                    weight=3,
                    opacity=0.8,
                    tooltip=f"速度: {speed:.1f}"
                ).add_to(m)
        else:
            # 普通の航跡表示
            folium.PolyLine(
                sorted_df[["latitude", "longitude"]].values.tolist(),
                color="blue",
                weight=3,
                opacity=0.8
            ).add_to(m)
    
    # ポイントの表示
    if show_points:
        # 表示するポイント数を制限
        max_points = 500
        if len(df) > max_points:
            point_df = df.sample(max_points)
            st.info(f"多数のポイントがあるため、{max_points}個のサンプルポイントを表示しています。")
        else:
            point_df = df
        
        # ポイントを追加
        for _, row in point_df.iterrows():
            popup_text = "<b>位置情報</b><br>"
            popup_text += f"緯度: {row['latitude']:.6f}<br>"
            popup_text += f"経度: {row['longitude']:.6f}<br>"
            
            if "timestamp" in row:
                popup_text += f"時刻: {row['timestamp']}<br>"
            
            if "speed" in row:
                popup_text += f"速度: {row['speed']:.1f}<br>"
            
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=3,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.7,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
    
    # マーカーの追加
    if add_markers:
        # タイムスタンプがあれば時間の区切りでマーカーを追加
        if "timestamp" in df.columns:
            sorted_df = df.sort_values("timestamp")
            
            # 開始点
            start_point = sorted_df.iloc[0]
            folium.Marker(
                location=[start_point["latitude"], start_point["longitude"]],
                popup="開始",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)
            
            # 終了点
            end_point = sorted_df.iloc[-1]
            folium.Marker(
                location=[end_point["latitude"], end_point["longitude"]],
                popup="終了",
                icon=folium.Icon(color="red", icon="stop")
            ).add_to(m)
            
            # 中間点（4等分）
            if len(sorted_df) > 10:
                for i in range(1, 4):
                    idx = len(sorted_df) * i // 4
                    mid_point = sorted_df.iloc[idx]
                    folium.Marker(
                        location=[mid_point["latitude"], mid_point["longitude"]],
                        popup=f"中間点 {i}",
                        icon=folium.Icon(color="blue", icon="info-sign")
                    ).add_to(m)
    
    # マップの表示
    folium_static(m)
    
    # 地理データの統計
    st.markdown("#### 地理データの統計")
    
    # 基本的な地理統計を計算
    geo_stats = [
        {"統計": "緯度範囲", "値": f"{df['latitude'].min():.6f} 〜 {df['latitude'].max():.6f}"},
        {"統計": "経度範囲", "値": f"{df['longitude'].min():.6f} 〜 {df['longitude'].max():.6f}"}
    ]
    
    # 速度があれば統計を追加
    if "speed" in df.columns:
        geo_stats.extend([
            {"統計": "平均速度", "値": f"{df['speed'].mean():.2f}"},
            {"統計": "最大速度", "値": f"{df['speed'].max():.2f}"},
            {"統計": "最小速度", "値": f"{df['speed'].min():.2f}"},
            {"統計": "速度標準偏差", "値": f"{df['speed'].std():.2f}"}
        ])
    
    # タイムスタンプがあれば移動距離を計算
    if "timestamp" in df.columns:
        sorted_df = df.sort_values("timestamp")
        
        # 簡易的な距離計算（正確な地理的距離ではない）
        lat_diff = sorted_df["latitude"].diff()
        lon_diff = sorted_df["longitude"].diff()
        distances = np.sqrt(lat_diff**2 + lon_diff**2) * 111000  # 緯度経度を約111kmに変換
        
        total_distance = distances.sum()
        geo_stats.append({"統計": "総移動距離（概算）", "値": f"{total_distance/1000:.2f} km"})
    
    # 統計を表示
    geo_stats_df = pd.DataFrame(geo_stats)
    st.dataframe(geo_stats_df, use_container_width=True, hide_index=True)


def render_statistical_analysis(container: GPSDataContainer):
    """
    統計分析の表示

    Parameters
    ----------
    container : GPSDataContainer
        対象のデータコンテナ
    """
    st.markdown("### 統計分析")
    
    # データフレームを取得
    df = container.data
    
    # 数値列の特定
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col].dtype) and col not in ["timestamp"]]
    
    if not numeric_cols:
        st.warning("統計分析可能な数値列がありません。")
        return
    
    # 分析の種類を選択
    analysis_type = st.radio(
        "分析の種類:",
        ["分布分析", "相関分析", "集計統計", "時系列分析"],
        horizontal=True,
        key="analysis_type_radio"
    )
    
    # 分布分析
    if analysis_type == "分布分析":
        st.markdown("#### 分布分析")
        
        # 分析対象の列を選択
        selected_column = st.selectbox(
            "分析する列を選択:",
            numeric_cols,
            key="distribution_column"
        )
        
        # ヒストグラムとボックスプロット
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**ヒストグラム**")
            
            # ヒストグラムのビン数を選択
            bins = st.slider("ビン数:", 5, 100, 30, key="histogram_bins")
            
            # ヒストグラムを表示
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(df[selected_column].dropna(), bins=bins, alpha=0.7)
            ax.set_xlabel(selected_column)
            ax.set_ylabel("頻度")
            ax.set_title(f"{selected_column}のヒストグラム")
            
            st.pyplot(fig)
        
        with col2:
            st.markdown("**ボックスプロット**")
            
            # ボックスプロットを表示
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.boxplot(df[selected_column].dropna())
            ax.set_ylabel(selected_column)
            ax.set_title(f"{selected_column}のボックスプロット")
            
            st.pyplot(fig)
        
        # 基本統計量
        st.markdown("**基本統計量**")
        stats = df[selected_column].describe()
        stats_df = pd.DataFrame(stats).T
        st.dataframe(stats_df, use_container_width=True)
        
        # 外れ値の分析
        st.markdown("**外れ値の分析**")
        
        # IQRを使用した外れ値の検出
        q1 = df[selected_column].quantile(0.25)
        q3 = df[selected_column].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = df[(df[selected_column] < lower_bound) | (df[selected_column] > upper_bound)]
        
        if len(outliers) > 0:
            st.info(f"外れ値が{len(outliers)}個検出されました（<{lower_bound:.2f} または >{upper_bound:.2f}）。")
            st.dataframe(outliers[["timestamp", selected_column]].head(10) if "timestamp" in df.columns else outliers[[selected_column]].head(10), use_container_width=True)
        else:
            st.success("外れ値は検出されませんでした。")
    
    # 相関分析
    elif analysis_type == "相関分析":
        st.markdown("#### 相関分析")
        
        # 相関行列を計算
        correlation = df[numeric_cols].corr()
        
        # 相関行列のヒートマップを表示
        st.markdown("**相関行列**")
        
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
        
        # 軸ラベルの設定
        ax.set_xticks(np.arange(len(numeric_cols)))
        ax.set_yticks(np.arange(len(numeric_cols)))
        ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
        ax.set_yticklabels(numeric_cols)
        
        # ヒートマップの値を表示
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                ax.text(j, i, f"{correlation.iloc[i, j]:.2f}",
                        ha="center", va="center", color="white" if abs(correlation.iloc[i, j]) > 0.5 else "black")
        
        plt.colorbar(im)
        plt.title("相関行列")
        plt.tight_layout()
        
        st.pyplot(fig)
        
        # 散布図行列
        st.markdown("**選択列の散布図**")
        
        # 散布図に表示する列を選択（最大4列）
        scatter_columns = st.multiselect(
            "散布図に表示する列を選択（最大4列）:",
            numeric_cols,
            default=numeric_cols[:min(4, len(numeric_cols))],
            max_selections=4,
            key="scatter_columns"
        )
        
        if len(scatter_columns) >= 2:
            # データ数が多い場合はサンプリング
            if len(df) > 1000:
                sample_df = df.sample(1000)
                st.info("データポイントが多いため、1000ポイントをサンプリングして表示しています。")
            else:
                sample_df = df
            
            # 散布図行列を表示
            fig, axes = plt.subplots(len(scatter_columns), len(scatter_columns), figsize=(12, 12))
            
            for i, col1 in enumerate(scatter_columns):
                for j, col2 in enumerate(scatter_columns):
                    if i == j:
                        # 対角線上はヒストグラム
                        axes[i, j].hist(sample_df[col1].dropna(), bins=20, alpha=0.7)
                        axes[i, j].set_title(col1)
                    else:
                        # 非対角線上は散布図
                        axes[i, j].scatter(sample_df[col2], sample_df[col1], alpha=0.5)
                        
                        # 相関係数を表示
                        corr = sample_df[[col1, col2]].corr().iloc[0, 1]
                        axes[i, j].set_title(f"r = {corr:.2f}")
                    
                    # 最下行のみx軸ラベルを表示
                    if i == len(scatter_columns) - 1:
                        axes[i, j].set_xlabel(col2)
                    
                    # 最左列のみy軸ラベルを表示
                    if j == 0:
                        axes[i, j].set_ylabel(col1)
            
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("散布図を表示するには、少なくとも2つの列を選択してください。")
    
    # 集計統計
    elif analysis_type == "集計統計":
        st.markdown("#### 集計統計")
        
        # 集計対象の列を選択
        target_column = st.selectbox(
            "集計対象の列を選択:",
            numeric_cols,
            key="aggregate_target_column"
        )
        
        # 時間的な集計の場合
        if "timestamp" in df.columns:
            st.markdown("**時間別の集計**")
            
            # 集計間隔を選択
            interval = st.selectbox(
                "集計間隔:",
                ["分ごと", "時間ごと", "日ごと", "月ごと"],
                key="aggregate_interval"
            )
            
            # 集計関数を選択
            agg_func = st.selectbox(
                "集計関数:",
                ["平均", "合計", "最大", "最小", "中央値", "標準偏差"],
                key="aggregate_function"
            )
            
            # 集計関数のマッピング
            agg_func_map = {
                "平均": "mean",
                "合計": "sum",
                "最大": "max",
                "最小": "min",
                "中央値": "median",
                "標準偏差": "std"
            }
            
            # 集計の実行
            df_copy = df.copy()
            
            # 時間列をインデックスに設定
            df_copy = df_copy.set_index("timestamp")
            
            # リサンプリング間隔の設定
            resample_map = {
                "分ごと": "1T",
                "時間ごと": "1H",
                "日ごと": "1D",
                "月ごと": "1M"
            }
            
            # リサンプリングと集計
            resampled = df_copy[target_column].resample(resample_map[interval]).agg(agg_func_map[agg_func])
            
            # 結果の表示
            st.markdown(f"**{interval}の{target_column}の{agg_func}**")
            
            if len(resampled) > 0:
                # データフレームとして表示
                st.dataframe(resampled.reset_index(), use_container_width=True)
                
                # 折れ線グラフで表示
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(resampled.index, resampled.values, "-o")
                ax.set_xlabel("時間")
                ax.set_ylabel(f"{target_column}の{agg_func}")
                ax.set_title(f"{interval}の{target_column}の{agg_func}")
                
                st.pyplot(fig)
            else:
                st.warning("集計結果が空です。異なる集計間隔を選択してください。")
        
        else:
            st.warning("時間別の集計を行うには、タイムスタンプ列が必要です。")
    
    # 時系列分析
    elif analysis_type == "時系列分析":
        st.markdown("#### 時系列分析")
        
        if "timestamp" not in df.columns:
            st.warning("時系列分析を行うには、タイムスタンプ列が必要です。")
            return
        
        # 分析対象の列を選択
        selected_column = st.selectbox(
            "分析する列を選択:",
            numeric_cols,
            key="time_series_column"
        )
        
        # タイムスタンプでソート
        df_sorted = df.sort_values("timestamp")
        
        # 時系列の変化率の計算
        df_sorted[f"{selected_column}_diff"] = df_sorted[selected_column].diff()
        df_sorted[f"{selected_column}_pct_change"] = df_sorted[selected_column].pct_change() * 100
        
        # タブで表示を切り替え
        ts_tab1, ts_tab2, ts_tab3 = st.tabs(["基本トレンド", "変化率", "移動平均"])
        
        with ts_tab1:
            st.markdown("**基本トレンド**")
            
            # 時系列プロット
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df_sorted["timestamp"], df_sorted[selected_column], "-")
            ax.set_xlabel("時間")
            ax.set_ylabel(selected_column)
            ax.set_title(f"{selected_column}の時系列変化")
            
            st.pyplot(fig)
        
        with ts_tab2:
            st.markdown("**変化率分析**")
            
            # 変化量と変化率のプロット
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
            
            # 変化量
            ax1.plot(df_sorted["timestamp"], df_sorted[f"{selected_column}_diff"], "-")
            ax1.set_ylabel(f"{selected_column}の変化量")
            ax1.set_title(f"{selected_column}の変化量")
            
            # 変化率
            ax2.plot(df_sorted["timestamp"], df_sorted[f"{selected_column}_pct_change"], "-")
            ax2.set_xlabel("時間")
            ax2.set_ylabel(f"{selected_column}の変化率 (%)")
            ax2.set_title(f"{selected_column}の変化率")
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # 変化率の分布
            st.markdown("**変化率の分布**")
            
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(df_sorted[f"{selected_column}_pct_change"].dropna(), bins=30, alpha=0.7)
            ax.set_xlabel("変化率 (%)")
            ax.set_ylabel("頻度")
            ax.set_title(f"{selected_column}の変化率の分布")
            
            st.pyplot(fig)
        
        with ts_tab3:
            st.markdown("**移動平均分析**")
            
            # 移動平均の窓サイズを選択
            window_sizes = st.multiselect(
                "移動平均の窓サイズを選択:",
                [5, 10, 20, 50, 100],
                default=[10],
                key="moving_average_window"
            )
            
            if window_sizes:
                # 移動平均の計算と表示
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # 原系列
                ax.plot(df_sorted["timestamp"], df_sorted[selected_column], "-", alpha=0.5, label="原系列")
                
                # 移動平均
                for window in window_sizes:
                    df_sorted[f"MA_{window}"] = df_sorted[selected_column].rolling(window=window).mean()
                    ax.plot(df_sorted["timestamp"], df_sorted[f"MA_{window}"], "-", label=f"{window}期移動平均")
                
                ax.set_xlabel("時間")
                ax.set_ylabel(selected_column)
                ax.set_title(f"{selected_column}の移動平均")
                ax.legend()
                
                st.pyplot(fig)
            else:
                st.info("移動平均の窓サイズを選択してください。")
