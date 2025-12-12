# -*- coding: utf-8 -*-
"""
Egress Factor - Calculate proximity to egress/evacuation routes
Closer to egress routes = higher cutting priority (safety concern)
"""

import geopandas as gpd
import pandas as pd
from .base_factor import BaseFactor
from ..config import DISTANCE_THRESHOLDS


class EgressFactor(BaseFactor):
    """
    Calculate egress route proximity factor scores
    
    Similar to CommunityFactor but for evacuation routes
    Trees near egress routes are higher priority (safety)
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
        Calculate egress proximity scores
        
        Args:
            grid: Grid cells GeoDataFrame
            source_data: Egress routes GeoDataFrame
            max_distance: Maximum distance to consider (meters)
            decay_type: Distance decay function
            
        Returns:
            Series of egress proximity scores
        """
        self.log("=" * 70)
        self.log("Calculating Egress Route Proximity Factor...")
        self.log("=" * 70)
        
        max_distance = max_distance or DISTANCE_THRESHOLDS['egress_max']
        
        self.log(f"Parameters: max_distance={max_distance}m, decay='{decay_type}'")
        self.log(f"Calculating distances from {len(grid)} cells to {len(source_data)} routes...")
        
        # Calculate grid cell centroids
        grid_centroids = grid.geometry.centroid
        
        # Calculate minimum distance to any egress route
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
        scores = self.calculate_distance_score(
            distances,
            max_distance=max_distance,
            decay_type=decay_type
        )
        
        self.log(f"✓ Egress proximity factor calculated")
        self.log(self.get_summary_stats(scores))
        
        return scores