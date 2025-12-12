# -*- coding: utf-8 -*-
"""
Hillshade/Shading Analysis for Ski Resort Suitability
"""
import numpy as np
import rasterio
from rasterio.transform import Affine
from ..utils.raster_utils import calculate_hillshade, normalize_array
from ..config import HILLSHADE_CRITERIA


class ShadingAnalyzer:
    """Analyze terrain shading for ski resort suitability"""
    
    def __init__(self, azimuth: float = 315, altitude: float = 45):
        """
        Initialize ShadingAnalyzer
        
        Args:
            azimuth: Sun azimuth angle in degrees (default: 315 = NW)
            altitude: Sun altitude angle in degrees (default: 45)
        """
        self.azimuth = azimuth
        self.altitude = altitude
        self.hillshade_array = None
        self.suitability_array = None
        self.criteria = HILLSHADE_CRITERIA
    
    def calculate_hillshade(self, dem_array: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Calculate hillshade from DEM
        
        Args:
            dem_array: Digital Elevation Model array
            cell_size: Cell size in meters
            
        Returns:
            Hillshade array (0-255)
        """
        print("\n" + "="*60)
        print("HILLSHADE ANALYSIS")
        print("="*60)
        
        print(f"Calculating hillshade (azimuth: {self.azimuth}°, altitude: {self.altitude}°)...")
        hillshade = calculate_hillshade(dem_array, cell_size, self.azimuth, self.altitude)
        
        print(f"  Hillshade range: {np.nanmin(hillshade):.2f} - {np.nanmax(hillshade):.2f}")
        print(f"  Mean hillshade: {np.nanmean(hillshade):.2f}")
        
        self.hillshade_array = hillshade
        return hillshade
    
    def calculate_suitability(self, hillshade_array: np.ndarray = None) -> np.ndarray:
        """
        Calculate shading suitability score (0-100)
        
        Moderate shading is preferred (better snow retention, protection from wind)
        
        Scoring rules:
        - Very bright (> optimal_shade + 50): score = 60 (too exposed)
        - Optimal (around optimal_shade ± 25): score = 100
        - Dark (< min_shade): score = 70 (protected, good for snow)
        
        Args:
            hillshade_array: Hillshade array (0-255) (if None, uses cached)
            
        Returns:
            Suitability score array (0-100)
        """
        if hillshade_array is None:
            if self.hillshade_array is None:
                raise ValueError("Hillshade not calculated. Call calculate_hillshade() first.")
            hillshade_array = self.hillshade_array
        
        print("\nCalculating hillshade suitability scores...")
        
        min_shade = self.criteria['min_shade']
        optimal_shade = self.criteria['optimal_shade']
        
        # Initialize suitability array
        suitability = np.zeros_like(hillshade_array)
        
        # Very dark (< min_shade): score = 70 (protected, good snow retention)
        mask_dark = hillshade_array < min_shade
        suitability[mask_dark] = 70
        
        # Optimal range (min_shade to optimal_shade + 50): score based on distance from optimal
        mask_moderate = (hillshade_array >= min_shade) & (hillshade_array <= optimal_shade + 50)
        if np.any(mask_moderate):
            # Gaussian-like scoring centered on optimal_shade
            distance_from_optimal = np.abs(hillshade_array[mask_moderate] - optimal_shade)
            suitability[mask_moderate] = 100 - (distance_from_optimal / 50) * 40
        
        # Very bright (> optimal_shade + 50): score = 60 (too exposed)
        mask_bright = hillshade_array > optimal_shade + 50
        suitability[mask_bright] = 60
        
        # Preserve NaN values
        suitability[np.isnan(hillshade_array)] = np.nan
        
        # Print statistics
        print(f"  Criteria:")
        print(f"    Min shade threshold: {min_shade}")
        print(f"    Optimal shade: {optimal_shade}")
        print(f"  Results:")
        print(f"    Dark (<{min_shade}): {np.sum(mask_dark)} cells")
        print(f"    Moderate ({min_shade}-{optimal_shade + 50}): {np.sum(mask_moderate)} cells")
        print(f"    Bright (>{optimal_shade + 50}): {np.sum(mask_bright)} cells")
        print(f"  Suitability range: {np.nanmin(suitability):.2f} - {np.nanmax(suitability):.2f}")
        
        self.suitability_array = suitability
        return suitability
    
    def save_hillshade(self, output_path: str, transform: Affine, crs: str):
        """
        Save hillshade raster to file
        
        Args:
            output_path: Output file path
            transform: Raster transform
            crs: Coordinate reference system
        """
        if self.hillshade_array is None:
            raise ValueError("Hillshade not calculated")
        
        height, width = self.hillshade_array.shape
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=self.hillshade_array.dtype,
            crs=crs,
            transform=transform,
            nodata=np.nan
        ) as dst:
            dst.write(self.hillshade_array, 1)
        
        print(f"\nHillshade raster saved to: {output_path}")