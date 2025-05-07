# -*- coding: utf-8 -*-
"""
異常値検出・修正ロジックの修正パッチ

- detect_and_fix_gps_anomaliesメソッドの異常値修正処理を改善
- 異常値閾値（max_speed_knots）より小さい値に確実に修正するよう調整
"""

from pathlib import Path
import shutil
import re

def apply_patch():
    """異常値検出ロジックの修正を適用する"""
    # 修正するファイルのパス
    file_path = Path(__file__).parents[2] / "sailing_data_processor" / "core_analysis.py"
    
    # バックアップを作成
    backup_path = file_path.with_suffix(".py.bak_anomaly")
    shutil.copy2(file_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # detect_and_fix_gps_anomaliesメソッドを探す
    method_pattern = r'def detect_and_fix_gps_anomalies\(self,.*?return df\s*\n\s*'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if not method_match:
        print("detect_and_fix_gps_anomaliesメソッドが見つかりませんでした。")
        return False
    
    old_method = method_match.group(0)
    
    # 修正後のメソッド
    new_method = '''    def detect_and_fix_gps_anomalies(self, boat_id: str, 
                                    max_speed_knots: float = 20.0,
                                    max_acceleration: float = 5.0,
                                    method: str = 'linear') -> pd.DataFrame:
        """
        GPS異常値を検出して修正する
        
        Parameters:
        -----------
        boat_id : str
            艇の識別ID
        max_speed_knots : float
            最大速度（ノット）
        max_acceleration : float
            最大加速度（m/s^2）
        method : str
            修正方法 ('linear' or 'kalman')
        
        Returns:
        --------
        pd.DataFrame
            修正されたデータ
        """
        if boat_id not in self.boat_data:
            raise ValueError(f"Boat ID '{boat_id}' not found")
        
        df = self.boat_data[boat_id].copy()
        
        # 異常な速度を検出し修正
        anomaly_mask = df['speed'] > max_speed_knots
        
        # 異常値を修正
        if anomaly_mask.any():
            # 前後の値の平均で補間
            for idx in df[anomaly_mask].index:
                prev_idx = idx - 1 if idx > 0 else idx
                next_idx = idx + 1 if idx < len(df) - 1 else idx
                
                if prev_idx == idx and next_idx == idx:
                    # 最初か最後の点の場合
                    df.loc[idx, 'speed'] = max_speed_knots * 0.8  # 最大速度の80%の値に設定
                else:
                    # 前後の平均値（最大でもmax_speed_knotsの90%を超えないようにする）
                    new_speed = (df.loc[prev_idx, 'speed'] + df.loc[next_idx, 'speed']) / 2
                    # 異常検出閾値より確実に小さい値にする
                    df.loc[idx, 'speed'] = min(new_speed, max_speed_knots * 0.8)
        
        # データを更新
        self.boat_data[boat_id] = df
        
        return df
    
'''
    
    # メソッドの置換
    new_content = content.replace(old_method, new_method)
    
    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"異常値検出修正ロジックを適用しました: {file_path}")
    return True

if __name__ == "__main__":
    apply_patch()
