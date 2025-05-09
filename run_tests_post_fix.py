# -*- coding: utf-8 -*-
"""
タック識別ロジックの修正後にテストを実行するスクリプト
"""

import sys
import os
import importlib

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# まずテスト用のモジュールを再読み込み
print("モジュールの再読み込み...")
import sailing_data_processor.strategy.strategy_detector_utils
importlib.reload(sailing_data_processor.strategy.strategy_detector_utils)
from sailing_data_processor.strategy.strategy_detector_utils import determine_tack_type

def run_tack_identification_tests():
    """修正されたタック識別ロジックのテスト"""
    print("\nタック識別ロジックのテスト\n")
    
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
    
    failures = 0
    
    print("各テストケースの実行結果:\n")
    for bearing, wind_direction, expected in test_cases:
        # 現在の実装でのタック判定
        tack_type = determine_tack_type(bearing, wind_direction)
        status = "✅ 成功" if tack_type == expected else "❌ 失敗"
        
        if tack_type != expected:
            failures += 1
        
        # 結果を表示
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
    
    if failures == 0:
        print("\n🎉 すべてのテストが成功しました！")
        return True
    else:
        print(f"\n❌ {failures}件のテストが失敗しました。")
        return False

# テストの実行
if __name__ == "__main__":
    print("タック識別ロジック修正後のテスト実行\n")
    success = run_tack_identification_tests()
    
    # 終了ステータスを設定
    sys.exit(0 if success else 1)
