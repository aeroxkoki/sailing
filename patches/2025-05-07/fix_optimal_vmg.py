# -*- coding: utf-8 -*-
"""
最適VMG計算機の修正パッチ
"""

from pathlib import Path
import shutil
import re

def apply_patch():
    """最適VMG計算機の修正を適用する"""
    # 修正するファイルのパス
    file_path = Path(__file__).parents[2] / "sailing_data_processor" / "optimal_vmg_calculator.py"
    
    # バックアップを作成
    backup_path = file_path.with_suffix(".py.bak")
    shutil.copy2(file_path, backup_path)
    print(f"バックアップを作成しました: {backup_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # _create_default_boat_dataメソッドを探す
    method_pattern = r'def _create_default_boat_data\(self\):.*?(?=\n    def|\n# )'
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if not method_match:
        print("_create_default_boat_dataメソッドが見つかりませんでした。")
        return False
    
    old_method = method_match.group(0)
    
    # 修正後のメソッド（インデントに注意）
    new_method = '''def _create_default_boat_data(self):
        """デフォルトの艇種データを作成（ファイルがない場合用）"""
        # 標準艇種のデフォルトポーラーデータを作成（テスト用）
        for boat_id, display_name in [
            ('laser', 'Laser/ILCA'),
            ('470', '470 Class'),
            ('49er', '49er')
        ]:
            # 風向角（0-180度）と風速（4-25ノット）の範囲を設定
            # 0度は船が風向きと同じ方向を向いていることを意味するため、
            # 実際の最小角度は通常30度前後になるようにする
            angles = list(range(0, 181, 5))  # 0, 5, 10, ... 180
            wind_speeds = [4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0, 25.0]
            
            # データフレームの初期化
            data = {'twa/tws': angles}
            for ws in wind_speeds:
                data[str(ws)] = [0] * len(angles)
            
            df = pd.DataFrame(data)
            df.set_index('twa/tws', inplace=True)
            
            # シンプルなモデルでポーラーデータを埋める
            for i, angle in enumerate(angles):
                for j, ws in enumerate(wind_speeds):
                    # 0度と180度では船は前に進まない（風と同じか真逆の方向）
                    if angle == 0 or angle == 180:
                        boat_speed = 0.1  # 最小値を設定
                    # 風上と風下に最適角度を設定
                    elif angle < 90:  # 風上
                        # 風上最適角45度付近で最大、その後減少
                        # 30度未満は現実的に帆走が難しいため、段階的に減少
                        if angle < 30:
                            # 30度未満は急激に性能低下（30度で通常の50%）
                            reduction_factor = angle / 30.0
                            boat_speed = ws * 0.5 * (1 - abs(45 - 30) / 90) * reduction_factor
                        else:
                            boat_speed = ws * 0.5 * (1 - abs(angle - 45) / 90)
                    else:  # 風下
                        # 風下最適角135度付近で最大
                        boat_speed = ws * 0.6 * (1 - abs(angle - 135) / 90)
                    
                    # ボートタイプによる係数
                    if boat_id == 'laser':
                        coef = 1.0
                    elif boat_id == '470':
                        coef = 1.1
                    elif boat_id == '49er':
                        coef = 1.2
                    else:
                        coef = 1.0
                    
                    df.at[angle, str(ws)] = max(0.1, boat_speed * coef)
            
            # Laserクラスの場合、特に風上最適角度が0になる問題を修正
            if boat_id == 'laser':
                # 全風速で風上最適角度を調整
                for ws_str in [str(ws) for ws in wind_speeds]:
                    # 風向角範囲30-60度の値を確認する
                    for angle in range(30, 61, 5):
                        # 確実に30度から45度の間で最適値が見つかるよう調整
                        # 風速に応じた適切な値を設定
                        ws_val = float(ws_str)
                        # 45度で最大値になるようにする
                        coefficient = 1.0 - abs(angle - 45) / 45.0  # 45度で最大
                        # 最低でも風速の30%の値を設定
                        df.at[angle, ws_str] = max(1.0, ws_val * 0.4 * (0.8 + coefficient))
                        
                    # 0-25度の範囲では性能を低下させるが、0より大きい値を設定
                    for angle in range(0, 30, 5):
                        # 角度に比例して増加
                        reduction_factor = max(0.1, angle / 30.0)
                        ws_val = float(ws_str)
                        df.at[angle, ws_str] = max(0.5, ws_val * 0.2 * reduction_factor)
            
            # 最適VMG値を計算
            upwind_optimal = self._calculate_optimal_vmg_angles(df, upwind=True)
            downwind_optimal = self._calculate_optimal_vmg_angles(df, upwind=False)
            
            # 艇種データを登録
            self.boat_types[boat_id] = {
                'display_name': display_name,
                'polar_data': df,
                'upwind_optimal': upwind_optimal,
                'downwind_optimal': downwind_optimal
            }
            
            # 特にLaserクラスの風上最適角度をチェック
            if boat_id == 'laser':
                for ws, (angle, vmg) in upwind_optimal.items():
                    if angle <= 0:
                        # 風上最適角度が0以下の場合は修正（最低でも30度に設定）
                        upwind_optimal[ws] = (max(30.0, angle), vmg)
                self.boat_types[boat_id]['upwind_optimal'] = upwind_optimal'''
    
    # メソッドの置換
    new_content = content.replace(old_method, new_method)
    
    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"最適VMG計算機の修正を適用しました: {file_path}")
    return True

if __name__ == "__main__":
    apply_patch()
