"""
wind_field_interpolator.py のパッチ

このパッチは以下の修正を適用します：
1. `interpolate_wind_field` メソッドに `qhull_options` パラメータを追加
2. LinearNDInterpolator と NearestNDInterpolator にこのオプションを渡すように修正
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをPathオブジェクトとして取得
project_root = Path(__file__).resolve().parent.parent

# パッチの対象ファイル
target_file = project_root / "sailing_data_processor" / "wind_field_interpolator.py"

def apply_patch():
    """パッチを適用する"""
    if not target_file.exists():
        print(f"対象ファイルが見つかりません: {target_file}")
        return False
    
    # ファイルを読み込み
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正パターン1: interpolate_wind_field メソッドのシグネチャを修正
    old_signature = "    def interpolate_wind_field(self, target_time: datetime, \n                             resolution: int = None, \n                             method: str = None) -> Optional[Dict[str, Any]]:"
    new_signature = "    def interpolate_wind_field(self, target_time: datetime, \n                             resolution: int = None, \n                             method: str = None,\n                             qhull_options: str = None) -> Optional[Dict[str, Any]]:"
    
    if old_signature not in content:
        print("シグネチャが見つかりません。ファイルが変更されている可能性があります。")
        return False
    
    content = content.replace(old_signature, new_signature)
    
    # 修正パターン2: _resample_wind_field メソッドの修正 (LinearNDInterpolator使用箇所)
    old_code = "            # LinearNDInterpolatorはDelaunay三角形分割を使用\n            interp_sin = LinearNDInterpolator(points, values_dir_sin)\n            interp_cos = LinearNDInterpolator(points, values_dir_cos)\n            interp_speed = LinearNDInterpolator(points, values_speed)\n            interp_conf = LinearNDInterpolator(points, values_conf)"
    
    new_code = "            # LinearNDInterpolatorはDelaunay三角形分割を使用\n            # qhull_optionsをメソッドパラメータから取得、または実装内でQJ指定\n            qhull_opt = qhull_options or 'QJ'  # QJオプションでエラー回避\n            \n            interp_sin = LinearNDInterpolator(points, values_dir_sin, qhull_options=qhull_opt)\n            interp_cos = LinearNDInterpolator(points, values_dir_cos, qhull_options=qhull_opt)\n            interp_speed = LinearNDInterpolator(points, values_speed, qhull_options=qhull_opt)\n            interp_conf = LinearNDInterpolator(points, values_conf, qhull_options=qhull_opt)"
    
    if old_code not in content:
        print("LinearNDInterpolator実装部分が見つかりません。")
        # 失敗してもファイル全体は保存しない
        return False
    
    content = content.replace(old_code, new_code)
    
    # 修正パターン3: _resample_wind_field メソッドのシグネチャを修正
    old_method_signature = "    def _resample_wind_field(self, wind_field: Dict[str, Any], resolution: int) -> Dict[str, Any]:"
    new_method_signature = "    def _resample_wind_field(self, wind_field: Dict[str, Any], resolution: int, qhull_options: str = None) -> Dict[str, Any]:"
    
    if old_method_signature not in content:
        print("_resample_wind_field シグネチャが見つかりません。")
        return False
    
    content = content.replace(old_method_signature, new_method_signature)
    
    # 修正パターン4: 各メソッドから_resample_wind_fieldを呼び出す際にパラメータを渡す
    # idw_interpolateメソッド内
    old_resample_call1 = "return self._resample_wind_field(nearest_field, resolution)"
    new_resample_call1 = "return self._resample_wind_field(nearest_field, resolution, qhull_options)"
    
    old_resample_call2 = "        field1_resampled = self._resample_wind_field(field1, resolution)\n        field2_resampled = self._resample_wind_field(field2, resolution)"
    new_resample_call2 = "        field1_resampled = self._resample_wind_field(field1, resolution, qhull_options)\n        field2_resampled = self._resample_wind_field(field2, resolution, qhull_options)"
    
    content = content.replace(old_resample_call1, new_resample_call1)
    content = content.replace(old_resample_call2, new_resample_call2)
    
    # 修正を適用
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"パッチ適用成功: {target_file}")
    return True

if __name__ == "__main__":
    print("WindFieldInterpolator パッチの適用を開始します...")
    if apply_patch():
        print("パッチ適用完了")
        sys.exit(0)
    else:
        print("パッチ適用失敗")
        sys.exit(1)
