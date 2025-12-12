# -*- coding: utf-8 -*-
"""
Population Factor - Calculate population density scores
Higher population = higher cutting priority (protect more people)
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from .base_factor import BaseFactor
from ..config import POPULATION_FIELDS


class PopulationFactor(BaseFactor):
    """
    Calculate population density factor scores
    
    Methods:
    1. Spatial join: Find population areas overlapping each grid cell
    2. Sum or average population in each cell
    3. Normalize to score
    """
    
    def calculate(
        self,
        grid: gpd.GeoDataFrame,
        source_data: gpd.GeoDataFrame,
        method: str = 'sum',
        **kwargs
    ) -> pd.Series:
        """
        Calculate population density scores
        
        Args:
            grid: Grid cells GeoDataFrame
            source_data: Population areas GeoDataFrame
            method: 'sum', 'average', or 'density'
            
        Returns:
            Series of population scores
        """
        self.log("=" * 70)
        self.log("Calculating Population Factor...")
        self.log("=" * 70)
        
        # Detect population field
        pop_field = self._detect_population_field(source_data)
        self.log(f"Using population field: '{pop_field}'")
        
        # Ensure grid has an ID
        grid = grid.copy()
        grid['grid_id'] = grid.index
        
        # Spatial join with overlay to handle partial overlaps
        self.log(f"Performing spatial overlay ({len(grid)} cells × {len(source_data)} areas)...")
        
        overlay = gpd.overlay(
            grid[['grid_id', 'geometry']],
            source_data[[pop_field, 'geometry']],
            how='intersection'
        )
        
        self.log(f"  → {len(overlay)} intersections found")
        
        if len(overlay) == 0:
            self.log("⚠ No population data intersects grid - returning zeros")
            return pd.Series(0, index=grid.index)
        
        # Simplified approach: Calculate area-weighted population
        # Add area of intersection
        overlay['overlap_area'] = overlay.geometry.area
        
        # Get total area of each source polygon by mapping back
        # Create a mapping of source polygon areas
        source_areas = source_data.geometry.area
        
        # For each overlay feature, get the original source polygon area
        # The overlay keeps track via index_right (or similar column)
        if 'index_right' in overlay.columns:
            overlay['total_area'] = overlay['index_right'].map(source_areas)
        elif 'idx_2' in overlay.columns:
            overlay['total_area'] = overlay['idx_2'].map(source_areas)
        else:
            # Fallback: use overlap area as total area (not ideal but won't crash)
            self.log("⚠ Cannot determine source polygon index, using overlap area")
            overlay['total_area'] = overlay['overlap_area']
        
        # Calculate weighted population
        # Weight = (overlap_area / total_area) * population
        overlay['weighted_pop'] = overlay[pop_field] * (overlay['overlap_area'] / overlay['total_area'])
        
        # Aggregate by grid cell
        if method == 'sum':
            pop_by_cell = overlay.groupby('grid_id')['weighted_pop'].sum()
        elif method == 'average':
            pop_by_cell = overlay.groupby('grid_id')['weighted_pop'].mean()
        elif method == 'density':
            pop_by_cell = overlay.groupby('grid_id')['weighted_pop'].sum()
            # Divide by cell area
            grid_areas = grid.set_index('grid_id').geometry.area
            pop_by_cell = pop_by_cell / grid_areas
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Normalize to scores
        scores = self.normalize_score(pop_by_cell, inverse=False)
        
        # Fill cells with no population with 0
        scores = scores.reindex(grid.index, fill_value=0)
        
        self.log(f"✓ Population factor calculated using '{method}' method")
        self.log(self.get_summary_stats(scores))
        
        return scores
    
    def _detect_population_field(self, gdf: gpd.GeoDataFrame) -> str:
        """Auto-detect the population field name"""
        # Try configured fields
        for field in POPULATION_FIELDS.values():
            if field in gdf.columns:
                return field
        
        # Try common variations
        common_names = [
            'POPULATION', 'Population', 'population', 'POP',
            'POP_TOTAL', 'TOTALPOP', 'TotalPop', 'pop_total',
            'PERSONS', 'Persons', 'persons'
        ]
        
        for name in common_names:
            if name in gdf.columns:
                return name
        
        # Use first numeric column
        numeric_cols = gdf.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            self.log(f"⚠ No standard population field found, using '{numeric_cols[0]}'")
            return numeric_cols[0]
        
        raise ValueError("No suitable population field found in data")