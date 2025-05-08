#\!/bin/bash
# Script to run the fixed tests

# Navigate to the project directory
cd "$(dirname "$0")"

# Set Python path to include the project root
export PYTHONPATH=.:$PYTHONPATH

# Run the specific failing tests
echo "Running test_core.py::TestSailingDataProcessor::test_process_multiple_boats..."
python3 -m pytest tests/test_core.py::TestSailingDataProcessor::test_process_multiple_boats -v

echo "Running test_data_model.py::TestCacheFunctions::test_cached_decorator..."
python3 -m pytest tests/test_data_model.py::TestCacheFunctions::test_cached_decorator -v

echo "Running test_sailing_data_processor.py::TestSailingDataProcessor::test_anomaly_detection..."
python3 -m pytest tests/test_sailing_data_processor.py::TestSailingDataProcessor::test_anomaly_detection -v

echo "Running test_sailing_data_processor.py::TestSailingDataProcessor::test_common_timeframe..."
python3 -m pytest tests/test_sailing_data_processor.py::TestSailingDataProcessor::test_common_timeframe -v

echo "Running test_sailing_data_processor.py::TestSailingDataProcessor::test_data_quality_report..."
python3 -m pytest tests/test_sailing_data_processor.py::TestSailingDataProcessor::test_data_quality_report -v

echo "All tests complete\!"
