#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup file for sailing-strategy-analyzer
"""

from setuptools import setup, find_packages

setup(
    name='sailing-strategy-analyzer',
    version='0.1.0',
    packages=find_packages(include=['sailing_data_processor', 'sailing_data_processor.*']),
    package_dir={'': '.'},
    python_requires='>=3.9',
    install_requires=[
        'numpy>=1.24.0',
        'pandas>=2.0.0',
        'scipy>=1.10.0',
        'gpxpy>=1.5.0',
        'geopy>=2.3.0',
        'scikit-learn>=1.2.0',
        'matplotlib>=3.8.0',
        'shapely>=2.0.0',
    ],
)
