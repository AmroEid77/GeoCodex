# -*- coding: utf-8 -*-
"""
Base class for interpolation methods
"""
from abc import ABC, abstractmethod
import numpy as np
import geopandas as gpd
from typing import Tuple


class BaseInterpolator(ABC):
    """Abstract base class for interpolation methods"""
    
    def __init__(self, name: str):
        """
        Initialize interpolator
        
        Args:
            name: Name of interpolation method
        """
        self.name = name
        self.is_fitted = False
    
    @abstractmethod
    def fit(self, points: gpd.GeoDataFrame, value_field: str):
        """
        Fit interpolation model to training points
        
        Args:
            points: GeoDataFrame with point observations
            value_field: Name of field containing values to interpolate
        """
        pass
    
    @abstractmethod
    def predict(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Predict values at new locations
        
        Args:
            x: X coordinates (1D or 2D array)
            y: Y coordinates (1D or 2D array)
            
        Returns:
            Predicted values (same shape as x and y)
        """
        pass
    
    def interpolate_to_grid(self, 
                           x_min: float, 
                           x_max: float,
                           y_min: float,
                           y_max: float,
                           cell_size: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Interpolate to a regular grid
        
        Args:
            x_min: Minimum x coordinate
            x_max: Maximum x coordinate
            y_min: Minimum y coordinate
            y_max: Maximum y coordinate
            cell_size: Grid cell size
            
        Returns:
            Tuple of (interpolated_values, x_grid, y_grid)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction. Call fit() first.")
        
        # Create grid
        x_coords = np.arange(x_min, x_max + cell_size, cell_size)
        y_coords = np.arange(y_min, y_max + cell_size, cell_size)
        x_grid, y_grid = np.meshgrid(x_coords, y_coords)
        
        # Predict at grid points
        z_grid = self.predict(x_grid, y_grid)
        
        return z_grid, x_grid, y_grid
    
    def cross_validate(self, points: gpd.GeoDataFrame, value_field: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform leave-one-out cross-validation
        
        Args:
            points: GeoDataFrame with point observations
            value_field: Name of field containing values to interpolate
            
        Returns:
            Tuple of (observed_values, predicted_values)
        """
        n_points = len(points)
        observed = np.zeros(n_points)
        predicted = np.zeros(n_points)
        
        print(f"  Performing leave-one-out cross-validation ({n_points} iterations)...")
        
        for i in range(n_points):
            # Leave one out
            train_points = points.drop(points.index[i])
            test_point = points.iloc[i]
            
            # Fit model without point i
            self.fit(train_points, value_field)
            
            # Predict at point i
            x_test = test_point.geometry.x
            y_test = test_point.geometry.y
            predicted[i] = self.predict(np.array([x_test]), np.array([y_test]))[0]
            observed[i] = test_point[value_field]
        
        return observed, predicted
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', fitted={self.is_fitted})"