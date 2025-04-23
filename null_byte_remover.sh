#\!/bin/bash

# nullバイトを削除するスクリプト
find backend -name "*.py" -type f | while read file; do
  # ファイルにnullバイトが含まれているか確認
  if grep -q "$(printf '\0')" "$file" 2>/dev/null; then
    echo "修正: $file"
    
    # 一時ファイル作成
    temp_file=$(mktemp)
    
    # nullバイトを削除して一時ファイルに書き込み
    tr -d '\000' < "$file" > "$temp_file"
    
    # 一時ファイルを元のファイルにコピー
    mv "$temp_file" "$file"
  fi
done

echo "完了: すべてのPythonファイルからnullバイトを削除しました"
