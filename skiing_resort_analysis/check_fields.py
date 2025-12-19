#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Field Name Validation Script for Skiing Resort Analysis
Checks if all expected field names match the actual PostGIS schema
"""

import geopandas as gpd
import os
from config import INPUT_FILES, SNOW_DEPTH_FIELD, STATION_ID_FIELD

def check_shapefile_fields(shapefile_path, expected_fields, layer_name):
    """
    Check if shapefile has expected fields
    
    Args:
        shapefile_path: Path to shapefile
        expected_fields: Dictionary of {purpose: field_name}
        layer_name: Name of layer for display
    """
    print(f"\n{'='*70}")
    print(f"LAYER: {layer_name}")
    print(f"{'='*70}")
    print(f"File: {shapefile_path}")
    
    if not os.path.exists(shapefile_path):
        print(f"❌ FILE NOT FOUND")
        return False
    
    try:
        gdf = gpd.read_file(shapefile_path)
        actual_fields = list(gdf.columns)
        
        print(f"\nActual fields in shapefile:")
        for field in actual_fields:
            if field != 'geometry':
                print(f"  - {field}")
        
        print(f"\nExpected fields:")
        all_match = True
        for purpose, field_name in expected_fields.items():
            if field_name in actual_fields:
                print(f"  ✓ {purpose}: '{field_name}' FOUND")
            else:
                print(f"  ❌ {purpose}: '{field_name}' NOT FOUND")
                all_match = False
                
                # Suggest alternatives
                similar = [f for f in actual_fields if field_name.lower() in f.lower() or f.lower() in field_name.lower()]
                if similar:
                    print(f"     → Similar fields found: {similar}")
        
        return all_match
        
    except Exception as e:
        print(f"❌ ERROR reading shapefile: {e}")
        return False


def main():
    """Main validation function"""
    print("\n" + "="*70)
    print("SKIING RESORT ANALYSIS - FIELD NAME VALIDATION")
    print("="*70)
    
    results = {}
    
    # Check snow points shapefile
    results['snow_points'] = check_shapefile_fields(
        INPUT_FILES['snow_points'],
        {
            'Snow Depth': SNOW_DEPTH_FIELD,
            'Station ID': STATION_ID_FIELD,
        },
        'Snow Measurement Points'
    )
    
    # Check contours shapefile
    results['contours'] = check_shapefile_fields(
        INPUT_FILES['contours'],
        {
            'Contour Elevation': 'CONTOUR',  # Uppercase in shapefile
        },
        'Contour Lines'
    )
    
    # Check dam line shapefile (no specific fields required, just geometry)
    results['dam_line'] = check_shapefile_fields(
        INPUT_FILES['dam_line'],
        {},  # No required fields
        'Dam Line (Reference only)'
    )
    
    # Check ridges shapefile
    results['ridges'] = check_shapefile_fields(
        INPUT_FILES['ridges'],
        {},  # No required fields in current analysis
        'Ridges (Reference only)'
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for layer, status in results.items():
        symbol = "✓" if status else "❌"
        print(f"{symbol} {layer}: {'PASS' if status else 'FAIL'}")
    
    print(f"\nResult: {passed}/{total} layers passed validation")
    
    if passed == total:
        print("\n✓ All field names are correct!")
        print("You can safely run the main analysis.")
    else:
        print("\n❌ Some field names don't match!")
        print("Please update config.py with the correct field names shown above.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
