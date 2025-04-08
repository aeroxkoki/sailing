"""
レース後戦略分析エンジン

コンテキスト認識型の戦略評価、重要ポイント特定、スキルレベル対応改善提案機能を提供します。
レースデータを包括的に分析し、セーラーの戦略と意思決定を評価・改善するための洞察を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
import logging
import json
import os

# 内部モジュールのインポート
from ..strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
from .strategy_evaluator import StrategyEvaluator
from .decision_points_analyzer import DecisionPointsAnalyzer
from .improvement_advisor import ImprovementAdvisor

# ロガーの設定
logger = logging.getLogger(__name__)

class PostRaceAnalyzer:
    """
    レース後戦略分析エンジン
    
    レースデータを包括的に分析し、戦略評価、重要ポイント特定、改善提案を行います。
    """
    
    def __init__(self, sailor_profile=None, race_context=None, analysis_level="advanced"):
        """
        初期化
        
        Parameters
        ----------
        sailor_profile : dict, optional
            セーラープロファイル情報, by default None
        race_context : dict, optional
            レース状況情報, by default None
        analysis_level : str, optional
            分析レベル ("basic", "intermediate", "advanced", "professional"), by default "advanced"
        """
        self.sailor_profile = sailor_profile or {}
        self.race_context = race_context or {}
        self.analysis_level = analysis_level
        
        # 各分析モジュールの初期化
        self.strategy_evaluator = StrategyEvaluator(sailor_profile, race_context)
        self.decision_analyzer = DecisionPointsAnalyzer(analysis_level=analysis_level)
        self.improvement_advisor = ImprovementAdvisor(sailor_profile, analysis_level=analysis_level)
        
        # 分析結果のキャッシュ
        self._analysis_cache = {}
        
        logger.info(f"PostRaceAnalyzer initialized with analysis level: {analysis_level}")
    
    def analyze_race(self, track_data, wind_data, competitor_data=None, course_data=None):
        """
        レースデータを分析
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        wind_data : DataFrame
            風データ
        competitor_data : DataFrame, optional
            競合艇データ, by default None
        course_data : dict, optional
            コース情報, by default None
            
        Returns
        -------
        dict
            分析結果
        """
        # キャッシュキーの生成
        cache_key = self._generate_cache_key(track_data, wind_data, competitor_data, course_data)
        
        # キャッシュ確認
        if cache_key in self._analysis_cache:
            logger.info("Using cached analysis result")
            return self._analysis_cache[cache_key]
        
        logger.info("Starting race analysis...")
        
        # レース文脈の強化
        self._enhance_race_context(track_data, wind_data, competitor_data, course_data)
        
        # 1. 戦略評価
        logger.info("Evaluating racing strategy...")
        strategy_evaluation = self.strategy_evaluator.evaluate_strategy(
            track_data, wind_data, competitor_data, course_data
        )
        
        # 2. 重要ポイント特定
        logger.info("Identifying key decision points...")
        decision_points = self.decision_analyzer.identify_key_points(
            track_data, wind_data, strategy_evaluation, course_data
        )
        
        # 3. 改善提案
        logger.info("Generating improvement suggestions...")
        improvement_suggestions = self.improvement_advisor.generate_suggestions(
            strategy_evaluation, decision_points, self.race_context
        )
        
        # 分析結果の統合
        analysis_result = {
            "strategy_evaluation": strategy_evaluation,
            "decision_points": decision_points,
            "improvement_suggestions": improvement_suggestions,
            "summary": self._generate_summary(strategy_evaluation, decision_points, improvement_suggestions),
            "race_context": self.race_context,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_level": self.analysis_level
        }
        
        # キャッシュに保存
        self._analysis_cache[cache_key] = analysis_result
        
        logger.info("Race analysis completed successfully")
        return analysis_result
    
    def _generate_cache_key(self, track_data, wind_data, competitor_data, course_data):
        """キャッシュキーの生成"""
        # トラックデータのハッシュ値
        track_hash = hash(tuple(track_data.index)) if isinstance(track_data, pd.DataFrame) else hash(str(track_data))
        
        # 風データのハッシュ値
        wind_hash = hash(tuple(wind_data.index)) if isinstance(wind_data, pd.DataFrame) else hash(str(wind_data))
        
        # 競合データのハッシュ値（存在する場合）
        competitor_hash = 0
        if competitor_data is not None:
            competitor_hash = hash(tuple(competitor_data.index)) if isinstance(competitor_data, pd.DataFrame) else hash(str(competitor_data))
        
        # コースデータのハッシュ値（存在する場合）
        course_hash = 0
        if course_data is not None:
            course_hash = hash(str(course_data))
        
        # 解析レベルと組み合わせて最終キーを生成
        return f"{track_hash}_{wind_hash}_{competitor_hash}_{course_hash}_{self.analysis_level}"
    
    def _enhance_race_context(self, track_data, wind_data, competitor_data, course_data):
        """レース文脈情報の強化"""
        
        # 既存のコンテキスト情報を保持
        enhanced_context = self.race_context.copy()
        
        # トラックデータからの情報抽出
        if isinstance(track_data, pd.DataFrame) and not track_data.empty:
            # レース期間
            if "timestamp" in track_data.columns:
                enhanced_context["race_start_time"] = track_data["timestamp"].min()
                enhanced_context["race_end_time"] = track_data["timestamp"].max()
                enhanced_context["race_duration"] = (
                    track_data["timestamp"].max() - track_data["timestamp"].min()
                ).total_seconds()
            
            # 平均・最大速度
            if "speed" in track_data.columns:
                enhanced_context["avg_speed"] = float(track_data["speed"].mean())
                enhanced_context["max_speed"] = float(track_data["speed"].max())
            
            # 移動距離
            if all(col in track_data.columns for col in ["latitude", "longitude"]):
                # 簡易的な距離計算
                enhanced_context["total_distance"] = self._calculate_total_distance(track_data)
        
        # 風データからの情報抽出
        if isinstance(wind_data, pd.DataFrame) and not wind_data.empty:
            if "wind_direction" in wind_data.columns:
                enhanced_context["avg_wind_direction"] = float(wind_data["wind_direction"].mean())
                
                # 風向変化の範囲
                min_dir = float(wind_data["wind_direction"].min())
                max_dir = float(wind_data["wind_direction"].max())
                
                # 方位角の特殊性を考慮（0と359は近い）
                if max_dir - min_dir > 180:
                    wind_dirs = wind_data["wind_direction"].values
                    wind_dirs_rad = np.radians(wind_dirs)
                    mean_sin = np.mean(np.sin(wind_dirs_rad))
                    mean_cos = np.mean(np.cos(wind_dirs_rad))
                    mean_dir = np.degrees(np.arctan2(mean_sin, mean_cos))
                    if mean_dir < 0:
                        mean_dir += 360
                    enhanced_context["avg_wind_direction"] = float(mean_dir)
                    
                    # 変動範囲の再計算
                    diffs = np.array([angle_difference(d, mean_dir) for d in wind_dirs])
                    enhanced_context["wind_direction_range"] = float(np.ptp(diffs))
                else:
                    enhanced_context["wind_direction_range"] = max_dir - min_dir
            
            if "wind_speed" in wind_data.columns:
                enhanced_context["avg_wind_speed"] = float(wind_data["wind_speed"].mean())
                enhanced_context["max_wind_speed"] = float(wind_data["wind_speed"].max())
                enhanced_context["wind_speed_range"] = float(
                    wind_data["wind_speed"].max() - wind_data["wind_speed"].min()
                )
        
        # 競合艇データからの情報抽出
        if competitor_data is not None and isinstance(competitor_data, pd.DataFrame) and not competitor_data.empty:
            enhanced_context["competitor_count"] = len(competitor_data["boat_id"].unique()) if "boat_id" in competitor_data.columns else 1
        
        # コースデータからの情報抽出
        if course_data is not None:
            if "marks" in course_data:
                enhanced_context["mark_count"] = len(course_data["marks"])
            
            if "course_type" in course_data:
                enhanced_context["course_type"] = course_data["course_type"]
            
            if "wind_conditions" in course_data:
                enhanced_context.update(course_data["wind_conditions"])
        
        # 文脈情報の更新
        self.race_context = enhanced_context
        logger.debug(f"Enhanced race context: {json.dumps(enhanced_context, default=str)}")
    
    def _calculate_total_distance(self, track_data):
        """トラックデータから総移動距離を計算"""
        if len(track_data) < 2:
            return 0.0
        
        total_distance = 0.0
        prev_lat = track_data.iloc[0]["latitude"]
        prev_lon = track_data.iloc[0]["longitude"]
        
        for _, row in track_data.iloc[1:].iterrows():
            lat = row["latitude"]
            lon = row["longitude"]
            
            # ハーバーサイン公式による距離計算
            distance = haversine_distance(prev_lat, prev_lon, lat, lon)
            total_distance += distance
            
            prev_lat = lat
            prev_lon = lon
        
        return total_distance
    
    def _generate_summary(self, strategy_evaluation, decision_points, improvement_suggestions):
        """分析結果サマリーの生成"""
        summary = {
            "overall_rating": strategy_evaluation.get("overall_rating", 0),
            "strengths": strategy_evaluation.get("strengths", [])[:3],  # 上位3つの強み
            "weaknesses": strategy_evaluation.get("weaknesses", [])[:3],  # 上位3つの弱み
            "critical_decisions": [],
            "key_improvement_areas": [],
            "wind_assessment": strategy_evaluation.get("wind_assessment", ""),
            "positioning_assessment": strategy_evaluation.get("positioning_assessment", ""),
            "execution_quality": strategy_evaluation.get("execution_quality", 0),
        }
        
        # 重要決断ポイントの抽出
        if decision_points and "high_impact_points" in decision_points:
            critical_decisions = []
            for point in decision_points["high_impact_points"][:3]:  # 上位3つの重要ポイント
                critical_decisions.append({
                    "time": point.get("time", ""),
                    "type": point.get("type", ""),
                    "description": point.get("description", ""),
                    "impact_score": point.get("impact_score", 0)
                })
            summary["critical_decisions"] = critical_decisions
        
        # 重点改善領域の抽出
        if improvement_suggestions and "priority_areas" in improvement_suggestions:
            key_areas = []
            for area in improvement_suggestions["priority_areas"][:3]:  # 上位3つの改善領域
                key_areas.append({
                    "area": area.get("area", ""),
                    "description": area.get("description", ""),
                    "priority": area.get("priority", 0),
                    "suggested_action": area.get("suggested_action", "")
                })
            summary["key_improvement_areas"] = key_areas
        
        return summary
    
    def compare_with_previous(self, previous_analysis_id, current_analysis=None):
        """過去の分析結果と比較"""
        # 過去の分析結果を読み込み
        previous_analysis = self.get_analysis_by_id(previous_analysis_id)
        if not previous_analysis:
            logger.warning(f"Previous analysis with ID {previous_analysis_id} not found")
            return None
        
        # 現在の分析結果
        if current_analysis is None:
            # 最新の分析結果を使用
            if not self._analysis_cache:
                logger.warning("No current analysis available for comparison")
                return None
            current_analysis = list(self._analysis_cache.values())[-1]
        
        # 比較分析
        comparison = {
            "overall_improvement": 0,
            "improved_areas": [],
            "declined_areas": [],
            "unchanged_areas": [],
            "new_strengths": [],
            "new_weaknesses": [],
            "resolved_weaknesses": [],
        }
        
        # 全体評価の比較
        prev_rating = previous_analysis.get("strategy_evaluation", {}).get("overall_rating", 0)
        curr_rating = current_analysis.get("strategy_evaluation", {}).get("overall_rating", 0)
        comparison["overall_improvement"] = curr_rating - prev_rating
        
        # 強みの比較
        prev_strengths = set(s.get("area", "") for s in previous_analysis.get("strategy_evaluation", {}).get("strengths", []))
        curr_strengths = set(s.get("area", "") for s in current_analysis.get("strategy_evaluation", {}).get("strengths", []))
        
        comparison["new_strengths"] = list(curr_strengths - prev_strengths)
        
        # 弱みの比較
        prev_weaknesses = set(w.get("area", "") for w in previous_analysis.get("strategy_evaluation", {}).get("weaknesses", []))
        curr_weaknesses = set(w.get("area", "") for w in current_analysis.get("strategy_evaluation", {}).get("weaknesses", []))
        
        comparison["new_weaknesses"] = list(curr_weaknesses - prev_weaknesses)
        comparison["resolved_weaknesses"] = list(prev_weaknesses - curr_weaknesses)
        
        # 評価項目ごとの比較
        for key in ["upwind_strategy", "downwind_strategy", "start_execution", "mark_rounding", "tactical_decisions"]:
            prev_score = previous_analysis.get("strategy_evaluation", {}).get(key, {}).get("score", 0)
            curr_score = current_analysis.get("strategy_evaluation", {}).get(key, {}).get("score", 0)
            
            diff = curr_score - prev_score
            item = {
                "area": key,
                "previous_score": prev_score,
                "current_score": curr_score,
                "difference": diff
            }
            
            if diff > 0.1:  # 10%以上の改善
                comparison["improved_areas"].append(item)
            elif diff < -0.1:  # 10%以上の低下
                comparison["declined_areas"].append(item)
            else:  # ほぼ変化なし
                comparison["unchanged_areas"].append(item)
        
        return comparison
    
    def export_analysis_report(self, analysis_id=None, format="html", template=None):
        """分析レポートのエクスポート"""
        # 分析結果の取得
        if analysis_id:
            analysis = self.get_analysis_by_id(analysis_id)
            if not analysis:
                logger.warning(f"Analysis with ID {analysis_id} not found")
                return None
        else:
            # 最新の分析結果を使用
            if not self._analysis_cache:
                logger.warning("No analysis available for export")
                return None
            analysis = list(self._analysis_cache.values())[-1]
        
        # フォーマットに応じたエクスポート処理
        if format.lower() == "html":
            return self._export_as_html(analysis, template)
        elif format.lower() == "json":
            return json.dumps(analysis, default=str, indent=2)
        elif format.lower() == "pdf":
            return self._export_as_pdf(analysis, template)
        else:
            logger.warning(f"Unsupported export format: {format}")
            return None
    
    def _export_as_html(self, analysis, template=None):
        """HTML形式でエクスポート"""
        # テンプレートの選択
        if template is None:
            # デフォルトテンプレートを使用
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>セーリング戦略分析レポート</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #003366; }
                    h2 { color: #0055a4; border-bottom: 1px solid #ccc; }
                    .section { margin-top: 20px; }
                    .metric { margin: 10px 0; }
                    .metric-name { font-weight: bold; }
                    .good { color: green; }
                    .average { color: orange; }
                    .poor { color: red; }
                    .decision-point { background-color: #f8f8f8; padding: 10px; margin: 10px 0; border-radius: 5px; }
                    .improvement { background-color: #f0f8ff; padding: 10px; margin: 10px 0; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>セーリング戦略分析レポート</h1>
                <p>分析日時: {analysis_timestamp}</p>
                <p>分析レベル: {analysis_level}</p>
                
                <div class="section">
                    <h2>全体評価</h2>
                    <div class="metric">
                        <span class="metric-name">総合評価:</span> 
                        <span class="{overall_rating_class}">{overall_rating}/10</span>
                    </div>
                    <div class="metric">
                        <span class="metric-name">実行品質:</span> 
                        <span class="{execution_quality_class}">{execution_quality}/10</span>
                    </div>
                </div>
                
                <div class="section">
                    <h2>強み</h2>
                    <ul>
                    {strengths_list}
                    </ul>
                </div>
                
                <div class="section">
                    <h2>改善点</h2>
                    <ul>
                    {weaknesses_list}
                    </ul>
                </div>
                
                <div class="section">
                    <h2>重要な決断ポイント</h2>
                    {decision_points}
                </div>
                
                <div class="section">
                    <h2>風の評価</h2>
                    <p>{wind_assessment}</p>
                </div>
                
                <div class="section">
                    <h2>ポジショニング評価</h2>
                    <p>{positioning_assessment}</p>
                </div>
                
                <div class="section">
                    <h2>優先改善領域</h2>
                    {improvement_areas}
                </div>
            </body>
            </html>
            """
        else:
            # 指定されたテンプレートを読み込み
            try:
                with open(template, 'r', encoding='utf-8') as f:
                    html_template = f.read()
            except Exception as e:
                logger.error(f"Error loading template: {e}")
                return None
        
        # テンプレート変数の置換
        summary = analysis.get("summary", {})
        
        # 評価クラスの決定
        overall_rating = summary.get("overall_rating", 0)
        if overall_rating >= 7:
            overall_rating_class = "good"
        elif overall_rating >= 5:
            overall_rating_class = "average"
        else:
            overall_rating_class = "poor"
        
        execution_quality = summary.get("execution_quality", 0)
        if execution_quality >= 7:
            execution_quality_class = "good"
        elif execution_quality >= 5:
            execution_quality_class = "average"
        else:
            execution_quality_class = "poor"
        
        # 強みリスト
        strengths_list = ""
        for strength in summary.get("strengths", []):
            strengths_list += f"<li>{strength.get('area', '')}: {strength.get('description', '')}</li>"
        
        # 弱みリスト
        weaknesses_list = ""
        for weakness in summary.get("weaknesses", []):
            weaknesses_list += f"<li>{weakness.get('area', '')}: {weakness.get('description', '')}</li>"
        
        # 決断ポイント
        decision_points_html = ""
        for point in summary.get("critical_decisions", []):
            decision_points_html += f"""
            <div class="decision-point">
                <h3>{point.get('type', '')} - {point.get('time', '')}</h3>
                <p>{point.get('description', '')}</p>
                <p><strong>影響スコア:</strong> {point.get('impact_score', 0)}/10</p>
            </div>
            """
        
        # 改善領域
        improvement_areas_html = ""
        for area in summary.get("key_improvement_areas", []):
            improvement_areas_html += f"""
            <div class="improvement">
                <h3>{area.get('area', '')}</h3>
                <p>{area.get('description', '')}</p>
                <p><strong>提案アクション:</strong> {area.get('suggested_action', '')}</p>
                <p><strong>優先度:</strong> {area.get('priority', 0)}/10</p>
            </div>
            """
        
        # テンプレート変数の置換
        html_content = html_template.format(
            analysis_timestamp=analysis.get("analysis_timestamp", ""),
            analysis_level=analysis.get("analysis_level", ""),
            overall_rating=overall_rating,
            overall_rating_class=overall_rating_class,
            execution_quality=execution_quality,
            execution_quality_class=execution_quality_class,
            strengths_list=strengths_list,
            weaknesses_list=weaknesses_list,
            decision_points=decision_points_html,
            wind_assessment=summary.get("wind_assessment", ""),
            positioning_assessment=summary.get("positioning_assessment", ""),
            improvement_areas=improvement_areas_html
        )
        
        return html_content
    
    def _export_as_pdf(self, analysis, template=None):
        """PDF形式でエクスポート"""
        # 注: この実装には外部ライブラリ(例: weasyprint)が必要
        # サンプル実装としてエラーメッセージを返す
        logger.warning("PDF export is not implemented yet")
        return None
    
    def get_analysis_by_id(self, analysis_id):
        """IDによる分析結果の取得"""
        # 実際の実装ではデータベースや外部ストレージから取得する
        # サンプル実装ではキャッシュから検索
        for key, analysis in self._analysis_cache.items():
            if str(key) == str(analysis_id):
                return analysis
        
        # ファイルシステムからの読み込みを試みる（例）
        try:
            file_path = f"analysis_results/{analysis_id}.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analysis from file: {e}")
        
        return None


# 補助関数
def angle_difference(angle1, angle2):
    """2つの角度の差分を計算（-180〜180度の範囲）"""
    diff = ((angle1 - angle2 + 180) % 360) - 180
    return abs(diff)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    ハーバーサイン公式による2点間の距離計算（メートル）
    
    Parameters
    ----------
    lat1, lon1 : float
        地点1の緯度・経度（度）
    lat2, lon2 : float
        地点2の緯度・経度（度）
        
    Returns
    -------
    float
        2点間の距離（メートル）
    """
    # 地球の半径（メートル）
    R = 6371000
    
    # 緯度経度をラジアンに変換
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 緯度・経度の差分
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # ハーバーサイン公式
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 距離の計算
    distance = R * c
    
    return distance
