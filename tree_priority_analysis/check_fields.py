"""
Diagnostic script to verify all field names match PostGIS schema
Run this before the main analysis to check field mappings
"""

import geopandas as gpd
import os
from config import (
    DATA_DIR, 
    MORTALITY_FIELDS, 
    POPULATION_FIELDS,
    COMMUNITY_FIELDS,
    EGRESS_FIELDS,
    GRID_FIELDS
)

def check_shapefile_fields(shapefile_path, expected_fields, description):
    """Check if shapefile has expected fields"""
    print(f"\n{'='*70}")
    print(f"Checking: {description}")
    print(f"File: {os.path.basename(shapefile_path)}")
    print(f"{'='*70}")
    
    if not os.path.exists(shapefile_path):
        print(f"❌ FILE NOT FOUND: {shapefile_path}")
        return False
    
    try:
        gdf = gpd.read_file(shapefile_path)
        print(f"✓ Loaded successfully: {len(gdf)} features")
        print(f"  CRS: {gdf.crs}")
        print(f"  Geometry Type: {gdf.geom_type.unique()}")
        print(f"\nActual Fields:")
        for i, col in enumerate(gdf.columns, 1):
            dtype = gdf[col].dtype
            print(f"  {i}. {col:20s} ({dtype})")
        
        print(f"\nExpected Fields from Config:")
        all_found = True
        for key, field_name in expected_fields.items():
            if isinstance(field_name, dict):
                continue  # Skip nested dicts
            if field_name in gdf.columns:
                print(f"  ✓ {key:20s} → '{field_name}'")
            else:
                print(f"  ❌ {key:20s} → '{field_name}' NOT FOUND!")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error loading shapefile: {e}")
        return False

def main():
    print("="*70)
    print("FIRE CREEK DATA FIELD VALIDATION")
    print("="*70)
    
    # Check each shapefile
    results = []
    
    # 1. Cutting Grid
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'CuttingGrids.shp'),
        GRID_FIELDS,
        "Cutting Grid (Analysis Base)"
    ))
    
    # 2. Mortality Data
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'SBNFMortalityt.shp'),
        MORTALITY_FIELDS,
        "Tree Mortality Data"
    ))
    
    # 3. Community Features
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'Communityfeatures.shp'),
        COMMUNITY_FIELDS,
        "Community Features (Buildings, Parks, Schools)"
    ))
    
    # 4. Egress Routes
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'EgressRoutes.shp'),
        EGRESS_FIELDS,
        "Egress/Evacuation Routes"
    ))
    
    # 5. Populated Areas
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'PopulatedAreast.shp'),
        POPULATION_FIELDS,
        "Populated Areas"
    ))
    
    # 6. Transmission Lines
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'Transmission.shp'),
        {},
        "Transmission Lines (High Voltage)"
    ))
    
    # 7. SubTransmission Lines
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'SubTransmission.shp'),
        {},
        "SubTransmission Lines (Medium Voltage)"
    ))
    
    # 8. Distribution Circuits
    results.append(check_shapefile_fields(
        os.path.join(DATA_DIR, 'DistCircuits.shp'),
        {},
        "Distribution Circuits"
    ))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Files Checked: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if all(results):
        print("\n✓ ALL FIELD MAPPINGS CORRECT!")
        print("  You can now run the main analysis:")
        print("  python -m tree_priority_analysis.main")
    else:
        print("\n❌ SOME FIELD MAPPINGS INCORRECT!")
        print("  Please update config.py with correct field names")
        print("  See details above for which fields are missing")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
