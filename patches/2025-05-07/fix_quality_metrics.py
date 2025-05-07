#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品質メトリクスクラスの修正

このスクリプトは quality_metrics_integration.py を修正します。
EnhancedQualityMetricsCalculator クラスに必要なメソッドを追加します。
"""

import os
import sys
import re
from pathlib import Path

# プロジェクトルートを取得
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 品質メトリクスクラスファイルのパス
metrics_file_path = os.path.join(project_root, 'sailing_data_processor', 'validation', 'quality_metrics_integration.py')

def fix_quality_metrics():
    """品質メトリクスクラスの修正を行う"""
    print(f"品質メトリクスクラスファイルの修正を開始: {metrics_file_path}")
    
    # ファイルを読み込む
    with open(metrics_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # EnhancedQualityMetricsCalculator クラスの終了位置を特定
    class_pattern = r'class EnhancedQualityMetricsCalculator\(QualityMetricsCalculator\):(.*?)(?:class |$)'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if class_match:
        class_end_pos = class_match.end(1)
        
        # 足りないメソッドを追加
        additional_methods = '''

    def calculate_category_quality_scores(self):
        """
        カテゴリ別の品質スコアを計算
        
        Returns
        -------
        Dict[str, float]
            カテゴリ別の品質スコア
        """
        # カテゴリ別の品質スコアを計算
        completeness_score = self.quality_scores.get("completeness", 100.0)
        accuracy_score = self.quality_scores.get("accuracy", 100.0)
        consistency_score = self.quality_scores.get("consistency", 100.0)
        
        return {
            "completeness": completeness_score,
            "accuracy": accuracy_score,
            "consistency": consistency_score
        }
    
    def generate_quality_score_visualization(self):
        """
        品質スコアの視覚化を生成
        
        Returns
        -------
        Tuple[go.Figure, go.Figure]
            ゲージチャートとバーチャート
        """
        import plotly.graph_objects as go
        
        # 総合スコアのゲージチャート
        gauge_chart = go.Figure(go.Indicator(
            mode="gauge+number",
            value=self.quality_scores.get("total", 100.0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "データ品質スコア"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self._get_score_color(self.quality_scores.get("total", 100.0))},
                'steps': [
                    {'range': [0, 25], 'color': "#E74C3C"},
                    {'range': [25, 50], 'color': "#E67E22"},
                    {'range': [50, 75], 'color': "#F1C40F"},
                    {'range': [75, 90], 'color': "#2ECC71"},
                    {'range': [90, 100], 'color': "#27AE60"}
                ]
            }
        ))
        
        # カテゴリ別スコアのバーチャート
        category_scores = self.calculate_category_quality_scores()
        
        bar_chart = go.Figure(go.Bar(
            x=list(category_scores.keys()),
            y=list(category_scores.values()),
            marker_color=[self._get_score_color(score) for score in category_scores.values()]
        ))
        
        bar_chart.update_layout(
            title="カテゴリ別品質スコア",
            yaxis_title="スコア",
            yaxis=dict(range=[0, 100])
        )
        
        return gauge_chart, bar_chart
    
    def _get_score_color(self, score):
        """スコアに応じた色を返す"""
        if score >= 90:
            return "#27AE60"  # 濃い緑
        elif score >= 75:
            return "#2ECC71"  # 緑
        elif score >= 50:
            return "#F1C40F"  # 黄色
        elif score >= 25:
            return "#E67E22"  # オレンジ
        else:
            return "#E74C3C"  # 赤
    
    def calculate_temporal_quality_scores(self):
        """
        時間帯別の品質スコアを計算
        
        Returns
        -------
        List[Dict[str, Any]]
            時間帯別の品質スコア
        """
        # データフレームがない場合は空リストを返す
        if self.data is None or len(self.data) == 0 or 'timestamp' not in self.data.columns:
            return []
        
        import pandas as pd
        from datetime import datetime, timedelta
        
        # タイムスタンプで並べ替え
        sorted_data = self.data.sort_values('timestamp')
        
        # 時間の範囲を計算
        min_time = sorted_data['timestamp'].min()
        max_time = sorted_data['timestamp'].max()
        time_range = max_time - min_time
        
        # 時間帯の数を決定（最大30区間）
        num_periods = min(30, len(self.data) // 20 + 1)
        
        # 時間帯の幅を計算
        period_width = time_range / num_periods
        
        # 各時間帯の品質スコアを計算
        temporal_scores = []
        
        for i in range(num_periods):
            period_start = min_time + period_width * i
            period_end = period_start + period_width
            
            # 時間帯に含まれるデータのインデックスを取得
            period_data = sorted_data[(sorted_data['timestamp'] >= period_start) & 
                                      (sorted_data['timestamp'] < period_end)]
            period_indices = period_data.index.tolist()
            
            # 時間帯に含まれる問題の数を計算
            problem_indices = set(self.problematic_indices["all"])
            problem_count = len(problem_indices.intersection(set(period_indices)))
            
            # 品質スコアを計算
            if len(period_indices) > 0:
                quality_score = 100.0 * (1.0 - problem_count / len(period_indices))
            else:
                quality_score = 100.0
            
            # 問題タイプの分布を計算
            problem_distribution = self._calculate_problem_type_distribution_for_period(period_indices)
            
            # 結果を追加
            temporal_scores.append({
                'period': f"{period_start.strftime('%H:%M:%S')} - {period_end.strftime('%H:%M:%S')}",
                'start_time': period_start,
                'end_time': period_end,
                'total_count': len(period_indices),
                'problem_count': problem_count,
                'quality_score': quality_score,
                'problem_distribution': problem_distribution
            })
        
        return temporal_scores
    
    def calculate_spatial_quality_scores(self):
        """
        空間グリッド別の品質スコアを計算
        
        Returns
        -------
        List[Dict[str, Any]]
            空間グリッド別の品質スコア
        """
        # データフレームがない場合は空リストを返す
        if self.data is None or len(self.data) == 0 or 'latitude' not in self.data.columns or 'longitude' not in self.data.columns:
            return []
        
        import numpy as np
        
        # 緯度経度の範囲を計算
        min_lat = self.data['latitude'].min()
        max_lat = self.data['latitude'].max()
        min_lon = self.data['longitude'].min()
        max_lon = self.data['longitude'].max()
        
        # グリッドの数を決定（最大で5x5グリッド）
        num_lat_grids = min(5, int(np.ceil((max_lat - min_lat) / 0.01)))
        num_lon_grids = min(5, int(np.ceil((max_lon - min_lon) / 0.01)))
        
        # グリッドサイズの計算
        lat_grid_size = (max_lat - min_lat) / num_lat_grids
        lon_grid_size = (max_lon - min_lon) / num_lon_grids
        
        # 各グリッドの品質スコアを計算
        spatial_scores = []
        
        for i in range(num_lat_grids):
            lat_start = min_lat + i * lat_grid_size
            lat_end = lat_start + lat_grid_size
            
            for j in range(num_lon_grids):
                lon_start = min_lon + j * lon_grid_size
                lon_end = lon_start + lon_grid_size
                
                # グリッドに含まれるデータのインデックスを取得
                grid_data = self.data[(self.data['latitude'] >= lat_start) & 
                                      (self.data['latitude'] < lat_end) & 
                                      (self.data['longitude'] >= lon_start) & 
                                      (self.data['longitude'] < lon_end)]
                grid_indices = grid_data.index.tolist()
                
                # グリッドにデータがある場合のみ計算
                if len(grid_indices) > 0:
                    # グリッドに含まれる問題の数を計算
                    problem_indices = set(self.problematic_indices["all"])
                    problem_count = len(problem_indices.intersection(set(grid_indices)))
                    
                    # 品質スコアを計算
                    quality_score = 100.0 * (1.0 - problem_count / len(grid_indices))
                    
                    # 問題タイプの分布を計算
                    problem_distribution = self._calculate_problem_type_distribution_for_period(grid_indices)
                    
                    # 結果を追加
                    spatial_scores.append({
                        'grid_id': f"Grid-{i}-{j}",
                        'lat_range': (lat_start, lat_end),
                        'lon_range': (lon_start, lon_end),
                        'center': ((lat_start + lat_end) / 2, (lon_start + lon_end) / 2),
                        'total_count': len(grid_indices),
                        'problem_count': problem_count,
                        'quality_score': quality_score,
                        'problem_distribution': problem_distribution
                    })
        
        return spatial_scores'''
        
        # クラスの終了位置に新しいメソッドを追加
        updated_content = content[:class_end_pos] + additional_methods + content[class_end_pos:]
        
        # 結果を保存
        with open(metrics_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"品質メトリクスクラスの修正が完了しました。")
        return True
    else:
        print(f"EnhancedQualityMetricsCalculator クラスが見つかりませんでした。")
        return False

if __name__ == "__main__":
    fix_quality_metrics()
