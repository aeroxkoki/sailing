# -*- coding: utf-8 -*-
"""
sailing_data_processor.boat_data_fusion モジュール

複数艇のデータを融合して風向風速場を推定するモジュール
このファイルは後方互換性のために維持されていますが、
boat_fusion パッケージの使用を推奨します。
"""

# 先進的な実装を boat_fusion パッケージから再エクスポート
from .boat_fusion.boat_data_fusion_base import BoatDataFusionModel

# 後方互換性のためのエイリアス
BoatDataFusion = BoatDataFusionModel
