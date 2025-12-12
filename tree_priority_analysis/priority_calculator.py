# -*- coding: utf-8 -*-
"""
Priority Calculator - Combine all factors into final priority scores
Applies weights and generates priority classifications
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Dict
from .config import WEIGHTS, PRIORITY_CLASSES, SCORE_RANGE


class PriorityCalculator:
    """
    Combine multiple factor scores into a final priority score
    
    Weighted sum approach:
    Priority = Σ(weight_i × score_i)
    """
    
    def __init__(self, weights: Dict[str, float] = None, verbose: bool = True):
        """
        Initialize calculator
        
        Args:
            weights: Dictionary of factor weights (must sum to 1.0)
            verbose: Enable verbose logging
        """
        self.weights = weights or WEIGHTS
        self.verbose = verbose
        
        # Validate weights
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def log(self, message: str):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[PriorityCalculator] {message}")
    
    def calculate(
        self,
        grid: gpd.GeoDataFrame,
        factor_scores: Dict[str, pd.Series]
    ) -> gpd.GeoDataFrame:
        """
        Calculate final priority scores
        
        Args:
            grid: Original grid GeoDataFrame
            factor_scores: Dictionary of factor scores (factor_name -> Series)
            
        Returns:
            GeoDataFrame with all factor scores and final priority
        """
        self.log("=" * 70)
        self.log("Calculating Final Priority Scores...")
        self.log("=" * 70)
        
        # Create result dataframe
        result = grid.copy()
        
        # Add individual factor scores
        for factor_name, scores in factor_scores.items():
            col_name = f"{factor_name}_score"
            result[col_name] = scores
            self.log(f"  Added {col_name}: mean={scores.mean():.2f}")
        
        # Calculate weighted sum
        self.log("\nApplying weights:")
        priority_score = pd.Series(0.0, index=result.index)
        
        for factor_name, weight in self.weights.items():
            if factor_name in factor_scores:
                contribution = factor_scores[factor_name] * weight
                priority_score += contribution
                self.log(f"  {factor_name:12} × {weight:.2f} = avg {contribution.mean():.2f}")
            else:
                self.log(f"  ⚠ {factor_name} not found in factor_scores, skipping")
        
        result['priority_score'] = priority_score
        
        # Add priority classification
        result['priority_class'] = result['priority_score'].apply(self._classify_priority)
        
        # Add priority rank (1 = highest priority)
        result['priority_rank'] = result['priority_score'].rank(ascending=False, method='min').astype(int)
        
        self.log("\n" + "=" * 70)
        self.log("FINAL PRIORITY SUMMARY")
        self.log("=" * 70)
        self.log(f"Score Range: [{priority_score.min():.2f}, {priority_score.max():.2f}]")
        self.log(f"Mean Score: {priority_score.mean():.2f}")
        self.log(f"Std Dev: {priority_score.std():.2f}")
        
        # Classification breakdown
        self.log("\nPriority Classification Breakdown:")
        class_counts = result['priority_class'].value_counts().sort_index()
        for priority_class, count in class_counts.items():
            percentage = (count / len(result)) * 100
            self.log(f"  {priority_class:12} : {count:5} cells ({percentage:5.1f}%)")
        
        return result
    
    def _classify_priority(self, score: float) -> str:
        """
        Classify a score into a priority class
        
        Args:
            score: Priority score (0-10)
            
        Returns:
            Priority class name
        """
        for class_name, (min_val, max_val) in PRIORITY_CLASSES.items():
            if min_val <= score < max_val:
                return class_name
        
        # Handle edge case for max score
        if score == SCORE_RANGE[1]:
            return 'Very High'
        
        return 'Very Low'
    
    def get_top_priority_cells(
        self,
        result: gpd.GeoDataFrame,
        n: int = 10
    ) -> gpd.GeoDataFrame:
        """
        Get the top N highest priority cells
        
        Args:
            result: Result GeoDataFrame with priority scores
            n: Number of top cells to return
            
        Returns:
            GeoDataFrame of top priority cells
        """
        return result.nlargest(n, 'priority_score')
    
    def export_summary_statistics(self, result: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Export summary statistics for the analysis
        
        Args:
            result: Result GeoDataFrame with all scores
            
        Returns:
            DataFrame with statistics
        """
        stats = []
        
        # Overall statistics
        stats.append({
            'metric': 'Total Grid Cells',
            'value': len(result),
            'unit': 'cells'
        })
        
        stats.append({
            'metric': 'Mean Priority Score',
            'value': f"{result['priority_score'].mean():.2f}",
            'unit': 'score'
        })
        
        # Factor contributions
        for factor_name in self.weights.keys():
            col_name = f"{factor_name}_score"
            if col_name in result.columns:
                weighted_contribution = result[col_name].mean() * self.weights[factor_name]
                stats.append({
                    'metric': f'{factor_name.title()} Contribution',
                    'value': f"{weighted_contribution:.2f}",
                    'unit': 'score'
                })
        
        # Class distribution
        for class_name in PRIORITY_CLASSES.keys():
            count = (result['priority_class'] == class_name).sum()
            percentage = (count / len(result)) * 100
            stats.append({
                'metric': f'{class_name} Cells',
                'value': f"{count} ({percentage:.1f}%)",
                'unit': 'cells'
            })
        
        return pd.DataFrame(stats)