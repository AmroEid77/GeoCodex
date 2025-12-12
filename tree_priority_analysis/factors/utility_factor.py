# -*- coding: utf-8 -*-
"""
Utility Factor - Calculate proximity to electric utilities
Closer to power lines = higher cutting priority (prevent outages/fires)
"""

import geopandas as gpd
import pandas as pd
from .base_factor import BaseFactor
from ..config import DISTANCE_THRESHOLDS


class UtilityFactor(BaseFactor):
    """
    Calculate utility proximity factor scores
    
    Trees near power lines are high priority to prevent:
    - Power outages
    - Fire hazards from fallen trees
    - Infrastructure damage
    """
    
    def calculate(
        self,
        grid: gpd.GeoDataFrame,
        source_data: gpd.GeoDataFrame,
        max_distance: float = None,
        decay_type: str = 'exponential',
        **kwargs
    ) -> pd.Series:
        """
        Calculate utility proximity scores
        
        Args:
            grid: Grid cells GeoDataFrame
            source_data: Combined utility features GeoDataFrame
            max_distance: Maximum distance to consider (meters)
            decay_type: Distance decay function (exponential for utilities)
            
        Returns:
            Series of utility proximity scores
        """
        self.log("=" * 70)
        self.log("Calculating Electric Utility Proximity Factor...")
        self.log("=" * 70)
        
        max_distance = max_distance or DISTANCE_THRESHOLDS['utility_max']
        
        self.log(f"Parameters: max_distance={max_distance}m, decay='{decay_type}'")
        self.log(f"Calculating distances from {len(grid)} cells to {len(source_data)} utilities...")
        
        # Calculate grid cell centroids
        grid_centroids = grid.geometry.centroid
        
        # Calculate minimum distance to any utility
        distances = []
        
        for idx, centroid in enumerate(grid_centroids):
            dists = source_data.geometry.distance(centroid)
            min_dist = dists.min()
            distances.append(min_dist)
            
            if (idx + 1) % 100 == 0:
                self.log(f"  Processed {idx + 1}/{len(grid)} cells...")
        
        distances = pd.Series(distances, index=grid.index)
        
        self.log(f"  Distance Range: [{distances.min():.1f}m, {distances.max():.1f}m]")
        
        # Convert distances to scores
        # Exponential decay: very close = very high score
        scores = self.calculate_distance_score(
            distances,
            max_distance=max_distance,
            decay_type=decay_type
        )
        
        self.log(f"✓ Utility proximity factor calculated")
        self.log(self.get_summary_stats(scores))
        
        return scores