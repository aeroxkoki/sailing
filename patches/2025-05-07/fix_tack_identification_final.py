# -*- coding: utf-8 -*-
"""
タック識別ロジック最終修正パッチ

- determine_tack_type関数のロジックを最終調整
- 風向と船の向きの相対的な関係の計算を正確に修正
"""

from pathlib import Path
import shutil
import re

def apply_patch():
    """タック識別ロジックの最終修正を適用する"""
    # 修正するファイルのパス
    file_path = Path(__file__).parents[2] / "sailing_data_processor" / "strategy" / "strategy_detector_utils.py"
    
    # バックアップを作成
    backup_path = file_path.with_suffix(".py.bak2")
    shutil.copy2(file_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # determine_tack_type関数を探す
    func_pattern = r'def determine_tack_type\(bearing: float, wind_direction: float\) -> str:.*?(?=\ndef|\Z)'
    func_match = re.search(func_pattern, content, re.DOTALL)
    
    if not func_match:
        print("determine_tack_type関数が見つかりませんでした。")
        return False
    
    old_func = func_match.group(0)
    
    # 修正後の関数（インデントに注意）
    new_func = '''def determine_tack_type(bearing: float, wind_direction: float) -> str:
    """
    タック種類を判定
    
    Parameters:
    -----------
    bearing : float
        進行方向角度（度）
    wind_direction : float
        風向角度（度、北を0として時計回り）
        
    Returns:
    --------
    str
        タック ('port'または'starboard')
    """
    # 方位の正規化
    bearing_norm = bearing % 360
    wind_norm = wind_direction % 360
    
    # 艇の進行方向に対して風がどちらから来るかを判定する
    # 風向と船が向いている方向の相対角度を計算
    
    # 風向と艇の向きの相対角度を計算
    # 風が右から来るならスターボード、左から来るならポート
    relative_angle = (wind_norm - bearing_norm) % 360
    
    # 0-180度なら右舷から風（スターボードタック）
    # 180-360度なら左舷から風（ポートタック）
    if 0 < relative_angle < 180:
        return 'starboard'  # 風が右から来る場合
    else:
        return 'port'       # 風が左から来る場合（180-360度または0度）
'''
    
    # 関数の置換
    new_content = content.replace(old_func, new_func)
    
    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"タック識別ロジックの最終修正を適用しました: {file_path}")
    return True

if __name__ == "__main__":
    apply_patch()
