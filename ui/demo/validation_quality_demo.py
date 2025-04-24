# -*- coding: utf-8 -*-
"""
拡張データ検証機能を使用したデモスクリプト

このスクリプトは、強化されたデータ品質メトリクス計算と視覚化機能の使用例を示しています。
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.io as pio
import streamlit as st

# プロジェクトのルートディレクトリをパスに追加
# (このスクリプトがsailing-strategy-analyzerディレクトリの直下にある場合)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir))
sys.path.insert(0, project_root)

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator
from sailing_data_processor.validation.visualization_integration import EnhancedValidationVisualizer, create_validation_visualizer


def create_sample_data(rows=1000, error_rate=0.1):
    """サンプルデータを生成する"""
    # 現在時刻から24時間のデータを生成
    base_time = datetime.now()
    timestamps = [base_time + timedelta(seconds=i*10) for i in range(rows)]
    
    # 基準となる緯度・経度
    base_lat, base_lon = 35.6, 139.7
    
    # 正常データの作成
    data = {
        "timestamp": timestamps,
        "latitude": [base_lat + (np.sin(i/100) * 0.01) for i in range(rows)],
        "longitude": [base_lon + (np.cos(i/100) * 0.01) for i in range(rows)],
        "speed": [np.abs(10 + np.sin(i/50) * 5) for i in range(rows)],
        "heading": [np.abs((i * 5) % 360) for i in range(rows)]
    }
    
    # エラーの導入
    error_indices = np.random.choice(rows, int(rows * error_rate), replace=False)
    
    # 欠損値の追加
    for idx in error_indices[:int(len(error_indices) * 0.3)]:
        col = np.random.choice(["latitude", "longitude", "speed", "heading"])
        data[col][idx] = np.nan
    
    # 範囲外の値の追加
    for idx in error_indices[int(len(error_indices) * 0.3):int(len(error_indices) * 0.6)]:
        col = np.random.choice(["speed", "heading"])
        if col == "speed":
            data[col][idx] = -10 if np.random.random() < 0.5 else 100  # 負の値または極端に大きな値
        else:
            data[col][idx] = -45 if np.random.random() < 0.5 else 400  # 負の角度または360度以上
    
    # 時間的異常（タイムスタンプの重複や逆転）
    for idx in error_indices[int(len(error_indices) * 0.6):int(len(error_indices) * 0.8)]:
        if idx > 0:
            # 前の時間と同じか前の時間よりも古い時間に設定
            if np.random.random() < 0.5:
                data["timestamp"][idx] = data["timestamp"][idx-1]  # 重複
            else:
                data["timestamp"][idx] = data["timestamp"][idx-1] - timedelta(seconds=5)  # 逆転
    
    # 空間的異常（急な位置ジャンプ）
    for idx in error_indices[int(len(error_indices) * 0.8):]:
        if np.random.random() < 0.5:
            data["latitude"][idx] = base_lat + (np.random.random() - 0.5) * 0.1  # 大きな移動
        else:
            data["longitude"][idx] = base_lon + (np.random.random() - 0.5) * 0.1  # 大きな移動
    
    return pd.DataFrame(data)


def main():
    """メイン関数"""
    st.set_page_config(page_title="データ品質視覚化デモ", layout="wide")
    
    st.title("拡張データ品質メトリクスと視覚化のデモ")
    st.write("""
    このデモでは、セーリングデータプロセッサの拡張データ品質メトリクス計算と視覚化機能を紹介します。
    サンプルデータを生成して検証と視覚化を行います。
    """)
    
    # サイドバーでパラメータ設定
    st.sidebar.header("データ生成パラメータ")
    rows = st.sidebar.slider("データポイント数", 100, 5000, 1000)
    error_rate = st.sidebar.slider("エラー率", 0.0, 0.5, 0.1, 0.01)
    
    # データを生成
    with st.spinner("サンプルデータを生成中..."):
        df = create_sample_data(rows, error_rate)
    
    st.write(f"生成されたデータ: {len(df)} 行")
    st.dataframe(df.head())
    
    # GPSDataContainerとDataValidatorの作成
    container = GPSDataContainer()
    container.data = df
    validator = DataValidator()
    
    # 検証の実行
    with st.spinner("データを検証中..."):
        validator.validate(container)
    
    # 拡張された視覚化クラスの作成
    visualizer = create_validation_visualizer(validator, container)
    
    # タブでセクションを分ける
    tabs = st.tabs(["品質スコア", "時間的品質", "空間的品質", "問題の分布", "詳細情報"])
    
    with tabs[0]:
        st.header("データ品質スコア")
        
        # カード表示
        quality_cards = visualizer.generate_quality_score_card()
        
        # 総合スコアを大きく表示
        total_score = quality_cards["total_score"]
        st.metric("総合品質スコア", f"{total_score:.1f} / 100", delta=None)
        
        # カテゴリ別スコアをカラムで表示
        cols = st.columns(3)
        for i, card in enumerate(quality_cards["cards"][1:]):  # 総合スコア以外を表示
            with cols[i]:
                st.metric(
                    card["title"], 
                    f"{card['value']:.1f}", 
                    delta=card["impact_level"], 
                    help=card["description"]
                )
        
        # ゲージチャートとバーチャート
        gauge_chart, bar_chart = visualizer.generate_quality_score_visualization()
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(gauge_chart, use_container_width=True)
        with col2:
            st.plotly_chart(bar_chart, use_container_width=True)
    
    with tabs[1]:
        st.header("時間的品質分布")
        
        # 時間的品質チャート
        temporal_chart = visualizer.generate_temporal_quality_chart()
        st.plotly_chart(temporal_chart, use_container_width=True)
        
        # 問題タイプの時間分布
        dashboard = visualizer.generate_problem_distribution_visualization()
        st.plotly_chart(dashboard["problem_type_stacked"], use_container_width=True)
    
    with tabs[2]:
        st.header("空間的品質分布")
        
        # 空間的品質マップ
        spatial_map = visualizer.generate_spatial_quality_map()
        st.plotly_chart(spatial_map, use_container_width=True)
        
        # 問題の密度ヒートマップ
        st.plotly_chart(dashboard["spatial_heatmap"], use_container_width=True)
    
    with tabs[3]:
        st.header("問題の分布")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 問題タイプの円グラフ
            st.plotly_chart(dashboard["problem_type_pie"], use_container_width=True)
        
        with col2:
            # 時間的な問題分布
            st.plotly_chart(dashboard["temporal_distribution"], use_container_width=True)
    
    with tabs[4]:
        st.header("詳細情報")
        
        # 簡易的な問題サマリーの表示
        issues_summary = {
            "総レコード数": len(df),
            "問題のあるレコード数": len(visualizer.quality_metrics.problematic_indices["all"]),
            "問題率": f"{len(visualizer.quality_metrics.problematic_indices['all']) / len(df) * 100:.2f}%",
            "欠損値のあるレコード": len(visualizer.quality_metrics.problematic_indices["missing_data"]),
            "範囲外の値のあるレコード": len(visualizer.quality_metrics.problematic_indices["out_of_range"]),
            "重複のあるレコード": len(visualizer.quality_metrics.problematic_indices["duplicates"]),
            "空間的異常のあるレコード": len(visualizer.quality_metrics.problematic_indices["spatial_anomalies"]),
            "時間的異常のあるレコード": len(visualizer.quality_metrics.problematic_indices["temporal_anomalies"])
        }
        
        st.json(issues_summary)
        
        # 問題の詳細テーブル（最初の20件）
        if visualizer.quality_metrics.problematic_indices["all"]:
            st.subheader("問題のあるレコード（最初の20件）")
            problem_indices = list(visualizer.quality_metrics.problematic_indices["all"])[:20]
            problem_data = df.iloc[problem_indices].copy()
            
            # 問題タイプの特定
            problem_data["問題タイプ"] = ""
            for idx in problem_indices:
                problem_types = []
                for type_name, indices in visualizer.quality_metrics.problematic_indices.items():
                    if type_name != "all" and idx in indices:
                        problem_types.append(type_name)
                problem_data.loc[idx, "問題タイプ"] = ", ".join(problem_types)
            
            st.dataframe(problem_data)
        else:
            st.info("問題のあるレコードはありません。")


if __name__ == "__main__":
    main()
