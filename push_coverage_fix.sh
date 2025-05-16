#\!/bin/bash
# Script to push coverage fixes to GitHub

cd "$(dirname "$0")"

# Add modified and new files
git add pyproject.toml pytest.ini run_tests.sh tests/test_import_all_modules.py tests/test_direct_wind_boat_fusion.py

# Commit with a descriptive message
git commit -m "Fix code coverage reporting for WindEstimator and BoatDataFusion modules"

# Push to the repository
git push

echo "Changes pushed to GitHub repository\!"
