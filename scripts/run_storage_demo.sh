#!/bin/bash
# ストレージソリューションデモの実行スクリプト

echo "セーリング戦略分析システム - ストレージソリューションデモを起動します..."
python3 -c "from sailing_data_processor.storage.storage_demo import main; main()"
