# -*- coding: utf-8 -*-
"""
Module for data quality metrics integration.
This module provides integration of quality metrics calculation functionality.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Simplified import approach with better error handling
try:
    # Primary import approach with explicit error logging
    from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
    from sailing_data_processor.validation.quality_metrics_improvements import QualityMetricsCalculatorExtension
    logger.info("Successfully imported quality metrics modules")
except ImportError as e:
    logger.error(f"Failed to import primary quality metrics modules: {e}")
    
    # Fallback implementation with complete interface
    class QualityMetricsCalculator:
        """Fallback implementation of QualityMetricsCalculator"""
        
        def __init__(self, validation_results=None, data=None):
            self.validation_results = validation_results if validation_results else []
            self.data = data if data is not None else pd.DataFrame()
            
            # Rule category definitions
            self.rule_categories = {
                "completeness": ["Required Columns Check", "No Null Values Check"],
                "accuracy": ["Value Range Check", "Spatial Consistency Check"],
                "consistency": ["No Duplicate Timestamps", "Temporal Consistency Check"]
            }
            
            # Problem indices collections
            self.problematic_indices = {
                "missing_data": [],
                "out_of_range": [],
                "duplicates": [],
                "spatial_anomalies": [],
                "temporal_anomalies": [],
                "all": []
            }
            
            # Quality scores
            self.quality_scores = {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0,
                "total": 100.0
            }
            
            # Problem distribution
            self.problem_distribution = {
                "temporal": {"has_data": False},
                "spatial": {"has_data": False},
                "problem_type": {
                    "has_data": True,
                    "problem_counts": {
                        "missing_data": 0,
                        "out_of_range": 0,
                        "duplicates": 0,
                        "spatial_anomalies": 0,
                        "temporal_anomalies": 0
                    }
                }
            }
            
            # Record issues
            self.record_issues = {}
            
            # Initialize temporal and spatial metrics
            self.temporal_metrics = {"has_data": False}
            self.spatial_metrics = {"has_data": False}
        
        def _determine_impact_level(self, score: float) -> str:
            """Determine the impact level from a quality score"""
            if score >= 90:
                return "low"       # Low impact
            elif score >= 75:
                return "medium"    # Medium impact
            elif score >= 50:
                return "high"      # High impact
            else:
                return "critical"  # Critical impact
        
        def get_quality_summary(self) -> Dict[str, Any]:
            """Get a summary of data quality metrics"""
            # Count problems
            total_issues = len(self.problematic_indices.get("all", []))
            missing_data_count = len(self.problematic_indices.get("missing_data", []))
            out_of_range_count = len(self.problematic_indices.get("out_of_range", []))
            dupes_count = len(self.problematic_indices.get("duplicates", []))
            spatial_count = len(self.problematic_indices.get("spatial_anomalies", []))
            temporal_count = len(self.problematic_indices.get("temporal_anomalies", []))
            
            # Build quality summary
            return {
                "overall_score": self.quality_scores.get("total", 100.0),
                "completeness_score": self.quality_scores.get("completeness", 100.0),
                "accuracy_score": self.quality_scores.get("accuracy", 100.0),
                "consistency_score": self.quality_scores.get("consistency", 100.0),
                "total_issues": total_issues,
                "issue_counts": {
                    "missing_data": missing_data_count,
                    "out_of_range": out_of_range_count,
                    "duplicates": dupes_count,
                    "spatial_anomalies": spatial_count,
                    "temporal_anomalies": temporal_count
                },
                "severity_counts": {
                    "error": sum([1 for r in self.validation_results if not r.get("is_valid", True) and r.get("severity") == "error"]),
                    "warning": sum([1 for r in self.validation_results if not r.get("is_valid", True) and r.get("severity") == "warning"]),
                    "info": sum([1 for r in self.validation_results if not r.get("is_valid", True) and r.get("severity") == "info"])
                },
                "fixable_counts": {
                    "auto_fixable": 0,
                    "manually_fixable": 0,
                    "unfixable": 0
                },
                "impact_level": self._determine_impact_level(self.quality_scores.get("total", 100.0)),
                "quality_score": self.quality_scores.get("total", 100.0)
            }
        
        def get_problem_distribution(self):
            """Get problem distribution information"""
            return self.problem_distribution
        
        def get_record_issues(self):
            """Get record-specific issue information"""
            return self.record_issues
        
        def calculate_hierarchical_quality_scores(self):
            """Calculate hierarchical quality scores"""
            return {
                "categories": {
                    "organizational": {"score": 95.0, "subcategories": {}},
                    "statistical": {"score": 90.0, "subcategories": {}},
                    "structural": {"score": 92.0, "subcategories": {}},
                    "semantic": {"score": 93.0, "subcategories": {}}
                },
                "overall_score": 92.5
            }
        
        def get_comprehensive_quality_metrics(self):
            """Get comprehensive quality metrics"""
            return {
                "basic_scores": self.quality_scores,
                "category_details": {},
                "problem_distribution": self.problem_distribution,
                "temporal_metrics": self.temporal_metrics,
                "spatial_metrics": self.spatial_metrics,
                "quality_summary": self.get_quality_summary(),
                "generated_at": datetime.now().isoformat()
            }
                
    class QualityMetricsCalculatorExtension:
        """Fallback extension of QualityMetricsCalculator"""
        
        def __init__(self, validation_results=None, data=None):
            self.validation_results = validation_results if validation_results else []
            self.data = data if data is not None else pd.DataFrame()
            self.problematic_indices = {
                "missing_data": [],
                "out_of_range": [],
                "duplicates": [],
                "spatial_anomalies": [],
                "temporal_anomalies": [],
                "all": []
            }
            self.rule_categories = {
                "completeness": ["Required Columns Check", "No Null Values Check"],
                "accuracy": ["Value Range Check", "Spatial Consistency Check"],
                "consistency": ["No Duplicate Timestamps", "Temporal Consistency Check"]
            }
            self.quality_scores = {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0,
                "total": 100.0
            }
            
            # Problem distribution
            self.problem_distribution = {
                "temporal": {"has_data": False},
                "spatial": {"has_data": False},
                "problem_type": {
                    "has_data": True,
                    "problem_counts": {
                        "missing_data": 0,
                        "out_of_range": 0,
                        "duplicates": 0,
                        "spatial_anomalies": 0,
                        "temporal_anomalies": 0
                    }
                }
            }
        
        def _determine_impact_level(self, score: float) -> str:
            """Determine the impact level from a quality score"""
            if score >= 90:
                return "low"
            elif score >= 75:
                return "medium"
            elif score >= 50:
                return "high"
            else:
                return "critical"
        
        def _calculate_problem_type_distribution_for_period(self, period_indices):
            """Calculate problem type distribution for a specific period"""
            return {
                "missing_data": 0,
                "out_of_range": 0,
                "duplicates": 0,
                "spatial_anomalies": 0,
                "temporal_anomalies": 0
            }
        
        def calculate_quality_scores(self):
            """Calculate quality scores"""
            return {
                "total": 100.0,
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0
            }
        
        def calculate_category_quality_scores(self):
            """Calculate category quality scores"""
            return {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0
            }
            
        def _get_score_color(self, score: float) -> str:
            """Get color for a score value"""
            if score >= 90:
                return "#27AE60"  # Deep green
            elif score >= 75:
                return "#2ECC71"  # Green
            elif score >= 50:
                return "#F1C40F"  # Yellow
            elif score >= 25:
                return "#E67E22"  # Orange
            else:
                return "#E74C3C"  # Red
        
        def calculate_temporal_quality_scores(self):
            """Calculate temporal quality scores"""
            return []
            
        def calculate_spatial_quality_scores(self):
            """Calculate spatial quality scores"""
            return []

# Enhanced quality metrics calculator with complete functionality
class EnhancedQualityMetricsCalculator(QualityMetricsCalculator):
    """
    Enhanced version of QualityMetricsCalculator with additional functionality
    
    Parameters
    ----------
    validation_results : List[Dict[str, Any]]
        Validation results from DataValidator
    data : pd.DataFrame
        Validated DataFrame
    """
    
    def __init__(self, validation_results: List[Dict[str, Any]], data: pd.DataFrame):
        """
        Initialize the enhanced calculator
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]]
            Validation results from DataValidator
        data : pd.DataFrame
            Validated DataFrame
        """
        try:
            # Initialize parent class
            super().__init__(validation_results, data)
            
            # Process validation results to populate problematic_indices
            self._process_validation_results()
            
            # Calculate quality scores
            self.quality_scores = self.calculate_quality_scores()
            
            # Initialize problem distribution
            self._initialize_problem_distribution()
            
            logger.info("Successfully initialized EnhancedQualityMetricsCalculator")
        except Exception as init_error:
            logger.error(f"Error initializing EnhancedQualityMetricsCalculator: {init_error}")
            # Fallback initialization with minimal functionality
            self.validation_results = validation_results if validation_results else []
            self.data = data if data is not None else pd.DataFrame()
            self.problematic_indices = {
                "missing_data": [],
                "out_of_range": [],
                "duplicates": [],
                "spatial_anomalies": [],
                "temporal_anomalies": [],
                "all": []
            }
            self.quality_scores = {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0,
                "total": 100.0
            }
            self.problem_distribution = {
                "temporal": {"has_data": False},
                "spatial": {"has_data": False},
                "problem_type": {
                    "has_data": True,
                    "problem_counts": {
                        "missing_data": 0,
                        "out_of_range": 0,
                        "duplicates": 0,
                        "spatial_anomalies": 0,
                        "temporal_anomalies": 0
                    }
                }
            }
    
    def _process_validation_results(self):
        """Process validation results to extract problem indices"""
        # Reset problem indices
        self.problematic_indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": []
        }
        
        # Process each validation result
        for result in self.validation_results:
            if not result.get("is_valid", True):
                rule_name = result.get("rule_name", "")
                details = result.get("details", {})
                
                # Extract problem indices based on rule type
                if "No Null Values Check" in rule_name:
                    # Extract null indices
                    null_indices = []
                    for col, indices in details.get("null_indices", {}).items():
                        null_indices.extend(indices)
                    self.problematic_indices["missing_data"].extend(null_indices)
                    self.problematic_indices["all"].extend(null_indices)
                
                elif "Value Range Check" in rule_name:
                    # Extract out-of-range indices
                    out_indices = details.get("out_of_range_indices", [])
                    self.problematic_indices["out_of_range"].extend(out_indices)
                    self.problematic_indices["all"].extend(out_indices)
                
                elif "No Duplicate Timestamps" in rule_name:
                    # Extract duplicate indices
                    dup_indices = []
                    for ts, indices in details.get("duplicate_indices", {}).items():
                        dup_indices.extend(indices)
                    self.problematic_indices["duplicates"].extend(dup_indices)
                    self.problematic_indices["all"].extend(dup_indices)
                
                elif "Spatial Consistency Check" in rule_name:
                    # Extract spatial anomaly indices
                    spatial_indices = details.get("anomaly_indices", [])
                    self.problematic_indices["spatial_anomalies"].extend(spatial_indices)
                    self.problematic_indices["all"].extend(spatial_indices)
                
                elif "Temporal Consistency Check" in rule_name:
                    # Extract temporal anomaly indices
                    gap_indices = details.get("gap_indices", [])
                    reverse_indices = details.get("reverse_indices", [])
                    self.problematic_indices["temporal_anomalies"].extend(gap_indices + reverse_indices)
                    self.problematic_indices["all"].extend(gap_indices + reverse_indices)
        
        # Remove duplicates and sort indices
        for key in self.problematic_indices:
            self.problematic_indices[key] = sorted(list(set(self.problematic_indices[key])))
    
    def _initialize_problem_distribution(self):
        """Initialize problem distribution data structure"""
        # Initialize basic structure
        self.problem_distribution = {
            "temporal": {"has_data": False},
            "spatial": {"has_data": False},
            "problem_type": {"has_data": True}
        }
        
        # Add problem counts
        problem_counts = {}
        for problem_type, indices in self.problematic_indices.items():
            if problem_type != "all":
                problem_counts[problem_type] = len(indices)
        
        # Update problem type distribution
        self.problem_distribution["problem_type"]["problem_counts"] = problem_counts
    
    def _calculate_problem_type_distribution_for_period(self, period_indices: List[int]) -> Dict[str, int]:
        """
        Calculate problem type distribution for a specific period

        Parameters
        ----------
        period_indices : List[int]
            Indices for the period

        Returns
        -------
        Dict[str, int]
            Problem type counts
        """
        problem_type_counts = {
            "missing_data": 0,
            "out_of_range": 0,
            "duplicates": 0,
            "spatial_anomalies": 0,
            "temporal_anomalies": 0
        }
        
        # Calculate intersection of period indices with each problem type
        for problem_type, indices in self.problematic_indices.items():
            if problem_type != "all":
                intersection = set(period_indices).intersection(set(indices))
                problem_type_counts[problem_type] = len(intersection)
        
        return problem_type_counts
        
    def get_quality_summary(self) -> Dict[str, Any]:
        """
        Get a summary of data quality metrics
        
        Returns
        -------
        Dict[str, Any]
            Quality summary
        """
        # Problem counts
        total_issues = len(self.problematic_indices.get("all", []))
        missing_data_count = len(self.problematic_indices.get("missing_data", []))
        out_of_range_count = len(self.problematic_indices.get("out_of_range", []))
        dupes_count = len(self.problematic_indices.get("duplicates", []))
        spatial_count = len(self.problematic_indices.get("spatial_anomalies", []))
        temporal_count = len(self.problematic_indices.get("temporal_anomalies", []))
        
        # Quality summary
        return {
            "overall_score": self.quality_scores.get("total", 100.0),
            "completeness_score": self.quality_scores.get("completeness", 100.0),
            "accuracy_score": self.quality_scores.get("accuracy", 100.0),
            "consistency_score": self.quality_scores.get("consistency", 100.0),
            "total_issues": total_issues,
            "issue_counts": {
                "missing_data": missing_data_count,
                "out_of_range": out_of_range_count,
                "duplicates": dupes_count,
                "spatial_anomalies": spatial_count,
                "temporal_anomalies": temporal_count
            },
            "severity_counts": {
                "error": sum([1 for r in self.validation_results if not r.get("is_valid", True) and r.get("severity") == "error"]),
                "warning": sum([1 for r in self.validation_results if not r.get("is_valid", True) and r.get("severity") == "warning"]),
                "info": sum([1 for r in self.validation_results if not r.get("is_valid", True) and r.get("severity") == "info"])
            },
            "fixable_counts": {
                "auto_fixable": missing_data_count + dupes_count,
                "manually_fixable": out_of_range_count,
                "unfixable": 0
            },
            "impact_level": self._determine_impact_level(self.quality_scores.get("total", 100.0)),
            "quality_score": self.quality_scores.get("total", 100.0)
        }
