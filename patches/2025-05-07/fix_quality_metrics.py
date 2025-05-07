#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
パッチスクリプト: 品質メトリクス関連の修正

EnhancedQualityMetricsCalculator クラスに generate_spatial_quality_map メソッドを追加します。
このメソッドは、GPSデータの品質分布を地図上に視覚化する機能を提供します。
"""

import os
import sys
from pathlib import Path

# パスの追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

def add_spatial_quality_map_method():
    """EnhancedQualityMetricsCalculator に generate_spatial_quality_map メソッドを追加"""
    file_path = os.path.join(project_root, 'sailing_data_processor', 'validation', 'quality_metrics_integration.py')
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # メソッドを追加するポイントを見つける（クラス内の最後のメソッドの後）
    insert_point = content.rfind('    def calculate_spatial_quality_scores')
    
    # calculate_spatial_quality_scores メソッドの終わりを見つける
    end_of_method = content.find('\n\n', insert_point)
    if end_of_method == -1:  # ファイルの末尾の場合
        end_of_method = len(content)
    
    # 新しいメソッドのコード
    new_method = """
    def generate_spatial_quality_map(self) -> 'go.Figure':
        \"\"\"
        空間的な品質分布のマップを生成
        
        GPSデータの空間的な品質分布を地図上に視覚化します。
        各エリアは品質スコアによって色分けされ、品質の空間的な変動を把握できます。
        
        Returns
        -------
        go.Figure
            品質マップの図
        \"\"\"
        import plotly.graph_objects as go
        from plotly.colors import sequential
        
        # 空間品質スコアの計算
        spatial_scores = self.calculate_spatial_quality_scores()
        
        if not spatial_scores:
            # データがない場合は空のマップを返す
            fig = go.Figure()
            fig.update_layout(
                title="空間品質マップ (データなし)",
                mapbox=dict(
                    style="open-street-map",
                    zoom=10
                )
            )
            return fig
            
        # マップのセンター位置を計算
        lats = [score['center'][0] for score in spatial_scores]
        lons = [score['center'][1] for score in spatial_scores]
        center_lat = sum(lats) / len(lats) if lats else 35.0
        center_lon = sum(lons) / len(lons) if lons else 135.0
            
        # 色をスコアに応じて設定
        colors = [self._get_score_color(score['quality_score']) for score in spatial_scores]
        
        # グリッド情報をテキストに整形
        hover_texts = []
        for score in spatial_scores:
            text = f"グリッド: {score['grid_id']}<br>" + \\
                   f"品質スコア: {score['quality_score']:.1f}<br>" + \\
                   f"問題数: {score['problem_count']}/{score['total_count']}"
            hover_texts.append(text)
        
        # マーカーサイズをデータ量に応じて調整
        marker_sizes = [max(8, min(20, 8 + (score['total_count'] / 10))) for score in spatial_scores]
        
        # マップの作成
        fig = go.Figure()
        
        # グリッドをマーカーとして追加
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(
                size=marker_sizes,
                color=colors,
                opacity=0.7
            ),
            text=hover_texts,
            hoverinfo='text',
            name='品質スコア'
        ))
        
        # レイアウト設定
        fig.update_layout(
            title="空間品質マップ",
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=11
            ),
            height=600,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig"""
    
    # メソッドを挿入
    updated_content = content[:end_of_method] + new_method + content[end_of_method:]
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
        
    print(f"[✓] EnhancedQualityMetricsCalculator に generate_spatial_quality_map メソッドを追加しました: {file_path}")
    return True

if __name__ == "__main__":
    print("パッチスクリプト: 品質メトリクス関連の修正を開始します")
    add_spatial_quality_map_method()
    print("パッチスクリプト: 修正完了")
