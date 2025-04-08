"""
sailing_data_processor.visualization.strategy_visualization モジュール

レース後戦略分析の可視化機能を提供します。
戦略的判断ポイント、パフォーマンス変化点、推奨改善領域などの視覚化を実装しています。
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import math
import io
import base64
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import warnings
import logging

class StrategyVisualizer:
    """
    レース戦略の可視化クラス
    
    レース戦略と意思決定の分析結果を視覚的に表現します。
    """
    
    def __init__(self, figure_size=(10, 6), dpi=100, theme="default"):
        """
        初期化
        
        Parameters
        ----------
        figure_size : tuple, optional
            図のサイズ (幅, 高さ) インチ単位, by default (10, 6)
        dpi : int, optional
            解像度 (dots per inch), by default 100
        theme : str, optional
            表示テーマ ("default", "dark", "minimal"), by default "default"
        """
        self.figure_size = figure_size
        self.dpi = dpi
        self.theme = theme
        
        # テーマに基づくスタイルの設定
        self._set_theme(theme)
        
        # ロギング設定
        self.logger = logging.getLogger("StrategyVisualizer")
    
    def _set_theme(self, theme):
        """テーマに基づくスタイルの設定"""
        if theme == "dark":
            plt.style.use('dark_background')
            self.colors = {
                "background": "#1e1e1e",
                "text": "#ffffff",
                "grid": "#333333",
                "primary": "#4e9bff",
                "secondary": "#ff6b6b",
                "highlight": "#ffff00",
                "upwind": "#4e9bff",
                "downwind": "#8cff66",
                "tack": "#ff6b6b",
                "gybe": "#ffcc00",
                "layline": "#ff00ff",
                "start": "#00ffff",
                "mark": "#ff9900",
                "good": "#8cff66",
                "average": "#ffcc00",
                "poor": "#ff6b6b",
                "cmap_performance": cm.viridis,
                "cmap_decisions": cm.coolwarm
            }
        elif theme == "minimal":
            plt.style.use('seaborn-v0_8-whitegrid')
            self.colors = {
                "background": "#ffffff",
                "text": "#333333",
                "grid": "#dddddd",
                "primary": "#1a53ff",
                "secondary": "#ff4d4d",
                "highlight": "#ff9900",
                "upwind": "#1a53ff",
                "downwind": "#33cc33",
                "tack": "#ff4d4d",
                "gybe": "#ff9900",
                "layline": "#cc00cc",
                "start": "#00cccc",
                "mark": "#ff8000",
                "good": "#33cc33",
                "average": "#ff9900",
                "poor": "#ff4d4d",
                "cmap_performance": cm.viridis,
                "cmap_decisions": cm.coolwarm
            }
        else:  # default
            plt.style.use('default')
            self.colors = {
                "background": "#ffffff",
                "text": "#333333",
                "grid": "#cccccc",
                "primary": "#1f77b4",
                "secondary": "#ff7f0e",
                "highlight": "#d62728",
                "upwind": "#1f77b4",
                "downwind": "#2ca02c",
                "tack": "#d62728",
                "gybe": "#ff7f0e",
                "layline": "#9467bd",
                "start": "#17becf",
                "mark": "#e377c2",
                "good": "#2ca02c",
                "average": "#ff7f0e",
                "poor": "#d62728",
                "cmap_performance": cm.viridis,
                "cmap_decisions": cm.coolwarm
            }
    
    def plot_strategic_points_map(self, track_data: pd.DataFrame, 
                                decision_points: List[Dict] = None,
                                course_data: Dict = None,
                                title: str = "戦略的判断ポイントの分布") -> Figure:
        """
        戦略的判断ポイントの地図上での分布プロット
        
        Parameters
        ----------
        track_data : pd.DataFrame
            GPSトラックデータを含むデータフレーム
            必要なカラム:
            - latitude, longitude: 位置
            - timestamp: 時刻（オプション）
        decision_points : List[Dict], optional
            戦略的判断ポイントのリスト, by default None
            各ポイントは以下のキーを含む辞書:
            - type: ポイントタイプ（例: "tack", "layline", "wind_shift"など）
            - position: [latitude, longitude]の形式での位置情報
            - impact_score: 影響度スコア
            - description: 説明
        course_data : Dict, optional
            コース情報（マーク位置など）, by default None
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not isinstance(track_data, pd.DataFrame) or track_data.empty:
            self.logger.warning("無効なトラックデータ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効なデータがありません", ha='center', va='center')
            return fig
            
        if 'latitude' not in track_data.columns or 'longitude' not in track_data.columns:
            self.logger.warning("必要なカラムがありません: latitude, longitude")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "必要なカラムがありません: latitude, longitude", ha='center', va='center')
            return fig
        
        # プロットの作成
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # トラックデータのプロット
        ax.plot(track_data['longitude'], track_data['latitude'], 
               color=self.colors["primary"], linewidth=2, alpha=0.7, label="航跡")
        
        # 開始点と終了点をマーク
        if 'timestamp' in track_data.columns:
            start_idx = track_data['timestamp'].idxmin()
            end_idx = track_data['timestamp'].idxmax()
            
            ax.scatter(track_data.loc[start_idx, 'longitude'], 
                      track_data.loc[start_idx, 'latitude'],
                      s=100, c=self.colors["start"], marker='o', 
                      edgecolors='black', linewidths=1, label="開始点")
            
            ax.scatter(track_data.loc[end_idx, 'longitude'], 
                      track_data.loc[end_idx, 'latitude'],
                      s=100, c=self.colors["highlight"], marker='s', 
                      edgecolors='black', linewidths=1, label="終了点")
        
        # コースデータがある場合はマークを表示
        if course_data and 'marks' in course_data:
            for i, mark in enumerate(course_data['marks']):
                if 'latitude' in mark and 'longitude' in mark:
                    ax.scatter(mark['longitude'], mark['latitude'], 
                              s=150, c=self.colors["mark"], marker='^', 
                              edgecolors='black', linewidths=1, alpha=0.8,
                              label="マーク" if i == 0 else "")
                    
                    # マーク番号のラベル
                    ax.annotate(str(i+1), 
                               (mark['longitude'], mark['latitude']),
                               color='white', fontweight='bold',
                               ha='center', va='center')
        
        # 判断ポイントのプロット
        if decision_points:
            # ポイントタイプ別のマーカーとカラーマッピング
            point_markers = {
                "tack": "o",         # 円
                "gybe": "s",         # 四角
                "layline": "d",      # ダイヤモンド
                "wind_shift": "^",   # 三角形
                "cross_point": "P",  # プラス四角
                "vmg_change": "*",   # 星
                "start": "X",        # ×印
                "mark_rounding": "h" # 六角形
            }
            
            point_colors = {
                "tack": self.colors["tack"],
                "gybe": self.colors["gybe"],
                "layline": self.colors["layline"],
                "wind_shift": self.colors["primary"],
                "cross_point": self.colors["secondary"],
                "vmg_change": self.colors["highlight"],
                "start": self.colors["start"],
                "mark_rounding": self.colors["mark"]
            }
            
            # プロット済みのポイントタイプを記録（凡例用）
            plotted_types = set()
            
            for point in decision_points:
                if 'position' in point and point['position']:
                    point_type = point.get('type', 'unknown')
                    pos = point.get('position')
                    
                    if pos and len(pos) == 2 and None not in pos:
                        lat, lon = pos
                        
                        # 影響度に基づいたマーカーサイズ
                        impact = point.get('impact_score', 5)
                        size = 50 + impact * 20  # サイズは影響度に比例
                        
                        # マーカーとカラーの取得
                        marker = point_markers.get(point_type, "o")
                        color = point_colors.get(point_type, self.colors["primary"])
                        
                        # ポイントのプロット
                        ax.scatter(lon, lat, s=size, c=color, marker=marker, 
                                 edgecolors='black', linewidths=1, alpha=0.8,
                                 label=f"{point_type}" if point_type not in plotted_types else "")
                        
                        # タイプを記録
                        plotted_types.add(point_type)
                        
                        # 高影響度のポイントには注釈を追加
                        if impact > 7:
                            desc = point.get('description', '')
                            if len(desc) > 30:
                                desc = desc[:27] + "..."
                                
                            ax.annotate(desc,
                                      (lon, lat),
                                      xytext=(10, 10), textcoords='offset points',
                                      fontsize=8, color=self.colors["text"],
                                      bbox=dict(boxstyle="round,pad=0.3", 
                                               fc=self.colors["background"], 
                                               ec=color, alpha=0.8))
        
        # グラフの装飾
        ax.set_xlabel('経度')
        ax.set_ylabel('緯度')
        ax.set_title(title)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # アスペクト比の調整
        # 緯度・経度は同じスケールになるよう調整
        ax.set_aspect('equal')
        
        # 凡例
        ax.legend(loc='best')
        
        # タイトレイアウト
        plt.tight_layout()
        
        return fig
    
    def plot_performance_timeline(self, track_data: pd.DataFrame,
                                performance_points: List[Dict] = None,
                                metrics: List[str] = None,
                                title: str = "パフォーマンス指標の時系列推移") -> Figure:
        """
        パフォーマンス指標の時系列プロット
        
        Parameters
        ----------
        track_data : pd.DataFrame
            GPSトラックデータを含むデータフレーム
            必要なカラム:
            - timestamp: 時刻
            - その他: 速度やVMGなどのパフォーマンス指標
        performance_points : List[Dict], optional
            パフォーマンス変化点のリスト, by default None
            各ポイントは以下のキーを含む辞書:
            - time: 変化点の時刻
            - type: 変化の種類（例: "speed_improvement", "vmg_drop"など）
            - magnitude: 変化の大きさ
            - description: 説明
        metrics : List[str], optional
            プロットする指標のリスト, by default None
            Noneの場合は'speed'と'vmg'をプロット（存在する場合）
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not isinstance(track_data, pd.DataFrame) or track_data.empty:
            self.logger.warning("無効なトラックデータ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効なデータがありません", ha='center', va='center')
            return fig
            
        if 'timestamp' not in track_data.columns:
            self.logger.warning("必要なカラム 'timestamp' がありません")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "必要なカラム 'timestamp' がありません", ha='center', va='center')
            return fig
        
        # プロットする指標の決定
        if metrics is None:
            metrics = []
            for metric in ['speed', 'vmg', 'performance_index']:
                if metric in track_data.columns:
                    metrics.append(metric)
        
        if not metrics:
            self.logger.warning("プロット可能な指標がありません")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "プロット可能な指標がありません", ha='center', va='center')
            return fig
        
        # データをタイムスタンプでソート
        df = track_data.sort_values('timestamp').copy()
        
        # 複数の指標をプロット
        fig, axes = plt.subplots(len(metrics), 1, figsize=(self.figure_size[0], 
                                                        self.figure_size[1] * len(metrics) * 0.7),
                                dpi=self.dpi, sharex=True)
        
        # 単一の指標の場合、axesをリストに変換
        if len(metrics) == 1:
            axes = [axes]
        
        # 各指標のプロット
        for i, metric in enumerate(metrics):
            ax = axes[i]
            
            # 指標の日本語名とカラー
            metric_names = {
                'speed': ('速度', self.colors["primary"]),
                'vmg': ('VMG', self.colors["secondary"]),
                'performance_index': ('パフォーマンス指標', self.colors["highlight"]),
                'heel': ('ヒール角', self.colors["tack"]),
                'twa': ('真風角', self.colors["gybe"]),
                'efficiency': ('効率', self.colors["layline"])
            }
            
            metric_name, color = metric_names.get(metric, (metric, self.colors["primary"]))
            
            # 指標のプロット
            ax.plot(df['timestamp'], df[metric], color=color, linewidth=2)
            
            # 性能変化点のプロット
            if performance_points:
                for point in performance_points:
                    if point.get('time') and point.get('type', '').lower() in metric.lower():
                        point_time = point['time']
                        
                        # 同時刻のデータポイントのインデックスを探す
                        idx = df['timestamp'].searchsorted(point_time)
                        if idx < len(df):
                            point_value = df.iloc[idx][metric] if idx < len(df) else None
                            
                            # 変化の種類に基づいた色
                            if 'improvement' in point.get('type', '').lower() or 'increase' in point.get('type', '').lower():
                                point_color = self.colors["good"]
                            elif 'drop' in point.get('type', '').lower() or 'decrease' in point.get('type', '').lower():
                                point_color = self.colors["poor"]
                            else:
                                point_color = self.colors["average"]
                            
                            # 変化点のマーカー
                            if point_value is not None:
                                ax.scatter(point_time, point_value, 
                                         s=100, c=point_color, marker='o', 
                                         edgecolors='black', linewidths=1)
                                
                                # 説明の注釈
                                description = point.get('description', '')
                                if description:
                                    if len(description) > 40:
                                        description = description[:37] + "..."
                                    
                                    ax.annotate(description,
                                              (point_time, point_value),
                                              xytext=(10, 10), textcoords='offset points',
                                              fontsize=8, color=self.colors["text"],
                                              bbox=dict(boxstyle="round,pad=0.3", 
                                                       fc=self.colors["background"], 
                                                       ec=point_color, alpha=0.8))
            
            # 軸ラベルとグリッド
            ax.set_ylabel(metric_name)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Y軸の範囲調整（最小値を0にするかどうか）
            ymin, ymax = ax.get_ylim()
            if ymin > 0:
                ax.set_ylim(0, ymax * 1.1)
            
            # 最後の指標でない場合はX軸ラベルを非表示
            if i < len(metrics) - 1:
                ax.tick_params(labelbottom=False)
        
        # X軸のフォーマットと表示
        time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        if time_range < 3600:  # 1時間未満
            date_format = DateFormatter('%H:%M:%S')
        elif time_range < 86400:  # 1日未満
            date_format = DateFormatter('%H:%M')
        else:  # 1日以上
            date_format = DateFormatter('%m/%d %H:%M')
            
        axes[-1].xaxis.set_major_formatter(date_format)
        axes[-1].set_xlabel('時刻')
        fig.autofmt_xdate()  # 日付ラベルを見やすく
        
        # タイトル
        fig.suptitle(title, fontsize=14)
        
        # タイトレイアウト
        plt.tight_layout()
        fig.subplots_adjust(top=0.95)  # タイトル用のスペース
        
        return fig
    
    def plot_improvement_recommendations(self, improvement_suggestions: Dict,
                                       title: str = "改善提案と重点領域") -> Figure:
        """
        改善提案と重点領域のプロット
        
        Parameters
        ----------
        improvement_suggestions : Dict
            improvement_advisorから生成された改善提案
            以下のキーを含むべき:
            - priority_areas: 優先的な改善領域
            - practice_tasks: 推奨練習課題
            - skill_benchmarks: スキルベンチマーク
        title : str, optional
            グラフのタイトル, by default "改善提案と重点領域"
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not improvement_suggestions or 'priority_areas' not in improvement_suggestions:
            self.logger.warning("無効な改善提案データ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効な改善提案データがありません", ha='center', va='center')
            return fig
        
        # プロットの作成（2行1列のサブプロット）
        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        gs = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.3)
        
        # 優先領域バブルチャート（上）
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_priority_areas_bubble(ax1, improvement_suggestions)
        
        # スキルベンチマークレーダーチャート（下）
        ax2 = fig.add_subplot(gs[1, 0], polar=True)
        self._plot_skill_benchmarks_radar(ax2, improvement_suggestions)
        
        # 全体のタイトル
        fig.suptitle(title, fontsize=14)
        
        # タイトレイアウト
        plt.tight_layout()
        fig.subplots_adjust(top=0.9)  # タイトル用のスペース
        
        return fig
    
    def _plot_priority_areas_bubble(self, ax, improvement_suggestions):
        """優先領域のバブルチャート"""
        priority_areas = improvement_suggestions.get('priority_areas', [])
        
        if not priority_areas:
            ax.text(0.5, 0.5, "優先領域データがありません", ha='center', va='center')
            ax.axis('off')
            return
        
        # 最大5つの領域を表示
        areas = priority_areas[:min(5, len(priority_areas))]
        
        # カテゴリごとのグルーピング
        categories = {}
        for area in areas:
            category = area.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(area)
        
        # カテゴリのマッピング
        category_order = [
            'basic_skills', 'technical_skills', 'tactical_skills', 
            'strategic_skills', 'mental_skills', 'physical_skills'
        ]
        
        category_names = {
            'basic_skills': '基本スキル',
            'technical_skills': '技術スキル',
            'tactical_skills': '戦術スキル',
            'strategic_skills': '戦略スキル',
            'mental_skills': 'メンタルスキル',
            'physical_skills': 'フィジカルスキル',
            'unknown': 'その他'
        }
        
        # カテゴリごとの色
        category_colors = {
            'basic_skills': self.colors["primary"],
            'technical_skills': self.colors["secondary"],
            'tactical_skills': self.colors["tack"],
            'strategic_skills': self.colors["gybe"],
            'mental_skills': self.colors["layline"],
            'physical_skills': self.colors["start"],
            'unknown': self.colors["mark"]
        }
        
        # バブルチャートデータ
        x_positions = []
        y_positions = []
        sizes = []
        colors = []
        labels = []
        
        for i, category in enumerate(category_order):
            if category in categories:
                cat_areas = categories[category]
                for j, area in enumerate(cat_areas):
                    # X位置はカテゴリごとに固定、Y位置は優先度
                    x_positions.append(i)
                    y_positions.append(area.get('priority', 0))
                    
                    # サイズは優先度に比例
                    sizes.append(1000 * area.get('priority', 1) / 10)
                    
                    # 色はカテゴリごとに固定
                    colors.append(category_colors.get(category, self.colors["primary"]))
                    
                    # ラベルは領域名
                    labels.append(area.get('display_name', ''))
        
        # バブルチャートのプロット
        scatter = ax.scatter(x_positions, y_positions, s=sizes, c=colors, alpha=0.7, 
                           edgecolors='black', linewidths=1)
        
        # ラベルの追加
        for i, label in enumerate(labels):
            ax.annotate(label, (x_positions[i], y_positions[i]),
                       ha='center', va='center', fontsize=10,
                       fontweight='bold', color='white')
        
        # カテゴリラベル（X軸）
        displayed_categories = [cat for cat in category_order if cat in categories]
        ax.set_xticks(range(len(displayed_categories)))
        ax.set_xticklabels([category_names.get(cat, cat) for cat in displayed_categories])
        
        # Y軸設定
        ax.set_ylabel('優先度')
        ax.set_ylim(0, 10.5)
        
        # グリッドと装飾
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_title('優先改善領域', fontsize=12)
    
    def _plot_skill_benchmarks_radar(self, ax, improvement_suggestions):
        """スキルベンチマークのレーダーチャート"""
        skill_benchmarks = improvement_suggestions.get('skill_benchmarks', {})
        
        if not skill_benchmarks or 'current_benchmarks' not in skill_benchmarks:
            ax.text(0.5, 0.5, "ベンチマークデータがありません", ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')
            return
        
        # ベンチマークデータの抽出
        current_benchmarks = skill_benchmarks.get('current_benchmarks', {})
        next_benchmarks = skill_benchmarks.get('next_benchmarks', {})
        actual_performance = skill_benchmarks.get('actual_performance', {})
        
        # レーダーチャートのカテゴリ
        categories = [
            '風上VMG効率', '風下VMG効率', 'タック効率', 'ジャイブ効率',
            'スタート精度', 'マーク回航効率', '戦術判断品質'
        ]
        
        # データのマッピング
        current_metrics = [
            current_benchmarks.get('upwind_vmg_efficiency', 0),
            current_benchmarks.get('downwind_vmg_efficiency', 0),
            current_benchmarks.get('tack_efficiency', 0),
            current_benchmarks.get('gybe_efficiency', 0),
            current_benchmarks.get('start_timing_accuracy', 0) / 10,  # スケール調整
            current_benchmarks.get('mark_rounding_efficiency', 0),
            current_benchmarks.get('tactical_decision_quality', 0)
        ]
        
        next_metrics = [
            next_benchmarks.get('upwind_vmg_efficiency', 0),
            next_benchmarks.get('downwind_vmg_efficiency', 0),
            next_benchmarks.get('tack_efficiency', 0),
            next_benchmarks.get('gybe_efficiency', 0),
            next_benchmarks.get('start_timing_accuracy', 0) / 10,  # スケール調整
            next_benchmarks.get('mark_rounding_efficiency', 0),
            next_benchmarks.get('tactical_decision_quality', 0)
        ]
        
        actual_metrics = []
        for i, metric in enumerate(['upwind_vmg_efficiency', 'downwind_vmg_efficiency', 
                                  'tack_efficiency', 'gybe_efficiency', 
                                  'start_timing_accuracy', 'mark_rounding_efficiency',
                                  'tactical_decision_quality']):
            if metric in actual_performance:
                value = actual_performance[metric]
                # スタート精度は反転（時間が短いほど良い）
                if metric == 'start_timing_accuracy':
                    value = value / 10  # スケール調整
                actual_metrics.append(value)
            else:
                # 実績がない場合は現在のベンチマークを使用
                actual_metrics.append(current_metrics[i])
        
        # カテゴリの数
        N = len(categories)
        
        # 角度の計算
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        
        # 閉じたグラフにするため、最初のカテゴリを最後にも追加
        categories.append(categories[0])
        current_metrics.append(current_metrics[0])
        next_metrics.append(next_metrics[0])
        actual_metrics.append(actual_metrics[0])
        angles.append(angles[0])
        
        # レーダーチャートの描画
        ax.plot(angles, current_metrics, color=self.colors["average"], linewidth=1, 
              linestyle='--', label='現在レベル基準値')
        ax.plot(angles, next_metrics, color=self.colors["good"], linewidth=1, 
              linestyle=':', label='次レベル基準値')
        ax.plot(angles, actual_metrics, color=self.colors["primary"], linewidth=2, 
              label='実際のパフォーマンス')
        
        # 塗りつぶし
        ax.fill(angles, actual_metrics, color=self.colors["primary"], alpha=0.25)
        
        # カテゴリラベル
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories[:-1], fontsize=8)
        
        # Y軸設定
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8)
        
        # 凡例
        ax.legend(loc='lower right', bbox_to_anchor=(0.9, 0.9))
        
        # タイトル
        current_level = skill_benchmarks.get('current_level', '')
        next_level = skill_benchmarks.get('next_level', '')
        if current_level and next_level:
            subtitle = f'現在: {current_level} → 次のレベル: {next_level}'
            ax.set_title('スキルベンチマーク評価\n' + subtitle, fontsize=11)
        else:
            ax.set_title('スキルベンチマーク評価', fontsize=11)
    
    def plot_strategy_evaluation_summary(self, strategy_evaluation: Dict,
                                       title: str = "戦略評価サマリー") -> Figure:
        """
        戦略評価結果のサマリープロット
        
        Parameters
        ----------
        strategy_evaluation : Dict
            strategy_evaluatorから生成された評価結果
            以下のキーを含むべき:
            - overall_rating: 総合評価点
            - upwind_strategy, downwind_strategy, start_execution, 
              mark_rounding, tactical_decisions: 各要素の評価
            - strengths, weaknesses: 強みと弱み
        title : str, optional
            グラフのタイトル, by default "戦略評価サマリー"
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not strategy_evaluation or 'overall_rating' not in strategy_evaluation:
            self.logger.warning("無効な戦略評価データ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効な戦略評価データがありません", ha='center', va='center')
            return fig
        
        # プロットの作成（2行1列のサブプロット）
        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[3, 2], hspace=0.4, wspace=0.3)
        
        # カテゴリ別評価のバーチャート（左上）
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_category_scores(ax1, strategy_evaluation)
        
        # 総合評価のゲージ（右上）
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_overall_rating_gauge(ax2, strategy_evaluation)
        
        # 強み弱みのテーブル（下段）
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_strengths_weaknesses(ax3, strategy_evaluation)
        
        # 全体のタイトル
        fig.suptitle(title, fontsize=14)
        
        # タイトレイアウト
        plt.tight_layout()
        fig.subplots_adjust(top=0.9)  # タイトル用のスペース
        
        return fig
    
    def _plot_category_scores(self, ax, strategy_evaluation):
        """カテゴリ別評価のバーチャート"""
        # スコアの抽出
        categories = {
            'upwind_strategy': '風上戦略',
            'downwind_strategy': '風下戦略',
            'start_execution': 'スタート',
            'mark_rounding': 'マーク回航',
            'tactical_decisions': '戦術判断'
        }
        
        scores = []
        labels = []
        colors = []
        
        for key, label in categories.items():
            if key in strategy_evaluation and 'score' in strategy_evaluation[key]:
                score = strategy_evaluation[key]['score']
                scores.append(score)
                labels.append(label)
                
                # スコアに基づいた色
                if score >= 7.5:
                    colors.append(self.colors["good"])
                elif score >= 5.0:
                    colors.append(self.colors["average"])
                else:
                    colors.append(self.colors["poor"])
        
        # バーチャートのプロット
        y_pos = range(len(labels))
        ax.barh(y_pos, scores, align='center', color=colors)
        
        # スコア値の表示
        for i, score in enumerate(scores):
            ax.text(score + 0.1, i, f'{score:.1f}', va='center')
        
        # 軸設定
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlim(0, 10.5)
        ax.set_xlabel('評価点')
        
        # グリッドと装飾
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax.set_title('カテゴリ別評価', fontsize=12)
    
    def _plot_overall_rating_gauge(self, ax, strategy_evaluation):
        """総合評価のゲージ"""
        # 総合評価の取得
        overall_rating = strategy_evaluation.get('overall_rating', 5.0)
        execution_quality = strategy_evaluation.get('execution_quality', 5.0)
        
        # 円形ゲージの描画
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 背景円（グレー）
        background = plt.Circle((0.5, 0.5), 0.4, color='lightgray', fill=True)
        ax.add_artist(background)
        
        # 評価値に基づく円弧（カラー）
        rating_ratio = overall_rating / 10.0
        
        # 色の決定
        if overall_rating >= 7.5:
            color = self.colors["good"]
        elif overall_rating >= 5.0:
            color = self.colors["average"]
        else:
            color = self.colors["poor"]
        
        # 円弧の角度計算（0度が右、反時計回り）
        start_angle = 90
        end_angle = start_angle + 360 * rating_ratio
        
        # 円弧の描画
        arc = mpatches.Wedge((0.5, 0.5), 0.4, start_angle, end_angle, width=0.1, color=color)
        ax.add_artist(arc)
        
        # 実行品質の円弧（内側）
        quality_ratio = execution_quality / 10.0
        quality_end_angle = start_angle + 360 * quality_ratio
        
        # 円弧の描画（内側）
        quality_arc = mpatches.Wedge((0.5, 0.5), 0.28, start_angle, quality_end_angle, width=0.1, 
                                    color=self.colors["primary"])
        ax.add_artist(quality_arc)
        
        # テキスト表示（中央）
        ax.text(0.5, 0.5, f'{overall_rating:.1f}/10', ha='center', va='center', 
              fontsize=16, fontweight='bold')
        
        # ラベル表示
        ax.text(0.5, 0.75, '総合評価', ha='center', va='center', fontsize=12)
        ax.text(0.5, 0.25, f'実行品質: {execution_quality:.1f}/10', ha='center', va='center', fontsize=10)
    
    def _plot_strengths_weaknesses(self, ax, strategy_evaluation):
        """強み弱みのテーブル"""
        # 強みと弱みの抽出
        strengths = strategy_evaluation.get('strengths', [])
        weaknesses = strategy_evaluation.get('weaknesses', [])
        
        # テーブル形式で表示
        ax.axis('off')
        
        if not strengths and not weaknesses:
            ax.text(0.5, 0.5, "強み・弱みの詳細データがありません", ha='center', va='center')
            return
        
        # テーブルヘッダー
        ax.text(0.25, 0.9, "強み", ha='center', va='center', fontsize=12, fontweight='bold', 
              color=self.colors["good"])
        ax.text(0.75, 0.9, "改善点", ha='center', va='center', fontsize=12, fontweight='bold', 
              color=self.colors["poor"])
        
        # 区切り線
        ax.axvline(x=0.5, ymin=0.1, ymax=0.9, color=self.colors["grid"], linestyle='-', linewidth=1)
        
        # 強みの表示
        for i, strength in enumerate(strengths[:3]):  # 最大3つ表示
            y_pos = 0.8 - i * 0.2
            area = strength.get('display_name', strength.get('area', ''))
            description = strength.get('description', '')
            
            text = f"{area}: {description}"
            if len(text) > 50:
                text = text[:47] + "..."
                
            ax.text(0.05, y_pos, "•", ha='left', va='center', fontsize=12, 
                  color=self.colors["good"])
            ax.text(0.08, y_pos, text, ha='left', va='center', fontsize=10)
        
        # 弱みの表示
        for i, weakness in enumerate(weaknesses[:3]):  # 最大3つ表示
            y_pos = 0.8 - i * 0.2
            area = weakness.get('display_name', weakness.get('area', ''))
            description = weakness.get('description', '')
            
            text = f"{area}: {description}"
            if len(text) > 50:
                text = text[:47] + "..."
                
            ax.text(0.55, y_pos, "•", ha='left', va='center', fontsize=12, 
                  color=self.colors["poor"])
            ax.text(0.58, y_pos, text, ha='left', va='center', fontsize=10)
    
    def plot_decision_point_details(self, decision_point: Dict,
                                  what_if_scenarios: List[Dict] = None,
                                  track_data: pd.DataFrame = None,
                                  title: str = "判断ポイント詳細分析") -> Figure:
        """
        個別の判断ポイントの詳細分析プロット
        
        Parameters
        ----------
        decision_point : Dict
            個別の判断ポイント情報
            以下のキーを含むべき:
            - type: ポイントの種類
            - time: 時刻
            - position: [latitude, longitude]
            - description: 説明
            - impact_score: 影響度スコア
        what_if_scenarios : List[Dict], optional
            代替シナリオのリスト, by default None
            各シナリオは以下のキーを含む辞書:
            - scenario: シナリオ名
            - outcome: 予想される結果
            - impact: 影響度
        track_data : pd.DataFrame, optional
            ポイント周辺のトラックデータ, by default None
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not decision_point:
            self.logger.warning("無効な判断ポイントデータ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効な判断ポイントデータがありません", ha='center', va='center')
            return fig
        
        # プロットの作成（2行1列のサブプロット）
        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        
        # 周辺トラックデータがある場合は2行2列、ない場合は1行2列
        if track_data is not None and 'latitude' in track_data.columns and 'longitude' in track_data.columns:
            gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1], hspace=0.3, wspace=0.3)
            
            # マップ表示（左下）
            ax_map = fig.add_subplot(gs[1, 0])
            self._plot_decision_point_map(ax_map, decision_point, track_data)
        else:
            gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.3)
        
        # 基本情報表示（左上または左全体）
        if track_data is not None:
            ax_info = fig.add_subplot(gs[0, 0])
        else:
            ax_info = fig.add_subplot(gs[0, 0])
        self._plot_decision_point_info(ax_info, decision_point)
        
        # 代替シナリオ表示（右側）
        ax_scenarios = fig.add_subplot(gs[:, 1])
        self._plot_what_if_scenarios(ax_scenarios, what_if_scenarios, decision_point)
        
        # 全体のタイトル
        point_type = decision_point.get('type', '')
        point_time = decision_point.get('time', '')
        if point_time:
            if isinstance(point_time, datetime):
                time_str = point_time.strftime('%H:%M:%S')
            else:
                time_str = str(point_time)
            title = f"{title} - {point_type} ({time_str})"
        
        fig.suptitle(title, fontsize=14)
        
        # タイトレイアウト
        plt.tight_layout()
        fig.subplots_adjust(top=0.9)  # タイトル用のスペース
        
        return fig
    
    def _plot_decision_point_info(self, ax, decision_point):
        """判断ポイントの基本情報表示"""
        ax.axis('off')
        
        # テキスト情報のフォーマット
        point_type = decision_point.get('type', 'Unknown')
        type_display = {
            'tack': 'タック',
            'gybe': 'ジャイブ',
            'layline': 'レイライン',
            'wind_shift': '風向変化',
            'cross_point': 'クロスポイント',
            'vmg_change': 'VMG変化',
            'start': 'スタート',
            'mark_rounding': 'マーク回航'
        }.get(point_type, point_type)
        
        time_display = ""
        point_time = decision_point.get('time', '')
        if point_time:
            if isinstance(point_time, datetime):
                time_display = point_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_display = str(point_time)
        
        impact_score = decision_point.get('impact_score', 0)
        confidence = decision_point.get('confidence', 0)
        
        # 影響度に基づく色
        if impact_score >= 7.5:
            impact_color = self.colors["good"] if impact_score > 0 else self.colors["poor"]
        elif impact_score >= 5.0:
            impact_color = self.colors["average"]
        else:
            impact_color = self.colors["poor"] if impact_score > 0 else self.colors["good"]
        
        # 詳細情報
        details = {}
        for key, value in decision_point.items():
            if key not in ['type', 'time', 'position', 'description', 'impact_score', 'confidence']:
                details[key] = value
        
        # 情報表示
        y_pos = 0.95
        line_height = 0.06
        
        # タイプと時刻
        ax.text(0.5, y_pos, f"判断タイプ: {type_display}", ha='center', va='top', 
              fontsize=12, fontweight='bold')
        y_pos -= line_height
        
        if time_display:
            ax.text(0.5, y_pos, f"時刻: {time_display}", ha='center', va='top', fontsize=10)
            y_pos -= line_height
        
        # 影響度
        ax.text(0.5, y_pos, f"影響度: {impact_score:.1f}/10", ha='center', va='top', 
              fontsize=11, color=impact_color, fontweight='bold')
        y_pos -= line_height
        
        if confidence > 0:
            ax.text(0.5, y_pos, f"信頼度: {confidence:.2f}", ha='center', va='top', fontsize=10)
            y_pos -= line_height
        
        # 説明
        y_pos -= line_height * 0.5
        ax.text(0.5, y_pos, "説明:", ha='center', va='top', fontsize=11, fontweight='bold')
        y_pos -= line_height
        
        description = decision_point.get('description', '')
        # 長い説明は折り返し
        if description:
            wrapped_desc = self._wrap_text(description, 40)
            for i, line in enumerate(wrapped_desc):
                ax.text(0.1, y_pos - i * line_height * 0.8, line, ha='left', va='top', fontsize=9)
            y_pos -= (len(wrapped_desc) * line_height * 0.8 + line_height)
        
        # 詳細情報
        if details:
            y_pos -= line_height * 0.5
            ax.text(0.5, y_pos, "詳細情報:", ha='center', va='top', fontsize=11, fontweight='bold')
            y_pos -= line_height
            
            for key, value in details.items():
                key_display = key.replace('_', ' ').title()
                # 数値は小数点以下2桁まで表示
                if isinstance(value, (int, float)):
                    value_display = f"{value:.2f}" if isinstance(value, float) else str(value)
                else:
                    value_display = str(value)
                
                ax.text(0.1, y_pos, f"{key_display}:", ha='left', va='top', fontsize=9)
                ax.text(0.5, y_pos, value_display, ha='left', va='top', fontsize=9)
                y_pos -= line_height * 0.8
    
    def _plot_decision_point_map(self, ax, decision_point, track_data):
        """判断ポイントの周辺マップ表示"""
        # ポイント位置の取得
        position = decision_point.get('position', None)
        if not position or len(position) != 2 or None in position:
            ax.text(0.5, 0.5, "有効な位置情報がありません", ha='center', va='center')
            ax.axis('off')
            return
        
        lat, lon = position
        
        # データフィルタリング
        time_point = decision_point.get('time', None)
        if time_point and 'timestamp' in track_data.columns:
            # 判断ポイントの前後1分間のデータ
            if isinstance(time_point, datetime):
                before_time = time_point - timedelta(minutes=1)
                after_time = time_point + timedelta(minutes=1)
                
                filtered_data = track_data[
                    (track_data['timestamp'] >= before_time) &
                    (track_data['timestamp'] <= after_time)
                ]
            else:
                # 時刻がdatetimeではない場合は全データを使用
                filtered_data = track_data
        else:
            # 時刻情報がない場合は、位置を中心に近傍のデータを抽出
            if track_data.empty:
                filtered_data = track_data
            else:
                # 計算された距離に基づいてフィルタリング
                track_data['distance'] = track_data.apply(
                    lambda row: self._calculate_distance(lat, lon, row['latitude'], row['longitude']),
                    axis=1
                )
                # 500m以内のデータ
                filtered_data = track_data[track_data['distance'] <= 500]
        
        # トラックデータのプロット
        if not filtered_data.empty:
            # 軌跡のプロット
            ax.plot(filtered_data['longitude'], filtered_data['latitude'], 
                   color=self.colors["primary"], linewidth=2, alpha=0.7)
            
            # 判断ポイントのハイライト
            ax.scatter(lon, lat, s=150, c=self.colors["highlight"], marker='o', 
                      edgecolors='black', linewidths=1, zorder=10)
        else:
            # データが少ない場合は単一ポイントのみ表示
            ax.scatter(lon, lat, s=150, c=self.colors["highlight"], marker='o', 
                      edgecolors='black', linewidths=1, zorder=10)
        
        # グラフの装飾
        ax.set_xlabel('経度')
        ax.set_ylabel('緯度')
        ax.set_title('位置情報', fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # アスペクト比の調整
        ax.set_aspect('equal')
    
    def _plot_what_if_scenarios(self, ax, what_if_scenarios, decision_point):
        """代替シナリオの表示"""
        ax.axis('off')
        
        if not what_if_scenarios:
            ax.text(0.5, 0.5, "代替シナリオデータがありません", ha='center', va='center')
            return
        
        # タイトル
        ax.text(0.5, 0.95, "代替シナリオ分析", ha='center', va='top', 
              fontsize=12, fontweight='bold')
        
        # 実際の判断の説明
        actual_decision = decision_point.get('description', '')
        if actual_decision:
            ax.text(0.5, 0.88, "実際の判断:", ha='center', va='top', fontsize=11)
            
            # 長いテキストは折り返し
            wrapped_text = self._wrap_text(actual_decision, 50)
            for i, line in enumerate(wrapped_text):
                ax.text(0.5, 0.83 - i * 0.04, line, ha='center', va='top', fontsize=9,
                      color=self.colors["primary"], fontweight='bold')
            
            # 区切り線
            y_line = 0.83 - len(wrapped_text) * 0.04 - 0.03
            ax.axhline(y=y_line, xmin=0.1, xmax=0.9, color=self.colors["grid"], 
                      linestyle='-', linewidth=1)
            
            start_y = y_line - 0.05
        else:
            start_y = 0.83
        
        # シナリオ表示
        for i, scenario in enumerate(what_if_scenarios[:3]):  # 最大3つ表示
            scenario_name = scenario.get('scenario', '')
            outcome = scenario.get('outcome', '')
            impact = scenario.get('impact', 0)
            
            # 影響度に基づく色
            if impact >= 0.7:
                impact_color = self.colors["good"]
            elif impact >= 0.4:
                impact_color = self.colors["average"]
            else:
                impact_color = self.colors["poor"]
            
            # シナリオ名
            y_pos = start_y - i * 0.25
            ax.text(0.1, y_pos, "シナリオ:", ha='left', va='top', fontsize=9, fontweight='bold')
            ax.text(0.3, y_pos, scenario_name, ha='left', va='top', fontsize=10, 
                  color=impact_color, fontweight='bold')
            
            # 影響度
            ax.text(0.1, y_pos - 0.05, "影響度:", ha='left', va='top', fontsize=9)
            ax.text(0.3, y_pos - 0.05, f"{impact:.2f}", ha='left', va='top', fontsize=9, 
                  color=impact_color)
            
            # 予想される結果
            ax.text(0.1, y_pos - 0.1, "予想結果:", ha='left', va='top', fontsize=9)
            
            # 長いテキストは折り返し
            wrapped_outcome = self._wrap_text(outcome, 40)
            for j, line in enumerate(wrapped_outcome):
                ax.text(0.3, y_pos - 0.1 - j * 0.04, line, ha='left', va='top', fontsize=9)
    
    def _wrap_text(self, text, max_chars):
        """テキストを指定文字数で折り返し"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + len(current_line) <= max_chars:
                current_line.append(word)
                current_length += len(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """2点間の距離を計算（メートル）"""
        # 地球の半径（メートル）
        R = 6371000
        
        # ラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 緯度経度の差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # ハーバーサイン公式
        a = (math.sin(dlat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        # 距離の計算
        distance = R * c
        
        return distance
    
    def get_base64_image(self, fig: Figure) -> str:
        """
        Matplotlib図をBase64エンコードされた画像に変換
        
        Parameters
        ----------
        fig : Figure
            Matplotlib Figure オブジェクト
            
        Returns
        -------
        str
            Base64エンコードされた画像データ
        """
        # 画像をメモリ上のバッファに保存
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
        buf.seek(0)
        
        # Base64エンコード
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        # HTMLで表示可能な形式に変換
        return f"data:image/png;base64,{img_str}"
