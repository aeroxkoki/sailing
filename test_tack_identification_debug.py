# -*- coding: utf-8 -*-
"""
タック識別ロジックのデバッグと最終修正

- determine_tack_type関数の問題を詳細に分析
- テストケースと期待値を確認
- ロジックを正確に修正
"""

import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 戦略検出ユーティリティをインポート
from sailing_data_processor.strategy.strategy_detector_utils import determine_tack_type

def debug_tack_identification():
    """タック識別の問題を詳細に分析する"""
    print("タック識別ロジックのデバッグ\n")
    
    # 問題のテストケース
    test_cases = [
        # 真風（風に正対）
        (0, 0, 'starboard'),     # 風に向かって直進
        (180, 180, 'starboard'), # 風から直接離れる
        
        # 境界線上
        (90, 270, 'starboard'),  # 真右から風
        (90, 90, 'port'),        # 真左から風
        
        # 360度の特殊ケース
        (0, 360, 'starboard'),   # 360° = 0°
        (360, 180, 'starboard'), # 360° = 0°
    ]
    
    print("問題の各テストケースを詳細に分析:\n")
    for bearing, wind_direction, expected in test_cases:
        # 現在の実装でのタック判定
        tack_type = determine_tack_type(bearing, wind_direction)
        status = "✅ 成功" if tack_type == expected else "❌ 失敗"
        
        # デバッグ情報を表示
        print(f"{status}: bearing={bearing}, wind_direction={wind_direction}")
        print(f"  期待値={expected}, 実際={tack_type}")
        
        # 詳細分析（風向と船の方向の関係）
        bearing_norm = bearing % 360
        wind_norm = wind_direction % 360
        relative_angle = (wind_norm - bearing_norm) % 360
        print(f"  正規化: bearing={bearing_norm}, wind={wind_norm}")
        print(f"  相対角度: {relative_angle}度")
        print(f"  風の位置: {'右舷' if 0 <= relative_angle <= 180 else '左舷'}")
        print()
    
    # 分析結果から問題点を特定
    print("\n問題の分析:")
    print("- 相対角度がちょうど0度または180度の場合の扱いが問題")
    print("- テストケースでは、風と船が同じ方向（0度や180度）の場合は starboard と期待")
    print("- 現在の実装では、0度の場合は port と判定している")
    
    # 修正案の提示
    print("\n修正案:")
    print("- 相対角度が0度と180度の場合の扱いを変更")
    print("- テストの期待値に合わせて、0度と180度の場合は starboard と判定")

def fix_tack_identification():
    """タック識別ロジックを修正する"""
    file_path = os.path.join(project_root, "sailing_data_processor", "strategy", "strategy_detector_utils.py")
    
    # バックアップを作成
    import shutil
    backup_path = file_path + ".bak3"
    shutil.copy2(file_path, backup_path)
    print(f"\nバックアップを作成しました: {backup_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # determine_tack_type関数を探す
    import re
    func_pattern = r'def determine_tack_type\(bearing: float, wind_direction: float\) -> str:.*?(?=\ndef|\Z)'
    func_match = re.search(func_pattern, content, re.DOTALL)
    
    if not func_match:
        print("determine_tack_type関数が見つかりませんでした。")
        return False
    
    old_func = func_match.group(0)
    
    # 修正後の関数
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
    
    # 風向と艇の方位の相対角度を計算
    relative_angle = (wind_norm - bearing_norm) % 360
    
    # テストケースに基づくルール：
    # 風が右から来る（相対角度 0-180度）または
    # 真正面/真後ろ（0度または180度）ならスターボードタック
    # それ以外（相対角度 181-359度）はポートタック
    if 0 <= relative_angle <= 180:
        return 'starboard'  # 風が右から来る場合または0/180度
    else:
        return 'port'       # 風が左から来る場合
'''
    
    # 関数の置換
    new_content = content.replace(old_func, new_func)
    
    # 修正を適用
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"タック識別ロジックの修正を適用しました: {file_path}")
    return True

def verify_fix():
    """修正が正しく適用されたか検証する"""
    print("\nタック識別ロジック修正の検証\n")
    
    # テストケース
    test_cases = [
        # 真風（風に正対）
        (0, 0, 'starboard'),     # 風に向かって直進
        (180, 180, 'starboard'), # 風から直接離れる
        
        # 境界線上
        (90, 270, 'starboard'),  # 真右から風
        (90, 90, 'port'),        # 真左から風
        
        # 360度の特殊ケース
        (0, 360, 'starboard'),   # 360° = 0°
        (360, 180, 'starboard'), # 360° = 0°
    ]
    
    all_passed = True
    for bearing, wind_direction, expected in test_cases:
        tack_type = determine_tack_type(bearing, wind_direction)
        if tack_type != expected:
            print(f"❌ 失敗: bearing={bearing}, wind_direction={wind_direction}, "
                  f"期待={expected}, 実際={tack_type}")
            all_passed = False
        else:
            print(f"✅ 成功: bearing={bearing}, wind_direction={wind_direction}, "
                  f"期待={expected}, 実際={tack_type}")
    
    if all_passed:
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print("\n❌ 一部のテストが失敗しました。")

if __name__ == "__main__":
    debug_tack_identification()
    fix_tack_identification()
    # 修正後のモジュールを再読み込み
    import importlib
    import sailing_data_processor.strategy.strategy_detector_utils
    importlib.reload(sailing_data_processor.strategy.strategy_detector_utils)
    from sailing_data_processor.strategy.strategy_detector_utils import determine_tack_type
    verify_fix()
