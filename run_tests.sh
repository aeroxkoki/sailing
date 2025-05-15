#!/bin/bash
# Script to run the core MVP tests

# Navigate to the project directory
cd "$(dirname "$0")"

# Set Python path to include the project root
export PYTHONPATH=.:$PYTHONPATH

# Import core modules explicitly to ensure coverage
echo "=== Explicitly Importing Core Modules ==="
python3 -c "
import sys
sys.path.insert(0, '.')
import sailing_data_processor
import sailing_data_processor.wind
import sailing_data_processor.boat_fusion
from sailing_data_processor.wind import WindEstimator
from sailing_data_processor.boat_fusion import BoatDataFusionModel
print('Core modules imported successfully')
"

# Run import tests first to ensure modules are properly detected
echo "=== Running Module Import Tests ==="
python3 -m pytest tests/test_import_all_modules.py -v

# Run the direct module tests
echo "=== Running Direct Module Tests ==="
python3 -m pytest tests/test_direct_wind_boat_fusion.py -v

# Run all core MVP tests
echo "=== Running Core MVP Tests ==="
python3 -m pytest tests/test_wind_estimator.py tests/test_wind_field_fusion.py tests/test_boat_data_fusion_refactored.py -v --cov=sailing_data_processor --cov-config=.coveragerc

echo "All MVP tests complete!"
