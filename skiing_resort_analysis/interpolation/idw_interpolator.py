# -*- coding: utf-8 -*-
"""
Inverse Distance Weighting (IDW) Interpolation
"""
import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree
from .base_interpolator import BaseInterpolator
from ..config import INTERPOLATION_PARAMS


class IDWInterpolator(BaseInterpolator):
    """Inverse Distance Weighting interpolation"""
    
    def __init__(self, power: float = None, radius: float = None):
        """
        Initialize IDW interpolator
        
        Args:
            power: Power parameter (default: from config)
            radius: Search radius in meters (default: from config)
        """
        super().__init__(name='IDW')
        
        # Get parameters from config if not provided
        if power is None:
            power = INTERPOLATION_PARAMS['idw']['power']
        if radius is None:
            radius = INTERPOLATION_PARAMS['idw']['radius']
        
        self.power = power
        self.radius = radius
        self.points_x = None
        self.points_y = None
        self.values = None
        self.tree = None
    
    def fit(self, points: gpd.GeoDataFrame, value_field: str):
        """
        Fit IDW model (store training points)
        
        Args:
            points: GeoDataFrame with point observations
            value_field: Name of field containing values to interpolate
        """
        # Extract coordinates and values
        self.points_x = points.geometry.x.values
        self.points_y = points.geometry.y.values
        self.values = points[value_field].values
        
        # Build spatial index for fast neighbor search
        coords = np.column_stack([self.points_x, self.points_y])
        self.tree = cKDTree(coords)
        
        self.is_fitted = True
    
    def predict(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Predict values using IDW
        
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
        
        # Flatten for processing
        x_flat = x.ravel()
        y_flat = y.ravel()
        n_points = len(x_flat)
        
        # Query points
        query_coords = np.column_stack([x_flat, y_flat])
        
        # Find neighbors within radius
        if self.radius is not None:
            # Use radius search
            neighbors_list = self.tree.query_ball_point(query_coords, r=self.radius)
            
            predictions = np.zeros(n_points)
            for i, neighbors in enumerate(neighbors_list):
                if len(neighbors) == 0:
                    # No neighbors within radius - use nearest
                    distance, idx = self.tree.query([query_coords[i]], k=1)
                    predictions[i] = self.values[idx[0]]
                else:
                    # Calculate distances to neighbors
                    distances = np.sqrt(
                        (query_coords[i, 0] - self.points_x[neighbors])**2 +
                        (query_coords[i, 1] - self.points_y[neighbors])**2
                    )
                    
                    # Handle zero distances (exact match)
                    zero_dist = distances == 0
                    if np.any(zero_dist):
                        predictions[i] = self.values[neighbors][zero_dist][0]
                    else:
                        # IDW formula: weighted average
                        weights = 1.0 / (distances ** self.power)
                        predictions[i] = np.sum(weights * self.values[neighbors]) / np.sum(weights)
        else:
            # Use all points (no radius restriction)
            predictions = np.zeros(n_points)
            for i in range(n_points):
                distances = np.sqrt(
                    (query_coords[i, 0] - self.points_x)**2 +
                    (query_coords[i, 1] - self.points_y)**2
                )
                
                # Handle zero distances
                zero_dist = distances == 0
                if np.any(zero_dist):
                    predictions[i] = self.values[zero_dist][0]
                else:
                    weights = 1.0 / (distances ** self.power)
                    predictions[i] = np.sum(weights * self.values) / np.sum(weights)
        
        # Reshape to original shape
        return predictions.reshape(original_shape)