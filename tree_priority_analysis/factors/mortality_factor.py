# -*- coding: utf-8 -*-
"""
Mortality Factor - Calculate tree mortality scores for each grid cell
Higher mortality = higher cutting priority
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from .base_factor import BaseFactor
from ..config import MORTALITY_FIELDS


class MortalityFactor(BaseFactor):
    """
    Calculate tree mortality factor scores
    
    Methods:
    1. Spatial join: Find trees in each grid cell
    2. Aggregate: Calculate average mortality or tree count per cell
    3. Normalize: Convert to 0-10 score (higher mortality = higher score)
    """
    
    def calculate(
        self,
        grid: gpd.GeoDataFrame,
        source_data: gpd.GeoDataFrame,
        method: str = 'average',
        **kwargs
    ) -> pd.Series:
        """
        Calculate mortality scores for each grid cell
        
        Args:
            grid: Grid cells GeoDataFrame
            source_data: Tree mortality data GeoDataFrame
            method: 'average', 'max', 'density', or 'weighted'
            
        Returns:
            Series of mortality scores indexed by grid index
        """
        self.log("=" * 70)
        self.log("Calculating Tree Mortality Factor...")
        self.log("=" * 70)
        
        # Detect mortality field name
        mortality_field = self._detect_mortality_field(source_data)
        self.log(f"Using mortality field: '{mortality_field}'")
        
        # Ensure grid has an ID for joining
        grid = grid.copy()
        grid['grid_id'] = grid.index
        
        # Spatial join: trees to grid cells
        self.log(f"Performing spatial join ({len(source_data)} trees → {len(grid)} cells)...")
        joined = gpd.sjoin(
            source_data,
            grid[['grid_id', 'geometry']],
            how='inner',
            predicate='intersects'  # Changed from 'within' to catch boundary trees
        )
        
        self.log(f"  → {len(joined)} trees matched to grid cells")
        
        # Check if any trees were matched
        if len(joined) == 0:
            self.log("⚠ WARNING: No trees matched to grid cells!")
            self.log("  Possible issues:")
            self.log("  1. CRS mismatch between grid and trees")
            self.log("  2. Grid and trees don't overlap spatially")
            self.log("  3. Wrong geometry type (expecting points)")
            return pd.Series(0, index=grid.index)
        
        # Calculate scores based on method
        if method == 'average':
            scores = self._calculate_average_mortality(joined, grid, mortality_field)
        elif method == 'max':
            scores = self._calculate_max_mortality(joined, grid, mortality_field)
        elif method == 'density':
            scores = self._calculate_density(joined, grid)
        elif method == 'weighted':
            scores = self._calculate_weighted(joined, grid, mortality_field)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Fill cells with no trees with 0
        scores = scores.reindex(grid.index, fill_value=0)
        
        self.log(f"✓ Mortality factor calculated using '{method}' method")
        self.log(self.get_summary_stats(scores))
        
        return scores
    
    def _detect_mortality_field(self, gdf: gpd.GeoDataFrame) -> str:
        """Auto-detect the mortality field name"""
        # Try configured field names first
        for field in MORTALITY_FIELDS.values():
            if field in gdf.columns:
                return field
        
        # Try common variations
        common_names = [
            'Tot_mortal', 'TOT_MORTAL', 'tot_mortal',  # Fire Creek specific
            'MORTALITY', 'Mortality', 'mortality',
            'MORT_PCT', 'mort_pct', 'MortPct',
            'MORT', 'Mort', 'mort',
            'PERCENT', 'Percent', 'percent',
            'DEAD_PERCENT', 'DeadPercent', 'Dead_Percent'
        ]
        
        for name in common_names:
            if name in gdf.columns:
                return name
        
        # If no match, use first numeric column
        numeric_cols = gdf.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            self.log(f"⚠ No standard mortality field found, using '{numeric_cols[0]}'")
            return numeric_cols[0]
        
        raise ValueError("No suitable mortality field found in data")
    
    def _calculate_average_mortality(
        self,
        joined: gpd.GeoDataFrame,
        grid: gpd.GeoDataFrame,
        mortality_field: str
    ) -> pd.Series:
        """Calculate average mortality percentage per cell"""
        mortality_by_cell = joined.groupby('grid_id')[mortality_field].mean()
        
        # Normalize to 0-10 scale
        scores = self.normalize_score(mortality_by_cell, inverse=False)
        
        return scores
    
    def _calculate_max_mortality(
        self,
        joined: gpd.GeoDataFrame,
        grid: gpd.GeoDataFrame,
        mortality_field: str
    ) -> pd.Series:
        """Use maximum mortality in each cell"""
        mortality_by_cell = joined.groupby('grid_id')[mortality_field].max()
        scores = self.normalize_score(mortality_by_cell, inverse=False)
        return scores
    
    def _calculate_density(
        self,
        joined: gpd.GeoDataFrame,
        grid: gpd.GeoDataFrame
    ) -> pd.Series:
        """Calculate tree density (count per area)"""
        # Count trees per cell
        tree_count = joined.groupby('grid_id').size()
        
        # Calculate cell areas (in square meters)
        grid = grid.copy()
        grid['area_m2'] = grid.geometry.area
        
        # Density = trees per square km
        density = (tree_count / grid.loc[tree_count.index, 'area_m2']) * 1_000_000
        
        scores = self.normalize_score(density, inverse=False)
        return scores
    
    def _calculate_weighted(
        self,
        joined: gpd.GeoDataFrame,
        grid: gpd.GeoDataFrame,
        mortality_field: str
    ) -> pd.Series:
        """Weight mortality by tree count (more dead trees = higher score)"""
        # Average mortality * log(tree count + 1)
        agg = joined.groupby('grid_id').agg({
            mortality_field: 'mean',
            'grid_id': 'size'  # Count
        })
        agg.columns = ['avg_mortality', 'tree_count']
        
        # Weighted score
        weighted = agg['avg_mortality'] * np.log1p(agg['tree_count'])
        
        scores = self.normalize_score(weighted, inverse=False)
        return scores