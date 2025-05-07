# -*- coding: utf-8 -*-
"""
タック識別ロジック修正パッチ
"""

from pathlib import Path
import shutil
import re

def apply_patch():
    """タック識別ロジックの修正を適用する"""
    # 修正するファイルのパス
    file_path = Path(__file__).parents[2] / "sailing_data_processor" / "strategy" / "strategy_detector_utils.py"
    
    # バックアップを作成
    backup_path = file_path.with_suffix(".py.bak")
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
    # 風向と艇の方位の角度差を計算
    # 風が艇の右側から来る場合はスターボードタック
    # 風が艇の左側から来る場合はポートタック
    
    # 艇の方位から風向を引く（艇の進行方向と風が来る方向の差）
    rel_wind = (bearing_norm - wind_norm) % 360
    
    # 0-180度の間なら右舷から風 → starboard tack
    # 180-360度の間なら左舷から風 → port tack
    return 'starboard' if 0 <= rel_wind <= 180 else 'port'
'''
    
    # 関数の置換
    new_content = content.replace(old_func, new_func)
    
    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"タック識別ロジックの修正を適用しました: {file_path}")
    return True

if __name__ == "__main__":
    apply_patch()
