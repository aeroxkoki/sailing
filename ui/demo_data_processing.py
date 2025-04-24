# -*- coding: utf-8 -*-
"""
ui.demo_data_processing

データ処理機能のデモアプリケーションです。
変換、集計、計算の各処理タイプと、それらを組み合わせたパイプラインの
機能をデモンストレーションします。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

from sailing_data_processor.reporting.data_processing.transforms import (
    DataTransformer, SmoothingTransform, ResamplingTransform, NormalizationTransform
)
from sailing_data_processor.reporting.data_processing.aggregators import (
    DataAggregator, TimeAggregator, SpatialAggregator, CategoryAggregator
)
from sailing_data_processor.reporting.data_processing.calculators import (
    BaseCalculator, PerformanceCalculator, StatisticalCalculator, CustomFormulaCalculator
)
from sailing_data_processor.reporting.data_processing.processing_pipeline import (
    ProcessingPipeline, ProcessingStep, ProcessingPipelineFactory
)
from ui.components.reporting.data_processing_panel import DataProcessingPanel
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
            'vmg': np.random.normal(6, 1.5, n) + np.sin(np.linspace(0, 5, n))
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
    
    # カテゴリデータを生成
    def generate_categorical_data(n=150):
        # レース結果のようなデータを生成
        races = ['Race 1', 'Race 2', 'Race 3', 'Race 4', 'Race 5']
        sailors = ['Sailor A', 'Sailor B', 'Sailor C', 'Sailor D', 'Sailor E', 'Sailor F', 'Sailor G']
        boat_classes = ['470', '49er', 'Laser', 'Finn', 'Nacra 17']
        weather_conditions = ['Light', 'Medium', 'Heavy']
        
        data = []
        
        for i in range(n):
            race = np.random.choice(races)
            sailor = np.random.choice(sailors)
            boat_class = np.random.choice(boat_classes)
            weather = np.random.choice(weather_conditions)
            
            # 性能指標を生成
            if weather == 'Light':
                speed_base = 5
                vmg_base = 3.5
            elif weather == 'Medium':
                speed_base = 8
                vmg_base = 5
            else:  # Heavy
                speed_base = 10
                vmg_base = 6
            
            # ボートクラスによる調整
            if boat_class == '49er':
                speed_multiplier = 1.3
                vmg_multiplier = 1.2
            elif boat_class == 'Nacra 17':
                speed_multiplier = 1.4
                vmg_multiplier = 1.25
            elif boat_class == '470':
                speed_multiplier = 1.1
                vmg_multiplier = 1.15
            elif boat_class == 'Finn':
                speed_multiplier = 1.0
                vmg_multiplier = 1.05
            else:  # Laser
                speed_multiplier = 0.9
                vmg_multiplier = 0.95
            
            # セーラーのスキルによる変動
            if sailor == 'Sailor A':
                skill_factor = 1.2
            elif sailor == 'Sailor B':
                skill_factor = 1.15
            elif sailor == 'Sailor C':
                skill_factor = 1.1
            elif sailor == 'Sailor D':
                skill_factor = 1.05
            elif sailor == 'Sailor E':
                skill_factor = 1.0
            elif sailor == 'Sailor F':
                skill_factor = 0.95
            else:  # Sailor G
                skill_factor = 0.9
            
            # 最終スピードとVMGを計算
            avg_speed = speed_base * speed_multiplier * skill_factor * (1 + np.random.normal(0, 0.1))
            avg_vmg = vmg_base * vmg_multiplier * skill_factor * (1 + np.random.normal(0, 0.1))
            
            # タッキング効率
            tacking_efficiency = 0.8 + np.random.normal(0, 0.1) * skill_factor
            tacking_efficiency = max(0.5, min(1.0, tacking_efficiency))
            
            # 完走時間（分）
            finish_time_base = {
                'Light': {'470': 45, '49er': 35, 'Laser': 50, 'Finn': 48, 'Nacra 17': 30},
                'Medium': {'470': 40, '49er': 30, 'Laser': 45, 'Finn': 42, 'Nacra 17': 25},
                'Heavy': {'470': 35, '49er': 28, 'Laser': 40, 'Finn': 38, 'Nacra 17': 22}
            }
            
            finish_time = finish_time_base[weather][boat_class] / skill_factor * (1 + np.random.normal(0, 0.1))
            
            # 順位を決定
            rank = int(np.clip(10 / skill_factor * (1 + np.random.normal(0, 0.3)), 1, 10))
            
            data.append({
                'race': race,
                'sailor': sailor,
                'boat_class': boat_class,
                'weather': weather,
                'avg_speed': avg_speed,
                'avg_vmg': avg_vmg,
                'tacking_efficiency': tacking_efficiency,
                'finish_time': finish_time,
                'rank': rank
            })
        
        return pd.DataFrame(data)
    
    # データを生成してコンテキストに追加
    context['time_series_data'] = generate_time_series()
    context['spatial_data'] = generate_spatial_data()
    context['categorical_data'] = generate_categorical_data()
    
    return context


def render_data_processing_demo(process_type, data, params):
    """
    データ処理デモを描画
    
    Parameters
    ----------
    process_type : str
        処理タイプ ('transform', 'aggregate', 'calculate')
    data : pd.DataFrame
        処理対象データ
    params : Dict[str, Any]
        処理パラメータ
        
    Returns
    -------
    pd.DataFrame
        処理結果データ
    """
    # 処理タイプに応じたプロセッサを作成
    processor = None
    processor_name = ""
    
    if process_type == 'transform':
        transform_type = params.get('transform_type', 'smoothing')
        
        if transform_type == 'smoothing':
            processor = SmoothingTransform(params)
            processor_name = "平滑化変換"
        elif transform_type == 'resampling':
            processor = ResamplingTransform(params)
            processor_name = "リサンプリング変換"
        elif transform_type == 'normalization':
            processor = NormalizationTransform(params)
            processor_name = "正規化変換"
    
    elif process_type == 'aggregate':
        aggregate_type = params.get('aggregate_type', 'time')
        
        if aggregate_type == 'time':
            processor = TimeAggregator(params)
            processor_name = "時間集計"
        elif aggregate_type == 'spatial':
            processor = SpatialAggregator(params)
            processor_name = "空間集計"
        elif aggregate_type == 'category':
            processor = CategoryAggregator(params)
            processor_name = "カテゴリ集計"
    
    elif process_type == 'calculate':
        calculate_type = params.get('calculate_type', 'performance')
        
        if calculate_type == 'performance':
            processor = PerformanceCalculator(params)
            processor_name = "パフォーマンス計算"
        elif calculate_type == 'statistical':
            processor = StatisticalCalculator(params)
            processor_name = "統計計算"
        elif calculate_type == 'custom':
            processor = CustomFormulaCalculator(params)
            processor_name = "カスタム計算"
    
    # 処理を実行
    result_data = None
    error_message = None
    
    if processor is not None:
        try:
            st.subheader(f"{processor_name}の実行")
            
            with st.spinner("処理中..."):
                start_time = datetime.now()
                
                if process_type == 'transform':
                    result_data = processor.transform(data)
                elif process_type == 'aggregate':
                    result_data = processor.aggregate(data)
                elif process_type == 'calculate':
                    result_data = processor.calculate(data)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                st.success(f"処理が完了しました（実行時間: {duration:.2f}秒）")
        
        except Exception as e:
            error_message = str(e)
            st.error(f"処理エラー: {error_message}")
    
    else:
        st.warning(f"適切なプロセッサが見つかりませんでした: {process_type}")
    
    return result_data, error_message


def render_pipeline_demo(pipeline, data):
    """
    パイプラインデモを描画
    
    Parameters
    ----------
    pipeline : ProcessingPipeline
        処理パイプライン
    data : pd.DataFrame
        処理対象データ
        
    Returns
    -------
    pd.DataFrame
        処理結果データ
    """
    # パイプラインの実行
    result_data = None
    error_message = None
    
    try:
        st.subheader(f"パイプラインの実行: {pipeline.name}")
        
        # パイプラインの構成を表示
        steps_info = []
        for i, step in enumerate(pipeline.steps):
            steps_info.append({
                "ステップ番号": i + 1,
                "ステップ名": step.name,
                "ステップタイプ": step.step_type,
                "プロセッサタイプ": type(step.processor).__name__
            })
        
        st.write("パイプライン構成:")
        st.table(pd.DataFrame(steps_info))
        
        # 中間結果を保存するかどうか
        store_intermediate = st.checkbox("中間結果を保存", value=True)
        
        with st.spinner("パイプライン実行中..."):
            start_time = datetime.now()
            
            result_data = pipeline.execute(data, store_intermediate)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            st.success(f"パイプラインの実行が完了しました（実行時間: {duration:.2f}秒）")
        
        # 実行ログを表示
        if pipeline.execution_log:
            st.write("### 実行ログ")
            
            log_df = pd.DataFrame(pipeline.execution_log)
            if not log_df.empty:
                st.dataframe(log_df)
        
        # 実行サマリーを表示
        st.write("### 実行サマリー")
        summary = pipeline.get_execution_summary()
        st.json(summary)
        
        # 中間結果を表示
        if store_intermediate and pipeline.intermediate_results:
            st.write("### 中間結果")
            
            for step_name, step_data in pipeline.intermediate_results.items():
                if step_name == 'input':
                    continue
                
                with st.expander(f"ステップ: {step_name}", expanded=False):
                    preview = DataPreviewComponent()
                    preview.render(step_data, f"{step_name}の結果")
    
    except Exception as e:
        error_message = str(e)
        st.error(f"パイプライン実行エラー: {error_message}")
    
    return result_data, error_message


def render_data_visualization(data, data_type):
    """
    データ可視化を描画
    
    Parameters
    ----------
    data : pd.DataFrame
        可視化対象データ
    data_type : str
        データタイプ ('time_series', 'spatial', 'categorical')
    """
    if data is None:
        st.warning("可視化するデータがありません")
        return
    
    if not isinstance(data, pd.DataFrame):
        try:
            data = pd.DataFrame(data)
        except:
            st.warning("データをDataFrameに変換できません")
            return
    
    if data_type == 'time_series':
        st.write("### 時系列データの可視化")
        
        # 時間列を特定
        time_cols = [col for col in data.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
        time_column = time_cols[0] if time_cols else None
        
        if time_column:
            # 数値列を特定
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            
            # 可視化する列を選択
            selected_columns = st.multiselect("可視化する列", options=numeric_cols, default=numeric_cols[:2])
            
            if selected_columns:
                # 時間列が日時型でない場合は変換を試みる
                if not pd.api.types.is_datetime64_any_dtype(data[time_column]):
                    try:
                        data[time_column] = pd.to_datetime(data[time_column])
                    except:
                        pass
                
                # 折れ線グラフの描画
                fig = px.line(data, x=time_column, y=selected_columns, title="時系列データ")
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("時間列が見つかりません")
    
    elif data_type == 'spatial':
        st.write("### 空間データの可視化")
        
        # 緯度経度列を特定
        lat_cols = [col for col in data.columns if col.lower() in ["lat", "latitude"]]
        lng_cols = [col for col in data.columns if col.lower() in ["lng", "lon", "longitude"]]
        
        if lat_cols and lng_cols:
            lat_column = lat_cols[0]
            lng_column = lng_cols[0]
            
            # カラー列を選択（オプション）
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col not in [lat_column, lng_column]]
            
            color_column = st.selectbox("カラー列", options=["なし"] + numeric_cols)
            
            # サイズ列を選択（オプション）
            size_column = st.selectbox("サイズ列", options=["なし"] + numeric_cols)
            
            # マップの描画
            if color_column == "なし" and size_column == "なし":
                fig = px.scatter_mapbox(data, lat=lat_column, lon=lng_column, title="位置データ")
            elif color_column != "なし" and size_column == "なし":
                fig = px.scatter_mapbox(data, lat=lat_column, lon=lng_column, color=color_column, title="位置データ")
            elif color_column == "なし" and size_column != "なし":
                fig = px.scatter_mapbox(data, lat=lat_column, lon=lng_column, size=size_column, title="位置データ")
            else:
                fig = px.scatter_mapbox(data, lat=lat_column, lon=lng_column, color=color_column, size=size_column, title="位置データ")
            
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("緯度経度列が見つかりません")
    
    elif data_type == 'categorical':
        st.write("### カテゴリデータの可視化")
        
        # カテゴリ列を特定
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if categorical_cols:
            # カテゴリと数値の組み合わせを選択
            category_column = st.selectbox("カテゴリ列", options=categorical_cols)
            
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            value_column = st.selectbox("数値列", options=numeric_cols) if numeric_cols else None
            
            if value_column:
                # 集計方法を選択
                agg_method = st.selectbox("集計方法", options=["平均", "合計", "最小", "最大", "カウント", "中央値"])
                agg_func_map = {
                    "平均": "mean", "合計": "sum", "最小": "min",
                    "最大": "max", "カウント": "count", "中央値": "median"
                }
                
                # グラフタイプを選択
                graph_type = st.selectbox("グラフタイプ", options=["棒グラフ", "箱ひげ図", "バイオリンプロット", "散布図"])
                
                # グラフの描画
                if graph_type == "棒グラフ":
                    fig = px.bar(
                        data.groupby(category_column)[value_column].agg(agg_func_map[agg_method]).reset_index(),
                        x=category_column,
                        y=value_column,
                        title=f"{category_column}別の{value_column}（{agg_method}）"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif graph_type == "箱ひげ図":
                    fig = px.box(
                        data,
                        x=category_column,
                        y=value_column,
                        title=f"{category_column}別の{value_column}分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif graph_type == "バイオリンプロット":
                    fig = px.violin(
                        data,
                        x=category_column,
                        y=value_column,
                        box=True,
                        title=f"{category_column}別の{value_column}分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif graph_type == "散布図":
                    if len(categorical_cols) > 1:
                        color_column = st.selectbox("色分け列", options=["なし"] + [col for col in categorical_cols if col != category_column])
                        
                        if color_column == "なし":
                            fig = px.scatter(
                                data,
                                x=category_column,
                                y=value_column,
                                title=f"{category_column}と{value_column}の関係"
                            )
                        else:
                            fig = px.scatter(
                                data,
                                x=category_column,
                                y=value_column,
                                color=color_column,
                                title=f"{category_column}と{value_column}の関係（{color_column}で色分け）"
                            )
                    else:
                        fig = px.scatter(
                            data,
                            x=category_column,
                            y=value_column,
                            title=f"{category_column}と{value_column}の関係"
                        )
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("カテゴリ列が見つかりません")
    
    else:
        st.warning(f"未対応のデータタイプ: {data_type}")


def create_sample_pipelines(data_type):
    """
    サンプルパイプラインを作成
    
    Parameters
    ----------
    data_type : str
        データタイプ ('time_series', 'spatial', 'categorical')
        
    Returns
    -------
    List[ProcessingPipeline]
        パイプラインのリスト
    """
    pipelines = []
    
    if data_type == 'time_series':
        # 移動平均と異常値除外パイプライン
        pipeline1 = ProcessingPipeline(name="時系列スムージングパイプライン")
        
        # 異常値を検出するカスタム計算
        outlier_calculator = StatisticalCalculator({
            'metrics': ['mean', 'std'],
            'columns': ['speed', 'wind_speed']
        })
        pipeline1.add_calculate_step(outlier_calculator, name="異常値統計計算")
        
        # スムージング変換
        smoother = SmoothingTransform({
            'method': 'moving_avg',
            'window_size': 5,
            'columns': ['speed', 'wind_speed', 'direction', 'wind_direction']
        })
        pipeline1.add_transform_step(smoother, name="移動平均スムージング")
        
        pipelines.append(pipeline1)
        
        # 時間集計パイプライン
        pipeline2 = ProcessingPipeline(name="時間集計分析パイプライン")
        
        # 時間集計
        time_aggregator = TimeAggregator({
            'time_column': 'timestamp',
            'time_unit': '5min',
            'aggregation_funcs': {
                'speed': 'mean',
                'direction': 'mean',
                'wind_speed': 'mean',
                'wind_direction': 'mean'
            }
        })
        pipeline2.add_aggregate_step(time_aggregator, name="5分間隔集計")
        
        # パフォーマンス計算
        performance_calculator = PerformanceCalculator({
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed',
            'metrics': ['vmg', 'target_ratio']
        })
        pipeline2.add_calculate_step(performance_calculator, name="VMG計算")
        
        pipelines.append(pipeline2)
    
    elif data_type == 'spatial':
        # 空間集計パイプライン
        pipeline1 = ProcessingPipeline(name="空間集計分析パイプライン")
        
        # 空間集計
        spatial_aggregator = SpatialAggregator({
            'lat_column': 'latitude',
            'lng_column': 'longitude',
            'method': 'grid',
            'grid_size': 0.0005,  # 約50mのグリッド
            'aggregation_funcs': {
                'speed': 'mean',
                'direction': 'mean',
                'wind_speed': 'mean',
                'wind_direction': 'mean',
                'wind_angle': 'mean'
            }
        })
        pipeline1.add_aggregate_step(spatial_aggregator, name="空間グリッド集計")
        
        pipelines.append(pipeline1)
        
        # VMG分析パイプライン
        pipeline2 = ProcessingPipeline(name="空間VMG分析パイプライン")
        
        # パフォーマンス計算
        performance_calculator = PerformanceCalculator({
            'speed_column': 'speed',
            'direction_column': 'direction',
            'wind_direction_column': 'wind_direction',
            'wind_speed_column': 'wind_speed',
            'metrics': ['vmg', 'target_ratio']
        })
        pipeline2.add_calculate_step(performance_calculator, name="VMG計算")
        
        # 空間集計
        spatial_aggregator = SpatialAggregator({
            'lat_column': 'latitude',
            'lng_column': 'longitude',
            'method': 'grid',
            'grid_size': 0.001,  # 約100mのグリッド
            'aggregation_funcs': {
                'speed': 'mean',
                'vmg': 'mean',
                'vmg_upwind': 'mean',
                'vmg_downwind': 'mean',
                'target_ratio': 'mean'
            }
        })
        pipeline2.add_aggregate_step(spatial_aggregator, name="VMG空間集計")
        
        pipelines.append(pipeline2)
    
    elif data_type == 'categorical':
        # カテゴリ集計パイプライン
        pipeline1 = ProcessingPipeline(name="カテゴリ分析パイプライン")
        
        # カテゴリ集計
        category_aggregator = CategoryAggregator({
            'category_columns': ['boat_class', 'weather'],
            'aggregation_funcs': {
                'avg_speed': 'mean',
                'avg_vmg': 'mean',
                'tacking_efficiency': 'mean',
                'finish_time': 'mean',
                'rank': 'mean'
            }
        })
        pipeline1.add_aggregate_step(category_aggregator, name="ボートクラス・天候別集計")
        
        pipelines.append(pipeline1)
        
        # パフォーマンス正規化パイプライン
        pipeline2 = ProcessingPipeline(name="パフォーマンス正規化パイプライン")
        
        # 正規化変換
        normalizer = NormalizationTransform({
            'method': 'min_max',
            'target_min': 0.0,
            'target_max': 10.0,
            'columns': ['avg_speed', 'avg_vmg', 'tacking_efficiency']
        })
        pipeline2.add_transform_step(normalizer, name="パフォーマンス指標正規化")
        
        # カスタム計算（総合指標）
        formula_calculator = CustomFormulaCalculator({
            'formulas': {
                'performance_index': 'avg_speed * 0.4 + avg_vmg * 0.4 + tacking_efficiency * 10 * 0.2'
            },
            'safe_mode': True
        })
        pipeline2.add_calculate_step(formula_calculator, name="総合パフォーマンス指標計算")
        
        pipelines.append(pipeline2)
    
    return pipelines


def main():
    """
    メイン関数
    """
    st.set_page_config(
        page_title="データ処理デモ",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("データ処理デモ")
    st.write("データの変換、集計、計算の各処理と、それらを組み合わせたパイプラインをデモンストレーションします。")
    
    # サンプルデータを読み込み
    data_context = load_sample_data()
    
    # データプレビューコンポーネント
    data_preview = DataPreviewComponent()
    
    # データ処理パネル
    data_processing_panel = DataProcessingPanel()
    
    # メニュー
    menu = st.sidebar.selectbox(
        "モード",
        options=["個別処理", "パイプライン処理"]
    )
    
    # データタイプの選択
    data_type = st.sidebar.selectbox(
        "データタイプ",
        options=["time_series", "spatial", "categorical"],
        format_func=lambda x: {
            "time_series": "時系列データ",
            "spatial": "空間データ",
            "categorical": "カテゴリデータ"
        }.get(x, x)
    )
    
    # データソースの選択
    data_source_map = {
        "time_series": "time_series_data",
        "spatial": "spatial_data",
        "categorical": "categorical_data"
    }
    data_source = data_source_map.get(data_type)
    data = data_context.get(data_source)
    
    # サイドバーにデータプレビュー
    st.sidebar.subheader("データプレビュー")
    with st.sidebar.expander("データプレビュー", expanded=False):
        data_preview.render(data, "選択データ")
    
    # 個別処理モード
    if menu == "個別処理":
        st.subheader("個別データ処理")
        
        # 処理タイプの選択
        process_type = st.selectbox(
            "処理タイプ",
            options=["transform", "aggregate", "calculate"],
            format_func=lambda x: {
                "transform": "変換処理",
                "aggregate": "集計処理",
                "calculate": "計算処理"
            }.get(x, x)
        )
        
        # 処理サブタイプの選択
        if process_type == "transform":
            process_subtype = st.selectbox(
                "変換タイプ",
                options=["smoothing", "resampling", "normalization"],
                format_func=lambda x: {
                    "smoothing": "平滑化",
                    "resampling": "リサンプリング",
                    "normalization": "正規化"
                }.get(x, x)
            )
        elif process_type == "aggregate":
            process_subtype = st.selectbox(
                "集計タイプ",
                options=["time", "spatial", "category"],
                format_func=lambda x: {
                    "time": "時間集計",
                    "spatial": "空間集計",
                    "category": "カテゴリ集計"
                }.get(x, x)
            )
        elif process_type == "calculate":
            process_subtype = st.selectbox(
                "計算タイプ",
                options=["performance", "statistical", "custom"],
                format_func=lambda x: {
                    "performance": "パフォーマンス計算",
                    "statistical": "統計計算",
                    "custom": "カスタム計算"
                }.get(x, x)
            )
        
        # 処理パラメータの設定
        st.subheader("処理パラメータ")
        
        params = {}
        
        if process_type == "transform":
            params["transform_type"] = process_subtype
            
            if process_subtype == "smoothing":
                params["method"] = st.selectbox(
                    "平滑化方法",
                    options=["moving_avg", "exponential", "median", "gaussian"],
                    format_func=lambda x: {
                        "moving_avg": "移動平均",
                        "exponential": "指数平滑化",
                        "median": "メディアンフィルタ",
                        "gaussian": "ガウシアンフィルタ"
                    }.get(x, x)
                )
                
                params["window_size"] = st.slider("窓サイズ", min_value=3, max_value=21, value=5, step=2)
                
                if params["method"] == "exponential":
                    params["alpha"] = st.slider("α値", min_value=0.1, max_value=1.0, value=0.3, step=0.1)
                
                if params["method"] == "gaussian":
                    params["sigma"] = st.slider("σ値", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
                
                # 数値列の選択
                numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                params["columns"] = st.multiselect("対象列", options=numeric_cols, default=numeric_cols[:3])
            
            elif process_subtype == "resampling":
                time_cols = [col for col in data.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
                
                if time_cols:
                    params["time_column"] = st.selectbox("時間列", options=time_cols)
                    
                    params["method"] = st.selectbox(
                        "リサンプリング方法",
                        options=["downsample", "upsample"],
                        format_func=lambda x: {
                            "downsample": "ダウンサンプリング（間引き）",
                            "upsample": "アップサンプリング（補間）"
                        }.get(x, x)
                    )
                    
                    params["rule"] = st.selectbox(
                        "時間間隔",
                        options=["1s", "5s", "10s", "30s", "1min", "5min", "10min", "30min", "1h", "2h", "6h"],
                        format_func=lambda x: {
                            "1s": "1秒", "5s": "5秒", "10s": "10秒", "30s": "30秒",
                            "1min": "1分", "5min": "5分", "10min": "10分", "30min": "30分",
                            "1h": "1時間", "2h": "2時間", "6h": "6時間"
                        }.get(x, x)
                    )
                    
                    if params["method"] == "upsample":
                        params["interpolation"] = st.selectbox(
                            "補間方法",
                            options=["linear", "cubic", "nearest"],
                            format_func=lambda x: {
                                "linear": "線形補間",
                                "cubic": "3次スプライン補間",
                                "nearest": "最近傍補間"
                            }.get(x, x)
                        )
                else:
                    st.warning("時間列が見つかりません")
            
            elif process_subtype == "normalization":
                params["method"] = st.selectbox(
                    "正規化方法",
                    options=["min_max", "z_score", "robust"],
                    format_func=lambda x: {
                        "min_max": "最小-最大正規化",
                        "z_score": "Z-スコア正規化",
                        "robust": "ロバスト正規化"
                    }.get(x, x)
                )
                
                if params["method"] == "min_max":
                    params["target_min"] = st.number_input("最小値", value=0.0)
                    params["target_max"] = st.number_input("最大値", value=1.0)
                
                # 数値列の選択
                numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                params["columns"] = st.multiselect("対象列", options=numeric_cols, default=numeric_cols[:3])
        
        elif process_type == "aggregate":
            params["aggregate_type"] = process_subtype
            
            if process_subtype == "time":
                time_cols = [col for col in data.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
                
                if time_cols:
                    params["time_column"] = st.selectbox("時間列", options=time_cols)
                    
                    params["time_unit"] = st.selectbox(
                        "時間単位",
                        options=["1s", "5s", "10s", "30s", "1min", "5min", "10min", "30min", "1h", "2h", "6h"],
                        format_func=lambda x: {
                            "1s": "1秒", "5s": "5秒", "10s": "10秒", "30s": "30秒",
                            "1min": "1分", "5min": "5分", "10min": "10分", "30min": "30分",
                            "1h": "1時間", "2h": "2時間", "6h": "6時間"
                        }.get(x, x)
                    )
                    
                    # 集計関数の設定
                    st.subheader("集計関数の設定")
                    
                    agg_funcs = {}
                    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                    selected_cols = st.multiselect("集計対象列", options=numeric_cols, default=numeric_cols[:3])
                    
                    for col in selected_cols:
                        agg_func = st.selectbox(
                            f"{col}の集計関数",
                            options=["mean", "sum", "min", "max", "count", "median"],
                            format_func=lambda x: {
                                "mean": "平均", "sum": "合計", "min": "最小",
                                "max": "最大", "count": "カウント", "median": "中央値"
                            }.get(x, x),
                            key=f"time_agg_{col}"
                        )
                        agg_funcs[col] = agg_func
                    
                    params["aggregation_funcs"] = agg_funcs
                else:
                    st.warning("時間列が見つかりません")
            
            elif process_subtype == "spatial":
                lat_cols = [col for col in data.columns if col.lower() in ["lat", "latitude"]]
                lng_cols = [col for col in data.columns if col.lower() in ["lng", "lon", "longitude"]]
                
                if lat_cols and lng_cols:
                    params["lat_column"] = st.selectbox("緯度列", options=lat_cols)
                    params["lng_column"] = st.selectbox("経度列", options=lng_cols)
                    
                    params["method"] = st.selectbox(
                        "集計方法",
                        options=["grid", "distance"],
                        format_func=lambda x: {
                            "grid": "グリッド方式",
                            "distance": "距離方式"
                        }.get(x, x)
                    )
                    
                    if params["method"] == "grid":
                        params["grid_size"] = st.number_input(
                            "グリッドサイズ（度単位、約100mは0.001度）",
                            min_value=0.0001, max_value=0.01, value=0.001, format="%.5f", step=0.0001
                        )
                    
                    else:  # distance
                        params["distance_threshold"] = st.number_input(
                            "距離閾値（メートル）",
                            min_value=10.0, max_value=1000.0, value=100.0, format="%.1f", step=10.0
                        )
                    
                    # 集計関数の設定
                    st.subheader("集計関数の設定")
                    
                    agg_funcs = {}
                    numeric_cols = [col for col in data.select_dtypes(include=[np.number]).columns if col not in [params["lat_column"], params["lng_column"]]]
                    selected_cols = st.multiselect("集計対象列", options=numeric_cols, default=numeric_cols[:3])
                    
                    for col in selected_cols:
                        agg_func = st.selectbox(
                            f"{col}の集計関数",
                            options=["mean", "sum", "min", "max", "count", "median"],
                            format_func=lambda x: {
                                "mean": "平均", "sum": "合計", "min": "最小",
                                "max": "最大", "count": "カウント", "median": "中央値"
                            }.get(x, x),
                            key=f"spatial_agg_{col}"
                        )
                        agg_funcs[col] = agg_func
                    
                    params["aggregation_funcs"] = agg_funcs
                else:
                    st.warning("緯度経度列が見つかりません")
            
            elif process_subtype == "category":
                categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if categorical_cols:
                    params["category_columns"] = st.multiselect("カテゴリ列", options=categorical_cols, default=[categorical_cols[0]])
                    
                    # 集計関数の設定
                    st.subheader("集計関数の設定")
                    
                    agg_funcs = {}
                    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                    selected_cols = st.multiselect("集計対象列", options=numeric_cols, default=numeric_cols[:3])
                    
                    for col in selected_cols:
                        agg_func = st.selectbox(
                            f"{col}の集計関数",
                            options=["mean", "sum", "min", "max", "count", "median"],
                            format_func=lambda x: {
                                "mean": "平均", "sum": "合計", "min": "最小",
                                "max": "最大", "count": "カウント", "median": "中央値"
                            }.get(x, x),
                            key=f"category_agg_{col}"
                        )
                        agg_funcs[col] = agg_func
                    
                    params["aggregation_funcs"] = agg_funcs
                else:
                    st.warning("カテゴリ列が見つかりません")
        
        elif process_type == "calculate":
            params["calculate_type"] = process_subtype
            
            if process_subtype == "performance":
                # 必要な列の特定
                speed_cols = [col for col in data.columns if "speed" in col.lower() and "wind" not in col.lower()]
                direction_cols = [col for col in data.columns if "direction" in col.lower() and "wind" not in col.lower()]
                wind_direction_cols = [col for col in data.columns if "wind" in col.lower() and "direction" in col.lower()]
                wind_speed_cols = [col for col in data.columns if "wind" in col.lower() and "speed" in col.lower()]
                
                if speed_cols and direction_cols and wind_direction_cols and wind_speed_cols:
                    params["speed_column"] = st.selectbox("速度列", options=speed_cols)
                    params["direction_column"] = st.selectbox("方向列", options=direction_cols)
                    params["wind_direction_column"] = st.selectbox("風向列", options=wind_direction_cols)
                    params["wind_speed_column"] = st.selectbox("風速列", options=wind_speed_cols)
                    
                    params["metrics"] = st.multiselect(
                        "計算する指標",
                        options=["vmg", "target_ratio", "tacking_efficiency"],
                        default=["vmg", "target_ratio"],
                        format_func=lambda x: {
                            "vmg": "VMG（風上/風下方向の有効速度）",
                            "target_ratio": "対ターゲット速度比率",
                            "tacking_efficiency": "タッキング効率"
                        }.get(x, x)
                    )
                else:
                    st.warning("必要な列（速度、方向、風向、風速）が見つかりません")
            
            elif process_subtype == "statistical":
                params["metrics"] = st.multiselect(
                    "計算する統計指標",
                    options=["mean", "median", "std", "min", "max", "percentile", "trend", "moving"],
                    default=["mean", "median", "std", "min", "max"],
                    format_func=lambda x: {
                        "mean": "平均値", "median": "中央値", "std": "標準偏差",
                        "min": "最小値", "max": "最大値", "percentile": "パーセンタイル",
                        "trend": "トレンド", "moving": "移動統計値"
                    }.get(x, x)
                )
                
                numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
                params["columns"] = st.multiselect("対象列", options=numeric_cols, default=numeric_cols[:3])
                
                if "percentile" in params["metrics"]:
                    percentiles_str = st.text_input("パーセンタイル値（カンマ区切り）", value="25, 50, 75")
                    params["percentiles"] = [float(p.strip()) for p in percentiles_str.split(",") if p.strip()]
                
                if "moving" in params["metrics"]:
                    params["window_size"] = st.slider("窓サイズ", min_value=3, max_value=30, value=10)
                
                if "trend" in params["metrics"]:
                    params["trend_method"] = st.selectbox(
                        "トレンド計算方法",
                        options=["linear", "polynomial"],
                        format_func=lambda x: {
                            "linear": "線形トレンド",
                            "polynomial": "多項式トレンド"
                        }.get(x, x)
                    )
                    
                    if params["trend_method"] == "polynomial":
                        params["trend_degree"] = st.slider("多項式次数", min_value=2, max_value=5, value=2)
            
            elif process_subtype == "custom":
                params["safe_mode"] = st.checkbox("安全モード（危険な関数の使用を制限）", value=True)
                
                st.write("計算式の設定:")
                st.info("カラム名をそのまま数式で利用できます。例: `speed * 0.5` や `sin(direction * 3.14 / 180)`")
                
                formula_count = st.number_input("計算式の数", min_value=1, max_value=5, value=1)
                formulas = {}
                
                for i in range(int(formula_count)):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        result_column = st.text_input(f"結果列名 {i+1}", value=f"result_{i+1}", key=f"custom_result_col_{i}")
                    
                    with col2:
                        formula = st.text_input(f"計算式 {i+1}", value="", key=f"custom_formula_{i}")
                    
                    if result_column and formula:
                        formulas[result_column] = formula
                
                params["formulas"] = formulas
        
        # 処理実行ボタン
        if st.button("処理を実行"):
            result_data, error_message = render_data_processing_demo(process_type, data, params)
            
            if result_data is not None:
                st.subheader("処理結果")
                
                # 結果のプレビュー
                data_preview.render(result_data, "処理結果データ")
                
                # 可視化
                render_data_visualization(result_data, data_type)
    
    # パイプライン処理モード
    else:  # menu == "パイプライン処理"
        st.subheader("パイプライン処理")
        
        # サンプルパイプラインを作成
        pipelines = create_sample_pipelines(data_type)
        
        # パイプラインの選択
        pipeline_names = [pipeline.name for pipeline in pipelines]
        selected_pipeline_name = st.selectbox("パイプライン", options=pipeline_names)
        
        # 選択されたパイプラインを取得
        selected_pipeline = next((p for p in pipelines if p.name == selected_pipeline_name), None)
        
        if selected_pipeline:
            # パイプラインを実行
            result_data, error_message = render_pipeline_demo(selected_pipeline, data)
            
            if result_data is not None:
                st.subheader("パイプライン処理結果")
                
                # 結果のプレビュー
                data_preview.render(result_data, "処理結果データ")
                
                # 可視化
                render_data_visualization(result_data, data_type)


if __name__ == "__main__":
    main()
