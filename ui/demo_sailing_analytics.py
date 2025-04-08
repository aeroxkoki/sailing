"""
ui.demo_sailing_analytics

セーリング分析ダッシュボードのデモアプリケーションです。
データ処理機能と統計分析グラフを組み合わせて、セーリングデータの分析を行います。
VMG分析、タッキング効率分析、風向効率分析などのセーリング特有の分析を可能にします。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
import io

from sailing_data_processor.reporting.elements.visualizations.statistical_charts import (
    TimeSeriesElement, BoxPlotElement, HeatMapElement, CorrelationElement
)
from sailing_data_processor.reporting.data_processing.transforms import (
    SmoothingTransform, ResamplingTransform, NormalizationTransform
)
from sailing_data_processor.reporting.data_processing.aggregators import (
    TimeAggregator, SpatialAggregator, CategoryAggregator
)
from sailing_data_processor.reporting.data_processing.calculators import (
    PerformanceCalculator, StatisticalCalculator
)
from sailing_data_processor.reporting.data_processing.sailing_metrics import (
    SailingMetricsCalculator
)
from sailing_data_processor.reporting.data_processing.processing_pipeline import (
    ProcessingPipeline, ProcessingStep
)
from ui.components.reporting.data_preview import DataPreviewComponent


def load_sample_data():
    """
    サンプルデータを生成または読み込む
    
    Returns
    -------
    Dict[str, Any]
        データコンテキスト
    """
    # コンテキストを初期化
    context = {}
    
    # 時系列データを生成
    def generate_time_series(n=200, freq='1min'):
        now = datetime.now()
        times = [now - timedelta(minutes=i) for i in range(n)]
        times.reverse()
        
        data = pd.DataFrame({
            'timestamp': times,
            'speed': np.random.normal(8, 2, n) + np.sin(np.linspace(0, 10, n)),
            'direction': np.cumsum(np.random.normal(0, 5, n)) % 360,
            'wind_speed': np.random.normal(12, 3, n) + np.sin(np.linspace(0, 4, n)) * 2,
            'wind_direction': (np.random.normal(270, 10, n) + np.sin(np.linspace(0, 8, n)) * 20) % 360,
            'temperature': np.random.normal(22, 3, n) + np.sin(np.linspace(0, 2, n)) * 3,
        })
        
        # ノイズを追加
        noise_idx = np.random.choice(range(n), int(n * 0.05), replace=False)
        data.loc[noise_idx, 'speed'] = data.loc[noise_idx, 'speed'] + np.random.normal(0, 8, len(noise_idx))
        
        return data
    
    # 空間データを生成
    def generate_spatial_data(n=300):
        # レース軌跡のようなデータを生成
        data = []
        
        # スタート地点
        lat_start, lng_start = 35.65, 139.75
        
        # 風向と風速
        wind_direction = 270  # 270度（西風）
        wind_speed = 15  # 15ノット
        
        # 前回の位置
        lat_prev, lng_prev = lat_start, lng_start
        
        # 向かっている方向
        heading = 0  # 0度（北）
        
        # ボートスピード
        boat_speed = 8  # 8ノット
        
        for i in range(n):
            # 新しい測定値
            timestamp = datetime.now() - timedelta(minutes=(n-i))
            
            # ボートの位置にランダムな微小変化を追加
            lat = lat_prev + np.sin(np.radians(heading)) * boat_speed * 0.0001 + np.random.normal(0, 0.0001)
            lng = lng_prev + np.cos(np.radians(heading)) * boat_speed * 0.0001 + np.random.normal(0, 0.0001)
            
            # 風向と風速に微小変化を追加
            wind_dir = (wind_direction + np.random.normal(0, 5)) % 360
            wind_spd = max(0, wind_speed + np.random.normal(0, 1))
            
            # ボートの向きをランダムに変更（タッキングをシミュレート）
            if i % 50 == 0:  # 約50件ごとにタッキング
                heading = (heading + 90 + np.random.normal(0, 10)) % 360
            else:
                heading = (heading + np.random.normal(0, 2)) % 360
            
            # ボートスピードを計算（風向とボートの向きの関係から）
            wind_angle = abs((wind_dir - heading) % 360)
            if wind_angle > 180:
                wind_angle = 360 - wind_angle
            
            # 風に対する角度とスピードの関係をモデル化
            if wind_angle < 30:  # 風上すぎる
                boat_spd = wind_spd * 0.2
            elif wind_angle < 45:  # 風上（最適）
                boat_spd = wind_spd * 0.6
            elif wind_angle < 90:  # リーチング
                boat_spd = wind_spd * 0.8
            elif wind_angle < 150:  # ブロードリーチ
                boat_spd = wind_spd * 0.7
            else:  # ランニング
                boat_spd = wind_spd * 0.5
            
            # ランダムな変動を追加
            boat_spd += np.random.normal(0, 1)
            boat_spd = max(0, boat_spd)
            
            # データポイントを追加
            data.append({
                'timestamp': timestamp,
                'latitude': lat,
                'longitude': lng,
                'speed': boat_spd,
                'direction': heading,
                'wind_direction': wind_dir,
                'wind_speed': wind_spd,
                'wind_angle': wind_angle,
                'leg': 1 + i // 50  # レグ番号（50点ごとに変更）
            })
            
            # 現在位置を更新
            lat_prev, lng_prev = lat, lng
        
        return pd.DataFrame(data)
    
    # データを生成してコンテキストに追加
    context['time_series_data'] = generate_time_series()
    context['spatial_data'] = generate_spatial_data()
    
    return context


def process_sailing_data(data, analysis_type):
    """
    セーリングデータを処理
    
    Parameters
    ----------
    data : pd.DataFrame
        処理対象データ
    analysis_type : str
        分析タイプ
        
    Returns
    -------
    pd.DataFrame
        処理結果データ
    """
    # パイプラインを作成
    pipeline = ProcessingPipeline(name=f"{analysis_type}分析パイプライン")
    
    # データの前処理（ノイズ除去、欠損値補間など）
    smoother = SmoothingTransform({
        'method': 'moving_avg',
        'window_size': 5,
        'columns': ['speed', 'wind_speed', 'direction', 'wind_direction']
    })
    pipeline.add_transform_step(smoother, name="平滑化")
    
    # 分析タイプに応じたステップを追加
    if analysis_type == "VMG":
        # VMG計算
        performance_calculator = PerformanceCalculator({
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed',
            'metrics': ['vmg', 'target_ratio']
        })
        pipeline.add_calculate_step(performance_calculator, name="VMG計算")
        
    elif analysis_type == "タッキング効率":
        # タッキング効率計算
        sailing_calculator = SailingMetricsCalculator({
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed',
            'metrics': ['tacking_efficiency']
        })
        pipeline.add_calculate_step(sailing_calculator, name="タッキング効率計算")
        
    elif analysis_type == "風向効率":
        # 風向効率計算
        sailing_calculator = SailingMetricsCalculator({
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed',
            'metrics': ['wind_angle_efficiency']
        })
        pipeline.add_calculate_step(sailing_calculator, name="風向効率計算")
        
    elif analysis_type == "統計分析":
        # 統計指標の計算
        statistical_calculator = StatisticalCalculator({
            'metrics': ['mean', 'median', 'std', 'percentile', 'trend'],
            'percentiles': [25, 50, 75],
            'trend_method': 'linear',
            'columns': ['speed', 'wind_speed', 'wind_angle']
        })
        pipeline.add_calculate_step(statistical_calculator, name="統計指標計算")
    
    # パイプラインを実行
    result_data = pipeline.execute(data)
    
    return result_data


def render_vmg_analysis(data):
    """
    VMG分析を描画
    
    Parameters
    ----------
    data : pd.DataFrame
        分析データ
    """
    st.subheader("VMG (Velocity Made Good) 分析")
    st.write("風上/風下方向の有効速度を分析します。VMGはセーリングにおいて重要な指標で、風に対する効率を表します。")
    
    # VMGデータの確認
    if 'vmg_upwind' not in data.columns or 'vmg_downwind' not in data.columns:
        st.warning("VMGデータが見つかりません。先に「VMG分析」を実行してください。")
        return
    
    # VMGヒストグラム
    st.write("### VMG分布")
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(
            data, 
            x='vmg_upwind', 
            nbins=30, 
            title="風上VMG分布",
            labels={'vmg_upwind': '風上VMG'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.histogram(
            data, 
            x='vmg_downwind', 
            nbins=30, 
            title="風下VMG分布",
            labels={'vmg_downwind': '風下VMG'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 風角度とVMGの関係
    st.write("### 風角度とVMGの関係")
    fig = px.scatter(
        data, 
        x='wind_angle', 
        y=['vmg_upwind', 'vmg_downwind'], 
        title="風角度とVMGの関係",
        labels={
            'wind_angle': '風角度（度）',
            'vmg_upwind': '風上VMG',
            'vmg_downwind': '風下VMG'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # VMG効率の時系列
    if 'timestamp' in data.columns and 'vmg_efficiency' in data.columns:
        st.write("### VMG効率の時系列変化")
        fig = px.line(
            data, 
            x='timestamp', 
            y='vmg_efficiency', 
            title="VMG効率の時系列変化",
            labels={
                'timestamp': '時間',
                'vmg_efficiency': 'VMG効率'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # VMGとボートスピードの関係
    st.write("### VMGとボートスピードの関係")
    fig = px.scatter(
        data, 
        x='speed', 
        y=['vmg_upwind', 'vmg_downwind'], 
        title="スピードとVMGの関係",
        labels={
            'speed': 'ボートスピード',
            'vmg_upwind': '風上VMG',
            'vmg_downwind': '風下VMG'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # VMG極図
    st.write("### VMG極図")
    fig = go.Figure()
    
    # 風角度を0-180度に正規化
    normalized_angle = data['wind_angle'].copy()
    normalized_angle = np.where(normalized_angle > 180, 360 - normalized_angle, normalized_angle)
    
    # 有効なVMG値のみを使用
    mask = ~np.isnan(data['vmg_upwind']) & ~np.isnan(data['vmg_downwind'])
    angles = normalized_angle[mask]
    vmg_upwind = data['vmg_upwind'][mask]
    vmg_downwind = data['vmg_downwind'][mask]
    
    # 散布図として風上VMGをプロット
    fig.add_trace(go.Scatterpolar(
        r=np.abs(vmg_upwind),
        theta=angles,
        mode='markers',
        name='風上VMG',
        marker=dict(color='blue', size=5, opacity=0.6)
    ))
    
    # 散布図として風下VMGをプロット
    fig.add_trace(go.Scatterpolar(
        r=np.abs(vmg_downwind),
        theta=angles,
        mode='markers',
        name='風下VMG',
        marker=dict(color='red', size=5, opacity=0.6)
    ))
    
    # レイアウト設定
    fig.update_layout(
        title="風角度別VMG極図",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, np.max([np.abs(vmg_upwind).max(), np.abs(vmg_downwind).max()]) * 1.1]
            ),
            angularaxis=dict(
                tickmode='array',
                tickvals=[0, 30, 45, 60, 90, 120, 135, 150, 180],
                ticktext=['0°', '30°', '45°', '60°', '90°', '120°', '135°', '150°', '180°'],
                direction='clockwise'
            )
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # VMG統計値
    st.write("### VMG統計値")
    
    # 風上/風下データの分割
    upwind_mask = data['wind_angle'] <= 90
    downwind_mask = data['wind_angle'] > 90
    
    upwind_data = data[upwind_mask]
    downwind_data = data[downwind_mask]
    
    # 統計値の計算
    vmg_stats = pd.DataFrame({
        '統計量': ['データ数', '平均VMG', '最大VMG', '最小VMG', '標準偏差'],
        '風上': [
            len(upwind_data),
            upwind_data['vmg_upwind'].mean(),
            upwind_data['vmg_upwind'].max(),
            upwind_data['vmg_upwind'].min(),
            upwind_data['vmg_upwind'].std()
        ],
        '風下': [
            len(downwind_data),
            downwind_data['vmg_downwind'].mean(),
            downwind_data['vmg_downwind'].max(),
            downwind_data['vmg_downwind'].min(),
            downwind_data['vmg_downwind'].std()
        ]
    })
    
    st.dataframe(vmg_stats)


def render_tacking_analysis(data):
    """
    タッキング効率分析を描画
    
    Parameters
    ----------
    data : pd.DataFrame
        分析データ
    """
    st.subheader("タッキング効率分析")
    st.write("タッキング（方向転換）の効率を分析します。タッキングはセーリングの重要な技術で、速度損失を最小限に抑えることが重要です。")
    
    # タッキングデータの確認
    if 'is_tacking' not in data.columns or 'tacking_efficiency' not in data.columns:
        st.warning("タッキングデータが見つかりません。先に「タッキング効率分析」を実行してください。")
        return
    
    # タッキングポイントの抽出
    tacking_points = data[data['is_tacking'] == True].copy()
    
    if len(tacking_points) == 0:
        st.info("タッキングポイントが検出されませんでした。")
        return
    
    # タッキング効率のヒストグラム
    st.write("### タッキング効率分布")
    fig = px.histogram(
        tacking_points, 
        x='tacking_efficiency', 
        nbins=20, 
        title="タッキング効率分布",
        labels={'tacking_efficiency': 'タッキング効率 (タッキング後/タッキング前の速度比)'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # タッキング効率の時系列
    if 'timestamp' in tacking_points.columns:
        st.write("### タッキング効率の時系列変化")
        fig = px.scatter(
            tacking_points, 
            x='timestamp', 
            y='tacking_efficiency', 
            title="タッキング効率の時系列変化",
            labels={
                'timestamp': '時間',
                'tacking_efficiency': 'タッキング効率'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # タッキング効率と風速の関係
    st.write("### タッキング効率と風速の関係")
    fig = px.scatter(
        tacking_points, 
        x='wind_speed', 
        y='tacking_efficiency', 
        title="風速とタッキング効率の関係",
        labels={
            'wind_speed': '風速',
            'tacking_efficiency': 'タッキング効率'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # タッキング効率と風角度の関係
    st.write("### タッキング効率と風角度の関係")
    fig = px.scatter(
        tacking_points, 
        x='wind_angle', 
        y='tacking_efficiency', 
        title="風角度とタッキング効率の関係",
        labels={
            'wind_angle': '風角度（度）',
            'tacking_efficiency': 'タッキング効率'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # タッキング統計値
    st.write("### タッキング統計値")
    
    # 統計値の計算
    tacking_stats = pd.DataFrame({
        '統計量': ['タッキング回数', '平均効率', '最大効率', '最小効率', '標準偏差'],
        '値': [
            len(tacking_points),
            tacking_points['tacking_efficiency'].mean(),
            tacking_points['tacking_efficiency'].max(),
            tacking_points['tacking_efficiency'].min(),
            tacking_points['tacking_efficiency'].std()
        ]
    })
    
    st.dataframe(tacking_stats)
    
    # タッキングの空間分布（マップ）
    if 'latitude' in tacking_points.columns and 'longitude' in tacking_points.columns:
        st.write("### タッキングの空間分布")
        fig = px.scatter_mapbox(
            tacking_points, 
            lat='latitude', 
            lon='longitude', 
            color='tacking_efficiency',
            size='tacking_efficiency',
            size_max=15,
            zoom=13,
            title="タッキングの空間分布（効率によって色分け）",
            mapbox_style="open-street-map",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig, use_container_width=True)


def render_wind_angle_analysis(data):
    """
    風向効率分析を描画
    
    Parameters
    ----------
    data : pd.DataFrame
        分析データ
    """
    st.subheader("風向効率分析")
    st.write("風向に対する艇速の効率を分析します。風向角度によって最適な艇速は異なり、その効率を把握することが重要です。")
    
    # 風向効率データの確認
    if 'wind_angle' not in data.columns:
        st.warning("風向データが見つかりません。先に「風向効率分析」を実行してください。")
        return
    
    # 風角度とスピードの関係
    st.write("### 風角度とスピードの関係")
    fig = px.scatter(
        data, 
        x='wind_angle', 
        y='speed', 
        title="風角度とスピードの関係",
        labels={
            'wind_angle': '風角度（度）',
            'speed': 'スピード'
        }
    )
    
    # 回帰線の追加
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 30, 45, 60, 90, 120, 135, 150, 180],
            ticktext=['0°', '30°', '45°', '60°', '90°', '120°', '135°', '150°', '180°']
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 風角度とスピードの箱ひげ図
    st.write("### 風角度別スピード分布")
    
    # 風角度をビンに分割
    bins = [0, 30, 45, 60, 90, 120, 135, 150, 180]
    bin_labels = ['0-30°', '30-45°', '45-60°', '60-90°', '90-120°', '120-135°', '135-150°', '150-180°']
    
    # 風角度を0-180度に正規化
    data['normalized_angle'] = data['wind_angle'].copy()
    data.loc[data['normalized_angle'] > 180, 'normalized_angle'] = 360 - data.loc[data['normalized_angle'] > 180, 'normalized_angle']
    
    # ビンに分割
    data['angle_bin'] = pd.cut(data['normalized_angle'], bins=bins, labels=bin_labels, right=False)
    
    # 箱ひげ図
    fig = px.box(
        data, 
        x='angle_bin', 
        y='speed', 
        title="風角度別スピード分布",
        labels={
            'angle_bin': '風角度ビン',
            'speed': 'スピード'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 風向効率の極図
    if 'wind_angle_efficiency' in data.columns:
        st.write("### 風向効率極図")
        
        fig = go.Figure()
        
        # 極座標散布図として風向効率をプロット
        fig.add_trace(go.Scatterpolar(
            r=data['speed'],
            theta=data['normalized_angle'],
            mode='markers',
            name='スピード',
            marker=dict(
                color=data['wind_angle_efficiency'],
                colorscale='Viridis',
                showscale=True,
                size=5,
                opacity=0.7,
                colorbar=dict(title='風向効率')
            )
        ))
        
        # レイアウト設定
        fig.update_layout(
            title="風角度別スピード極図（風向効率で色分け）",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, data['speed'].max() * 1.1]
                ),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=[0, 30, 45, 60, 90, 120, 135, 150, 180],
                    ticktext=['0°', '30°', '45°', '60°', '90°', '120°', '135°', '150°', '180°'],
                    direction='clockwise'
                )
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 風向効率の統計値
    st.write("### 風向角度別統計値")
    
    # 風角度ビン別の統計値を計算
    angle_stats = data.groupby('angle_bin')['speed'].agg(['count', 'mean', 'std', 'min', 'max']).reset_index()
    angle_stats.columns = ['風角度ビン', 'データ数', '平均速度', '標準偏差', '最小速度', '最大速度']
    
    st.dataframe(angle_stats)


def render_statistical_analysis(data):
    """
    統計分析を描画
    
    Parameters
    ----------
    data : pd.DataFrame
        分析データ
    """
    st.subheader("統計分析")
    st.write("セーリングデータの統計的な分析を行います。速度、風速、風角度などの統計値や分布を把握できます。")
    
    # 数値列を特定
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    
    # 分析対象列の選択
    analysis_columns = st.multiselect(
        "分析対象列を選択",
        options=numeric_cols,
        default=['speed', 'wind_speed', 'wind_angle']
    )
    
    if not analysis_columns:
        st.warning("分析対象の列を選択してください。")
        return
    
    # ヒストグラム
    st.write("### データ分布（ヒストグラム）")
    for col in analysis_columns:
        fig = px.histogram(
            data, 
            x=col, 
            nbins=30, 
            title=f"{col}の分布",
            labels={col: col}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 相関分析
    if len(analysis_columns) > 1:
        st.write("### 相関分析")
        correlation_matrix = data[analysis_columns].corr()
        
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            color_continuous_scale='RdBu_r',
            labels=dict(x="変数", y="変数", color="相関係数"),
            title="相関行列ヒートマップ"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 散布図行列
        st.write("### 散布図行列")
        fig = px.scatter_matrix(
            data[analysis_columns],
            title="散布図行列",
            labels={col: col for col in analysis_columns}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 時系列分析（時間データがある場合）
    if 'timestamp' in data.columns:
        st.write("### 時系列分析")
        
        # 移動平均を計算
        window_size = st.slider("移動平均の窓サイズ", min_value=1, max_value=30, value=5)
        
        for col in analysis_columns:
            # 移動平均を計算
            data[f'{col}_ma'] = data[col].rolling(window=window_size, center=True).mean()
            
            fig = px.line(
                data, 
                x='timestamp', 
                y=[col, f'{col}_ma'], 
                title=f"{col}の時系列変化",
                labels={
                    'timestamp': '時間',
                    col: col,
                    f'{col}_ma': f'{col} (移動平均)'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 統計値
    st.write("### 基本統計値")
    stats = data[analysis_columns].describe().T
    st.dataframe(stats)


def render_data_explorer(data):
    """
    データエクスプローラーを描画
    
    Parameters
    ----------
    data : pd.DataFrame
        表示対象データ
    """
    st.subheader("データエクスプローラー")
    
    # データプレビューコンポーネント
    data_preview = DataPreviewComponent()
    data_preview.render(data, "データプレビュー")
    
    # データのエクスポート
    st.write("### データのエクスポート")
    
    # 列の選択
    all_columns = data.columns.tolist()
    selected_columns = st.multiselect(
        "エクスポートする列を選択",
        options=all_columns,
        default=all_columns
    )
    
    if selected_columns:
        export_data = data[selected_columns]
        
        # CSVエクスポート
        csv = export_data.to_csv(index=False)
        st.download_button(
            label="CSVとしてダウンロード",
            data=csv,
            file_name="sailing_analysis_data.csv",
            mime="text/csv"
        )
        
        # Excelエクスポート
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_data.to_excel(writer, sheet_name='Data', index=False)
            
            # シートへのアクセス
            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            # フォーマット
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # ヘッダー行にフォーマットを適用
            for col_num, value in enumerate(export_data.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
        
        st.download_button(
            label="Excelとしてダウンロード",
            data=buffer.getvalue(),
            file_name="sailing_analysis_data.xlsx",
            mime="application/vnd.ms-excel"
        )


def main():
    """
    メイン関数
    """
    st.set_page_config(
        page_title="セーリング分析ダッシュボード",
        page_icon="⛵",
        layout="wide"
    )
    
    st.title("セーリング分析ダッシュボード")
    st.write("データ処理と統計分析を組み合わせたセーリングデータ分析ツールです。VMG分析、タッキング効率分析、風向効率分析などが可能です。")
    
    # セッションステートの初期化
    if 'data' not in st.session_state:
        # サンプルデータを読み込み
        data_context = load_sample_data()
        st.session_state.data = data_context['spatial_data']  # デフォルトでは空間データを使用
    
    # サイドバー
    st.sidebar.title("分析設定")
    
    # データソースの選択
    data_source = st.sidebar.radio(
        "データソース",
        options=["サンプルデータ", "アップロードデータ"],
        index=0
    )
    
    if data_source == "サンプルデータ":
        sample_type = st.sidebar.selectbox(
            "サンプルデータの種類",
            options=["時系列データ", "空間データ"],
            index=1
        )
        
        # サンプルデータを読み込み
        data_context = load_sample_data()
        
        if sample_type == "時系列データ":
            st.session_state.data = data_context['time_series_data']
        else:  # "空間データ"
            st.session_state.data = data_context['spatial_data']
            
    else:  # "アップロードデータ"
        uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])
        
        if uploaded_file is not None:
            try:
                # CSVを読み込み
                data = pd.read_csv(uploaded_file)
                
                # 時間列の変換（必要であれば）
                if 'timestamp' in data.columns:
                    try:
                        data['timestamp'] = pd.to_datetime(data['timestamp'])
                    except:
                        pass
                
                st.session_state.data = data
                st.sidebar.success("データを正常に読み込みました。")
            except Exception as e:
                st.sidebar.error(f"データの読み込みに失敗しました: {str(e)}")
    
    # 分析タイプの選択
    analysis_type = st.sidebar.selectbox(
        "分析タイプ",
        options=["データエクスプローラー", "VMG分析", "タッキング効率分析", "風向効率分析", "統計分析"],
        index=0
    )
    
    # 分析の実行
    if analysis_type != "データエクスプローラー":
        if st.sidebar.button(f"{analysis_type}を実行"):
            with st.spinner(f"{analysis_type}を実行中..."):
                # データを処理
                processed_data = process_sailing_data(st.session_state.data, analysis_type.split('分析')[0])
                st.session_state.data = processed_data
                st.sidebar.success(f"{analysis_type}が完了しました。")
    
    # 選択された分析タイプに応じた表示
    if analysis_type == "データエクスプローラー":
        render_data_explorer(st.session_state.data)
    elif analysis_type == "VMG分析":
        render_vmg_analysis(st.session_state.data)
    elif analysis_type == "タッキング効率分析":
        render_tacking_analysis(st.session_state.data)
    elif analysis_type == "風向効率分析":
        render_wind_angle_analysis(st.session_state.data)
    elif analysis_type == "統計分析":
        render_statistical_analysis(st.session_state.data)


if __name__ == "__main__":
    main()
