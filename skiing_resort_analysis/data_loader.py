# -*- coding: utf-8 -*-
"""
Data Loader for Skiing Resort Analysis
Loads DEM raster and snow point shapefiles with validation
"""
import os
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject
import numpy as np
from typing import Tuple, Dict
from .config import INPUT_FILES, SNOW_DEPTH_FIELD, STATION_ID_FIELD

class DataLoader:
    """Handles loading and validation of input data for skiing resort analysis"""
    
    def __init__(self, target_crs: str = 'EPSG:26710'):
        """
        Initialize DataLoader
        
        Args:
            target_crs: Target coordinate reference system (default: NAD27 UTM Zone 10N)
        """
        self.target_crs = target_crs
        self.dem_data = None
        self.dem_transform = None
        self.dem_meta = None
        self.snow_points = None
        
    def load_dem(self, dem_path: str = None) -> Tuple[np.ndarray, rasterio.Affine, dict]:
        """
        Load DEM raster file
        
        Args:
            dem_path: Path to DEM file (default: from config)
            
        Returns:
            Tuple of (dem_array, transform, metadata)
        """
        if dem_path is None:
            dem_path = INPUT_FILES['dem']
            
        if not os.path.exists(dem_path):
            raise FileNotFoundError(f"DEM file not found: {dem_path}")
        
        print(f"Loading DEM from: {dem_path}")
        
        with rasterio.open(dem_path) as src:
            # Read first band (elevation)
            dem_array = src.read(1)
            transform = src.transform
            meta = src.meta.copy()
            
            # Check CRS
            source_crs = src.crs.to_string() if src.crs else None
            print(f"  DEM CRS: {source_crs}")
            print(f"  DEM Shape: {dem_array.shape}")
            print(f"  DEM Resolution: {src.res}")
            print(f"  DEM Bounds: {src.bounds}")
            print(f"  Elevation Range: {np.nanmin(dem_array):.2f} - {np.nanmax(dem_array):.2f} m")
            
            # Handle nodata values
            if src.nodata is not None:
                dem_array = np.where(dem_array == src.nodata, np.nan, dem_array)
            
            # Store for later use
            self.dem_data = dem_array
            self.dem_transform = transform
            self.dem_meta = meta
            
        return dem_array, transform, meta
    
    def load_snow_points(self, snow_path: str = None) -> gpd.GeoDataFrame:
        """
        Load snow measurement points shapefile
        
        Args:
            snow_path: Path to snow points shapefile (default: from config)
            
        Returns:
            GeoDataFrame with snow points
        """
        if snow_path is None:
            snow_path = INPUT_FILES['snow_points']
            
        if not os.path.exists(snow_path):
            raise FileNotFoundError(f"Snow points file not found: {snow_path}")
        
        print(f"\nLoading snow points from: {snow_path}")
        
        # Load shapefile
        gdf = gpd.read_file(snow_path)
        
        # Validate required fields
        if SNOW_DEPTH_FIELD not in gdf.columns:
            raise ValueError(f"Required field '{SNOW_DEPTH_FIELD}' not found in snow points")
        
        # Check CRS
        print(f"  Original CRS: {gdf.crs}")
        
        # Transform to target CRS if needed
        if gdf.crs and gdf.crs.to_string() != self.target_crs:
            print(f"  Transforming to: {self.target_crs}")
            gdf = gdf.to_crs(self.target_crs)
        
        # Remove invalid geometries
        gdf = gdf[gdf.geometry.is_valid]
        
        # Remove points with null snow depth
        original_count = len(gdf)
        gdf = gdf[gdf[SNOW_DEPTH_FIELD].notna()]
        removed = original_count - len(gdf)
        if removed > 0:
            print(f"  Removed {removed} points with null snow depth")
        
        # Extract coordinates
        gdf['x'] = gdf.geometry.x
        gdf['y'] = gdf.geometry.y
        
        print(f"  Points loaded: {len(gdf)}")
        print(f"  Snow depth range: {gdf[SNOW_DEPTH_FIELD].min():.2f} - {gdf[SNOW_DEPTH_FIELD].max():.2f}")
        print(f"  Bounds: {gdf.total_bounds}")
        
        # Store for later use
        self.snow_points = gdf
        
        return gdf
    
    def load_vector_layer(self, layer_name: str) -> gpd.GeoDataFrame:
        """
        Load additional vector layer (dam_line, ridges, contours)
        
        Args:
            layer_name: Name of layer in INPUT_FILES config
            
        Returns:
            GeoDataFrame
        """
        if layer_name not in INPUT_FILES:
            raise ValueError(f"Unknown layer: {layer_name}")
        
        layer_path = INPUT_FILES[layer_name]
        
        if not os.path.exists(layer_path):
            raise FileNotFoundError(f"Layer file not found: {layer_path}")
        
        print(f"\nLoading {layer_name} from: {layer_path}")
        
        gdf = gpd.read_file(layer_path)
        
        # Transform to target CRS if needed
        if gdf.crs and gdf.crs.to_string() != self.target_crs:
            print(f"  Transforming from {gdf.crs} to {self.target_crs}")
            gdf = gdf.to_crs(self.target_crs)
        
        print(f"  Features loaded: {len(gdf)}")
        
        return gdf
    
    def get_dem_extent(self) -> Dict[str, float]:
        """
        Get DEM extent as bounding box
        
        Returns:
            Dictionary with minx, miny, maxx, maxy
        """
        if self.dem_data is None or self.dem_transform is None:
            raise ValueError("DEM not loaded. Call load_dem() first.")
        
        height, width = self.dem_data.shape
        
        # Get corner coordinates
        minx, miny = self.dem_transform * (0, height)
        maxx, maxy = self.dem_transform * (width, 0)
        
        return {
            'minx': minx,
            'miny': miny,
            'maxx': maxx,
            'maxy': maxy
        }
    
    def validate_spatial_overlap(self) -> bool:
        """
        Validate that snow points overlap with DEM extent
        
        Returns:
            True if there is overlap, False otherwise
        """
        if self.dem_data is None:
            raise ValueError("DEM not loaded. Call load_dem() first.")
        
        if self.snow_points is None:
            raise ValueError("Snow points not loaded. Call load_snow_points() first.")
        
        dem_extent = self.get_dem_extent()
        snow_bounds = self.snow_points.total_bounds  # [minx, miny, maxx, maxy]
        
        # Check for overlap
        overlap_x = not (snow_bounds[2] < dem_extent['minx'] or snow_bounds[0] > dem_extent['maxx'])
        overlap_y = not (snow_bounds[3] < dem_extent['miny'] or snow_bounds[1] > dem_extent['maxy'])
        
        has_overlap = overlap_x and overlap_y
        
        print("\nSpatial Overlap Validation:")
        print(f"  DEM Extent: ({dem_extent['minx']:.2f}, {dem_extent['miny']:.2f}) - ({dem_extent['maxx']:.2f}, {dem_extent['maxy']:.2f})")
        print(f"  Snow Points Extent: ({snow_bounds[0]:.2f}, {snow_bounds[1]:.2f}) - ({snow_bounds[2]:.2f}, {snow_bounds[3]:.2f})")
        print(f"  Overlap: {'YES ✓' if has_overlap else 'NO ✗'}")
        
        return has_overlap
    
    def load_all(self) -> Tuple[np.ndarray, rasterio.Affine, dict, gpd.GeoDataFrame]:
        """
        Load all required data (DEM + snow points) and validate
        
        Returns:
            Tuple of (dem_array, transform, metadata, snow_gdf)
        """
        # Load DEM
        dem_array, transform, meta = self.load_dem()
        
        # Load snow points
        snow_gdf = self.load_snow_points()
        
        # Validate overlap
        if not self.validate_spatial_overlap():
            print("\n⚠ WARNING: Snow points do not overlap with DEM extent!")
        
        return dem_array, transform, meta, snow_gdf