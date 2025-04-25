#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ElementTypeの問題を診断するためのテストスクリプト
"""

import sys
import traceback

def main():
    print("テスト開始: ElementType診断")
    print(f"Pythonバージョン: {sys.version}")
    print(f"Pythonパス: {sys.path}")
    
    # ステップ1: モジュールのインポート
    try:
        print("\nステップ1: sailing_data_processor のインポート")
        import sailing_data_processor
        print(f"モジュールバージョン: {sailing_data_processor.__version__ if hasattr(sailing_data_processor, '__version__') else '不明'}")
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()
        return

    # ステップ2: template_model モジュールのインポート
    try:
        print("\nステップ2: template_model モジュールのインポート")
        from sailing_data_processor.reporting.templates import template_model
        print("テンプレートモデルのインポート成功")
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()
        return

    # ステップ3: ElementType 列挙型の確認
    try:
        print("\nステップ3: ElementType 列挙型の確認")
        from sailing_data_processor.reporting.templates.template_model import ElementType
        print(f"ElementType クラス: {ElementType}")
        print(f"ElementType メンバー: {list(ElementType)}")
        print(f"ElementType 値: {[e.value for e in ElementType]}")
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()
        return

    # ステップ4: base_element モジュールのインポート
    try:
        print("\nステップ4: base_element モジュールのインポート")
        from sailing_data_processor.reporting.elements import base_element
        print("base_element モジュールのインポート成功")
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()
        return

    # ステップ5: content_elements モジュールのインポート
    try:
        print("\nステップ5: content_elements モジュールのインポート")
        from sailing_data_processor.reporting.elements import content_elements
        print("content_elements モジュールのインポート成功")
    except Exception as e:
        print(f"エラー: {e}")
        traceback.print_exc()
        return

    print("\nテスト完了")

if __name__ == "__main__":
    main()
