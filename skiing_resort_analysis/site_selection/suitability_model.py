# -*- coding: utf-8 -*-
"""
Suitability Model for Ski Resort Site Selection
Combines multiple factors using weighted overlay
"""
import numpy as np
import rasterio
from rasterio.transform import Affine
import geopandas as gpd
from shapely.geometry import Point, Polygon
from scipy.ndimage import label, maximum_filter
from typing import List, Tuple, Dict
from ..config import SUITABILITY_WEIGHTS, SUITABILITY_THRESHOLD


class SuitabilityModel:
    """Weighted overlay suitability model for ski resort site selection"""
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize SuitabilityModel
        
        Args:
            weights: Dictionary of factor weights (default: from config)
        """
        if weights is None:
            weights = SUITABILITY_WEIGHTS
        
        # Validate weights
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0 (current sum: {total})")
        
        self.weights = weights
        self.suitability_array = None
    
    def calculate_suitability(self, 
                             slope_suitability: np.ndarray,
                             aspect_suitability: np.ndarray,
                             hillshade_suitability: np.ndarray,
                             snow_suitability: np.ndarray = None) -> np.ndarray:
        """
        Calculate overall suitability using weighted overlay
        
        Args:
            slope_suitability: Slope suitability scores (0-100)
            aspect_suitability: Aspect suitability scores (0-100)
            hillshade_suitability: Hillshade suitability scores (0-100)
            snow_suitability: Snow depth suitability scores (0-100, optional)
            
        Returns:
            Overall suitability scores (0-100)
        """
        print("\n" + "="*60)
        print("SUITABILITY MODEL - WEIGHTED OVERLAY")
        print("="*60)
        
        print(f"\nWeights:")
        print(f"  Slope: {self.weights['slope']*100:.1f}%")
        print(f"  Aspect: {self.weights['aspect']*100:.1f}%")
        print(f"  Hillshade: {self.weights['hillshade']*100:.1f}%")
        if snow_suitability is not None:
            print(f"  Snow depth: {self.weights['snow_depth']*100:.1f}%")
        
        # Initialize suitability
        suitability = np.zeros_like(slope_suitability)
        
        # Weighted overlay
        suitability += slope_suitability * self.weights['slope']
        suitability += aspect_suitability * self.weights['aspect']
        suitability += hillshade_suitability * self.weights['hillshade']
        
        if snow_suitability is not None:
            suitability += snow_suitability * self.weights['snow_depth']
        else:
            # Redistribute snow weight to other factors
            remaining_weight = 1.0 - self.weights['snow_depth']
            suitability = suitability / remaining_weight
        
        # Preserve NaN values
        mask_nan = (np.isnan(slope_suitability) | 
                    np.isnan(aspect_suitability) | 
                    np.isnan(hillshade_suitability))
        suitability[mask_nan] = np.nan
        
        print(f"\nOverall Suitability:")
        print(f"  Range: {np.nanmin(suitability):.2f} - {np.nanmax(suitability):.2f}")
        print(f"  Mean: {np.nanmean(suitability):.2f}")
        print(f"  Median: {np.nanmedian(suitability):.2f}")
        
        # Count cells by suitability class
        high_suit = np.sum(suitability >= 80)
        moderate_suit = np.sum((suitability >= 60) & (suitability < 80))
        low_suit = np.sum(suitability < 60)
        
        print(f"\nSuitability Classes:")
        print(f"  High (≥80): {high_suit} cells")
        print(f"  Moderate (60-80): {moderate_suit} cells")
        print(f"  Low (<60): {low_suit} cells")
        
        self.suitability_array = suitability
        return suitability
    
    def extract_suitable_areas(self, 
                               transform: Affine,
                               crs: str,
                               threshold: float = None) -> gpd.GeoDataFrame:
        """
        Extract suitable areas as polygons
        
        Args:
            transform: Raster transform
            crs: Coordinate reference system
            threshold: Minimum suitability threshold (default: from config)
            
        Returns:
            GeoDataFrame with suitable area polygons
        """
        if self.suitability_array is None:
            raise ValueError("Suitability not calculated")
        
        if threshold is None:
            threshold = SUITABILITY_THRESHOLD
        
        print(f"\nExtracting suitable areas (threshold ≥ {threshold})...")
        
        # Binary mask of suitable cells
        suitable_mask = self.suitability_array >= threshold
        suitable_mask = suitable_mask.astype(int)
        
        # Label connected regions
        labeled_array, num_features = label(suitable_mask)
        
        print(f"  Found {num_features} suitable regions")
        
        # Extract polygons for each region
        features = []
        for region_id in range(1, num_features + 1):
            region_mask = labeled_array == region_id
            region_suitability = self.suitability_array[region_mask]
            
            # Calculate region statistics
            area_cells = np.sum(region_mask)
            mean_suitability = np.mean(region_suitability)
            max_suitability = np.max(region_suitability)
            
            # Get region bounds
            rows, cols = np.where(region_mask)
            
            if len(rows) == 0:
                continue
            
            # Create simple bounding box polygon
            min_row, max_row = rows.min(), rows.max()
            min_col, max_col = cols.min(), cols.max()
            
            # Convert to coordinates
            x_min, y_max = transform * (min_col, min_row)
            x_max, y_min = transform * (max_col + 1, max_row + 1)
            
            # Create polygon
            polygon = Polygon([
                (x_min, y_min),
                (x_max, y_min),
                (x_max, y_max),
                (x_min, y_max),
                (x_min, y_min)
            ])
            
            features.append({
                'geometry': polygon,
                'region_id': region_id,
                'area_cells': area_cells,
                'mean_suitability': mean_suitability,
                'max_suitability': max_suitability,
            })
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(features, crs=crs)
        
        # Sort by mean suitability
        gdf = gdf.sort_values('mean_suitability', ascending=False)
        
        print(f"  Total suitable area: {gdf['area_cells'].sum()} cells")
        
        return gdf
    
    def find_best_locations(self, 
                           transform: Affine,
                           crs: str,
                           n_locations: int = 5) -> gpd.GeoDataFrame:
        """
        Find N best point locations for ski resort
        
        Args:
            transform: Raster transform
            crs: Coordinate reference system
            n_locations: Number of best locations to find
            
        Returns:
            GeoDataFrame with best location points
        """
        if self.suitability_array is None:
            raise ValueError("Suitability not calculated")
        
        print(f"\nFinding {n_locations} best locations...")
        
        # Find local maxima using maximum filter
        local_max = maximum_filter(np.nan_to_num(self.suitability_array, nan=0), size=20)
        is_local_max = (self.suitability_array == local_max) & (self.suitability_array > 0)
        
        # Get coordinates and values of local maxima
        rows, cols = np.where(is_local_max)
        values = self.suitability_array[rows, cols]
        
        # Sort by suitability (descending)
        sort_idx = np.argsort(values)[::-1]
        rows = rows[sort_idx]
        cols = cols[sort_idx]
        values = values[sort_idx]
        
        # Take top N
        n = min(n_locations, len(rows))
        
        features = []
        for i in range(n):
            # Convert to coordinates
            x, y = transform * (cols[i] + 0.5, rows[i] + 0.5)
            
            features.append({
                'geometry': Point(x, y),
                'rank': i + 1,
                'suitability': values[i],
                'row': rows[i],
                'col': cols[i],
            })
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(features, crs=crs)
        
        print(f"  Top {n} locations identified:")
        for idx, row in gdf.iterrows():
            print(f"    Rank {row['rank']}: Suitability = {row['suitability']:.2f}")
        
        return gdf
    
    def save_suitability(self, output_path: str, transform: Affine, crs: str):
        """
        Save suitability raster to file
        
        Args:
            output_path: Output file path
            transform: Raster transform
            crs: Coordinate reference system
        """
        if self.suitability_array is None:
            raise ValueError("Suitability not calculated")
        
        height, width = self.suitability_array.shape
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=self.suitability_array.dtype,
            crs=crs,
            transform=transform,
            nodata=np.nan
        ) as dst:
            dst.write(self.suitability_array, 1)
        
        print(f"\nSuitability raster saved to: {output_path}")