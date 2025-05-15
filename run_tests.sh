#!/bin/bash
# Script to run the core MVP tests

# Navigate to the project directory
cd "$(dirname "$0")"

# Set Python path to include the project root
export PYTHONPATH=.:$PYTHONPATH

# Run import tests first to ensure modules are properly detected
echo "=== Running Module Import Tests ==="
python3 -m pytest tests/test_import_all_modules.py -v

# Run the direct module tests
echo "=== Running Direct Module Tests ==="
python3 -m pytest tests/test_direct_wind_boat_fusion.py -v

# Run all core MVP tests
echo "=== Running Core MVP Tests ==="
python3 -m pytest tests/test_wind_estimator.py tests/test_wind_field_fusion.py tests/test_boat_data_fusion_refactored.py -v

echo "All MVP tests complete!"
