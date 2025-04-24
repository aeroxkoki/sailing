# -*- coding: utf-8 -*-
"""
スキルレベル対応改善提案機能

セーラーのスキルレベルに合わせたパーソナライズされた改善提案を生成する機能です。
戦略評価や重要ポイント分析の結果に基づいて、セーラーの成長に役立つ提案を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
import logging
import json
from collections import defaultdict

# ロガーの設定
logger = logging.getLogger(__name__)

class ImprovementAdvisor:
    """
    スキルレベル対応改善提案生成器
    
    分析結果とセーラーのスキルレベルに基づいて
    パーソナライズされた改善提案を生成します。
    """
    
    # スキルレベル定義
    SKILL_LEVELS = {
        "beginner": 1,      # 初心者
        "intermediate": 2,  # 中級者
        "advanced": 3,      # 上級者
        "expert": 4,        # エキスパート
        "professional": 5   # プロフェッショナル
    }
    
    def __init__(self, sailor_profile=None, analysis_level="advanced"):
        """
        初期化
        
        Parameters
        ----------
        sailor_profile : dict, optional
            セーラープロファイル情報, by default None
        analysis_level : str, optional
            分析レベル, by default "advanced"
        """
        self.sailor_profile = sailor_profile or {}
        self.analysis_level = analysis_level
        
        # セーラーのスキルレベル取得
        self.skill_level = self._determine_skill_level()
        
        # 知識ベースの設定
        self._setup_knowledge_base()
        
        logger.info(f"ImprovementAdvisor initialized with skill level: {self.skill_level}")
    
    def _determine_skill_level(self):
        """セーラーのスキルレベルを決定"""
        # プロファイルからスキルレベルを推定または取得
        if "skill_level" in self.sailor_profile:
            level_str = self.sailor_profile["skill_level"]
            return self.SKILL_LEVELS.get(level_str, 2)  # デフォルトは中級者
        
        # スキルレベル関連情報がある場合
        if "experience_years" in self.sailor_profile:
            years = self.sailor_profile["experience_years"]
            
            # 経験年数に基づく簡易判定
            if years < 2:
                return self.SKILL_LEVELS["beginner"]
            elif years < 5:
                return self.SKILL_LEVELS["intermediate"]
            elif years < 10:
                return self.SKILL_LEVELS["advanced"]
            else:
                return self.SKILL_LEVELS["expert"]
        
        # 競技レベル情報がある場合
        if "competition_level" in self.sailor_profile:
            comp_level = self.sailor_profile["competition_level"]
            
            # 競技レベルに基づく判定
            if comp_level in ["国際", "international", "olympic"]:
                return self.SKILL_LEVELS["professional"]
            elif comp_level in ["国内", "national"]:
                return self.SKILL_LEVELS["expert"]
            elif comp_level in ["地域", "regional"]:
                return self.SKILL_LEVELS["advanced"]
            elif comp_level in ["クラブ", "club"]:
                return self.SKILL_LEVELS["intermediate"]
            else:
                return self.SKILL_LEVELS["beginner"]
        
        # デフォルトは中級者
        return self.SKILL_LEVELS["intermediate"]
    
    def _setup_knowledge_base(self):
        """知識ベースのセットアップ"""
        # 改善領域のカテゴリ（基本スキル、戦術、技術、精神面など）
        self.improvement_categories = {
            "basic_skills": {
                "name": "基本スキル",
                "relevance": {
                    "beginner": 1.0,    # 非常に関連性が高い
                    "intermediate": 0.7,
                    "advanced": 0.3,
                    "expert": 0.1,
                    "professional": 0.0  # 関連性なし
                }
            },
            "technical_skills": {
                "name": "技術スキル",
                "relevance": {
                    "beginner": 0.8,
                    "intermediate": 1.0,  # 最も関連性が高い
                    "advanced": 0.8,
                    "expert": 0.5,
                    "professional": 0.3
                }
            },
            "tactical_skills": {
                "name": "戦術スキル",
                "relevance": {
                    "beginner": 0.2,
                    "intermediate": 0.7,
                    "advanced": 1.0,    # 最も関連性が高い
                    "expert": 0.9,
                    "professional": 0.8
                }
            },
            "strategic_skills": {
                "name": "戦略スキル",
                "relevance": {
                    "beginner": 0.1,
                    "intermediate": 0.4,
                    "advanced": 0.8,
                    "expert": 1.0,      # 最も関連性が高い
                    "professional": 1.0
                }
            },
            "mental_skills": {
                "name": "メンタルスキル",
                "relevance": {
                    "beginner": 0.4,
                    "intermediate": 0.6,
                    "advanced": 0.8,
                    "expert": 0.9,
                    "professional": 1.0   # 最も関連性が高い
                }
            },
            "physical_skills": {
                "name": "フィジカルスキル",
                "relevance": {
                    "beginner": 0.5,
                    "intermediate": 0.7,
                    "advanced": 0.8,
                    "expert": 0.9,
                    "professional": 1.0
                }
            }
        }
        
        # 具体的な改善領域（各カテゴリに複数の領域）
        self.improvement_areas = {
            "boat_handling": {
                "name": "艇の操作",
                "category": "basic_skills",
                "skill_specific_advice": {
                    "beginner": "基本的な艇の操作方法を習得し、安定した帆走ができるようにしましょう。",
                    "intermediate": "様々な風速や波の状況での艇のコントロールを向上させましょう。",
                    "advanced": "微妙な体重移動や帆の調整で艇の性能を最大限に引き出しましょう。",
                    "expert": "極限状況でも正確な艇のコントロールを維持する技術を磨きましょう。",
                    "professional": "艇の限界性能を引き出すための最適な操作を常に探求しましょう。"
                }
            },
            "sail_trim": {
                "name": "セール調整",
                "category": "technical_skills",
                "skill_specific_advice": {
                    "beginner": "基本的なセールトリム（メインシートとジブシート）の効果を理解しましょう。",
                    "intermediate": "風速や風向に応じたセールトリムの調整方法を習得しましょう。",
                    "advanced": "風のシフトや変化に素早く対応したセール調整を行いましょう。",
                    "expert": "繊細なセール形状の調整でパフォーマンスを最適化しましょう。",
                    "professional": "風と波の条件に応じた最適なセール形状を常に維持しましょう。"
                }
            },
            "tacking_gybing": {
                "name": "タック・ジャイブ",
                "category": "technical_skills",
                "skill_specific_advice": {
                    "beginner": "安定したタックとジャイブの基本手順を練習しましょう。",
                    "intermediate": "タックとジャイブ時の速度損失を最小限に抑える技術を向上させましょう。",
                    "advanced": "様々な風と波の条件でも滑らかで速いタック・ジャイブを実行しましょう。",
                    "expert": "戦略的なタイミングでのタック・ジャイブの実行技術を磨きましょう。",
                    "professional": "極限状況でも完璧なタック・ジャイブを実行する技術を維持しましょう。"
                }
            },
            "start_technique": {
                "name": "スタート技術",
                "category": "tactical_skills",
                "skill_specific_advice": {
                    "beginner": "スタートラインの理解とタイミングの基本を習得しましょう。",
                    "intermediate": "有利なスタートポジションの確保と正確なタイミングを練習しましょう。",
                    "advanced": "他艇との駆け引きを考慮したスタート戦術を向上させましょう。",
                    "expert": "様々なスタート状況に対応した高度な戦術を磨きましょう。",
                    "professional": "レース全体を考慮した最適なスタート戦略を実行しましょう。"
                }
            },
            "wind_strategy": {
                "name": "風の戦略",
                "category": "strategic_skills",
                "skill_specific_advice": {
                    "beginner": "風の方向と強さの基本的な読み方を学びましょう。",
                    "intermediate": "風のシフトやパターンを予測し、基本的な戦略に活かしましょう。",
                    "advanced": "風の地形効果や時間変化を考慮した戦略を練習しましょう。",
                    "expert": "微妙な風の変化を予測し、リスク管理を含めた戦略を立てましょう。",
                    "professional": "複雑な風況での最適な戦略決定と実行を極めましょう。"
                }
            },
            "mark_rounding": {
                "name": "マーク回航",
                "category": "tactical_skills",
                "skill_specific_advice": {
                    "beginner": "安全で基本的なマーク回航の手順を習得しましょう。",
                    "intermediate": "効率的なマーク回航とスムーズな艇の操作を練習しましょう。",
                    "advanced": "最適なアプローチ角度と他艇との関係を考慮した回航を習得しましょう。",
                    "expert": "戦略的なマーク回航と次のレグへの効率的な移行を極めましょう。",
                    "professional": "混雑したマークでも最大限の優位性を得る回航技術を磨きましょう。"
                }
            },
            "layline_judgment": {
                "name": "レイライン判断",
                "category": "tactical_skills",
                "skill_specific_advice": {
                    "beginner": "レイラインの基本概念と重要性を理解しましょう。",
                    "intermediate": "風向変化を考慮したレイライン判断を練習しましょう。",
                    "advanced": "他艇との関係と風の予測に基づいたレイライン判断を向上させましょう。",
                    "expert": "リスク分析を含めた戦略的なレイライン判断を磨きましょう。",
                    "professional": "様々な状況での最適なレイラインアプローチを極めましょう。"
                }
            },
            "fleet_positioning": {
                "name": "フリートポジショニング",
                "category": "strategic_skills",
                "skill_specific_advice": {
                    "beginner": "フリート内での位置取りの基本概念を学びましょう。",
                    "intermediate": "風の状況に応じた基本的なフリートポジショニングを練習しましょう。",
                    "advanced": "他艇との関係を考慮した戦略的なポジショニングを習得しましょう。",
                    "expert": "レース全体を見据えた高度なポジショニング戦略を磨きましょう。",
                    "professional": "様々なレース状況での最適なリスク管理とポジショニングを極めましょう。"
                }
            },
            "risk_management": {
                "name": "リスク管理",
                "category": "strategic_skills",
                "skill_specific_advice": {
                    "beginner": "基本的な安全管理とリスク認識を習得しましょう。",
                    "intermediate": "風や他艇の状況に応じたリスク評価を練習しましょう。",
                    "advanced": "戦略的なリスク判断とトレードオフの評価を向上させましょう。",
                    "expert": "様々な状況での最適なリスク・リワード判断を磨きましょう。",
                    "professional": "レース展開全体を考慮した高度なリスク戦略を極めましょう。"
                }
            },
            "decision_making": {
                "name": "意思決定",
                "category": "mental_skills",
                "skill_specific_advice": {
                    "beginner": "基本的な判断基準と意思決定の練習を始めましょう。",
                    "intermediate": "プレッシャーの中での冷静な判断力を養いましょう。",
                    "advanced": "複数の要素を考慮した素早い意思決定能力を向上させましょう。",
                    "expert": "不確実な状況での最適な判断力を磨きましょう。",
                    "professional": "限られた情報での直感的かつ正確な判断能力を極めましょう。"
                }
            },
            "adaptation": {
                "name": "適応力",
                "category": "mental_skills",
                "skill_specific_advice": {
                    "beginner": "変化する風や波への基本的な対応方法を学びましょう。",
                    "intermediate": "様々な条件変化に素早く対応する技術を練習しましょう。",
                    "advanced": "予期せぬ状況変化への効果的な適応力を向上させましょう。",
                    "expert": "極端な条件変化でも冷静に対応できる適応力を磨きましょう。",
                    "professional": "あらゆる状況変化を機会に変える高度な適応力を極めましょう。"
                }
            },
            "endurance": {
                "name": "持久力",
                "category": "physical_skills",
                "skill_specific_advice": {
                    "beginner": "基本的な体力づくりと長時間の集中力維持を練習しましょう。",
                    "intermediate": "セーリング特有の筋持久力トレーニングを取り入れましょう。",
                    "advanced": "長時間レースでのパフォーマンス維持能力を向上させましょう。",
                    "expert": "極限状況でも高いパフォーマンスを維持する能力を磨きましょう。",
                    "professional": "連続したレースでも最高のパフォーマンスを維持する能力を極めましょう。"
                }
            }
        }
        
        # 練習課題のデータベース（各改善領域ごとの具体的練習）
        self.practice_tasks = {
            "boat_handling": [
                {
                    "name": "直線保持練習",
                    "description": "風上または風下に向かって、一定の角度を保ったまま直線帆走する練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "バランス感覚練習",
                    "description": "様々な風速で艇のバランスを維持しながら帆走する練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "微細操作練習",
                    "description": "最小限の舵の動きで艇をコントロールする練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "極限状況練習",
                    "description": "強風や波の中での艇のコントロール技術を磨く練習。",
                    "skill_level": ["advanced", "expert", "professional"]
                }
            ],
            "sail_trim": [
                {
                    "name": "基本トリム練習",
                    "description": "風速と風向に応じた基本的なセールトリムの調整練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "微調整練習",
                    "description": "セールの形状を微調整してパフォーマンスを最適化する練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "動的トリム練習",
                    "description": "風や波の変化に応じて素早くセールトリムを調整する練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "極限パフォーマンス練習",
                    "description": "様々な条件で艇の限界性能を引き出すセールトリムの練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "tacking_gybing": [
                {
                    "name": "基本マニューバー練習",
                    "description": "基本的なタックとジャイブの手順を反復練習。",
                    "skill_level": ["beginner"]
                },
                {
                    "name": "速度損失最小化練習",
                    "description": "マニューバー時の速度損失を最小限に抑える技術練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "素早いマニューバー練習",
                    "description": "戦術的状況での素早く正確なタックとジャイブの練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "極限状況マニューバー",
                    "description": "強風や波の中での完璧なマニューバー技術を磨く練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "start_technique": [
                {
                    "name": "スタートライン練習",
                    "description": "スタートラインに対する正確なアプローチとタイミングの練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "スタートポジション練習",
                    "description": "有利なスタートポジションの確保と維持の練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "他艇との駆け引き練習",
                    "description": "スタート前の他艇との駆け引きと戦術的ポジショニングの練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "リスクスタート練習",
                    "description": "リスクの高いスタート戦略の判断と実行の練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "wind_strategy": [
                {
                    "name": "風向変化観察練習",
                    "description": "風向の変化パターンを観察し記録する練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "シフト対応練習",
                    "description": "風向シフトに素早く対応した戦略変更の練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "風予測練習",
                    "description": "地形や雲の動きから風の変化を予測する練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "複合風況分析練習",
                    "description": "複雑な風況での最適な戦略決定プロセスの練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "mark_rounding": [
                {
                    "name": "基本回航練習",
                    "description": "基本的なマーク回航の手順と技術の練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "効率的回航練習",
                    "description": "速度損失を最小限に抑えた効率的なマーク回航の練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "混雑回航練習",
                    "description": "他艇が多い状況での戦術的なマーク回航の練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "戦略的回航練習",
                    "description": "次のレグを見据えた戦略的なマーク回航と位置取りの練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "layline_judgment": [
                {
                    "name": "基本レイライン練習",
                    "description": "基本的なレイライン判断とアプローチの練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "風変化考慮練習",
                    "description": "風向変化を考慮したレイライン判断の練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "他艇考慮練習",
                    "description": "他艇の位置を考慮した戦術的なレイライン判断の練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "リスク管理レイライン練習",
                    "description": "リスクと機会のバランスを考慮した高度なレイライン判断の練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "fleet_positioning": [
                {
                    "name": "基本ポジション練習",
                    "description": "フリート内での基本的な位置取りの理解と練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "風向考慮ポジション練習",
                    "description": "風向変化を考慮したフリートポジショニングの練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "戦略的ポジション練習",
                    "description": "他艇との関係を考慮した戦略的なポジショニングの練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "リスク分散ポジション練習",
                    "description": "レース全体を見据えたリスク管理とポジショニングの練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "risk_management": [
                {
                    "name": "基本リスク認識練習",
                    "description": "セーリング中の基本的なリスク要因の認識と評価の練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "リスク評価練習",
                    "description": "風や他艇の状況に応じたリスク評価と判断の練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "リスク・リワード練習",
                    "description": "リスクとリワードのバランスを考慮した意思決定の練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "戦略的リスク練習",
                    "description": "レース状況に応じた戦略的なリスク管理の練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "decision_making": [
                {
                    "name": "基本判断練習",
                    "description": "基本的な状況での意思決定プロセスを練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "複合判断練習",
                    "description": "複数の要素を考慮した意思決定の練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "プレッシャー下判断練習",
                    "description": "時間制約やプレッシャーの中での冷静な判断力を養う練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "直感的判断練習",
                    "description": "限られた情報での直感的かつ正確な判断能力を養う練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "adaptation": [
                {
                    "name": "条件変化対応練習",
                    "description": "変化する風や波の条件への基本的な対応練習。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "素早い適応練習",
                    "description": "様々な条件変化に素早く適応するための練習。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "予期せぬ変化対応練習",
                    "description": "予期せぬ状況変化への効果的な対応を練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "極限適応練習",
                    "description": "極端な条件変化を機会に変える高度な適応力の練習。",
                    "skill_level": ["expert", "professional"]
                }
            ],
            "endurance": [
                {
                    "name": "基本持久力練習",
                    "description": "セーリングに必要な基本的な筋持久力トレーニング。",
                    "skill_level": ["beginner", "intermediate"]
                },
                {
                    "name": "集中力持続練習",
                    "description": "長時間の集中力を維持するためのトレーニング。",
                    "skill_level": ["intermediate", "advanced"]
                },
                {
                    "name": "疲労下パフォーマンス練習",
                    "description": "疲労した状態でも高いパフォーマンスを維持する練習。",
                    "skill_level": ["advanced", "expert"]
                },
                {
                    "name": "連続パフォーマンス練習",
                    "description": "連続したレースでも最高のパフォーマンスを維持する練習。",
                    "skill_level": ["expert", "professional"]
                }
            ]
        }
    
    def generate_suggestions(self, strategy_evaluation, decision_points, race_context):
        """
        改善提案の生成
        
        Parameters
        ----------
        strategy_evaluation : dict
            戦略評価結果
        decision_points : dict
            重要決断ポイント
        race_context : dict
            レース状況情報
            
        Returns
        -------
        dict
            改善提案
        """
        logger.info("Generating improvement suggestions")
        
        try:
            # 改善領域の優先度付け
            prioritized_areas = self.prioritize_improvement_areas(strategy_evaluation)
            
            # 練習課題の生成
            practice_tasks = self.generate_practice_tasks(prioritized_areas)
            
            # 成長パスの作成
            development_path = self.create_development_path(
                self.skill_level, 
                prioritized_areas
            )
            
            # スキルベンチマークの生成
            skill_benchmarks = self.generate_skill_benchmarks(
                self.skill_level, 
                strategy_evaluation
            )
            
            # 改善提案の統合
            suggestions = {
                "priority_areas": prioritized_areas,
                "practice_tasks": practice_tasks,
                "development_path": development_path,
                "skill_benchmarks": skill_benchmarks,
                "summary": self._generate_suggestion_summary(
                    prioritized_areas, practice_tasks, development_path
                )
            }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}", exc_info=True)
            return {
                "priority_areas": [],
                "practice_tasks": [],
                "development_path": [],
                "skill_benchmarks": {},
                "summary": "改善提案の生成中にエラーが発生しました。"
            }
    
    def prioritize_improvement_areas(self, strategy_evaluation):
        """改善領域の優先度付け"""
        logger.info("Prioritizing improvement areas")
        
        # 戦略評価から弱みを抽出
        weaknesses = strategy_evaluation.get("weaknesses", [])
        
        # 弱みから改善領域へのマッピング
        improvement_areas = []
        
        # 弱みごとに対応する改善領域を特定
        for weakness in weaknesses:
            area = weakness.get("area", "")
            description = weakness.get("description", "")
            score = weakness.get("score", 5.0)
            
            # 対応する改善領域のマッピング
            if "upwind_strategy" in area:
                mapped_areas = ["wind_strategy", "tacking_gybing", "layline_judgment"]
            elif "downwind_strategy" in area:
                mapped_areas = ["wind_strategy", "sail_trim", "adaptation"]
            elif "start_execution" in area:
                mapped_areas = ["start_technique", "boat_handling", "decision_making"]
            elif "mark_rounding" in area:
                mapped_areas = ["mark_rounding", "boat_handling", "risk_management"]
            elif "tactical_decisions" in area:
                mapped_areas = ["decision_making", "risk_management", "adaptation"]
            elif "tack_efficiency" in area:
                mapped_areas = ["tacking_gybing", "boat_handling", "technical_skills"]
            elif "specific_mark_rounding" in area:
                mapped_areas = ["mark_rounding", "boat_handling"]
            elif "adaptation" in area:
                mapped_areas = ["adaptation", "wind_strategy", "decision_making"]
            else:
                # 明確なマッピングがない場合
                mapped_areas = ["decision_making", "adaptation", "technical_skills"]
            
            # 各マッピング領域を追加
            for mapped_area in mapped_areas:
                if mapped_area in self.improvement_areas:
                    area_info = self.improvement_areas[mapped_area]
                    
                    # このスキルレベルでの関連性を取得
                    skill_level_str = self._get_skill_level_str(self.skill_level)
                    relevance = self.improvement_categories[area_info["category"]]["relevance"].get(skill_level_str, 1.0)
                    
                    # 改善領域の情報
                    area_item = {
                        "area": mapped_area,
                        "display_name": area_info["name"],
                        "category": area_info["category"],
                        "category_name": self.improvement_categories[area_info["category"]]["name"],
                        "weakness_description": description,
                        "priority": (10 - score) * relevance,  # スコアが低いほど優先度が高い
                        "relevance": relevance,
                        "suggested_action": area_info["skill_specific_advice"][skill_level_str]
                    }
                    
                    improvement_areas.append(area_item)
        
        # 優先度でソート
        prioritized_areas = sorted(improvement_areas, key=lambda x: x["priority"], reverse=True)
        
        # 重複を除去（同じareaは最も優先度が高いもののみ残す）
        unique_areas = []
        added_areas = set()
        
        for area in prioritized_areas:
            if area["area"] not in added_areas:
                unique_areas.append(area)
                added_areas.add(area["area"])
        
        return unique_areas
    
    def generate_practice_tasks(self, improvement_areas):
        """練習課題の生成"""
        logger.info("Generating practice tasks")
        
        practice_tasks = []
        skill_level_str = self._get_skill_level_str(self.skill_level)
        
        # 各改善領域に対応する練習課題を抽出
        for area_info in improvement_areas[:3]:  # 上位3つの領域のみ
            area = area_info["area"]
            
            if area in self.practice_tasks:
                area_tasks = self.practice_tasks[area]
                
                # このスキルレベルに適した練習課題を選択
                suitable_tasks = [
                    task for task in area_tasks 
                    if skill_level_str in task["skill_level"]
                ]
                
                # スキルレベルに完全一致する課題がない場合、近いレベルの課題を選択
                if not suitable_tasks:
                    if self.skill_level <= 2:  # 初級〜中級
                        suitable_tasks = [
                            task for task in area_tasks 
                            if "beginner" in task["skill_level"] or "intermediate" in task["skill_level"]
                        ]
                    else:  # 上級〜プロ
                        suitable_tasks = [
                            task for task in area_tasks 
                            if "advanced" in task["skill_level"] or "expert" in task["skill_level"]
                        ]
                
                # タスクをランダムに選択（多様性を確保）
                np.random.shuffle(suitable_tasks)
                selected_tasks = suitable_tasks[:min(2, len(suitable_tasks))]
                
                for task in selected_tasks:
                    task_info = {
                        "area": area,
                        "area_name": area_info["display_name"],
                        "name": task["name"],
                        "description": task["description"],
                        "priority": area_info["priority"]
                    }
                    practice_tasks.append(task_info)
        
        # 優先度でソート
        return sorted(practice_tasks, key=lambda x: x["priority"], reverse=True)
    
    def create_development_path(self, current_skill_level, target_areas):
        """成長パスの作成"""
        logger.info("Creating development path")
        
        development_path = []
        current_level_str = self._get_skill_level_str(current_skill_level)
        
        # 次のスキルレベル
        next_level = min(current_skill_level + 1, self.SKILL_LEVELS["professional"])
        next_level_str = self._get_skill_level_str(next_level)
        
        # 対象領域から成長パスを作成
        for area_info in target_areas[:3]:  # 上位3つの領域のみ
            area = area_info["area"]
            
            if area in self.improvement_areas:
                # 現在のレベルと次のレベルのアドバイスを取得
                current_advice = self.improvement_areas[area]["skill_specific_advice"][current_level_str]
                next_advice = self.improvement_areas[area]["skill_specific_advice"][next_level_str]
                
                path_step = {
                    "area": area,
                    "area_name": area_info["display_name"],
                    "current_status": current_advice,
                    "next_goal": next_advice,
                    "priority": area_info["priority"]
                }
                
                development_path.append(path_step)
        
        # 優先度でソート
        return sorted(development_path, key=lambda x: x["priority"], reverse=True)
    
    def generate_skill_benchmarks(self, skill_level, performance_metrics):
        """スキルベンチマークの生成"""
        logger.info("Generating skill benchmarks")
        
        # 性能メトリクスからベンチマークを生成
        # 実際の実装では、同レベルのセーラーの平均値などを参照する
        skill_level_str = self._get_skill_level_str(skill_level)
        
        # 基本的なベンチマーク設定
        benchmarks = {
            "beginner": {
                "upwind_vmg_efficiency": 0.5,
                "downwind_vmg_efficiency": 0.5,
                "tack_efficiency": 0.4,
                "gybe_efficiency": 0.4,
                "start_timing_accuracy": 5.0,  # 秒単位の誤差
                "mark_rounding_efficiency": 0.5,
                "tactical_decision_quality": 0.4
            },
            "intermediate": {
                "upwind_vmg_efficiency": 0.65,
                "downwind_vmg_efficiency": 0.65,
                "tack_efficiency": 0.6,
                "gybe_efficiency": 0.6,
                "start_timing_accuracy": 3.0,
                "mark_rounding_efficiency": 0.65,
                "tactical_decision_quality": 0.6
            },
            "advanced": {
                "upwind_vmg_efficiency": 0.75,
                "downwind_vmg_efficiency": 0.75,
                "tack_efficiency": 0.75,
                "gybe_efficiency": 0.75,
                "start_timing_accuracy": 2.0,
                "mark_rounding_efficiency": 0.8,
                "tactical_decision_quality": 0.75
            },
            "expert": {
                "upwind_vmg_efficiency": 0.85,
                "downwind_vmg_efficiency": 0.85,
                "tack_efficiency": 0.85,
                "gybe_efficiency": 0.85,
                "start_timing_accuracy": 1.0,
                "mark_rounding_efficiency": 0.9,
                "tactical_decision_quality": 0.85
            },
            "professional": {
                "upwind_vmg_efficiency": 0.95,
                "downwind_vmg_efficiency": 0.95,
                "tack_efficiency": 0.95,
                "gybe_efficiency": 0.95,
                "start_timing_accuracy": 0.5,
                "mark_rounding_efficiency": 0.95,
                "tactical_decision_quality": 0.95
            }
        }
        
        # 現在のレベルのベンチマーク
        current_benchmarks = benchmarks.get(skill_level_str, benchmarks["intermediate"])
        
        # 次のレベルのベンチマーク
        next_level_str = self._get_skill_level_str(min(skill_level + 1, self.SKILL_LEVELS["professional"]))
        next_benchmarks = benchmarks.get(next_level_str, benchmarks["advanced"])
        
        # 実際のパフォーマンスを抽出（存在する場合）
        actual_performance = {}
        strategy_eval = performance_metrics.get("strategy_evaluation", {})
        
        if "upwind_strategy" in strategy_eval and "metrics" in strategy_eval["upwind_strategy"]:
            metrics = strategy_eval["upwind_strategy"]["metrics"]
            if "vmg_efficiency" in metrics:
                actual_performance["upwind_vmg_efficiency"] = metrics["vmg_efficiency"]
        
        if "downwind_strategy" in strategy_eval and "metrics" in strategy_eval["downwind_strategy"]:
            metrics = strategy_eval["downwind_strategy"]["metrics"]
            if "vmg_efficiency" in metrics:
                actual_performance["downwind_vmg_efficiency"] = metrics["vmg_efficiency"]
        
        # ベンチマーク情報の統合
        skill_benchmark_data = {
            "current_level": skill_level_str,
            "next_level": next_level_str,
            "current_benchmarks": current_benchmarks,
            "next_benchmarks": next_benchmarks,
            "actual_performance": actual_performance
        }
        
        return skill_benchmark_data
    
    def adapt_suggestions_to_skill(self, suggestions, skill_level):
        """提案をスキルレベルに適応させる"""
        logger.info(f"Adapting suggestions to skill level: {skill_level}")
        
        skill_level_str = self._get_skill_level_str(skill_level)
        
        # 提案の適応
        adapted_suggestions = suggestions.copy()
        
        # 優先領域の調整
        if "priority_areas" in adapted_suggestions:
            for area in adapted_suggestions["priority_areas"]:
                if "suggested_action" in area and area["area"] in self.improvement_areas:
                    area["suggested_action"] = self.improvement_areas[area["area"]]["skill_specific_advice"][skill_level_str]
        
        # 練習課題の調整
        if "practice_tasks" in adapted_suggestions:
            new_tasks = []
            for task in adapted_suggestions["practice_tasks"]:
                area = task.get("area")
                if area in self.practice_tasks:
                    # このスキルレベルに適した課題を検索
                    suitable_tasks = [
                        t for t in self.practice_tasks[area] 
                        if skill_level_str in t["skill_level"]
                    ]
                    
                    if suitable_tasks:
                        # ランダムに1つ選択
                        selected_task = np.random.choice(suitable_tasks)
                        new_task = task.copy()
                        new_task["name"] = selected_task["name"]
                        new_task["description"] = selected_task["description"]
                        new_tasks.append(new_task)
                    else:
                        new_tasks.append(task)
                else:
                    new_tasks.append(task)
            
            adapted_suggestions["practice_tasks"] = new_tasks
        
        # 成長パスの調整
        if "development_path" in adapted_suggestions:
            for path in adapted_suggestions["development_path"]:
                area = path.get("area")
                if area in self.improvement_areas:
                    next_level = min(skill_level + 1, self.SKILL_LEVELS["professional"])
                    next_level_str = self._get_skill_level_str(next_level)
                    
                    path["current_status"] = self.improvement_areas[area]["skill_specific_advice"][skill_level_str]
                    path["next_goal"] = self.improvement_areas[area]["skill_specific_advice"][next_level_str]
        
        return adapted_suggestions
    
    def track_progress(self, sailor_id, target_areas, past_performances):
        """進捗の追跡"""
        logger.info(f"Tracking progress for sailor: {sailor_id}")
        
        # 過去のパフォーマンスデータがない場合
        if not past_performances:
            return {
                "status": "insufficient_data",
                "message": "進捗を追跡するための過去のパフォーマンスデータが不足しています。"
            }
        
        # 時系列でソート
        sorted_performances = sorted(
            past_performances,
            key=lambda p: p.get("timestamp", datetime.min)
        )
        
        # 対象領域ごとの進捗を追跡
        area_progress = {}
        
        for area in target_areas:
            area_name = area.get("area")
            
            # 領域に関連するメトリクスを抽出
            metrics_values = []
            
            for perf in sorted_performances:
                # メトリクスのマッピング
                value = None
                
                if area_name == "boat_handling" or area_name == "technical_skills":
                    # 艇の操作や技術スキルは速度変動と関連
                    if "speed_stability" in perf:
                        value = perf["speed_stability"]
                    elif "speed_variability" in perf:
                        value = 1.0 - perf["speed_variability"]  # 変動が少ないほど安定
                
                elif area_name == "tacking_gybing":
                    # タック・ジャイブ効率
                    if "tack_efficiency" in perf:
                        value = perf["tack_efficiency"]
                    elif "maneuver_efficiency" in perf:
                        value = perf["maneuver_efficiency"]
                
                elif area_name == "start_technique":
                    # スタート技術
                    if "start_timing_error" in perf:
                        value = 10.0 - min(10.0, perf["start_timing_error"])  # 誤差が小さいほど高評価
                    elif "start_quality" in perf:
                        value = perf["start_quality"]
                
                elif area_name == "wind_strategy" or area_name == "tactical_skills":
                    # 風の戦略や戦術スキル
                    if "vmg_efficiency" in perf:
                        value = perf["vmg_efficiency"]
                    elif "tactical_score" in perf:
                        value = perf["tactical_score"]
                
                elif area_name == "mark_rounding":
                    # マーク回航
                    if "mark_rounding_efficiency" in perf:
                        value = perf["mark_rounding_efficiency"]
                    elif "mark_score" in perf:
                        value = perf["mark_score"]
                
                # 他の領域も同様に...
                
                if value is not None:
                    metrics_values.append({
                        "timestamp": perf.get("timestamp", datetime.min),
                        "value": value
                    })
            
            # 進捗の計算
            if metrics_values:
                first_value = metrics_values[0]["value"]
                last_value = metrics_values[-1]["value"]
                
                change = last_value - first_value
                change_percent = (change / max(0.01, first_value)) * 100
                
                area_progress[area_name] = {
                    "first_measurement": metrics_values[0],
                    "last_measurement": metrics_values[-1],
                    "change": change,
                    "change_percent": change_percent,
                    "trend": "improving" if change > 0 else "declining",
                    "all_measurements": metrics_values
                }
            else:
                area_progress[area_name] = {
                    "status": "no_data",
                    "message": f"{area_name}の進捗を追跡するためのメトリクスがありません。"
                }
        
        return {
            "status": "success",
            "area_progress": area_progress,
            "overall_progress": self._calculate_overall_progress(area_progress)
        }
    
    def _calculate_overall_progress(self, area_progress):
        """全体的な進捗の計算"""
        # 有効な進捗データを持つ領域のみを考慮
        valid_areas = [
            area for area, progress in area_progress.items()
            if "change" in progress
        ]
        
        if not valid_areas:
            return {
                "status": "insufficient_data",
                "message": "全体的な進捗を計算するためのデータが不足しています。"
            }
        
        # 変化率の平均を計算
        avg_change_percent = sum(
            area_progress[area]["change_percent"]
            for area in valid_areas
        ) / len(valid_areas)
        
        # 傾向の判定
        if avg_change_percent > 5:
            trend = "significant_improvement"
            message = "全体的に大きな改善が見られます。"
        elif avg_change_percent > 1:
            trend = "moderate_improvement"
            message = "全体的に穏やかな改善が見られます。"
        elif avg_change_percent >= -1:
            trend = "stable"
            message = "全体的に安定したパフォーマンスを維持しています。"
        elif avg_change_percent >= -5:
            trend = "slight_decline"
            message = "全体的に若干の低下傾向が見られます。"
        else:
            trend = "significant_decline"
            message = "全体的に大きな低下傾向が見られます。"
        
        return {
            "status": "success",
            "avg_change_percent": avg_change_percent,
            "trend": trend,
            "message": message
        }
    
    def _generate_suggestion_summary(self, prioritized_areas, practice_tasks, development_path):
        """提案サマリーの生成"""
        skill_level_str = self._get_skill_level_str(self.skill_level)
        
        # 優先領域の特定
        top_areas = prioritized_areas[:min(3, len(prioritized_areas))]
        area_names = [area["display_name"] for area in top_areas]
        
        if not area_names:
            return "改善提案を生成するための十分なデータがありません。より多くのパフォーマンスデータを収集してください。"
        
        # レベル別のメッセージ
        level_intro = ""
        if skill_level_str == "beginner":
            level_intro = "初心者レベルでは、基本的なスキルの習得が重要です。"
        elif skill_level_str == "intermediate":
            level_intro = "中級者レベルでは、基本スキルの応用と技術の向上が重要です。"
        elif skill_level_str == "advanced":
            level_intro = "上級者レベルでは、高度な技術と戦術の洗練が重要です。"
        elif skill_level_str == "expert":
            level_intro = "エキスパートレベルでは、繊細な技術の最適化と戦略的判断の向上が重要です。"
        else:  # professional
            level_intro = "プロフェッショナルレベルでは、極限状況でのパフォーマンス維持と微細な改善が重要です。"
        
        # 基本サマリー
        if len(area_names) == 1:
            areas_text = f"{area_names[0]}"
        elif len(area_names) == 2:
            areas_text = f"{area_names[0]}と{area_names[1]}"
        else:
            areas_text = f"{area_names[0]}、{area_names[1]}、および{area_names[2]}"
        
        summary = [
            f"{level_intro} 現在のパフォーマンスに基づくと、{areas_text}に焦点を当てた改善が推奨されます。"
        ]
        
        # 練習課題の紹介
        if practice_tasks:
            task_examples = [task["name"] for task in practice_tasks[:min(2, len(practice_tasks))]]
            task_text = f"{task_examples[0]}"
            if len(task_examples) > 1:
                task_text += f"や{task_examples[1]}"
            
            summary.append(f"具体的な練習として、{task_text}などに取り組むことで効果的なスキル向上が期待できます。")
        
        # 成長パスについて
        if development_path:
            next_level_str = self._get_skill_level_str(min(self.skill_level + 1, self.SKILL_LEVELS["professional"]))
            summary.append(f"{next_level_str}レベルへの成長を目指す場合、段階的な練習と継続的な評価が重要です。")
        
        return " ".join(summary)
    
    def _get_skill_level_str(self, level_int):
        """整数のスキルレベルから文字列表現に変換"""
        level_map = {v: k for k, v in self.SKILL_LEVELS.items()}
        return level_map.get(level_int, "intermediate")
