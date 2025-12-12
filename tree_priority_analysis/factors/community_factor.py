# -*- coding: utf-8 -*-
"""
Community Factor - Calculate proximity to community features
Closer to community features = higher cutting priority
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from .base_factor import BaseFactor
from ..config import DISTANCE_THRESHOLDS


class CommunityFactor(BaseFactor):
    """
    Calculate community proximity factor scores
    
    Methods:
    1. Calculate distance from each grid cell centroid to nearest community feature
    2. Convert distance to score (inverse: closer = higher score)
    3. Apply distance decay function
    """
    
    def calculate(
        self,
        grid: gpd.GeoDataFrame,
        source_data: gpd.GeoDataFrame,
        max_distance: float = None,
        decay_type: str = 'linear',
        **kwargs
    ) -> pd.Series:
        """
        Calculate community proximity scores
        
        Args:
            grid: Grid cells GeoDataFrame
            source_data: Community features GeoDataFrame
            max_distance: Maximum distance to consider (meters)
            decay_type: Distance decay function ('linear', 'inverse', 'exponential')
            
        Returns:
            Series of community proximity scores
        """
        self.log("=" * 70)
        self.log("Calculating Community Proximity Factor...")
        self.log("=" * 70)
        
        max_distance = max_distance or DISTANCE_THRESHOLDS['community_max']
        
        self.log(f"Parameters: max_distance={max_distance}m, decay='{decay_type}'")
        self.log(f"Calculating distances from {len(grid)} cells to {len(source_data)} features...")
        
        # Calculate grid cell centroids for point-based distance
        grid_centroids = grid.geometry.centroid
        
        # Calculate minimum distance to any community feature
        distances = []
        
        for idx, centroid in enumerate(grid_centroids):
            # Distance to all community features
            dists = source_data.geometry.distance(centroid)
            min_dist = dists.min()
            distances.append(min_dist)
            
            if (idx + 1) % 100 == 0:
                self.log(f"  Processed {idx + 1}/{len(grid)} cells...")
        
        distances = pd.Series(distances, index=grid.index)
        
        self.log(f"  Distance Range: [{distances.min():.1f}m, {distances.max():.1f}m]")
        
        # Convert distances to scores
        scores = self.calculate_distance_score(
            distances,
            max_distance=max_distance,
            decay_type=decay_type
        )
        
        self.log(f"✓ Community proximity factor calculated")
        self.log(self.get_summary_stats(scores))
        
        return scores