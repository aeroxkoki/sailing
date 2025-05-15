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
        List[Dict]
            各時間点の風場データ（テスト用にフォーマット調整）
        """
        # 元の実装を呼び出し
        orig_result = super().create_spatiotemporal_wind_field(time_points, grid_resolution)
        
        # テスト用に出力形式を変換
        result_list = []
        for time_point, field_data in orig_result.items():
            # テスト用フォーマットに変換
            test_format = {
                'time': time_point,
                'grid': {
                    'lat_grid': field_data.get('lat_grid'),
                    'lon_grid': field_data.get('lon_grid')
                },
                'wind_directions': field_data.get('wind_direction'),
                'wind_speeds': field_data.get('wind_speed')
            }
            result_list.append(test_format)
        
        return result_list
