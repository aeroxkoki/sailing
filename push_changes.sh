#!/bin/bash
# Script to push changes to GitHub

# エラーで即時終了
set -e

# Set the working directory to the project root
cd "$(dirname "$0")" || exit

echo "Current directory: $(pwd)"

# パッチの適用
echo "Applying quality metrics patches..."
bash patches/2025-05-07/run_fixed_tests.sh || { echo "Failed to apply patches"; exit 1; }

# Add all changes
echo "Adding changes..."
git add sailing_data_processor/validation/quality_metrics.py
git add sailing_data_processor/validation/quality_metrics_integration.py
git add patches/2025-05-07/fix_missing_methods.py
git add patches/2025-05-07/run_fixed_tests.sh

# Commit changes with a descriptive message
echo "Committing changes..."
git commit -m "Fix quality metrics calculation and visualization issues"

# Push to GitHub
echo "Pushing to GitHub..."
git push

echo "Done! Changes have been successfully applied and pushed to GitHub."
