# -*- coding: utf-8 -*-
"""
コンテキスト認識型戦略評価エンジン

セーリングレースの戦略と意思決定を文脈情報に基づいて評価します。
風況、コース状況、他艇の位置などを考慮した包括的な評価を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
import logging

# ロガー設定
logger = logging.getLogger(__name__)

class StrategyEvaluator:
    """
    戦略評価エンジン
    
    レース戦略と意思決定をコンテキスト情報に基づいて評価します。
    """
    
    def __init__(self, sailor_profile=None, race_context=None):
        """
        初期化
        
        Parameters
        ----------
        sailor_profile : dict, optional
            セーラープロファイル情報, by default None
        race_context : dict, optional
            レース状況情報, by default None
        """
        self.sailor_profile = sailor_profile or {}
        self.race_context = race_context or {}
        
        # 評価モデルの設定
        self._configure_evaluation_models()
        
        logger.info("StrategyEvaluator initialized")
    
    def _configure_evaluation_models(self):
        """評価モデルの設定"""
        # 評価基準と重み
        self.evaluation_weights = {
            "upwind_strategy": 0.25,     # 風上戦略の重み
            "downwind_strategy": 0.20,   # 風下戦略の重み
            "start_execution": 0.15,     # スタート実行の重み
            "mark_rounding": 0.15,       # マーク回航の重み
            "tactical_decisions": 0.25,   # 戦術的判断の重み
        }
        
        # スキルレベルに応じた評価基準の調整
        skill_level = self.sailor_profile.get("skill_level", "intermediate")
        
        if skill_level == "beginner":
            # 初心者はスタートとマーク回航の基本的な実行に重点
            self.evaluation_weights["start_execution"] = 0.20
            self.evaluation_weights["mark_rounding"] = 0.20
            self.evaluation_weights["tactical_decisions"] = 0.15
        elif skill_level == "advanced" or skill_level == "expert":
            # 上級者は戦術的判断と風上戦略に重点
            self.evaluation_weights["tactical_decisions"] = 0.30
            self.evaluation_weights["upwind_strategy"] = 0.30
            self.evaluation_weights["start_execution"] = 0.10
        elif skill_level == "professional":
            # プロは競争戦略により焦点
            self.evaluation_weights["tactical_decisions"] = 0.35
            self.evaluation_weights["upwind_strategy"] = 0.25
            self.evaluation_weights["downwind_strategy"] = 0.20
            self.evaluation_weights["start_execution"] = 0.10
            self.evaluation_weights["mark_rounding"] = 0.10
    
    def evaluate_strategy(self, track_data, wind_data, competitor_data=None, course_data=None):
        """
        全体戦略の評価
        
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
            戦略評価結果
        """
        logger.info("Evaluating overall racing strategy")
        
        # データの検証
        if track_data.empty or wind_data.empty:
            logger.warning("Empty track or wind data provided for evaluation")
            return self._generate_empty_evaluation("Insufficient data for evaluation")
        
        try:
            # 各戦略要素の評価
            upwind_eval = self.evaluate_upwind_strategy(track_data, wind_data, course_data)
            downwind_eval = self.evaluate_downwind_strategy(track_data, wind_data, course_data)
            start_eval = self.evaluate_start_strategy(track_data, wind_data, competitor_data, course_data)
            mark_eval = self.evaluate_mark_rounding(track_data, wind_data, course_data, competitor_data)
            tactical_eval = self.evaluate_tactical_decisions(track_data, wind_data, course_data)
            
            # 風況の評価
            wind_assessment = self._assess_wind_conditions(wind_data)
            
            # ポジショニングの評価
            positioning_assessment = self._assess_positioning(track_data, competitor_data, course_data)
            
            # 変化への適応力評価
            adaptation_score = self.evaluate_adaptation_to_changes(track_data, wind_data)
            
            # 総合評価のための各要素の統合
            overall_rating = (
                upwind_eval["score"] * self.evaluation_weights["upwind_strategy"] +
                downwind_eval["score"] * self.evaluation_weights["downwind_strategy"] +
                start_eval["score"] * self.evaluation_weights["start_execution"] +
                mark_eval["score"] * self.evaluation_weights["mark_rounding"] +
                tactical_eval["score"] * self.evaluation_weights["tactical_decisions"]
            )
            
            # 実行品質の総合評価（様々な要素から算出）
            execution_quality = self._calculate_execution_quality(
                upwind_eval, downwind_eval, start_eval, mark_eval, adaptation_score
            )
            
            # 強みと弱みの特定
            strengths, weaknesses = self._identify_strengths_and_weaknesses(
                upwind_eval, downwind_eval, start_eval, mark_eval, tactical_eval, adaptation_score
            )
            
            # 評価結果の統合
            evaluation_result = {
                "overall_rating": overall_rating,
                "execution_quality": execution_quality,
                "upwind_strategy": upwind_eval,
                "downwind_strategy": downwind_eval,
                "start_execution": start_eval,
                "mark_rounding": mark_eval,
                "tactical_decisions": tactical_eval,
                "adaptation_to_changes": adaptation_score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "wind_assessment": wind_assessment,
                "positioning_assessment": positioning_assessment
            }
            
            logger.info(f"Strategy evaluation completed with overall rating: {overall_rating:.2f}/10")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error during strategy evaluation: {str(e)}", exc_info=True)
            return self._generate_empty_evaluation(f"Error in evaluation: {str(e)}")
    
    def evaluate_start_strategy(self, track_data, wind_data, competitor_data=None, course_data=None):
        """スタート戦略の評価"""
        logger.info("Evaluating start strategy")
        
        # スタート戦略の評価結果の初期化
        evaluation = {
            "score": 0.0,
            "comments": [],
            "metrics": {}
        }
        
        try:
            # コースデータからスタートラインの情報を取得
            if course_data and "start_line" in course_data:
                start_line = course_data["start_line"]
            else:
                # スタートライン情報がない場合、最初の時間帯のデータで推定
                logger.info("No start line information, estimating from early track data")
                evaluation["comments"].append("スタートライン情報が不足しています。トラックデータから推定した値を使用しています。")
                # 実際の実装ではスタートライン推定ロジックを追加
                start_line = self._estimate_start_line(track_data)
            
            # レース開始時刻の特定
            if course_data and "start_time" in course_data:
                start_time = course_data["start_time"]
            else:
                # トラックデータから開始時刻を推定
                start_time = self._estimate_start_time(track_data)
            
            # スタート前1分間と後1分間のデータを抽出
            start_window_before = track_data[
                (track_data["timestamp"] >= start_time - timedelta(seconds=60)) &
                (track_data["timestamp"] < start_time)
            ]
            
            start_window_after = track_data[
                (track_data["timestamp"] >= start_time) &
                (track_data["timestamp"] < start_time + timedelta(seconds=60))
            ]
            
            # メトリクスの計算
            
            # 1. スタートタイミングの精度
            # スタート時刻とトラックの交点のタイミング誤差を計算
            if not start_window_before.empty and not start_window_after.empty:
                timing_error = self._calculate_start_timing_error(start_window_before, start_window_after, start_time, start_line)
                # 0-10秒の誤差を10点満点で評価（誤差が少ないほど高得点）
                timing_score = max(0, 10 - timing_error)
                evaluation["metrics"]["timing_error"] = timing_error
                evaluation["metrics"]["timing_score"] = timing_score
                
                if timing_error <= 2:
                    evaluation["comments"].append("スタートタイミングが非常に優れています。ほぼ完璧なタイミングでラインを切っています。")
                elif timing_error <= 5:
                    evaluation["comments"].append("スタートタイミングは良好です。少しの改善の余地があります。")
                else:
                    evaluation["comments"].append("スタートタイミングにはかなりの改善の余地があります。")
            else:
                timing_score = 5.0  # データ不足の場合は中間値
                evaluation["comments"].append("スタート時のデータが不足しているため、タイミング評価は限定的です。")
            
            # 2. ポジショニングの評価
            # スタートラインでの位置（有利サイドへの近さなど）
            positioning_score = self._evaluate_start_positioning(start_window_after, start_line, wind_data, competitor_data)
            evaluation["metrics"]["positioning_score"] = positioning_score
            
            # 3. スピードビルドアップ評価
            # スタート直後の加速と速度維持
            speed_score = self._evaluate_start_speed(start_window_before, start_window_after)
            evaluation["metrics"]["speed_score"] = speed_score
            
            # 4. 戦術的判断の評価（風の活用、他艇との関係など）
            if competitor_data is not None:
                tactics_score = self._evaluate_start_tactics(start_window_before, start_window_after, competitor_data, wind_data)
                evaluation["metrics"]["tactics_score"] = tactics_score
            else:
                tactics_score = None
                evaluation["comments"].append("競合艇データがないため、スタート戦術の完全な評価ができません。")
            
            # 総合スコアの計算
            if tactics_score is not None:
                # すべての評価要素がある場合
                evaluation["score"] = (timing_score * 0.4 + positioning_score * 0.3 + 
                                     speed_score * 0.2 + tactics_score * 0.1)
            else:
                # 競合艇データがない場合
                evaluation["score"] = (timing_score * 0.5 + positioning_score * 0.3 + 
                                     speed_score * 0.2)
            
            # スコアを0-10の範囲に正規化
            evaluation["score"] = min(10, max(0, evaluation["score"]))
            
            logger.info(f"Start strategy evaluation completed with score: {evaluation['score']:.2f}/10")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating start strategy: {str(e)}", exc_info=True)
            evaluation["comments"].append(f"スタート戦略の評価中にエラーが発生しました: {str(e)}")
            evaluation["score"] = 5.0  # エラー時は中間値を返す
            return evaluation
    
    def evaluate_upwind_strategy(self, track_data, wind_data, leg_data=None):
        """風上戦略の評価"""
        logger.info("Evaluating upwind strategy")
        
        # 風上戦略の評価結果の初期化
        evaluation = {
            "score": 0.0,
            "comments": [],
            "metrics": {}
        }
        
        try:
            # 風上レグの識別
            if leg_data and "upwind_legs" in leg_data:
                # コースデータから風上レグ情報を取得
                upwind_legs = leg_data["upwind_legs"]
                upwind_data = self._extract_leg_data(track_data, upwind_legs)
            else:
                # コースデータがない場合、風向情報を使って風上レグを推定
                upwind_data = self._identify_upwind_legs(track_data, wind_data)
                evaluation["comments"].append("風上レグ情報が提供されていないため、風データから推定しています。")
            
            if upwind_data.empty:
                logger.warning("No upwind leg data identified")
                evaluation["comments"].append("風上レグデータを特定できませんでした。")
                evaluation["score"] = 5.0  # データ不足の場合は中間値
                return evaluation
            
            # 風上帆走時のVMG（Velocity Made Good）の計算
            upwind_data = self._calculate_vmg(upwind_data, wind_data, "upwind")
            
            # 1. VMG効率の評価
            vmg_efficiency = self._evaluate_vmg_efficiency(upwind_data, "upwind")
            evaluation["metrics"]["vmg_efficiency"] = vmg_efficiency
            
            if vmg_efficiency >= 0.9:
                evaluation["comments"].append("風上でのVMG効率は極めて高いです。最適な風上角度を維持できています。")
            elif vmg_efficiency >= 0.75:
                evaluation["comments"].append("風上でのVMG効率は良好です。")
            else:
                evaluation["comments"].append("風上でのVMG効率を向上させる余地があります。ボートスピードかポインティング能力を改善しましょう。")
            
            # 2. タック回数と効率の評価
            tack_metrics = self._evaluate_tacks(upwind_data)
            evaluation["metrics"].update(tack_metrics)
            
            if tack_metrics["tack_count"] > 0:
                if tack_metrics["avg_tack_vmg_loss"] <= 0.15:
                    evaluation["comments"].append("タック時のVMG損失が少なく、効率的な方向転換ができています。")
                else:
                    evaluation["comments"].append("タック時のVMG損失を減らす余地があります。より効率的な方向転換を練習しましょう。")
                
                if tack_metrics["tack_frequency_score"] >= 7:
                    evaluation["comments"].append("タック回数は適切です。")
                elif tack_metrics["tack_frequency_score"] <= 4:
                    evaluation["comments"].append("タック回数が多すぎる傾向があります。不必要なタックを減らすことでパフォーマンスが向上する可能性があります。")
            
            # 3. 風向変化への対応評価
            wind_shifts_response = self._evaluate_wind_shifts_response(upwind_data, wind_data)
            evaluation["metrics"].update(wind_shifts_response)
            
            if wind_shifts_response["wind_shift_response_score"] >= 8:
                evaluation["comments"].append("風向変化への対応が優れています。シフトを適切に活用できています。")
            elif wind_shifts_response["wind_shift_response_score"] >= 6:
                evaluation["comments"].append("風向変化への対応は良好ですが、一部のシフトをより効果的に活用できる可能性があります。")
            else:
                evaluation["comments"].append("風向変化への対応に改善の余地があります。風向の変化をより注意深く観察し、タイミング良く対応することを意識しましょう。")
            
            # 4. レイラインアプローチの評価
            if leg_data and "marks" in leg_data:
                layline_metrics = self._evaluate_layline_approach(upwind_data, leg_data["marks"], wind_data)
                evaluation["metrics"].update(layline_metrics)
                
                if layline_metrics["layline_approach_score"] >= 8:
                    evaluation["comments"].append("レイラインへのアプローチが非常に良いです。最適なタイミングでレイラインに到達しています。")
                elif layline_metrics["layline_approach_score"] >= 6:
                    evaluation["comments"].append("レイラインへのアプローチは良好ですが、さらに最適化できる余地があります。")
                else:
                    evaluation["comments"].append("レイラインへのアプローチに改善の余地があります。早すぎるレイライン到達やオーバースタンディングに注意しましょう。")
            else:
                evaluation["comments"].append("マーク情報がないため、レイラインアプローチの詳細評価はできません。")
            
            # 総合スコアの計算
            vmg_weight = 0.4
            tack_weight = 0.2
            wind_shift_weight = 0.3
            layline_weight = 0.1
            
            vmg_score = vmg_efficiency * 10  # 0-1スケールを0-10に変換
            tack_score = (tack_metrics.get("tack_efficiency_score", 5) + 
                         tack_metrics.get("tack_frequency_score", 5)) / 2
            wind_shift_score = wind_shifts_response.get("wind_shift_response_score", 5)
            
            if "layline_approach_score" in evaluation["metrics"]:
                layline_score = evaluation["metrics"]["layline_approach_score"]
                evaluation["score"] = (vmg_score * vmg_weight + 
                                    tack_score * tack_weight + 
                                    wind_shift_score * wind_shift_weight + 
                                    layline_score * layline_weight)
            else:
                # レイライン情報がない場合は重みを再分配
                adjusted_vmg_weight = vmg_weight + layline_weight * 0.5
                adjusted_wind_shift_weight = wind_shift_weight + layline_weight * 0.5
                
                evaluation["score"] = (vmg_score * adjusted_vmg_weight + 
                                    tack_score * tack_weight + 
                                    wind_shift_score * adjusted_wind_shift_weight)
            
            # スコアを0-10の範囲に正規化
            evaluation["score"] = min(10, max(0, evaluation["score"]))
            
            logger.info(f"Upwind strategy evaluation completed with score: {evaluation['score']:.2f}/10")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating upwind strategy: {str(e)}", exc_info=True)
            evaluation["comments"].append(f"風上戦略の評価中にエラーが発生しました: {str(e)}")
            evaluation["score"] = 5.0  # エラー時は中間値を返す
            return evaluation
    
    def evaluate_downwind_strategy(self, track_data, wind_data, leg_data=None):
        """風下戦略の評価"""
        logger.info("Evaluating downwind strategy")
        
        # 風下戦略の評価結果の初期化
        evaluation = {
            "score": 0.0,
            "comments": [],
            "metrics": {}
        }
        
        try:
            # 風下レグの識別
            if leg_data and "downwind_legs" in leg_data:
                # コースデータから風下レグ情報を取得
                downwind_legs = leg_data["downwind_legs"]
                downwind_data = self._extract_leg_data(track_data, downwind_legs)
            else:
                # コースデータがない場合、風向情報を使って風下レグを推定
                downwind_data = self._identify_downwind_legs(track_data, wind_data)
                evaluation["comments"].append("風下レグ情報が提供されていないため、風データから推定しています。")
            
            if downwind_data.empty:
                logger.warning("No downwind leg data identified")
                evaluation["comments"].append("風下レグデータを特定できませんでした。")
                evaluation["score"] = 5.0  # データ不足の場合は中間値
                return evaluation
            
            # 風下帆走時のVMG（Velocity Made Good）の計算
            downwind_data = self._calculate_vmg(downwind_data, wind_data, "downwind")
            
            # 1. VMG効率の評価
            vmg_efficiency = self._evaluate_vmg_efficiency(downwind_data, "downwind")
            evaluation["metrics"]["vmg_efficiency"] = vmg_efficiency
            
            if vmg_efficiency >= 0.9:
                evaluation["comments"].append("風下でのVMG効率は極めて高いです。最適な風下角度を維持できています。")
            elif vmg_efficiency >= 0.75:
                evaluation["comments"].append("風下でのVMG効率は良好です。")
            else:
                evaluation["comments"].append("風下でのVMG効率を向上させる余地があります。ボートスピードや艇の姿勢を改善しましょう。")
            
            # 2. ジャイブ評価
            jibe_metrics = self._evaluate_jibes(downwind_data)
            evaluation["metrics"].update(jibe_metrics)
            
            if jibe_metrics["jibe_count"] > 0:
                if jibe_metrics["avg_jibe_vmg_loss"] <= 0.1:
                    evaluation["comments"].append("ジャイブ時のVMG損失が少なく、効率的な操船ができています。")
                else:
                    evaluation["comments"].append("ジャイブ時のVMG損失を減らす余地があります。より滑らかなジャイブを練習しましょう。")
                
                if jibe_metrics["jibe_frequency_score"] >= 7:
                    evaluation["comments"].append("ジャイブ回数は適切です。")
                elif jibe_metrics["jibe_frequency_score"] <= 4:
                    evaluation["comments"].append("ジャイブ回数が多すぎる傾向があります。不必要なジャイブを減らすことでパフォーマンスが向上する可能性があります。")
            
            # 3. 風の変化・パフの活用評価
            wind_exploitation = self._evaluate_wind_exploitation(downwind_data, wind_data)
            evaluation["metrics"].update(wind_exploitation)
            
            if wind_exploitation["puff_exploitation_score"] >= 8:
                evaluation["comments"].append("風のパフ（突風）を非常に効果的に活用できています。")
            elif wind_exploitation["puff_exploitation_score"] >= 6:
                evaluation["comments"].append("風のパフの活用は良好ですが、さらに改善の余地があります。")
            else:
                evaluation["comments"].append("風のパフの活用に改善の余地があります。速度変化や方向変化に注目して、パフを見つけて活用する技術を磨きましょう。")
            
            # 4. コース選択とレイラインアプローチの評価
            if leg_data and "marks" in leg_data:
                course_metrics = self._evaluate_downwind_course(downwind_data, leg_data["marks"], wind_data)
                evaluation["metrics"].update(course_metrics)
                
                if course_metrics["course_selection_score"] >= 8:
                    evaluation["comments"].append("風下でのコース選択が非常に良いです。最適なコースを航行できています。")
                elif course_metrics["course_selection_score"] >= 6:
                    evaluation["comments"].append("風下でのコース選択は良好ですが、さらに最適化できる余地があります。")
                else:
                    evaluation["comments"].append("風下でのコース選択に改善の余地があります。不利な水域や風の陰を避け、有利なエリアを見つける観察力を磨きましょう。")
            else:
                evaluation["comments"].append("マーク情報がないため、風下コース選択の詳細評価はできません。")
            
            # 総合スコアの計算
            vmg_weight = 0.35
            jibe_weight = 0.20
            wind_exploitation_weight = 0.30
            course_weight = 0.15
            
            vmg_score = vmg_efficiency * 10  # 0-1スケールを0-10に変換
            jibe_score = (jibe_metrics.get("jibe_efficiency_score", 5) + 
                        jibe_metrics.get("jibe_frequency_score", 5)) / 2
            wind_exploitation_score = wind_exploitation.get("puff_exploitation_score", 5)
            
            if "course_selection_score" in evaluation["metrics"]:
                course_score = evaluation["metrics"]["course_selection_score"]
                evaluation["score"] = (vmg_score * vmg_weight + 
                                    jibe_score * jibe_weight + 
                                    wind_exploitation_score * wind_exploitation_weight + 
                                    course_score * course_weight)
            else:
                # コース情報がない場合は重みを再分配
                adjusted_vmg_weight = vmg_weight + course_weight * 0.5
                adjusted_wind_exploitation_weight = wind_exploitation_weight + course_weight * 0.5
                
                evaluation["score"] = (vmg_score * adjusted_vmg_weight + 
                                    jibe_score * jibe_weight + 
                                    wind_exploitation_score * adjusted_wind_exploitation_weight)
            
            # スコアを0-10の範囲に正規化
            evaluation["score"] = min(10, max(0, evaluation["score"]))
            
            logger.info(f"Downwind strategy evaluation completed with score: {evaluation['score']:.2f}/10")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating downwind strategy: {str(e)}", exc_info=True)
            evaluation["comments"].append(f"風下戦略の評価中にエラーが発生しました: {str(e)}")
            evaluation["score"] = 5.0  # エラー時は中間値を返す
            return evaluation
    
    def evaluate_mark_rounding(self, track_data, wind_data, mark_data=None, competitor_data=None):
        """マーク回航の評価"""
        logger.info("Evaluating mark rounding")
        
        # マーク回航の評価結果の初期化
        evaluation = {
            "score": 0.0,
            "comments": [],
            "metrics": {},
            "mark_details": []
        }
        
        try:
            # マーク情報の確認
            if mark_data is None or "marks" not in mark_data:
                logger.warning("No mark data provided for evaluation")
                evaluation["comments"].append("マーク情報が不足しているため、回航評価は限定的です。")
                # マーク情報がない場合はトラックデータから推定を試みる
                marks = self._estimate_mark_positions(track_data)
                if not marks:
                    evaluation["score"] = 5.0  # データ不足の場合は中間値
                    return evaluation
            else:
                marks = mark_data["marks"]
            
            # 各マークの回航評価
            all_mark_scores = []
            mark_details = []
            
            for i, mark in enumerate(marks):
                mark_position = (mark.get("latitude"), mark.get("longitude"))
                mark_type = mark.get("type", "unknown")
                
                # マーク回航データの抽出
                mark_rounding_data = self._extract_mark_rounding_data(track_data, mark_position)
                
                if mark_rounding_data.empty:
                    logger.warning(f"No data found for mark {i+1}")
                    continue
                
                # 1. 回航の滑らかさと効率の評価
                smoothness = self._evaluate_rounding_smoothness(mark_rounding_data)
                
                # 2. 回航時の速度維持の評価
                speed_maintenance = self._evaluate_rounding_speed_maintenance(mark_rounding_data)
                
                # 3. 戦術的アプローチの評価（他艇との関係など）
                if competitor_data is not None:
                    tactical_approach = self._evaluate_rounding_tactics(mark_rounding_data, competitor_data, mark_position)
                else:
                    tactical_approach = None
                
                # 4. マークタイプに基づいた特定評価
                type_specific_score = self._evaluate_mark_by_type(mark_rounding_data, mark_type, wind_data)
                
                # マークごとの総合スコア計算
                mark_score = (smoothness["score"] * 0.4 + 
                            speed_maintenance["score"] * 0.4 + 
                            (tactical_approach["score"] if tactical_approach else 0) * 0.1 + 
                            type_specific_score["score"] * 0.1)
                
                # 特定のコメントがあれば追加
                mark_comments = []
                if smoothness["score"] >= 8:
                    mark_comments.append("回航ラインが非常に滑らかです。")
                elif smoothness["score"] <= 5:
                    mark_comments.append("回航の滑らかさに改善の余地があります。")
                    
                if speed_maintenance["score"] >= 8:
                    mark_comments.append("回航中の速度維持が優れています。")
                elif speed_maintenance["score"] <= 5:
                    mark_comments.append("回航中の速度損失を減らす余地があります。")
                
                # マーク詳細情報の保存
                mark_detail = {
                    "mark_number": i + 1,
                    "mark_type": mark_type,
                    "score": mark_score,
                    "smoothness": smoothness["score"],
                    "speed_maintenance": speed_maintenance["score"],
                    "tactical_approach": tactical_approach["score"] if tactical_approach else None,
                    "type_specific_score": type_specific_score["score"],
                    "comments": mark_comments
                }
                
                mark_details.append(mark_detail)
                all_mark_scores.append(mark_score)
            
            # 全マークの平均スコアを計算
            if all_mark_scores:
                evaluation["score"] = sum(all_mark_scores) / len(all_mark_scores)
                evaluation["mark_details"] = mark_details
                
                # 総合コメントの生成
                if evaluation["score"] >= 8:
                    evaluation["comments"].append("マーク回航の技術が非常に優れています。滑らかさと速度維持のバランスが取れています。")
                elif evaluation["score"] >= 6:
                    evaluation["comments"].append("マーク回航は良好ですが、特定のマークでさらに改善の余地があります。")
                else:
                    evaluation["comments"].append("マーク回航に改善の余地があります。特に滑らかさと速度維持について練習を重ねることをお勧めします。")
                
                # マークごとの特筆事項があれば追加
                best_mark = max(mark_details, key=lambda x: x["score"])
                worst_mark = min(mark_details, key=lambda x: x["score"])
                
                if best_mark["score"] - worst_mark["score"] > 2:
                    evaluation["comments"].append(f"マーク間でパフォーマンスにばらつきがあります。マーク{worst_mark['mark_number']}の回航技術を{best_mark['mark_number']}のレベルに近づけるとよいでしょう。")
            else:
                evaluation["comments"].append("マーク回航データが十分に得られませんでした。評価は限定的です。")
                evaluation["score"] = 5.0  # データ不足の場合は中間値
            
            # スコアを0-10の範囲に正規化
            evaluation["score"] = min(10, max(0, evaluation["score"]))
            
            logger.info(f"Mark rounding evaluation completed with score: {evaluation['score']:.2f}/10")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating mark rounding: {str(e)}", exc_info=True)
            evaluation["comments"].append(f"マーク回航の評価中にエラーが発生しました: {str(e)}")
            evaluation["score"] = 5.0  # エラー時は中間値を返す
            return evaluation
    
    def evaluate_tactical_decisions(self, track_data, wind_data, decision_points=None):
        """戦術的決断の評価"""
        logger.info("Evaluating tactical decisions")
        
        # 戦術的決断の評価結果の初期化
        evaluation = {
            "score": 0.0,
            "comments": [],
            "metrics": {},
            "decision_evaluations": []
        }
        
        try:
            # 決断ポイントの確認
            if decision_points is None or not decision_points:
                logger.info("No decision points provided, attempting to detect from data")
                # 決断ポイントの自動検出を試みる（実際の実装では詳細なアルゴリズムが必要）
                detected_points = self._detect_tactical_decision_points(track_data, wind_data)
                if not detected_points:
                    evaluation["comments"].append("戦術的決断ポイントを自動検出できませんでした。評価は限定的です。")
                    evaluation["score"] = 5.0  # データ不足の場合は中間値
                    return evaluation
                decision_points = detected_points
            
            # 各決断ポイントの評価
            decision_scores = []
            decision_evaluations = []
            
            for i, decision in enumerate(decision_points):
                # 決断のタイプと時刻を取得
                decision_type = decision.get("type", "unknown")
                decision_time = decision.get("time")
                decision_position = decision.get("position")
                
                # 決断前後のデータを抽出
                before_after_data = self._extract_decision_window_data(track_data, decision_time)
                
                if before_after_data["before"].empty or before_after_data["after"].empty:
                    logger.warning(f"Insufficient data for decision point {i+1}")
                    continue
                
                # 決断の評価
                decision_eval = self._evaluate_single_decision(
                    decision_type, 
                    before_after_data, 
                    wind_data, 
                    decision.get("context", {})
                )
                
                # 評価結果の保存
                decision_eval["decision_index"] = i + 1
                decision_eval["time"] = decision_time
                decision_eval["type"] = decision_type
                
                decision_evaluations.append(decision_eval)
                decision_scores.append(decision_eval["score"])
            
            # 全決断の平均スコアを計算
            if decision_scores:
                evaluation["score"] = sum(decision_scores) / len(decision_scores)
                evaluation["decision_evaluations"] = decision_evaluations
                
                # 意思決定の一貫性を評価
                score_std = np.std(decision_scores) if len(decision_scores) > 1 else 0
                consistency_score = max(0, 10 - score_std * 2)  # 標準偏差が小さいほど一貫性が高い
                evaluation["metrics"]["decision_consistency"] = consistency_score
                
                # 風向変化への対応力を評価
                wind_response = self._evaluate_wind_shift_response_quality(decision_evaluations, wind_data)
                evaluation["metrics"]["wind_shift_response"] = wind_response
                
                # 戦術的判断のタイミングを評価
                timing_score = self._evaluate_decision_timing(decision_evaluations)
                evaluation["metrics"]["decision_timing"] = timing_score
                
                # 総合コメントの生成
                if evaluation["score"] >= 8:
                    evaluation["comments"].append("戦術的判断が非常に優れています。状況に応じた適切な判断ができています。")
                elif evaluation["score"] >= 6:
                    evaluation["comments"].append("戦術的判断は良好ですが、一部の判断ではさらに改善の余地があります。")
                else:
                    evaluation["comments"].append("戦術的判断に改善の余地があります。特に風の変化への対応と判断のタイミングに注意しましょう。")
                
                # 一貫性についてのコメント
                if consistency_score >= 8:
                    evaluation["comments"].append("判断の一貫性が高く、安定した戦術を維持できています。")
                elif consistency_score <= 5:
                    evaluation["comments"].append("判断にばらつきがあります。より一貫した戦術判断を心がけましょう。")
                
                # 特筆すべき良い判断と改善すべき判断を指摘
                if decision_evaluations:
                    best_decision = max(decision_evaluations, key=lambda x: x["score"])
                    worst_decision = min(decision_evaluations, key=lambda x: x["score"])
                    
                    if best_decision["score"] >= 8:
                        evaluation["comments"].append(f"特に優れていた判断: {best_decision['time']}の{best_decision['type']}判断。{best_decision.get('strengths', ['適切な判断'])[0]}")
                    
                    if worst_decision["score"] <= 5 and len(decision_evaluations) > 1:
                        evaluation["comments"].append(f"改善の余地がある判断: {worst_decision['time']}の{worst_decision['type']}判断。{worst_decision.get('weaknesses', ['より慎重な判断が必要'])[0]}")
            else:
                evaluation["comments"].append("評価可能な戦術的判断データが得られませんでした。")
                evaluation["score"] = 5.0  # データ不足の場合は中間値
            
            # スコアを0-10の範囲に正規化
            evaluation["score"] = min(10, max(0, evaluation["score"]))
            
            logger.info(f"Tactical decisions evaluation completed with score: {evaluation['score']:.2f}/10")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating tactical decisions: {str(e)}", exc_info=True)
            evaluation["comments"].append(f"戦術的判断の評価中にエラーが発生しました: {str(e)}")
            evaluation["score"] = 5.0  # エラー時は中間値を返す
            return evaluation
    
    def evaluate_adaptation_to_changes(self, track_data, wind_data, wind_shifts=None):
        """変化への適応力評価"""
        logger.info("Evaluating adaptation to changes")
        
        # 変化への適応力の評価結果の初期化
        adaptation_scores = {}
        
        try:
            # 風向変化の検出または取得
            if wind_shifts is None:
                # 風向変化の自動検出を試みる
                detected_shifts = self._detect_wind_shifts(wind_data)
                if not detected_shifts:
                    logger.warning("No wind shifts detected")
                    return 5.0  # 風向変化がない場合は中間値
                wind_shifts = detected_shifts
            
            # 各風向変化に対する適応の評価
            shift_response_scores = []
            
            for shift in wind_shifts:
                shift_time = shift.get("time")
                shift_magnitude = shift.get("magnitude", 0)
                shift_direction = shift.get("direction", "")
                
                # 風向変化の前後のデータを抽出
                before_after_data = self._extract_wind_shift_window_data(track_data, shift_time)
                
                if before_after_data["before"].empty or before_after_data["after"].empty:
                    logger.warning(f"Insufficient data for wind shift at {shift_time}")
                    continue
                
                # 風向変化の特性に応じて対応を評価
                if shift_magnitude > 15:  # 大きな風向変化
                    # 風向変化後の戦術変更を評価
                    strategy_change = self._evaluate_strategy_change_after_shift(
                        before_after_data["before"], before_after_data["after"], 
                        shift_direction, shift_magnitude
                    )
                    shift_response_scores.append(strategy_change)
                else:  # 小さな風向変化
                    # 小さな風向変化への微調整を評価
                    adjustment = self._evaluate_minor_shift_adjustment(
                        before_after_data["before"], before_after_data["after"], 
                        shift_direction, shift_magnitude
                    )
                    shift_response_scores.append(adjustment)
            
            # 全体的な変化適応スコアを計算
            if shift_response_scores:
                adaptation_score = sum(shift_response_scores) / len(shift_response_scores)
                
                # 風向変化の大きさに応じて重み付け
                if any(shift.get("magnitude", 0) > 20 for shift in wind_shifts):
                    adaptation_scores["major_shift_adaptation"] = adaptation_score
                    logger.info("Major wind shifts detected and evaluated")
                else:
                    adaptation_scores["minor_shift_adaptation"] = adaptation_score
                    logger.info("Minor wind shifts evaluated")
            else:
                adaptation_score = 5.0  # データ不足の場合は中間値
            
            # 風速変化への適応も評価（オプション）
            wind_speed_changes = self._detect_wind_speed_changes(wind_data)
            if wind_speed_changes:
                speed_adaptation = self._evaluate_wind_speed_adaptation(track_data, wind_speed_changes)
                adaptation_scores["speed_adaptation"] = speed_adaptation
                
                # 風向と風速の適応スコアを統合
                adaptation_score = (adaptation_score * 0.7 + speed_adaptation * 0.3)
            
            # スコアを0-10の範囲に正規化
            adaptation_score = min(10, max(0, adaptation_score))
            adaptation_scores["overall_adaptation"] = adaptation_score
            
            logger.info(f"Adaptation to changes evaluation completed with score: {adaptation_score:.2f}/10")
            return adaptation_score
            
        except Exception as e:
            logger.error(f"Error evaluating adaptation to changes: {str(e)}", exc_info=True)
            return 5.0  # エラー時は中間値を返す
    
    def simulate_alternative_strategy(self, track_data, wind_data, strategy_params):
        """代替戦略のシミュレーション"""
        logger.info("Simulating alternative strategy")
        
        # 代替戦略シミュレーション結果の初期化
        simulation_result = {
            "original_score": 0.0,
            "alternative_score": 0.0,
            "potential_improvement": 0.0,
            "details": {},
            "comments": []
        }
        
        try:
            # オリジナル戦略の評価
            original_eval = self.evaluate_strategy(track_data, wind_data)
            simulation_result["original_score"] = original_eval["overall_rating"]
            
            # 戦略パラメータの取得
            strategy_type = strategy_params.get("type", "unknown")
            modification = strategy_params.get("modification", {})
            
            # 戦略の種類に応じたシミュレーション
            if strategy_type == "different_tack_timing":
                # タックタイミングの変更シミュレーション
                tack_point = modification.get("tack_point")
                time_offset = modification.get("time_offset", 0)
                
                alternative_result = self._simulate_different_tack_timing(
                    track_data, wind_data, tack_point, time_offset
                )
                
                simulation_result["details"]["tack_timing"] = alternative_result
                simulation_result["alternative_score"] = alternative_result["estimated_score"]
                
            elif strategy_type == "different_layline_approach":
                # レイラインアプローチの変更シミュレーション
                mark = modification.get("mark")
                approach_type = modification.get("approach_type", "early")
                
                alternative_result = self._simulate_different_layline_approach(
                    track_data, wind_data, mark, approach_type
                )
                
                simulation_result["details"]["layline_approach"] = alternative_result
                simulation_result["alternative_score"] = alternative_result["estimated_score"]
                
            elif strategy_type == "wind_shift_response":
                # 風向変化への対応変更シミュレーション
                shift_point = modification.get("shift_point")
                response_type = modification.get("response_type", "immediate_tack")
                
                alternative_result = self._simulate_wind_shift_response(
                    track_data, wind_data, shift_point, response_type
                )
                
                simulation_result["details"]["shift_response"] = alternative_result
                simulation_result["alternative_score"] = alternative_result["estimated_score"]
                
            else:
                logger.warning(f"Unknown strategy type for simulation: {strategy_type}")
                simulation_result["comments"].append(f"未知の戦略タイプ '{strategy_type}' はシミュレーションできません。")
                return simulation_result
            
            # 改善の可能性を計算
            simulation_result["potential_improvement"] = (
                simulation_result["alternative_score"] - simulation_result["original_score"]
            )
            
            # コメントの生成
            if simulation_result["potential_improvement"] > 1.0:
                simulation_result["comments"].append(f"代替戦略により大幅なパフォーマンス向上の可能性があります（+{simulation_result['potential_improvement']:.1f}点）。")
            elif simulation_result["potential_improvement"] > 0:
                simulation_result["comments"].append(f"代替戦略により若干のパフォーマンス向上の可能性があります（+{simulation_result['potential_improvement']:.1f}点）。")
            else:
                simulation_result["comments"].append(f"選択した戦略が最適であり、シミュレーションした代替案では改善が見られません（{simulation_result['potential_improvement']:.1f}点）。")
            
            logger.info(f"Alternative strategy simulation completed with potential improvement: {simulation_result['potential_improvement']:.2f}")
            return simulation_result
            
        except Exception as e:
            logger.error(f"Error simulating alternative strategy: {str(e)}", exc_info=True)
            simulation_result["comments"].append(f"代替戦略のシミュレーション中にエラーが発生しました: {str(e)}")
            return simulation_result
    
    def _generate_empty_evaluation(self, reason):
        """空の評価結果を生成"""
        return {
            "overall_rating": 5.0,  # 中間値
            "comments": [reason],
            "upwind_strategy": {"score": 5.0, "comments": [reason]},
            "downwind_strategy": {"score": 5.0, "comments": [reason]},
            "start_execution": {"score": 5.0, "comments": [reason]},
            "mark_rounding": {"score": 5.0, "comments": [reason]},
            "tactical_decisions": {"score": 5.0, "comments": [reason]},
            "strengths": [],
            "weaknesses": [{"area": "data_quality", "description": reason}]
        }
    
    def _calculate_execution_quality(self, upwind_eval, downwind_eval, start_eval, mark_eval, adaptation_score):
        """実行品質の総合評価を計算"""
        # 各要素の実行品質関連スコアを抽出
        execution_elements = []
        
        # 風上戦略からVMG効率を考慮
        if "vmg_efficiency" in upwind_eval.get("metrics", {}):
            execution_elements.append(upwind_eval["metrics"]["vmg_efficiency"] * 10)  # 0-1スケールを0-10に変換
        
        # 風下戦略からVMG効率を考慮
        if "vmg_efficiency" in downwind_eval.get("metrics", {}):
            execution_elements.append(downwind_eval["metrics"]["vmg_efficiency"] * 10)
        
        # スタート実行からタイミングとスピードスコアを考慮
        if "timing_score" in start_eval.get("metrics", {}):
            execution_elements.append(start_eval["metrics"]["timing_score"])
        
        if "speed_score" in start_eval.get("metrics", {}):
            execution_elements.append(start_eval["metrics"]["speed_score"])
        
        # マーク回航からスムーズさと速度維持を考慮
        for mark_detail in mark_eval.get("mark_details", []):
            if "smoothness" in mark_detail:
                execution_elements.append(mark_detail["smoothness"])
            
            if "speed_maintenance" in mark_detail:
                execution_elements.append(mark_detail["speed_maintenance"])
        
        # 変化への適応力も考慮
        if adaptation_score > 0:
            execution_elements.append(adaptation_score)
        
        # 実行品質の計算（すべての要素の平均）
        if execution_elements:
            execution_quality = sum(execution_elements) / len(execution_elements)
        else:
            execution_quality = 5.0  # 中間値
        
        return min(10, max(0, execution_quality))
    
    def _identify_strengths_and_weaknesses(self, upwind_eval, downwind_eval, start_eval, mark_eval, tactical_eval, adaptation_score):
        """強みと弱みを特定"""
        strengths = []
        weaknesses = []
        
        # 評価カテゴリと閾値の定義
        categories = [
            {"name": "upwind_strategy", "eval": upwind_eval, "display": "風上戦略", "threshold": 7.5},
            {"name": "downwind_strategy", "eval": downwind_eval, "display": "風下戦略", "threshold": 7.5},
            {"name": "start_execution", "eval": start_eval, "display": "スタート実行", "threshold": 7.5},
            {"name": "mark_rounding", "eval": mark_eval, "display": "マーク回航", "threshold": 7.5},
            {"name": "tactical_decisions", "eval": tactical_eval, "display": "戦術的判断", "threshold": 7.5},
            {"name": "adaptation", "eval": {"score": adaptation_score}, "display": "変化への適応力", "threshold": 7.5}
        ]
        
        # 強みの特定（閾値以上のスコア）
        for category in categories:
            score = category["eval"].get("score", 0)
            if score >= category["threshold"]:
                strength = {
                    "area": category["name"],
                    "display_name": category["display"],
                    "score": score,
                    "description": self._generate_strength_description(category["name"], score, category["eval"])
                }
                strengths.append(strength)
        
        # 弱みの特定（閾値未満のスコア）
        for category in categories:
            score = category["eval"].get("score", 0)
            if score < category["threshold"] and score > 0:  # スコアが0の場合は評価されていない
                weakness = {
                    "area": category["name"],
                    "display_name": category["display"],
                    "score": score,
                    "description": self._generate_weakness_description(category["name"], score, category["eval"])
                }
                weaknesses.append(weakness)
        
        # サブカテゴリの詳細分析（特定の弱みをより詳細に）
        self._analyze_subcategory_details(upwind_eval, downwind_eval, start_eval, mark_eval, tactical_eval, strengths, weaknesses)
        
        # スコアでソート（強みは高い順、弱みは低い順）
        strengths.sort(key=lambda x: x["score"], reverse=True)
        weaknesses.sort(key=lambda x: x["score"])
        
        return strengths, weaknesses
    
    def _generate_strength_description(self, category, score, evaluation):
        """強みの詳細説明を生成"""
        # カテゴリごとの強み説明
        if category == "upwind_strategy":
            if "vmg_efficiency" in evaluation.get("metrics", {}) and evaluation["metrics"]["vmg_efficiency"] >= 0.85:
                return "風上での高いVMG効率を維持できています。最適な風上角度を保ちながら効率的に帆走できています。"
            return "風上戦略が特に優れており、効率的な風上帆走ができています。"
            
        elif category == "downwind_strategy":
            if "vmg_efficiency" in evaluation.get("metrics", {}) and evaluation["metrics"]["vmg_efficiency"] >= 0.85:
                return "風下での高いVMG効率を維持できています。最適な風下角度で帆走し、速度を維持できています。"
            return "風下戦略が特に優れており、効率的な風下帆走ができています。"
            
        elif category == "start_execution":
            if "timing_score" in evaluation.get("metrics", {}) and evaluation["metrics"]["timing_score"] >= 8:
                return "スタートタイミングが非常に正確です。最適なタイミングでラインを切ることができています。"
            return "スタート実行が特に優れており、レースの出だしで優位に立てています。"
            
        elif category == "mark_rounding":
            return "マークの回航技術が優れており、スムーズかつ速度を維持した回航ができています。"
            
        elif category == "tactical_decisions":
            if "decision_consistency" in evaluation.get("metrics", {}) and evaluation["metrics"]["decision_consistency"] >= 8:
                return "戦術的判断が一貫して高いレベルで維持されています。状況に応じた適切な判断ができています。"
            return "戦術的判断が優れており、レース状況に応じた適切な判断ができています。"
            
        elif category == "adaptation":
            return "変化に対する適応力が高く、風向や風速の変化に素早く効果的に対応できています。"
            
        return f"{category}が特に優れています。"
    
    def _generate_weakness_description(self, category, score, evaluation):
        """弱みの詳細説明を生成"""
        # カテゴリごとの弱み説明
        if category == "upwind_strategy":
            if "vmg_efficiency" in evaluation.get("metrics", {}) and evaluation["metrics"]["vmg_efficiency"] < 0.7:
                return "風上でのVMG効率を向上させる余地があります。最適な風上角度の維持と速度のバランスを改善しましょう。"
            return "風上戦略に改善の余地があります。タックのタイミングやコース選択を最適化しましょう。"
            
        elif category == "downwind_strategy":
            if "vmg_efficiency" in evaluation.get("metrics", {}) and evaluation["metrics"]["vmg_efficiency"] < 0.7:
                return "風下でのVMG効率を向上させる余地があります。最適な風下角度での帆走と風のパフの活用を練習しましょう。"
            return "風下戦略に改善の余地があります。ジャイブのタイミングやコース選択を最適化しましょう。"
            
        elif category == "start_execution":
            if "timing_score" in evaluation.get("metrics", {}) and evaluation["metrics"]["timing_score"] < 5:
                return "スタートタイミングの精度を向上させる必要があります。より正確なスタートタイミングの練習を重ねましょう。"
            return "スタート実行に改善の余地があります。スタート前の準備とポジショニングを改善しましょう。"
            
        elif category == "mark_rounding":
            return "マークの回航技術に改善の余地があります。より滑らかな回航と速度維持の技術を練習しましょう。"
            
        elif category == "tactical_decisions":
            if "decision_consistency" in evaluation.get("metrics", {}) and evaluation["metrics"]["decision_consistency"] < 5:
                return "戦術的判断の一貫性に改善の余地があります。より安定した判断ができるよう、戦術理解を深めましょう。"
            return "戦術的判断に改善の余地があります。風や他艇の動きへの対応をより的確に行えるよう練習しましょう。"
            
        elif category == "adaptation":
            return "変化への適応力に改善の余地があります。風向や風速の変化をより早く察知し、効果的に対応する練習をしましょう。"
            
        return f"{category}に改善の余地があります。"
    
    def _analyze_subcategory_details(self, upwind_eval, downwind_eval, start_eval, mark_eval, tactical_eval, strengths, weaknesses):
        """サブカテゴリの詳細分析"""
        # 例: 特定のマーク回航が極端に低評価の場合
        if mark_eval and "mark_details" in mark_eval:
            worst_mark = None
            for mark in mark_eval["mark_details"]:
                if worst_mark is None or mark["score"] < worst_mark["score"]:
                    worst_mark = mark
            
            if worst_mark and worst_mark["score"] < 5:
                weakness = {
                    "area": "specific_mark_rounding",
                    "display_name": f"マーク{worst_mark['mark_number']}の回航",
                    "score": worst_mark["score"],
                    "description": f"マーク{worst_mark['mark_number']}の回航に特に改善の余地があります。"
                    f"{', '.join(worst_mark['comments'])}"
                }
                weaknesses.append(weakness)
        
        # タックの効率が低い場合
        if upwind_eval and "metrics" in upwind_eval:
            tack_metrics = upwind_eval["metrics"]
            if "tack_efficiency_score" in tack_metrics and tack_metrics["tack_efficiency_score"] < 5:
                weakness = {
                    "area": "tack_efficiency",
                    "display_name": "タック効率",
                    "score": tack_metrics["tack_efficiency_score"],
                    "description": "タック時のVMG損失が大きいです。より効率的なタック技術を練習しましょう。"
                }
                weaknesses.append(weakness)
    
    def _assess_wind_conditions(self, wind_data):
        """風況の評価"""
        # 風向と風速の安定性を分析
        if wind_data.empty:
            return "風データが不足しているため、詳細な風況評価はできません。"
        
        try:
            # 風向変化の計算
            if "wind_direction" in wind_data.columns:
                # 角度データの特殊性を考慮（0度と359度は近い）
                wind_dirs = wind_data["wind_direction"].values
                wind_dirs_rad = np.radians(wind_dirs)
                
                # 風向の中央値（メジアン）を計算
                mean_sin = np.median(np.sin(wind_dirs_rad))
                mean_cos = np.median(np.cos(wind_dirs_rad))
                median_dir = np.degrees(np.arctan2(mean_sin, mean_cos))
                if median_dir < 0:
                    median_dir += 360
                
                # 風向の変動性（扇形標準偏差）を計算
                diffs = np.array([angle_difference(d, median_dir) for d in wind_dirs])
                direction_variability = np.std(diffs)
                
                wind_direction_desc = ""
                if direction_variability < 10:
                    wind_direction_desc = "風向は非常に安定しています。"
                elif direction_variability < 20:
                    wind_direction_desc = "風向は比較的安定していますが、若干の変動があります。"
                elif direction_variability < 30:
                    wind_direction_desc = "風向に中程度の変動があります。風向の変化を注視する必要があります。"
                else:
                    wind_direction_desc = "風向の変動が大きいです。頻繁な風向変化に対応する必要があります。"
            else:
                wind_direction_desc = ""
            
            # 風速変化の計算
            if "wind_speed" in wind_data.columns:
                mean_speed = wind_data["wind_speed"].mean()
                speed_std = wind_data["wind_speed"].std()
                
                # 変動係数（標準偏差÷平均）を計算
                if mean_speed > 0:
                    speed_variability = speed_std / mean_speed
                else:
                    speed_variability = 0
                
                wind_speed_desc = ""
                if speed_variability < 0.1:
                    wind_speed_desc = "風速は非常に安定しています。"
                elif speed_variability < 0.2:
                    wind_speed_desc = "風速は比較的安定していますが、若干の変動があります。"
                elif speed_variability < 0.3:
                    wind_speed_desc = "風速に中程度の変動があります。風速の変化を注視する必要があります。"
                else:
                    wind_speed_desc = "風速の変動が大きいです。頻繁なパフやラルに対応する必要があります。"
                
                # 風速のカテゴリを特定
                if mean_speed < 5:
                    wind_speed_cat = "弱風"
                elif mean_speed < 10:
                    wind_speed_cat = "軽風〜中風"
                elif mean_speed < 15:
                    wind_speed_cat = "中風〜強風"
                else:
                    wind_speed_cat = "強風"
            else:
                wind_speed_desc = ""
                wind_speed_cat = ""
            
            # 風況の総合評価
            assessment = ""
            if wind_direction_desc and wind_speed_desc:
                assessment = f"{wind_speed_cat}条件です。{wind_direction_desc} {wind_speed_desc}"
                
                # 戦略的アドバイスを追加
                if direction_variability > 25 and speed_variability > 0.25:
                    assessment += " 変動性の高い風況での帆走戦略に重点を置く必要があります。変化の早期発見と素早い対応が重要です。"
                elif direction_variability > 25:
                    assessment += " 風向変化に敏感に対応する戦略が重要です。風上のヘッダーとリフトを特に意識しましょう。"
                elif speed_variability > 0.25:
                    assessment += " 風速変化（パフとラル）を効果的に活用する戦略が重要です。パフでの加速と方向転換のタイミングを意識しましょう。"
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing wind conditions: {str(e)}", exc_info=True)
            return "風況の評価中にエラーが発生しました。"
    
    def _assess_positioning(self, track_data, competitor_data, course_data):
        """ポジショニングの評価"""
        assessment = ""
        
        # 競合艇データがない場合
        if competitor_data is None or competitor_data.empty:
            return "競合艇データがないため、詳細なポジショニング評価はできません。"
        
        try:
            # 競合艇との相対位置の分析
            # ...（実際の実装ではより詳細なアルゴリズムが必要）
            
            # 仮のポジショニング評価を返す
            assessment = "コース全体を通して、競合艇に対して良好なポジショニングを維持できています。特に風上レグでの位置取りが良好です。"
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing positioning: {str(e)}", exc_info=True)
            return "ポジショニングの評価中にエラーが発生しました。"
    
    # 以下、内部実装用のヘルパーメソッド
    # （これらは本来は詳細な実装が必要ですが、
    # スケルトンのみを提供しています）
    
    def _estimate_start_line(self, track_data):
        """トラックデータからスタートラインを推定"""
        # 簡易実装として、最初の一定時間のデータから推定
        return {"start_line": "estimated"}
    
    def _estimate_start_time(self, track_data):
        """トラックデータからスタート時刻を推定"""
        # 簡易実装として、データの最初の時刻を返す
        if "timestamp" in track_data.columns and not track_data.empty:
            return track_data["timestamp"].min()
        return datetime.now()
    
    def _calculate_start_timing_error(self, before_data, after_data, start_time, start_line):
        """スタートタイミングの誤差を計算"""
        # 簡易実装として、ランダムな誤差を返す
        return np.random.uniform(0, 10)
    
    def _evaluate_start_positioning(self, start_data, start_line, wind_data, competitor_data):
        """スタート時のポジショニングを評価"""
        # 簡易実装として、ランダムなスコアを返す
        return np.random.uniform(5, 10)
    
    def _evaluate_start_speed(self, before_data, after_data):
        """スタート時の速度を評価"""
        # 簡易実装として、ランダムなスコアを返す
        return np.random.uniform(5, 10)
    
    def _evaluate_start_tactics(self, before_data, after_data, competitor_data, wind_data):
        """スタート時の戦術を評価"""
        # 簡易実装として、ランダムなスコアを返す
        return np.random.uniform(5, 10)
    
    def _extract_leg_data(self, track_data, legs):
        """指定されたレグのデータを抽出"""
        # 簡易実装として、全データを返す
        return track_data
    
    def _identify_upwind_legs(self, track_data, wind_data):
        """風上レグを識別"""
        # 簡易実装として、全データを返す
        return track_data
    
    def _identify_downwind_legs(self, track_data, wind_data):
        """風下レグを識別"""
        # 簡易実装として、全データを返す
        return track_data
    
    def _calculate_vmg(self, leg_data, wind_data, leg_type):
        """VMG（Velocity Made Good）を計算"""
        # 簡易実装として、元のデータに仮のVMG列を追加
        result = leg_data.copy()
        result["vmg"] = np.random.uniform(0, leg_data["speed"].max(), len(leg_data))
        return result
    
    def _evaluate_vmg_efficiency(self, leg_data, leg_type):
        """VMG効率を評価"""
        # 簡易実装として、ランダムな効率値を返す
        return np.random.uniform(0.7, 0.95)
    
    def _evaluate_tacks(self, upwind_data):
        """タックの評価"""
        # 簡易実装として、仮のタック評価を返す
        return {
            "tack_count": 5,
            "avg_tack_vmg_loss": 0.2,
            "tack_efficiency_score": 7.5,
            "tack_frequency_score": 8.0
        }
    
    def _evaluate_wind_shifts_response(self, upwind_data, wind_data):
        """風向変化への対応評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "wind_shift_response_score": 7.0,
            "detected_shifts": 3,
            "favorable_shifts_used": 2
        }
    
    def _evaluate_layline_approach(self, upwind_data, marks, wind_data):
        """レイラインアプローチの評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "layline_approach_score": 6.5,
            "early_layline_percentage": 20,
            "optimal_layline_percentage": 60,
            "late_layline_percentage": 20
        }
    
    def _evaluate_jibes(self, downwind_data):
        """ジャイブの評価"""
        # 簡易実装として、仮のジャイブ評価を返す
        return {
            "jibe_count": 4,
            "avg_jibe_vmg_loss": 0.15,
            "jibe_efficiency_score": 8.0,
            "jibe_frequency_score": 7.5
        }
    
    def _evaluate_wind_exploitation(self, downwind_data, wind_data):
        """風の活用評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "puff_exploitation_score": 7.5,
            "detected_puffs": 8,
            "effectively_used_puffs": 6
        }
    
    def _evaluate_downwind_course(self, downwind_data, marks, wind_data):
        """風下コース選択の評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "course_selection_score": 8.0,
            "optimal_route_adherence": 0.8,
            "traffic_avoidance_score": 7.5
        }
    
    def _extract_mark_rounding_data(self, track_data, mark_position):
        """マーク回航時のデータを抽出"""
        # 簡易実装として、全データを返す
        return track_data
    
    def _evaluate_rounding_smoothness(self, mark_data):
        """回航の滑らかさを評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "score": np.random.uniform(5, 10),
            "path_deviation": np.random.uniform(0, 0.5)
        }
    
    def _evaluate_rounding_speed_maintenance(self, mark_data):
        """回航時の速度維持を評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "score": np.random.uniform(5, 10),
            "speed_loss_percentage": np.random.uniform(0, 30)
        }
    
    def _evaluate_rounding_tactics(self, mark_data, competitor_data, mark_position):
        """回航時の戦術を評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "score": np.random.uniform(5, 10),
            "position_gain": np.random.randint(-2, 3)
        }
    
    def _evaluate_mark_by_type(self, mark_data, mark_type, wind_data):
        """マークタイプに基づく評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "score": np.random.uniform(5, 10),
            "type_specific_quality": np.random.uniform(0, 1)
        }
    
    def _estimate_mark_positions(self, track_data):
        """トラックデータからマーク位置を推定"""
        # 簡易実装として、空のリストを返す
        return []
    
    def _detect_tactical_decision_points(self, track_data, wind_data):
        """戦術的決断ポイントを検出"""
        # 簡易実装として、空のリストを返す
        return []
    
    def _extract_decision_window_data(self, track_data, decision_time):
        """決断ポイントの前後データを抽出"""
        # 簡易実装として、仮のデータを返す
        return {
            "before": track_data,
            "after": track_data
        }
    
    def _evaluate_single_decision(self, decision_type, before_after_data, wind_data, context):
        """単一の決断を評価"""
        # 簡易実装として、仮の評価を返す
        return {
            "score": np.random.uniform(5, 10),
            "strengths": ["適切な判断"],
            "weaknesses": [],
            "details": {}
        }
    
    def _evaluate_wind_shift_response_quality(self, decision_evaluations, wind_data):
        """風向変化への対応品質を評価"""
        # 簡易実装として、ランダムな評価を返す
        return np.random.uniform(5, 10)
    
    def _evaluate_decision_timing(self, decision_evaluations):
        """判断のタイミングを評価"""
        # 簡易実装として、ランダムな評価を返す
        return np.random.uniform(5, 10)
    
    def _detect_wind_shifts(self, wind_data):
        """風向変化を検出"""
        # 簡易実装として、空のリストを返す
        return []
    
    def _extract_wind_shift_window_data(self, track_data, shift_time):
        """風向変化前後のデータを抽出"""
        # 簡易実装として、仮のデータを返す
        return {
            "before": track_data,
            "after": track_data
        }
    
    def _evaluate_strategy_change_after_shift(self, before_data, after_data, shift_direction, shift_magnitude):
        """風向変化後の戦術変更を評価"""
        # 簡易実装として、ランダムな評価を返す
        return np.random.uniform(5, 10)
    
    def _evaluate_minor_shift_adjustment(self, before_data, after_data, shift_direction, shift_magnitude):
        """小さな風向変化への調整を評価"""
        # 簡易実装として、ランダムな評価を返す
        return np.random.uniform(5, 10)
    
    def _detect_wind_speed_changes(self, wind_data):
        """風速変化を検出"""
        # 簡易実装として、空のリストを返す
        return []
    
    def _evaluate_wind_speed_adaptation(self, track_data, speed_changes):
        """風速変化への適応を評価"""
        # 簡易実装として、ランダムな評価を返す
        return np.random.uniform(5, 10)
    
    def _simulate_different_tack_timing(self, track_data, wind_data, tack_point, time_offset):
        """異なるタックタイミングをシミュレーション"""
        # 簡易実装として、仮の結果を返す
        return {
            "estimated_score": np.random.uniform(5, 10),
            "details": {
                "estimated_vmg_change": np.random.uniform(-0.1, 0.1),
                "position_impact": "favorable" if np.random.random() > 0.5 else "unfavorable"
            }
        }
    
    def _simulate_different_layline_approach(self, track_data, wind_data, mark, approach_type):
        """異なるレイラインアプローチをシミュレーション"""
        # 簡易実装として、仮の結果を返す
        return {
            "estimated_score": np.random.uniform(5, 10),
            "details": {
                "distance_change": np.random.uniform(-50, 50),
                "risk_change": np.random.uniform(-0.2, 0.2)
            }
        }
    
    def _simulate_wind_shift_response(self, track_data, wind_data, shift_point, response_type):
        """風向変化への対応をシミュレーション"""
        # 簡易実装として、仮の結果を返す
        return {
            "estimated_score": np.random.uniform(5, 10),
            "details": {
                "position_gain": np.random.uniform(-100, 100),
                "vmg_impact": np.random.uniform(-0.1, 0.1)
            }
        }
