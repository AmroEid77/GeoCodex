# -*- coding: utf-8 -*-
"""
Validation Metrics for Interpolation
Calculate accuracy metrics for cross-validation
"""

import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """
    Calculate validation metrics
    
    Args:
        actual: Actual values
        predicted: Predicted values
        
    Returns:
        Dictionary of metrics
    """
    # Remove NaN values
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual = actual[mask]
    predicted = predicted[mask]
    
    if len(actual) == 0:
        return {
            'rmse': np.nan,
            'mae': np.nan,
            'r2': np.nan,
            'mean_error': np.nan,
            'std_error': np.nan,
            'n_samples': 0
        }
    
    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mae = mean_absolute_error(actual, predicted)
    r2 = r2_score(actual, predicted)
    
    errors = actual - predicted
    mean_error = np.mean(errors)
    std_error = np.std(errors)
    
    return {
        'rmse': round(rmse, 3),
        'mae': round(mae, 3),
        'r2': round(r2, 3),
        'mean_error': round(mean_error, 3),
        'std_error': round(std_error, 3),
        'n_samples': len(actual)
    }


def print_metrics(metrics: Dict[str, float], method_name: str = "Method"):
    """Print validation metrics in formatted way"""
    print(f"\n{'='*60}")
    print(f"{method_name} - Validation Metrics")
    print(f"{'='*60}")
    print(f"  RMSE (Root Mean Square Error):  {metrics['rmse']:.3f}")
    print(f"  MAE (Mean Absolute Error):      {metrics['mae']:.3f}")
    print(f"  R² (Coefficient of Determination): {metrics['r2']:.3f}")
    print(f"  Mean Error:                     {metrics['mean_error']:.3f}")
    print(f"  Std Error:                      {metrics['std_error']:.3f}")
    print(f"  Number of Samples:              {metrics['n_samples']}")
    print(f"{'='*60}\n")


def compare_methods(results) -> str:
    """
    Compare multiple interpolation methods
    
    Args:
        results: Dict of {method_name: metrics_dict} or list of dicts with 'method' key
        
    Returns:
        Name of best method (lowest RMSE)
    """
    print("\n" + "="*60)
    print("INTERPOLATION METHOD COMPARISON")
    print("="*60)
    
    # Convert list to dictionary if needed
    if isinstance(results, list):
        results = {item['method']: item for item in results}
    
    # Create comparison table
    print(f"{'Method':<20} {'RMSE':<10} {'MAE':<10} {'R²':<10}")
    print("-" * 60)
    
    best_method = None
    best_rmse = float('inf')
    
    for method, metrics in results.items():
        print(f"{method:<20} {metrics['rmse']:<10.3f} {metrics['mae']:<10.3f} {metrics['r2']:<10.3f}")
        
        if metrics['rmse'] < best_rmse:
            best_rmse = metrics['rmse']
            best_method = method
    
    print("="*60)
    print(f"✓ Best Method: {best_method} (RMSE: {best_rmse:.3f})")
    print("="*60 + "\n")
    
    return best_method