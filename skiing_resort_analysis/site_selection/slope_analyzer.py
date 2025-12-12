# -*- coding: utf-8 -*-
"""
Slope Analysis for Ski Resort Suitability
"""
import numpy as np
import rasterio
from rasterio.transform import Affine
from typing import Tuple
from ..utils.raster_utils import calculate_slope, normalize_array
from ..config import SLOPE_CRITERIA


class SlopeAnalyzer:
    """Analyze slope suitability for skiing"""
    
    def __init__(self):
        """Initialize SlopeAnalyzer"""
        self.slope_array = None
        self.suitability_array = None
        self.criteria = SLOPE_CRITERIA
    
    def calculate_slope(self, dem_array: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Calculate slope from DEM
        
        Args:
            dem_array: Digital Elevation Model array
            cell_size: Cell size in meters
            
        Returns:
            Slope array in degrees
        """
        print("\n" + "="*60)
        print("SLOPE ANALYSIS")
        print("="*60)
        
        print(f"Calculating slope (cell size: {cell_size}m)...")
        slope = calculate_slope(dem_array, cell_size)
        
        print(f"  Slope range: {np.nanmin(slope):.2f}° - {np.nanmax(slope):.2f}°")
        print(f"  Mean slope: {np.nanmean(slope):.2f}°")
        
        self.slope_array = slope
        return slope
    
    def calculate_suitability(self, slope_array: np.ndarray = None) -> np.ndarray:
        """
        Calculate slope suitability score (0-100)
        
        Scoring rules:
        - < min_slope: 0 (too flat)
        - min_slope to optimal_min: linear ramp 50-100
        - optimal_min to optimal_max: 100 (perfect)
        - optimal_max to max_slope: linear ramp 100-50
        - > max_slope: 0 (too steep/dangerous)
        
        Args:
            slope_array: Slope array in degrees (if None, uses cached)
            
        Returns:
            Suitability score array (0-100)
        """
        if slope_array is None:
            if self.slope_array is None:
                raise ValueError("Slope not calculated. Call calculate_slope() first.")
            slope_array = self.slope_array
        
        print("\nCalculating slope suitability scores...")
        
        min_slope = self.criteria['min_slope']
        optimal_min = self.criteria['optimal_min']
        optimal_max = self.criteria['optimal_max']
        max_slope = self.criteria['max_slope']
        
        # Initialize suitability array
        suitability = np.zeros_like(slope_array)
        
        # Too flat (< min_slope): score = 0
        mask_too_flat = slope_array < min_slope
        suitability[mask_too_flat] = 0
        
        # Marginal low slope (min_slope to optimal_min): score = 50-100
        mask_marginal_low = (slope_array >= min_slope) & (slope_array < optimal_min)
        if np.any(mask_marginal_low):
            suitability[mask_marginal_low] = 50 + 50 * (
                (slope_array[mask_marginal_low] - min_slope) / (optimal_min - min_slope)
            )
        
        # Optimal range (optimal_min to optimal_max): score = 100
        mask_optimal = (slope_array >= optimal_min) & (slope_array <= optimal_max)
        suitability[mask_optimal] = 100
        
        # Marginal high slope (optimal_max to max_slope): score = 100-50
        mask_marginal_high = (slope_array > optimal_max) & (slope_array <= max_slope)
        if np.any(mask_marginal_high):
            suitability[mask_marginal_high] = 100 - 50 * (
                (slope_array[mask_marginal_high] - optimal_max) / (max_slope - optimal_max)
            )
        
        # Too steep (> max_slope): score = 0
        mask_too_steep = slope_array > max_slope
        suitability[mask_too_steep] = 0
        
        # Preserve NaN values
        suitability[np.isnan(slope_array)] = np.nan
        
        # Print statistics
        print(f"  Criteria:")
        print(f"    Min slope: {min_slope}°")
        print(f"    Optimal range: {optimal_min}° - {optimal_max}°")
        print(f"    Max slope: {max_slope}°")
        print(f"  Results:")
        print(f"    Too flat (<{min_slope}°): {np.sum(mask_too_flat)} cells")
        print(f"    Marginal low ({min_slope}-{optimal_min}°): {np.sum(mask_marginal_low)} cells")
        print(f"    Optimal ({optimal_min}-{optimal_max}°): {np.sum(mask_optimal)} cells")
        print(f"    Marginal high ({optimal_max}-{max_slope}°): {np.sum(mask_marginal_high)} cells")
        print(f"    Too steep (>{max_slope}°): {np.sum(mask_too_steep)} cells")
        print(f"  Suitability range: {np.nanmin(suitability):.2f} - {np.nanmax(suitability):.2f}")
        
        self.suitability_array = suitability
        return suitability
    
    def save_slope(self, output_path: str, transform: Affine, crs: str):
        """
        Save slope raster to file
        
        Args:
            output_path: Output file path
            transform: Raster transform
            crs: Coordinate reference system
        """
        if self.slope_array is None:
            raise ValueError("Slope not calculated")
        
        height, width = self.slope_array.shape
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=self.slope_array.dtype,
            crs=crs,
            transform=transform,
            nodata=np.nan
        ) as dst:
            dst.write(self.slope_array, 1)
        
        print(f"\nSlope raster saved to: {output_path}")