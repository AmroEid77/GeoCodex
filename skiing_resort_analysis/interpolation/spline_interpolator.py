# -*- coding: utf-8 -*-
"""
Spline Interpolation using SciPy
"""
import numpy as np
import geopandas as gpd
from scipy.interpolate import Rbf
from .base_interpolator import BaseInterpolator
from ..config import INTERPOLATION_PARAMS


class SplineInterpolator(BaseInterpolator):
    """Radial Basis Function (Spline) interpolation"""
    
    def __init__(self, smoothing: float = None, function: str = 'thin_plate'):
        """
        Initialize Spline interpolator
        
        Args:
            smoothing: Smoothing parameter (default: from config)
            function: RBF function type (default: 'thin_plate')
        """
        super().__init__(name='Spline')
        
        # Get parameters from config if not provided
        if smoothing is None:
            smoothing = INTERPOLATION_PARAMS['spline']['smoothing']
        
        self.smoothing = smoothing
        self.function = function
        self.rbf_model = None
        self.points_x = None
        self.points_y = None
        self.values = None
    
    def fit(self, points: gpd.GeoDataFrame, value_field: str):
        """
        Fit Spline model
        
        Args:
            points: GeoDataFrame with point observations
            value_field: Name of field containing values to interpolate
        """
        # Extract coordinates and values
        self.points_x = points.geometry.x.values
        self.points_y = points.geometry.y.values
        self.values = points[value_field].values
        
        # Create RBF interpolator
        self.rbf_model = Rbf(
            self.points_x,
            self.points_y,
            self.values,
            function=self.function,
            smooth=self.smoothing
        )
        
        self.is_fitted = True
    
    def predict(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Predict values using Spline
        
        Args:
            x: X coordinates
            y: Y coordinates
            
        Returns:
            Predicted values
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Ensure arrays
        x = np.asarray(x)
        y = np.asarray(y)
        
        # RBF can handle both 1D and 2D inputs
        predictions = self.rbf_model(x, y)
        
        return predictions