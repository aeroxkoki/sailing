# -*- coding: utf-8 -*-
"""
Correction options module.
This module provides functions for defining correction options for data issues.
"""

from typing import Dict, List, Any


def get_correction_options(problem_type: str) -> List[Dict[str, Any]]:
    """
    問題タイプに基づいた修正オプションを取得
    
    Parameters
    ----------
    problem_type : str
        問題タイプ ('missing_data', 'out_of_range', 'duplicates', 'spatial_anomalies', 'temporal_anomalies')
        
    Returns
    -------
    List[Dict[str, Any]]
        修正オプションのリスト
    """
    # 問題タイプに対応する修正オプションのマッピング
    options_mapping = {
        "missing_data": [
            {
                "id": "interpolate_linear",
                "name": "線形補間",
                "description": "前後の値から欠損値を補間します",
                "fix_type": "interpolate",
                "params": {"method": "linear"}
            },
            {
                "id": "interpolate_time",
                "name": "時間ベース補間",
                "description": "時間の経過に基づいて補間します",
                "fix_type": "interpolate",
                "params": {"method": "time"}
            },
            {
                "id": "fill_forward",
                "name": "前方向に埋める",
                "description": "直前の値で欠損値を埋めます",
                "fix_type": "interpolate",
                "params": {"method": "ffill"}
            },
            {
                "id": "fill_backward",
                "name": "後方向に埋める",
                "description": "直後の値で欠損値を埋めます",
                "fix_type": "interpolate",
                "params": {"method": "bfill"}
            },
            {
                "id": "remove_rows",
                "name": "行を削除",
                "description": "欠損値を含む行を削除します",
                "fix_type": "remove",
                "params": {}
            }
        ],
        "out_of_range": [
            {
                "id": "clip_values",
                "name": "値を制限",
                "description": "範囲外の値を最小値または最大値に制限します",
                "fix_type": "replace",
                "params": {"method": "clip"}
            },
            {
                "id": "replace_with_null",
                "name": "NULLに置換",
                "description": "範囲外の値をNULLに置き換えます",
                "fix_type": "replace",
                "params": {"method": "null"}
            },
            {
                "id": "remove_rows",
                "name": "行を削除",
                "description": "範囲外の値を含む行を削除します",
                "fix_type": "remove",
                "params": {}
            }
        ],
        "duplicates": [
            {
                "id": "offset_timestamps",
                "name": "タイムスタンプをずらす",
                "description": "重複するタイムスタンプを少しずつずらします",
                "fix_type": "adjust",
                "params": {"method": "offset"}
            },
            {
                "id": "keep_first",
                "name": "最初の行を保持",
                "description": "重複するうち最初の行のみを保持します",
                "fix_type": "remove",
                "params": {"method": "keep_first"}
            },
            {
                "id": "remove_all",
                "name": "すべて削除",
                "description": "重複するタイムスタンプを持つ行をすべて削除します",
                "fix_type": "remove",
                "params": {"method": "remove_all"}
            }
        ],
        "spatial_anomalies": [
            {
                "id": "spatial_interpolate",
                "name": "位置を補間",
                "description": "異常な位置を前後のポイントから補間します",
                "fix_type": "interpolate",
                "params": {"columns": ["latitude", "longitude"]}
            },
            {
                "id": "spatial_remove",
                "name": "異常ポイントを削除",
                "description": "空間的に異常なポイントを削除します",
                "fix_type": "remove",
                "params": {}
            }
        ],
        "temporal_anomalies": [
            {
                "id": "remove_reverse",
                "name": "逆行を削除",
                "description": "タイムスタンプが逆行しているポイントを削除します",
                "fix_type": "remove",
                "params": {"filter": "reverse"}
            },
            {
                "id": "fix_timestamps",
                "name": "タイムスタンプを修正",
                "description": "タイムスタンプが逆行している場合に修正します",
                "fix_type": "adjust",
                "params": {"method": "fix_reverse"}
            },
            {
                "id": "mark_gaps",
                "name": "ギャップをマーク",
                "description": "大きな時間ギャップをメタデータにマークします",
                "fix_type": "metadata",
                "params": {"method": "mark_gaps"}
            }
        ]
    }
    
    # 問題タイプに対応するオプションを返す
    return options_mapping.get(problem_type, [])
