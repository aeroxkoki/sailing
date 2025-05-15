# -*- coding: utf-8 -*-
\"\"\"
sailing_data_processor.boat_fusion モジュール

複数船舶データを融合して風向風速を推定するモジュール
\"\"\"

# コア機能の実装をimport
from .boat_fusion.boat_data_fusion_base import BoatDataFusionModel as OriginalModel

# テスト用の互換性クラス
class BoatDataFusionModel(OriginalModel):
    """
    テスト互換性のためのアダプタークラス
    """
    
    def create_spatiotemporal_wind_field(self, time_points, grid_resolution=20):
        """
        時空間風場の生成（テスト互換性用にフォーマット調整）
        
        Parameters:
        -----------
        time_points : List[datetime]
            風場を生成する時間点のリスト
        grid_resolution : int
            空間グリッドの解像度
            
        Returns:
        --------
        Dict[datetime, Dict[str, Any]]
            各時間点の風場データ
        """
        # 元の実装を呼び出し
        return super().create_spatiotemporal_wind_field(time_points, grid_resolution)
        
        # 注：元のコードではList形式に変換していましたが、テストコードを
        # Dict形式に対応させたので、ここでは変換せずにそのまま返します
