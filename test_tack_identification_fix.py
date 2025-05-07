# -*- coding: utf-8 -*-
"""
タック識別ロジックの修正が正しく適用されたかをテストするスクリプト
"""

import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 戦略検出ユーティリティを直接インポート
from sailing_data_processor.strategy.strategy_detector_utils import determine_tack_type

def test_determine_tack_type_edge_cases():
    """境界条件でのタックタイプ判定をテスト"""
    edge_cases = [
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
    for bearing, wind_direction, expected in edge_cases:
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
    print("タック識別ロジック修正テスト開始...\n")
    test_determine_tack_type_edge_cases()
