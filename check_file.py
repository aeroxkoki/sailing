#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
単一ファイルの構文チェック
"""

import sys

def check_syntax_print_error():
    """ファイルの構文チェックを行い、エラーを表示する"""
    if len(sys.argv) < 2:
        print("Usage: python check_file.py filename")
        sys.exit(1)
    
    filename = sys.argv[1]
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        print(f"File reading successful: {filename}")
        try:
            compile(source, filename, 'exec')
            print("No syntax errors found!")
            sys.exit(0)
        except SyntaxError as e:
            print(f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}")
            
            # エラー箇所の前後の行を表示
            lines = source.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            
            print("\nContext:")
            for i in range(start, end):
                prefix = ">>> " if i + 1 == e.lineno else "    "
                print(f"{prefix}{i+1}: {lines[i]}")
            
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_syntax_print_error()
