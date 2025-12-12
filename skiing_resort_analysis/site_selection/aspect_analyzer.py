# -*- coding: utf-8 -*-
"""
Aspect Analysis for Ski Resort Suitability
"""
import numpy as np
import rasterio
from rasterio.transform import Affine
from ..utils.raster_utils import calculate_aspect
from ..config import ASPECT_CRITERIA


class AspectAnalyzer:
    """Analyze aspect suitability for skiing (north-facing slopes preferred)"""
    
    def __init__(self):
        """Initialize AspectAnalyzer"""
        self.aspect_array = None
        self.suitability_array = None
        self.criteria = ASPECT_CRITERIA
    
    def calculate_aspect(self, dem_array: np.ndarray, cell_size: float) -> np.ndarray:
        """
        Calculate aspect from DEM
        
        Args:
            dem_array: Digital Elevation Model array
            cell_size: Cell size in meters
            
        Returns:
            Aspect array in degrees (0-360, 0=North)
        """
        print("\n" + "="*60)
        print("ASPECT ANALYSIS")
        print("="*60)
        
        print(f"Calculating aspect (cell size: {cell_size}m)...")
        aspect = calculate_aspect(dem_array, cell_size)
        
        print(f"  Aspect range: {np.nanmin(aspect):.2f}° - {np.nanmax(aspect):.2f}°")
        
        self.aspect_array = aspect
        return aspect
    
    def calculate_suitability(self, aspect_array: np.ndarray = None) -> np.ndarray:
        """
        Calculate aspect suitability score (0-100)
        
        North-facing slopes (315-45°) are most suitable (less sun exposure, better snow retention)
        
        Scoring rules:
        - Preferred (315-360° or 0-45°): 100
        - Acceptable (270-315° or 45-90°): 70
        - Less favorable (90-180°): 30 (south-facing, too much sun)
        - Unfavorable (180-270°): 50 (south-west to west)
        
        Args:
            aspect_array: Aspect array in degrees (if None, uses cached)
            
        Returns:
            Suitability score array (0-100)
        """
        if aspect_array is None:
            if self.aspect_array is None:
                raise ValueError("Aspect not calculated. Call calculate_aspect() first.")
            aspect_array = self.aspect_array
        
        print("\nCalculating aspect suitability scores...")
        
        preferred_min = self.criteria['preferred_min']  # 315
        preferred_max = self.criteria['preferred_max']  # 45
        acceptable_min = self.criteria['acceptable_min']  # 270
        acceptable_max = self.criteria['acceptable_max']  # 90
        
        # Initialize suitability array
        suitability = np.zeros_like(aspect_array)
        
        # Preferred: North-facing (315-360° or 0-45°): score = 100
        mask_north = (aspect_array >= preferred_min) | (aspect_array <= preferred_max)
        suitability[mask_north] = 100
        
        # Acceptable: Northwest or Northeast (270-315° or 45-90°): score = 70
        mask_nw = (aspect_array >= acceptable_min) & (aspect_array < preferred_min)
        mask_ne = (aspect_array > preferred_max) & (aspect_array <= acceptable_max)
        mask_acceptable = mask_nw | mask_ne
        suitability[mask_acceptable] = 70
        
        # Less favorable: East to South (90-180°): score = 30
        mask_south = (aspect_array > acceptable_max) & (aspect_array <= 180)
        suitability[mask_south] = 30
        
        # Unfavorable: South to West (180-270°): score = 50
        mask_sw_west = (aspect_array > 180) & (aspect_array < acceptable_min)
        suitability[mask_sw_west] = 50
        
        # Preserve NaN values
        suitability[np.isnan(aspect_array)] = np.nan
        
        # Print statistics
        print(f"  Criteria:")
        print(f"    Preferred: North-facing ({preferred_min}-360° or 0-{preferred_max}°)")
        print(f"    Acceptable: NW/NE ({acceptable_min}-{preferred_min}° or {preferred_max}-{acceptable_max}°)")
        print(f"  Results:")
        print(f"    North (preferred): {np.sum(mask_north)} cells")
        print(f"    NW/NE (acceptable): {np.sum(mask_acceptable)} cells")
        print(f"    East-South: {np.sum(mask_south)} cells")
        print(f"    SW-West: {np.sum(mask_sw_west)} cells")
        print(f"  Suitability range: {np.nanmin(suitability):.2f} - {np.nanmax(suitability):.2f}")
        
        self.suitability_array = suitability
        return suitability
    
    def save_aspect(self, output_path: str, transform: Affine, crs: str):
        """
        Save aspect raster to file
        
        Args:
            output_path: Output file path
            transform: Raster transform
            crs: Coordinate reference system
        """
        if self.aspect_array is None:
            raise ValueError("Aspect not calculated")
        
        height, width = self.aspect_array.shape
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=self.aspect_array.dtype,
            crs=crs,
            transform=transform,
            nodata=np.nan
        ) as dst:
            dst.write(self.aspect_array, 1)
        
        print(f"\nAspect raster saved to: {output_path}")