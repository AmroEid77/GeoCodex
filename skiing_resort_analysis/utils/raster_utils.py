# -*- coding: utf-8 -*-
"""
Raster Utility Functions
Common raster operations for terrain analysis
"""

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from typing import Tuple


def create_empty_raster_like(
    template_path: str,
    output_path: str,
    data: np.ndarray,
    nodata: float = -9999
) -> None:
    """
    Create a new raster with same properties as template
    
    Args:
        template_path: Path to template raster
        output_path: Path for output raster
        data: Numpy array of values
        nodata: NoData value
    """
    with rasterio.open(template_path) as src:
        profile = src.profile.copy()
        profile.update(
            dtype=rasterio.float32,
            count=1,
            compress='lzw',
            nodata=nodata
        )
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data.astype(rasterio.float32), 1)


def calculate_slope(dem_array: np.ndarray, cell_size: float) -> np.ndarray:
    """
    Calculate slope in degrees from DEM
    
    Args:
        dem_array: DEM elevation values
        cell_size: Pixel size in map units
        
    Returns:
        Slope array in degrees
    """
    # Calculate gradients
    dy, dx = np.gradient(dem_array, cell_size)
    
    # Calculate slope in radians then convert to degrees
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    
    return slope_deg


def calculate_aspect(dem_array: np.ndarray, cell_size: float) -> np.ndarray:
    """
    Calculate aspect (orientation) in degrees from DEM
    
    Args:
        dem_array: DEM elevation values
        cell_size: Pixel size in map units
        
    Returns:
        Aspect array in degrees (0-360, 0=North)
    """
    # Calculate gradients
    dy, dx = np.gradient(dem_array, cell_size)
    
    # Calculate aspect in radians
    aspect_rad = np.arctan2(-dy, dx)
    
    # Convert to degrees (0-360, 0=North)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg = 90 - aspect_deg
    aspect_deg[aspect_deg < 0] += 360
    
    # Handle flat areas (slope = 0)
    slope = calculate_slope(dem_array, cell_size)
    aspect_deg[slope < 0.1] = -1  # -1 indicates flat area
    
    return aspect_deg


def calculate_hillshade(
    dem_array: np.ndarray,
    cell_size: float,
    azimuth: float = 315,
    altitude: float = 45
) -> np.ndarray:
    """
    Calculate hillshade from DEM
    
    Args:
        dem_array: DEM elevation values
        cell_size: Pixel size in map units
        azimuth: Sun azimuth in degrees (0-360, 0=North)
        altitude: Sun altitude in degrees (0-90)
        
    Returns:
        Hillshade array (0-255)
    """
    # Convert angles to radians
    azimuth_rad = np.radians(360 - azimuth + 90)
    altitude_rad = np.radians(altitude)
    
    # Calculate gradients
    dy, dx = np.gradient(dem_array, cell_size)
    
    # Calculate slope and aspect
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect_rad = np.arctan2(-dy, dx)
    
    # Calculate hillshade
    hillshade = (
        np.sin(altitude_rad) * np.cos(slope_rad) +
        np.cos(altitude_rad) * np.sin(slope_rad) *
        np.cos(azimuth_rad - aspect_rad)
    )
    
    # Scale to 0-255
    hillshade = np.clip(hillshade * 255, 0, 255)
    
    return hillshade


def normalize_array(
    array: np.ndarray,
    min_val: float = 0,
    max_val: float = 100,
    mask_nodata: bool = True,
    nodata_value: float = -9999
) -> np.ndarray:
    """
    Normalize array to specified range
    
    Args:
        array: Input array
        min_val: Minimum value for output
        max_val: Maximum value for output
        mask_nodata: Whether to preserve nodata values
        nodata_value: NoData value to preserve
        
    Returns:
        Normalized array
    """
    if mask_nodata:
        mask = array == nodata_value
    
    arr_min = np.nanmin(array[array != nodata_value])
    arr_max = np.nanmax(array[array != nodata_value])
    
    if arr_max == arr_min:
        normalized = np.full_like(array, (min_val + max_val) / 2)
    else:
        normalized = (array - arr_min) / (arr_max - arr_min)
        normalized = normalized * (max_val - min_val) + min_val
    
    if mask_nodata:
        normalized[mask] = nodata_value
    
    return normalized


def reclassify_array(
    array: np.ndarray,
    breaks: list,
    values: list,
    nodata_value: float = -9999
) -> np.ndarray:
    """
    Reclassify array based on break points
    
    Args:
        array: Input array
        breaks: List of break points [min, b1, b2, ..., max]
        values: List of output values (len = len(breaks) - 1)
        nodata_value: NoData value
        
    Returns:
        Reclassified array
    """
    result = np.full_like(array, nodata_value)
    mask = array != nodata_value
    
    for i in range(len(breaks) - 1):
        condition = (array >= breaks[i]) & (array < breaks[i + 1]) & mask
        result[condition] = values[i]
    
    return result