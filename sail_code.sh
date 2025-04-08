#!/bin/bash
# sailing-strategy-analyzerプロジェクト用コマンドラッパー
# Claude Desktop/Codeとの接続問題を回避するためのスクリプト
# すべてのコマンド実行は必ずこのスクリプトを通してください

PROJECT_DIR="/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer"
cd "$PROJECT_DIR" || exit 1

# 環境変数を強制的に上書き
export EDITOR=nano
export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1
export TERM=xterm-256color

# コマンド引数の解析
COMMAND=$1
shift  # 最初の引数を削除

# コマンドに応じて処理を分岐
case "$COMMAND" in
  edit)
    # editコマンドをSafe Edit Helper に置き換え
    echo "安全なエディタを使用しています..."
    python3 "$PROJECT_DIR/edit_helper.py" "$@"
    ;;
    
  python|python3)
    # Pythonコマンドの実行
    python3 "$@"
    ;;
    
  run)
    # アプリケーションの実行
    cd "$PROJECT_DIR/ui" || exit 1
    streamlit run app.py
    ;;
    
  test)
    # テストの実行
    cd "$PROJECT_DIR" || exit 1
    python3 -m pytest "$@"
    ;;
    
  install)
    # 依存パッケージのインストール
    echo "プロジェクト依存パッケージをインストールしています..."
    python3 -m pip install -r requirements.txt
    ;;
    
  show)
    # ファイル内容を表示 (エディタ起動なし)
    echo "ファイル内容を表示: $1"
    if [ -f "$1" ]; then
      cat "$1"
    else
      echo "エラー: ファイル '$1' が見つかりません"
      exit 1
    fi
    ;;
    
  exec)
    # 任意のコマンドを安全に実行
    echo "コマンドを実行: $*"
    $@
    ;;
    
  help|--help|-h)
    # ヘルプの表示
    echo "使用方法: $0 <command> [options]"
    echo ""
    echo "利用可能なコマンド:"
    echo "  edit <file> [line]   - 指定されたファイルを安全に編集（行番号オプション）"
    echo "  python <args>        - Pythonコマンドを実行"
    echo "  python3 <args>       - Pythonコマンドを実行（python3）"
    echo "  run                  - Streamlitアプリケーションを実行"
    echo "  test [args]          - pytestを実行して単体テストを行う"
    echo "  install              - 依存パッケージをインストール"
    echo "  show <file>          - ファイル内容を表示（エディタを起動せず）"
    echo "  exec <command>       - 任意のコマンドを安全に実行"
    echo "  help                 - このヘルプを表示"
    echo ""
    echo "注意: Claudeとの接続を維持するには、すべてのコマンドをこのスクリプト経由で実行してください"
    echo ""
    ;;
    
  *)
    # 未知のコマンド
    echo "エラー: 未知のコマンド '$COMMAND'"
    echo "使用可能なコマンドを確認するには '$0 help' を実行してください"
    exit 1
    ;;
esac
