#\!/bin/bash
# Script to push changes to GitHub

# Set the working directory to the project root
cd "$(dirname "$0")" || exit

echo "Current directory: $(pwd)"

# Add all changes
echo "Adding changes..."
git add sailing_data_processor/strategy/__init__.py
git add sailing_data_processor/strategy/strategy_detector_with_propagation.py
git add test_strategy_imports.py

# Commit changes with a descriptive message
echo "Committing changes..."
git commit -m "Fix encoding issues and circular imports in strategy detector module"

# Push to GitHub
echo "Pushing to GitHub..."
git push

echo "Done\!"
