"""
sailing_data_processor.visualization.shift_visualization モジュール

風向シフトの検出結果を視覚化するための機能を提供します。
ヒートマップ、方位図、時系列グラフなどの視覚化手法を実装しています。
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

class ShiftVisualizer:
    """
    風向シフトの視覚化クラス
    
    風向シフトの検出結果を視覚的に表現する機能を提供します。
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
        self.logger = logging.getLogger("ShiftVisualizer")
    
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
                "shift_colors": ["#ff6b6b", "#4e9bff", "#ffcc00", "#8cff66"],
                "wind_field": cm.viridis,
                "shift_cmap": cm.coolwarm
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
                "shift_colors": ["#ff4d4d", "#1a53ff", "#ff9900", "#33cc33"],
                "wind_field": cm.viridis,
                "shift_cmap": cm.coolwarm
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
                "shift_colors": ["#d62728", "#1f77b4", "#ff7f0e", "#2ca02c"],
                "wind_field": cm.viridis,
                "shift_cmap": cm.coolwarm
            }
    
    def plot_wind_direction_timeline(self, wind_data: pd.DataFrame, 
                                   shifts: List[Dict] = None, 
                                   title: str = "風向の時系列と検出されたシフト") -> Figure:
        """
        風向の時系列と検出されたシフトのプロット
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風向データを含むデータフレーム
            必要なカラム:
            - timestamp: 時刻
            - wind_direction: 風向（度）
            - wind_speed: 風速（オプション）
        shifts : List[Dict], optional
            検出されたシフトのリスト, by default None
            各シフトは以下のキーを含む辞書:
            - timestamp: シフト発生時刻
            - before_direction: シフト前の風向
            - after_direction: シフト後の風向
            - direction_change: 風向変化量
            - confidence: 信頼度
            - shift_type: シフトタイプ
        title : str, optional
            グラフのタイトル, by default "風向の時系列と検出されたシフト"
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not isinstance(wind_data, pd.DataFrame) or wind_data.empty:
            self.logger.warning("無効な風向データ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効なデータがありません", ha='center', va='center')
            return fig
            
        if 'timestamp' not in wind_data.columns or 'wind_direction' not in wind_data.columns:
            self.logger.warning("必要なカラムがありません: timestamp, wind_direction")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "必要なカラムがありません: timestamp, wind_direction", ha='center', va='center')
            return fig
        
        # データを時間順にソート
        df = wind_data.copy().sort_values('timestamp')
        
        # プロットの作成
        fig, ax1 = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # 風向のプロット（主軸）
        ax1.plot(df['timestamp'], df['wind_direction'], 
               color=self.colors["primary"], linewidth=2, label="風向")
        
        # 風速のプロット（副軸、存在する場合）
        if 'wind_speed' in df.columns:
            ax2 = ax1.twinx()
            ax2.plot(df['timestamp'], df['wind_speed'], 
                   color=self.colors["secondary"], linewidth=1.5, 
                   linestyle='--', alpha=0.7, label="風速")
            ax2.set_ylabel('風速 (ノット)', color=self.colors["secondary"])
            ax2.tick_params(axis='y', labelcolor=self.colors["secondary"])
            
            # 凡例を結合
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            ax1.legend(loc='upper left')
        
        # シフトポイントのプロット
        if shifts:
            # シフトタイプごとのマーカー定義
            shift_markers = {
                "OSCILLATION": "o",   # 円
                "PERSISTENT": "s",    # 四角
                "TREND": "^",         # 三角形
                "PHASE": "d",         # ダイヤモンド
                "UNKNOWN": "x"        # バツ印
            }
            
            # シフトタイプごとのグループ分け
            shift_by_type = {}
            for shift in shifts:
                shift_type = shift.get('shift_type', 'UNKNOWN')
                if shift_type not in shift_by_type:
                    shift_by_type[shift_type] = []
                shift_by_type[shift_type].append(shift)
            
            # 各タイプごとにプロット
            for i, (shift_type, type_shifts) in enumerate(shift_by_type.items()):
                # 色とマーカーの選択
                color_idx = i % len(self.colors["shift_colors"])
                color = self.colors["shift_colors"][color_idx]
                marker = shift_markers.get(shift_type, "o")
                
                # 位置とサイズデータの準備
                timestamps = [shift['timestamp'] for shift in type_shifts]
                directions = [shift.get('after_direction', shift.get('before_direction', 0)) 
                             for shift in type_shifts]
                confidences = [shift.get('confidence', 0.5) for shift in type_shifts]
                
                # サイズを信頼度に基づいて調整（50〜200）
                sizes = [50 + c * 150 for c in confidences]
                
                # プロット
                scatter = ax1.scatter(timestamps, directions, s=sizes, 
                                    c=[color] * len(timestamps), 
                                    marker=marker, alpha=0.7, 
                                    edgecolors='black', linewidths=1,
                                    label=f"{shift_type}シフト")
                
                # 信頼度の高いシフトには注釈を追加
                for j, shift in enumerate(type_shifts):
                    if shift.get('confidence', 0) > 0.7:  # 高信頼度のシフトのみ
                        change = shift.get('direction_change', 0)
                        direction = "右" if change > 0 else "左"
                        ax1.annotate(f"{abs(change):.1f}°{direction}",
                                   (timestamps[j], directions[j]),
                                   xytext=(10, 0), textcoords='offset points',
                                   fontsize=9, color=self.colors["text"])
            
            # 凡例を更新
            handles, labels = ax1.get_legend_handles_labels()
            if 'wind_speed' in df.columns:
                handles = handles[:2] + handles[2::len(shift_by_type)]
                labels = labels[:2] + [l for l in labels[2:] if "シフト" in l]
            else:
                handles = handles[:1] + handles[1::len(shift_by_type)]
                labels = labels[:1] + [l for l in labels[1:] if "シフト" in l]
                
            ax1.legend(handles, labels, loc='upper left')
        
        # グラフの装飾
        ax1.set_xlabel('時刻')
        ax1.set_ylabel('風向 (度)', color=self.colors["primary"])
        ax1.tick_params(axis='y', labelcolor=self.colors["primary"])
        ax1.set_title(title)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 風向の範囲を0-360度に調整
        y_min, y_max = ax1.get_ylim()
        if y_max - y_min < 180:  # 表示範囲が狭い場合は自動調整
            ax1.set_ylim([max(0, y_min - 10), min(360, y_max + 10)])
        
        # X軸のフォーマット
        time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        if time_range < 3600:  # 1時間未満
            date_format = DateFormatter('%H:%M:%S')
        elif time_range < 86400:  # 1日未満
            date_format = DateFormatter('%H:%M')
        else:  # 1日以上
            date_format = DateFormatter('%m/%d %H:%M')
            
        ax1.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()  # 日付ラベルを見やすく
        
        # タイトの設定
        plt.tight_layout()
        
        return fig
    
    def plot_wind_rose_with_shifts(self, wind_data: pd.DataFrame, 
                                 shifts: List[Dict] = None, 
                                 title: str = "風配図とシフトパターン") -> Figure:
        """
        風配図と検出されたシフトのプロット
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風向データを含むデータフレーム
            必要なカラム:
            - wind_direction: 風向（度）
            - wind_speed: 風速（オプション）
        shifts : List[Dict], optional
            検出されたシフトのリスト, by default None
        title : str, optional
            グラフのタイトル, by default "風配図とシフトパターン"
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not isinstance(wind_data, pd.DataFrame) or wind_data.empty:
            self.logger.warning("無効な風向データ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効なデータがありません", ha='center', va='center')
            return fig
            
        if 'wind_direction' not in wind_data.columns:
            self.logger.warning("必要なカラム 'wind_direction' がありません")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "必要なカラム 'wind_direction' がありません", ha='center', va='center')
            return fig
        
        # 風速データがあるかどうか
        has_speed = 'wind_speed' in wind_data.columns
        
        # 方位角をラジアンに変換 (北=0、時計回り)
        dir_rad = np.radians(90 - wind_data['wind_direction'])
        
        # プロットの作成 (極座標)
        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='polar')
        
        # 風向のヒストグラムを作成
        bin_size = 10  # 10度刻み
        nbins = 360 // bin_size
        bin_edges = np.linspace(0, 2*np.pi, nbins+1)
        
        if has_speed:
            # 風速に基づいた風配図（風速をビンごとに集計）
            dir_deg = 90 - wind_data['wind_direction']  # 気象学的方位に変換
            dir_deg = (dir_deg + 360) % 360  # 0-360の範囲に正規化
            
            # 風速のビン
            speed_bins = [0, 5, 10, 15, 20, float('inf')]
            speed_labels = ["0-5", "5-10", "10-15", "15-20", "20+"]
            
            # 風向をビンに分類
            dir_bin = np.digitize(dir_deg, np.linspace(0, 360, nbins+1)) - 1
            
            # 風速をビンに分類
            speed_bin = np.digitize(wind_data['wind_speed'], speed_bins) - 1
            
            # ビンごとの集計
            bin_counts = np.zeros((nbins, len(speed_bins)-1))
            
            for i in range(len(dir_bin)):
                if dir_bin[i] < nbins and speed_bin[i] < len(speed_bins)-1:
                    bin_counts[dir_bin[i], speed_bin[i]] += 1
            
            # 各方位のトータルを計算
            bin_totals = np.sum(bin_counts, axis=1)
            bin_totals = np.where(bin_totals == 0, 1, bin_totals)  # ゼロ除算防止
            
            # スタックドバープロット用の準備
            bottoms = np.zeros(nbins)
            
            # 風速ビンごとにプロット（積み上げ）
            for i, (label, color) in enumerate(zip(speed_labels, 
                                               plt.cm.viridis(np.linspace(0, 1, len(speed_labels))))):
                heights = bin_counts[:, i] / bin_totals.max() * 100
                
                # バープロット（極座標）
                bars = ax.bar(np.linspace(0, 2*np.pi, nbins, endpoint=False), 
                            heights, width=2*np.pi/nbins, bottom=bottoms,
                            color=color, alpha=0.7, label=f"{label} ノット")
                
                bottoms += heights
        else:
            # 単純な風向ヒストグラム
            counts, _ = np.histogram(dir_rad, bins=bin_edges)
            
            # 正規化（％表示）
            counts = counts / counts.max() * 100
            
            # バープロット（極座標）
            bars = ax.bar(bin_edges[:-1], counts, width=2*np.pi/nbins, 
                        color=self.colors["primary"], alpha=0.7)
        
        # シフトの表示（矢印）
        if shifts:
            # 信頼度と重要度に基づいてシフトをフィルタ・ソート
            filtered_shifts = [s for s in shifts if s.get('confidence', 0) > 0.5]
            filtered_shifts.sort(key=lambda s: s.get('confidence', 0) * s.get('significance', 1), 
                               reverse=True)
            
            # 最大10件まで表示
            top_shifts = filtered_shifts[:10]
            
            for shift in top_shifts:
                before_dir = shift.get('before_direction', 0)
                after_dir = shift.get('after_direction', 0)
                
                # 方位を極座標形式に変換
                before_rad = np.radians(90 - before_dir)
                after_rad = np.radians(90 - after_dir)
                
                # 信頼度に基づいた透明度
                alpha = min(1.0, shift.get('confidence', 0.5) + 0.3)
                
                # シフトタイプに基づいた色
                shift_type = shift.get('shift_type', 'UNKNOWN')
                if shift_type == "PERSISTENT":
                    color = self.colors["shift_colors"][0]
                elif shift_type == "TREND":
                    color = self.colors["shift_colors"][1]
                elif shift_type == "OSCILLATION":
                    color = self.colors["shift_colors"][2]
                else:
                    color = self.colors["shift_colors"][3]
                
                # 始点と終点の座標（極座標→直交座標）
                # 矢印の長さをスケール調整
                arrow_scale = 0.8  # 円の半径に対する割合
                
                x_start = arrow_scale * np.cos(before_rad)
                y_start = arrow_scale * np.sin(before_rad)
                x_end = arrow_scale * np.cos(after_rad)
                y_end = arrow_scale * np.sin(after_rad)
                
                # 矢印の描画（直交座標系）
                ax_cartesian = fig.add_axes(ax.get_position(), frameon=False)
                ax_cartesian.set_xlim(-1.1, 1.1)
                ax_cartesian.set_ylim(-1.1, 1.1)
                ax_cartesian.axis('off')
                
                ax_cartesian.annotate("", xy=(x_end, y_end), xytext=(x_start, y_start),
                                   arrowprops=dict(arrowstyle="->", color=color, 
                                                 linewidth=2, alpha=alpha))
                
                # シフト量の表示（大きなシフトのみ）
                if abs(shift.get('direction_change', 0)) > 10:
                    # テキストの位置（矢印の中間）
                    x_text = (x_start + x_end) / 2
                    y_text = (y_start + y_end) / 2
                    
                    # シフト方向と大きさ
                    change = shift.get('direction_change', 0)
                    direction = "右" if change > 0 else "左"
                    
                    # テキスト表示
                    ax_cartesian.text(x_text, y_text, f"{abs(change):.0f}°{direction}", 
                                   color=color, fontsize=9, fontweight='bold',
                                   ha='center', va='center', alpha=alpha)
        
        # 方位の設定（北が上になるように）
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)  # 時計回り
        
        # 方位ラベル
        ax.set_xticks(np.radians([0, 45, 90, 135, 180, 225, 270, 315]))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        
        # 凡例とグリッド
        if has_speed:
            ax.legend(loc='lower right', bbox_to_anchor=(1.2, 0.1))
        
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # タイトル
        plt.title(title)
        
        return fig
    
    def plot_shift_analysis_dashboard(self, wind_data: pd.DataFrame, 
                                     shifts: List[Dict], 
                                     analysis_results: Dict = None) -> Figure:
        """
        風向シフト分析ダッシュボードのプロット
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風向データを含むデータフレーム
        shifts : List[Dict]
            検出されたシフトのリスト
        analysis_results : Dict, optional
            パターン分析結果, by default None
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # プロットの作成（2行2列のサブプロット）
        fig = plt.figure(figsize=(self.figure_size[0]*2, self.figure_size[1]*2), dpi=self.dpi)
        gs = fig.add_gridspec(2, 2, wspace=0.3, hspace=0.4)
        
        # 風向の時系列プロット（左上）
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_wind_timeline_subplot(ax1, wind_data, shifts)
        
        # 風配図（右上）
        ax2 = fig.add_subplot(gs[0, 1], projection='polar')
        self._plot_wind_rose_subplot(ax2, wind_data, shifts)
        
        # シフト分析結果（左下）
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_shift_summary_subplot(ax3, shifts, analysis_results)
        
        # パターン分析と予測（右下）
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_pattern_analysis_subplot(ax4, wind_data, analysis_results)
        
        # 全体のタイトル
        title = "風向シフト総合分析ダッシュボード"
        if analysis_results and "pattern_type" in analysis_results.get("aggregate", {}):
            pattern = analysis_results["aggregate"]["pattern_type"]
            pattern_ja = {
                "periodic": "周期的", 
                "trending": "トレンド", 
                "oscillating": "振動",
                "complex": "複合", 
                "trend_with_oscillations": "トレンド+振動", 
                "stable": "安定", 
                "mixed": "混合"
            }.get(pattern, "不明")
            
            title += f" - パターン: {pattern_ja}"
            
        fig.suptitle(title, fontsize=16)
        
        # タイトの設定
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # suptitleのためのスペースを確保
        
        return fig
    
    def _plot_wind_timeline_subplot(self, ax, wind_data, shifts):
        """風向の時系列プロット（サブプロット用）"""
        # データを時間順にソート
        df = wind_data.copy().sort_values('timestamp')
        
        # 風向のプロット
        ax.plot(df['timestamp'], df['wind_direction'], 
              color=self.colors["primary"], linewidth=2)
        
        # シフトポイントのプロット
        if shifts:
            # シフトの重要度でサイズを調整
            sizes = [30 + s.get('significance', 0.5) * 100 if 'significance' in s 
                   else 30 + s.get('confidence', 0.5) * 100 for s in shifts]
            
            # シフトタイプ別の色分け
            colors = []
            for shift in shifts:
                shift_type = shift.get('shift_type', 'UNKNOWN')
                if shift_type == "PERSISTENT":
                    colors.append(self.colors["shift_colors"][0])
                elif shift_type == "TREND":
                    colors.append(self.colors["shift_colors"][1])
                elif shift_type == "OSCILLATION":
                    colors.append(self.colors["shift_colors"][2])
                else:
                    colors.append(self.colors["shift_colors"][3])
            
            # シフトポイントのプロット
            ax.scatter([s['timestamp'] for s in shifts], 
                      [s.get('after_direction', s.get('before_direction', 0)) for s in shifts], 
                      s=sizes, c=colors, alpha=0.7, edgecolors='black', linewidths=1)
        
        # グラフの装飾
        ax.set_xlabel('時刻')
        ax.set_ylabel('風向 (度)')
        ax.set_title('風向の時系列とシフトポイント')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # X軸のフォーマット
        time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        if time_range < 3600:  # 1時間未満
            date_format = DateFormatter('%H:%M:%S')
        elif time_range < 86400:  # 1日未満
            date_format = DateFormatter('%H:%M')
        else:  # 1日以上
            date_format = DateFormatter('%m/%d %H:%M')
            
        ax.xaxis.set_major_formatter(date_format)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    
    def _plot_wind_rose_subplot(self, ax, wind_data, shifts):
        """風配図のプロット（サブプロット用）"""
        # 方位角をラジアンに変換
        dir_rad = np.radians(90 - wind_data['wind_direction'])
        
        # 風向のヒストグラムを作成
        bin_size = 15  # 15度刻み
        nbins = 360 // bin_size
        bin_edges = np.linspace(0, 2*np.pi, nbins+1)
        counts, _ = np.histogram(dir_rad, bins=bin_edges)
        
        # 正規化（％表示）
        counts = counts / counts.max() * 100
        
        # バープロット（極座標）
        ax.bar(bin_edges[:-1], counts, width=2*np.pi/nbins, 
             color=self.colors["primary"], alpha=0.7)
        
        # 主要なシフト（上位5件）をベクトルで表示
        if shifts:
            # 信頼度と重要度でソート
            sorted_shifts = sorted(shifts, 
                                 key=lambda s: s.get('confidence', 0) * s.get('significance', 1), 
                                 reverse=True)
            
            for shift in sorted_shifts[:5]:
                before_dir = shift.get('before_direction', 0)
                after_dir = shift.get('after_direction', 0)
                
                # 方位を極座標形式に変換
                before_rad = np.radians(90 - before_dir)
                after_rad = np.radians(90 - after_dir)
                
                # シフトの大きさに応じた矢印の長さ
                scale = min(1.0, abs(shift.get('direction_change', 0)) / 180)
                arrow_length = 0.3 + scale * 0.5  # 0.3-0.8の範囲
                
                # 矢印の描画
                ax.annotate("", xy=(after_rad, arrow_length * 100), 
                          xytext=(before_rad, arrow_length * 100),
                          arrowprops=dict(arrowstyle="->", 
                                        color=self.colors["highlight"], 
                                        linewidth=2))
        
        # 方位の設定
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        
        # 方位ラベル
        ax.set_xticks(np.radians([0, 45, 90, 135, 180, 225, 270, 315]))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        
        # グリッド
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # タイトル
        ax.set_title('風配図とシフトパターン')
    
    def _plot_shift_summary_subplot(self, ax, shifts, analysis_results):
        """シフト分析結果のプロット（サブプロット用）"""
        # シフトがない場合
        if not shifts:
            ax.text(0.5, 0.5, "検出されたシフトがありません", 
                  ha='center', va='center', fontsize=12)
            ax.axis('off')
            return
            
        # シフトタイプの集計
        shift_types = {}
        for shift in shifts:
            shift_type = shift.get('shift_type', 'UNKNOWN')
            shift_types[shift_type] = shift_types.get(shift_type, 0) + 1
        
        # 信頼度の分布
        confidences = [shift.get('confidence', 0) for shift in shifts]
        
        # 変化量の分布
        changes = [abs(shift.get('direction_change', 0)) for shift in shifts]
        
        # 左側：シフトタイプの円グラフ
        ax.pie(shift_types.values(), labels=shift_types.keys(), autopct='%1.1f%%',
             colors=self.colors["shift_colors"][:len(shift_types)],
             wedgeprops={'edgecolor': 'white'})
        
        # テキスト情報の追加
        info_text = f"検出シフト数: {len(shifts)}\n"
        info_text += f"平均信頼度: {np.mean(confidences):.2f}\n"
        info_text += f"平均変化量: {np.mean(changes):.1f}°\n"
        
        if analysis_results:
            aggregate = analysis_results.get("aggregate", {})
            if "stability" in aggregate:
                stability = aggregate["stability"] * 100
                info_text += f"風の安定性: {stability:.1f}%\n"
                
            if "predictability" in aggregate:
                pred = aggregate["predictability"] * 100
                info_text += f"予測可能性: {pred:.1f}%\n"
        
        # タイトルとテキスト情報
        ax.set_title('シフト分析サマリー')
        ax.text(1.1, 0.5, info_text, transform=ax.transAxes, 
              fontsize=10, verticalalignment='center')
    
    def _plot_pattern_analysis_subplot(self, ax, wind_data, analysis_results):
        """パターン分析と予測のプロット（サブプロット用）"""
        # 分析結果がない場合
        if not analysis_results:
            ax.text(0.5, 0.5, "パターン分析結果がありません", 
                  ha='center', va='center', fontsize=12)
            ax.axis('off')
            return
            
        # テキスト情報の表示
        y_pos = 0.95
        line_height = 0.06
        
        # タイトル
        ax.text(0.5, y_pos, "風パターン分析と予測", ha='center', va='top', 
              fontsize=12, fontweight='bold')
        y_pos -= line_height * 1.5
        
        # パターンタイプ
        if "aggregate" in analysis_results and "pattern_type" in analysis_results["aggregate"]:
            pattern = analysis_results["aggregate"]["pattern_type"]
            pattern_ja = {
                "periodic": "周期的", 
                "trending": "トレンド", 
                "oscillating": "振動",
                "complex": "複合", 
                "trend_with_oscillations": "トレンド+振動", 
                "stable": "安定", 
                "mixed": "混合"
            }.get(pattern, "不明")
            
            ax.text(0.5, y_pos, f"パターンタイプ: {pattern_ja}", 
                  ha='center', va='top', fontsize=11)
            y_pos -= line_height
        
        # 周期性
        if "periodicity" in analysis_results and analysis_results["periodicity"].get("has_periodicity", False):
            period = analysis_results["periodicity"].get("main_period_minutes", 0)
            strength = analysis_results["periodicity"].get("pattern_strength", 0) * 100
            
            ax.text(0.5, y_pos, f"周期性: {period:.1f}分 (強度: {strength:.1f}%)", 
                  ha='center', va='top', fontsize=10)
            y_pos -= line_height
        
        # トレンド
        if "trend" in analysis_results and analysis_results["trend"].get("has_trend", False):
            rate = analysis_results["trend"].get("direction_trend_rate", 0)
            direction = "右回り" if rate > 0 else "左回り"
            strength = analysis_results["trend"].get("trend_strength", 0) * 100
            
            ax.text(0.5, y_pos, f"トレンド: {abs(rate):.2f}°/分 {direction} (強度: {strength:.1f}%)", 
                  ha='center', va='top', fontsize=10)
            y_pos -= line_height
        
        # 振動
        if "oscillations" in analysis_results and analysis_results["oscillations"].get("has_oscillations", False):
            amp = analysis_results["oscillations"].get("oscillation_amplitude", 0)
            freq = analysis_results["oscillations"].get("oscillation_frequency", 0)
            
            period_sec = 60 / freq if freq > 0 else 0
            
            ax.text(0.5, y_pos, f"振動: 振幅 ±{amp:.1f}° (周期: {period_sec:.1f}秒)", 
                  ha='center', va='top', fontsize=10)
            y_pos -= line_height
        
        # 洞察と推奨事項
        y_pos -= line_height
        ax.text(0.5, y_pos, "主要な洞察:", ha='center', va='top', 
              fontsize=11, fontweight='bold')
        y_pos -= line_height
        
        if "aggregate" in analysis_results and "key_insights" in analysis_results["aggregate"]:
            insights = analysis_results["aggregate"]["key_insights"]
            for insight in insights[:3]:  # 最大3つまで表示
                ax.text(0.1, y_pos, "•", ha='left', va='top', fontsize=10)
                ax.text(0.15, y_pos, insight, ha='left', va='top', fontsize=9)
                y_pos -= line_height
        
        y_pos -= line_height * 0.5
        ax.text(0.5, y_pos, "戦略的推奨事項:", ha='center', va='top', 
              fontsize=11, fontweight='bold')
        y_pos -= line_height
        
        if "recommendations" in analysis_results and "strategy_recommendations" in analysis_results["recommendations"]:
            recommendations = analysis_results["recommendations"]["strategy_recommendations"]
            for rec in recommendations[:3]:  # 最大3つまで表示
                ax.text(0.1, y_pos, "•", ha='left', va='top', fontsize=10)
                
                # 長いテキストの場合は省略
                if len(rec) > 70:
                    rec_text = rec[:67] + "..."
                else:
                    rec_text = rec
                    
                ax.text(0.15, y_pos, rec_text, ha='left', va='top', fontsize=9)
                y_pos -= line_height
        
        # 軸を非表示
        ax.axis('off')
    
    def plot_shift_heatmap(self, lat_lon_data: pd.DataFrame, 
                          shifts: List[Dict] = None,
                          title: str = "風向シフトの地理的分布") -> Figure:
        """
        風向シフトの地理的分布ヒートマップ
        
        Parameters
        ----------
        lat_lon_data : pd.DataFrame
            位置データを含むデータフレーム
            必要なカラム:
            - latitude, longitude: 位置
            - wind_direction: 風向（オプション）
        shifts : List[Dict], optional
            検出されたシフトのリスト
            各シフトは以下のキーを含む必要があります:
            - position: (latitude, longitude)の形式での位置情報
        title : str, optional
            グラフのタイトル
            
        Returns
        -------
        Figure
            Matplotlib Figure オブジェクト
        """
        # 入力データの検証
        if not isinstance(lat_lon_data, pd.DataFrame) or lat_lon_data.empty:
            self.logger.warning("無効な位置データ")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "有効な位置データがありません", ha='center', va='center')
            return fig
            
        if 'latitude' not in lat_lon_data.columns or 'longitude' not in lat_lon_data.columns:
            self.logger.warning("必要なカラムがありません: latitude, longitude")
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            ax.text(0.5, 0.5, "必要なカラムがありません: latitude, longitude", ha='center', va='center')
            return fig
        
        # プロットの作成
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        # トラックデータのプロット
        ax.scatter(lat_lon_data['longitude'], lat_lon_data['latitude'], 
                 s=10, c='gray', alpha=0.3)
        
        # 風向データがある場合、風向に色付け
        if 'wind_direction' in lat_lon_data.columns:
            # 風向データのサンプリング（密度を下げる）
            if len(lat_lon_data) > 100:
                sample_idx = np.linspace(0, len(lat_lon_data) - 1, 100, dtype=int)
                sampled_data = lat_lon_data.iloc[sample_idx]
            else:
                sampled_data = lat_lon_data
            
            # 風向ベクトルの描画
            for _, row in sampled_data.iterrows():
                # 風向の単位ベクトル（風が吹いてくる方向）
                wind_rad = np.radians(90 - row['wind_direction'])  # 気象学的方位に変換
                dx = np.cos(wind_rad) * 0.0005  # スケール調整
                dy = np.sin(wind_rad) * 0.0005  # スケール調整
                
                # ベクトルの描画
                ax.arrow(row['longitude'], row['latitude'], dx, dy, 
                       head_width=0.0002, head_length=0.0002, 
                       color='blue', alpha=0.5)
        
        # シフトポイントのヒートマップ（カーネル密度推定）
        if shifts and any('position' in s for s in shifts):
            from scipy.stats import gaussian_kde
            
            # 位置情報があるシフトのみ抽出
            shifts_with_pos = [s for s in shifts if 'position' in s and s['position'][0] is not None]
            
            if shifts_with_pos:
                # シフトの密度を計算
                shift_points = np.array([[s['position'][1], s['position'][0]] for s in shifts_with_pos])
                
                # シフトがあまりにも少ない場合はヒートマップではなく単純な散布図
                if len(shift_points) < 10:
                    # 散布図によるシフトの表示
                    for shift in shifts_with_pos:
                        lat, lon = shift['position']
                        confidence = shift.get('confidence', 0.5)
                        significance = shift.get('significance', confidence)
                        size = 50 + significance * 150  # サイズは重要度に比例
                        
                        # シフトタイプ別の色
                        shift_type = shift.get('shift_type', 'UNKNOWN')
                        if shift_type == "PERSISTENT":
                            color = self.colors["shift_colors"][0]
                        elif shift_type == "TREND":
                            color = self.colors["shift_colors"][1]
                        elif shift_type == "OSCILLATION":
                            color = self.colors["shift_colors"][2]
                        else:
                            color = self.colors["shift_colors"][3]
                        
                        # シフトマーカーのプロット
                        ax.scatter(lon, lat, s=size, c=color, marker='o', 
                                 edgecolors='black', linewidths=1, alpha=0.7,
                                 zorder=10)
                else:
                    # カーネル密度推定による滑らかなヒートマップ
                    try:
                        # グリッドの作成
                        lon_min, lon_max = lat_lon_data['longitude'].min(), lat_lon_data['longitude'].max()
                        lat_min, lat_max = lat_lon_data['latitude'].min(), lat_lon_data['latitude'].max()
                        
                        # マージンの追加
                        lon_margin = (lon_max - lon_min) * 0.05
                        lat_margin = (lat_max - lat_min) * 0.05
                        
                        lon_min -= lon_margin
                        lon_max += lon_margin
                        lat_min -= lat_margin
                        lat_max += lat_margin
                        
                        # 細かいグリッド
                        lon_grid, lat_grid = np.mgrid[lon_min:lon_max:100j, lat_min:lat_max:100j]
                        positions = np.vstack([lon_grid.ravel(), lat_grid.ravel()])
                        
                        # カーネル密度推定
                        kde = gaussian_kde(shift_points.T)
                        z = kde(positions)
                        
                        # 結果の整形
                        z = z.reshape(lon_grid.shape)
                        
                        # コンターヒートマップの描画
                        contour = ax.contourf(lon_grid, lat_grid, z.T, cmap=self.colors["shift_cmap"], 
                                           alpha=0.7, levels=15)
                        
                        # カラーバー
                        cbar = plt.colorbar(contour, ax=ax, shrink=0.8)
                        cbar.set_label('シフト密度')
                        
                        # 重要なシフトのマーカー表示
                        important_shifts = [s for s in shifts_with_pos 
                                         if s.get('significance', 0) > 0.7 or s.get('confidence', 0) > 0.8]
                        
                        for shift in important_shifts[:10]:  # 最大10個まで表示
                            lat, lon = shift['position']
                            confidence = shift.get('confidence', 0.5)
                            size = 50 + confidence * 100
                            
                            ax.scatter(lon, lat, s=size, c='yellow', marker='*', 
                                     edgecolors='black', linewidths=1, alpha=0.9,
                                     zorder=10)
                            
                    except Exception as e:
                        self.logger.warning(f"ヒートマップ作成中にエラーが発生しました: {str(e)}")
                        
                        # エラー時は単純な散布図に切り替え
                        for shift in shifts_with_pos:
                            lat, lon = shift['position']
                            confidence = shift.get('confidence', 0.5)
                            size = 50 + confidence * 150
                            
                            ax.scatter(lon, lat, s=size, c='red', marker='o', 
                                     alpha=0.7, zorder=10)
        
        # グラフの装飾
        ax.set_xlabel('経度')
        ax.set_ylabel('緯度')
        ax.set_title(title)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # アスペクト比の調整
        # 緯度・経度は同じスケールになるよう調整
        ax.set_aspect('equal')
        
        # 凡例
        from matplotlib.lines import Line2D
        
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                 label='航跡データ', alpha=0.3, markersize=8)
        ]
        
        if shifts:
            legend_elements.extend([
                Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors["shift_colors"][0], 
                     label='持続的シフト', markersize=10),
                Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors["shift_colors"][1], 
                     label='トレンドシフト', markersize=10),
                Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors["shift_colors"][2], 
                     label='振動シフト', markersize=10)
            ])
            
            # シフトが多数ある場合はヒートマップの凡例も追加
            if len([s for s in shifts if 'position' in s and s['position'][0] is not None]) >= 10:
                legend_elements.append(
                    Line2D([0], [0], marker='*', color='w', markerfacecolor='yellow', 
                         label='重要なシフト', markersize=12)
                )
        
        ax.legend(handles=legend_elements, loc='upper right')
        
        return fig
    
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
