# -*- coding: utf-8 -*-
"""
Data Loader - Load and validate all spatial datasets
Handles shapefile loading, CRS transformation, and validation
"""

import os
import geopandas as gpd
from typing import Dict, Optional
from shapely.geometry import Point, LineString, Polygon
from .config import SHAPEFILES, ANALYSIS_CRS, OPTIONS


class DataLoader:
    """Load and validate spatial datasets for tree priority analysis"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.data: Dict[str, gpd.GeoDataFrame] = {}
        
    def log(self, message: str):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[DataLoader] {message}")
    
    def load_all(self) -> Dict[str, gpd.GeoDataFrame]:
        """
        Load all required shapefiles
        
        Returns:
            Dictionary of GeoDataFrames keyed by layer name
        """
        self.log("=" * 70)
        self.log("Loading spatial datasets...")
        self.log("=" * 70)
        
        for name, path in SHAPEFILES.items():
            self.data[name] = self.load_shapefile(name, path)
        
        self.log(f"\n✓ Successfully loaded {len(self.data)} datasets")
        return self.data
    
    def load_shapefile(
        self, 
        name: str, 
        path: str, 
        required: bool = True
    ) -> Optional[gpd.GeoDataFrame]:
        """
        Load a single shapefile with validation
        
        Args:
            name: Layer name for logging
            path: Path to shapefile
            required: If True, raise error if file missing
            
        Returns:
            GeoDataFrame or None if not required and missing
        """
        if not os.path.exists(path):
            if required:
                raise FileNotFoundError(f"Required shapefile not found: {path}")
            else:
                self.log(f"⚠ Optional file not found: {name}")
                return None
        
        self.log(f"Loading {name}...")
        
        try:
            gdf = gpd.read_file(path)
            
            # Validation
            if gdf.empty:
                self.log(f"  ⚠ Warning: {name} is empty")
                return gdf
            
            # Check for geometry column
            if gdf.geometry.name is None:
                raise ValueError(f"{name} has no geometry column")
            
            # Validate geometries
            if OPTIONS['validate_geometries']:
                invalid_count = (~gdf.geometry.is_valid).sum()
                if invalid_count > 0:
                    self.log(f"  ⚠ {invalid_count} invalid geometries found, fixing...")
                    gdf['geometry'] = gdf.geometry.buffer(0)  # Fix invalid geometries
            
            # Transform to target CRS
            original_crs = gdf.crs
            if gdf.crs != ANALYSIS_CRS:
                self.log(f"  → Transforming from {original_crs} to {ANALYSIS_CRS}")
                gdf = gdf.to_crs(ANALYSIS_CRS)
            
            self.log(f"  ✓ Loaded {len(gdf)} features | Geometry: {gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else 'N/A'}")
            
            return gdf
            
        except Exception as e:
            self.log(f"  ✗ Error loading {name}: {e}")
            if required:
                raise
            return None
    
    def combine_utility_layers(self) -> gpd.GeoDataFrame:
        """
        Combine all utility layers (transmission, sub-transmission, circuits) into one
        
        Returns:
            Combined GeoDataFrame of all utilities
        """
        self.log("Combining utility layers...")
        
        utility_layers = []
        for name in ['transmission', 'sub_transmission', 'dist_circuits']:
            if name in self.data and self.data[name] is not None:
                gdf = self.data[name].copy()
                gdf['utility_type'] = name
                utility_layers.append(gdf)
        
        if not utility_layers:
            raise ValueError("No utility layers found to combine")
        
        combined = gpd.GeoDataFrame(
            pd.concat(utility_layers, ignore_index=True),
            crs=ANALYSIS_CRS
        )
        
        self.log(f"  ✓ Combined {len(combined)} utility features from {len(utility_layers)} layers")
        return combined
    
    def get_summary(self) -> str:
        """Generate a summary report of loaded data"""
        lines = [
            "\n" + "=" * 70,
            "DATA SUMMARY",
            "=" * 70,
        ]
        
        for name, gdf in self.data.items():
            if gdf is not None:
                geom_type = gdf.geometry.geom_type.mode()[0] if len(gdf) > 0 else "N/A"
                lines.append(f"{name:20} | {len(gdf):6} features | {geom_type:15} | CRS: {gdf.crs}")
            else:
                lines.append(f"{name:20} | NOT LOADED")
        
        lines.append("=" * 70)
        return "\n".join(lines)


# Convenience imports
import pandas as pd