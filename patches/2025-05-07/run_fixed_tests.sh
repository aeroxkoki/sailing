#!/bin/bash

# This script runs the session manager tests after applying the fixes
# Usage: ./run_fixed_tests.sh

cd /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer

echo "===== Applying session manager fixes ====="

# Apply the session manager patch
python3 patches/2025-05-07/fix_session_manager.py

echo "===== Running session manager tests ====="
python3 -m pytest tests/test_project/test_session_manager.py -v

echo "===== Tests completed ====="

# Push changes to GitHub
echo "===== Pushing changes to GitHub ====="
git add sailing_data_processor/project/session_manager.py
git add tests/test_project/test_session_manager.py
git add patches/2025-05-07/fix_session_manager.py
git add patches/2025-05-07/run_fixed_tests.sh
git add patches/2025-05-07/session_manager.py
git commit -m "Fix session manager test failures"
git push

echo "===== Changes pushed successfully ====="
