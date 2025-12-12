# -*- coding: utf-8 -*-
"""
Kriging Interpolation using PyKrige
"""
import numpy as np
import geopandas as gpd
from pykrige.ok import OrdinaryKriging
from .base_interpolator import BaseInterpolator
from ..config import INTERPOLATION_PARAMS


class KrigingInterpolator(BaseInterpolator):
    """Ordinary Kriging interpolation"""
    
    def __init__(self, variogram_model: str = None, nlags: int = None):
        """
        Initialize Kriging interpolator
        
        Args:
            variogram_model: Variogram model type (default: from config)
            nlags: Number of lags for variogram (default: from config)
        """
        super().__init__(name='Kriging')
        
        # Get parameters from config if not provided
        if variogram_model is None:
            variogram_model = INTERPOLATION_PARAMS['kriging']['variogram_model']
        if nlags is None:
            nlags = INTERPOLATION_PARAMS['kriging']['nlags']
        
        self.variogram_model = variogram_model
        self.nlags = nlags
        self.kriging_model = None
        self.points_x = None
        self.points_y = None
        self.values = None
    
    def fit(self, points: gpd.GeoDataFrame, value_field: str):
        """
        Fit Kriging model
        
        Args:
            points: GeoDataFrame with point observations
            value_field: Name of field containing values to interpolate
        """
        # Extract coordinates and values
        self.points_x = points.geometry.x.values
        self.points_y = points.geometry.y.values
        self.values = points[value_field].values
        
        # Create Ordinary Kriging model
        self.kriging_model = OrdinaryKriging(
            self.points_x,
            self.points_y,
            self.values,
            variogram_model=self.variogram_model,
            nlags=self.nlags,
            enable_plotting=False,
            verbose=False
        )
        
        self.is_fitted = True
    
    def predict(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Predict values using Kriging
        
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
        original_shape = x.shape
        
        # PyKrige expects 1D arrays or grids
        if x.ndim == 2 and y.ndim == 2:
            # Grid input - extract unique coordinates
            x_coords = x[0, :]  # First row
            y_coords = y[:, 0]  # First column
            
            # Predict on grid
            z, ss = self.kriging_model.execute('grid', x_coords, y_coords)
            
            return z
        else:
            # Point input
            x_flat = x.ravel()
            y_flat = y.ravel()
            
            # Predict at points
            z, ss = self.kriging_model.execute('points', x_flat, y_flat)
            
            return z.reshape(original_shape)