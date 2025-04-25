#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本的なインポートテスト
"""

import sys
import time

def main():
    print("Simple test started")
    
    try:
        # sailing_data_processor のインポート
        import sailing_data_processor
        print(f"Successfully imported sailing_data_processor")
        
        # reporting.elements のインポート
        from sailing_data_processor.reporting.elements import content_elements
        print(f"Successfully imported content_elements")
        
        # reporting.templates のインポート
        from sailing_data_processor.reporting.templates import template_model
        print(f"Successfully imported template_model")
        
        # ElementType 列挙型の確認
        from sailing_data_processor.reporting.templates.template_model import ElementType
        print(f"ElementType values: {[e.value for e in ElementType]}")
        
        # テキスト要素のテスト作成
        from sailing_data_processor.reporting.elements.content_elements import TextElement
        from sailing_data_processor.reporting.templates.template_model import ElementModel
        
        model = ElementModel(ElementType.TEXT, {"content": "Hello, World!"})
        text_element = TextElement(model)
        print(f"Created TextElement: {text_element.element_type}")
        
        html = text_element.render({})
        print(f"Rendered HTML: {html}")
        
        print("All tests passed!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
