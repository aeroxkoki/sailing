#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

def main():
    # Set the correct PYTHONPATH
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.environ["PYTHONPATH"] = project_root
    
    # Run the tests
    cmd = [sys.executable, "-m", "pytest", "tests/test_project/test_session_manager.py", "-v"]
    process = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    # Print the output
    print("STDOUT:")
    print(process.stdout)
    
    print("STDERR:")
    print(process.stderr)
    
    return process.returncode

if __name__ == "__main__":
    sys.exit(main())
