# -*- coding: utf-8 -*-
"""
Test script for top locations visualization
"""
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Fix PROJ database
try:
    import pyproj
    os.environ['PROJ_LIB'] = pyproj.datadir.get_data_dir()
except Exception:
    pass

import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from rasterio.transform import from_bounds

from skiing_resort_analysis.utils.location_visualizer import (
    create_location_suitability_plot,
    create_location_detail_plots
)

def test_location_visualizations():
    """Test the location visualization functions"""
    
    print("="*70)
    print("TESTING TOP LOCATIONS VISUALIZATION")
    print("="*70)
    
    # Create synthetic test data
    print("\n1. Creating synthetic test data...")
    
    # Create a synthetic suitability array (100x100)
    np.random.seed(42)
    suitability = np.random.rand(100, 100) * 100
    
    # Add some high suitability "hotspots"
    suitability[20:30, 20:30] = 95 + np.random.rand(10, 10) * 5  # Hotspot 1
    suitability[50:60, 70:80] = 90 + np.random.rand(10, 10) * 5  # Hotspot 2
    suitability[75:85, 30:40] = 85 + np.random.rand(10, 10) * 5  # Hotspot 3
    
    # Create synthetic terrain data
    slope = np.random.rand(100, 100) * 45
    aspect = np.random.rand(100, 100) * 360
    hillshade = np.random.rand(100, 100) * 255
    snow = np.random.rand(100, 100) * 30
    
    # Create transform (10m pixel size)
    transform = from_bounds(0, 0, 1000, 1000, 100, 100)
    
    # Create synthetic best locations GeoDataFrame
    locations_data = [
        {'rank': 1, 'suitability': 98.5, 'geometry': Point(250, 750)},  # Row 25, Col 25
        {'rank': 2, 'suitability': 93.2, 'geometry': Point(750, 250)},  # Row 75, Col 75
        {'rank': 3, 'suitability': 87.8, 'geometry': Point(350, 150)},  # Row 85, Col 35
        {'rank': 4, 'suitability': 85.1, 'geometry': Point(600, 400)},
        {'rank': 5, 'suitability': 82.3, 'geometry': Point(450, 650)},
    ]
    best_locations_gdf = gpd.GeoDataFrame(locations_data, crs="EPSG:32610")
    
    # Create synthetic suitable areas (can be None for basic test)
    suitable_areas_gdf = None
    
    print("✓ Test data created")
    
    # Test 1: Main visualization
    print("\n2. Testing main location visualization...")
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        create_location_suitability_plot(
            suitability_array=suitability,
            best_locations_gdf=best_locations_gdf,
            suitable_areas_gdf=suitable_areas_gdf,
            transform=transform,
            output_path=os.path.join(output_dir, "test_top_locations.png"),
            title="Test Ski Resort Locations"
        )
        print("✓ Main visualization test passed")
    except Exception as e:
        print(f"✗ Main visualization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Detail plots
    print("\n3. Testing detail location plots...")
    try:
        create_location_detail_plots(
            suitability_array=suitability,
            best_locations_gdf=best_locations_gdf,
            transform=transform,
            slope_array=slope,
            aspect_array=aspect,
            hillshade_array=hillshade,
            snow_array=snow,
            output_path=os.path.join(output_dir, "test_location_details.png"),
            zoom_size=20
        )
        print("✓ Detail plots test passed")
    except Exception as e:
        print(f"✗ Detail plots test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED")
    print("="*70)
    print(f"\nTest outputs saved to: {output_dir}/")
    print("  - test_top_locations.png")
    print("  - test_location_details.png")
    
    return True


if __name__ == '__main__':
    success = test_location_visualizations()
    sys.exit(0 if success else 1)
