# -*- coding: utf-8 -*-
"""
Quick test script for Tree Priority Analysis
Run this to test the complete pipeline
"""

import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print("=" * 70)
print("TREE CUTTING PRIORITY ANALYSIS - QUICK TEST")
print("=" * 70)

# Step 1: Check if data exists
print("\n[Step 1] Checking for data files...")

from tree_priority_analysis.config import SHAPEFILES, DATA_DIR

print(f"\nData directory: {DATA_DIR}")
print(f"\nLooking for shapefiles:")

missing_files = []
found_files = []

for name, path in SHAPEFILES.items():
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"  {status} {name:20} : {os.path.basename(path)}")
    
    if exists:
        found_files.append(name)
    else:
        missing_files.append(name)

print(f"\nFound: {len(found_files)}/{len(SHAPEFILES)} files")

if missing_files:
    print(f"\n⚠️  MISSING FILES:")
    for name in missing_files:
        print(f"    - {name}: {os.path.basename(SHAPEFILES[name])}")
    print(f"\n💡 Please copy your shapefiles to: {DATA_DIR}")
    print(f"\nExpected files:")
    print("  - CuttingGrids.shp")
    print("  - SBNFMortalityt.shp")
    print("  - Communityfeatures.shp")
    print("  - EgressRoutes.shp")
    print("  - PopulatedAreast.shp")
    print("  - Transmission.shp")
    print("  - SubTransmission.shp")
    print("  - DistCircuits.shp")
    print("  - (and their accompanying .dbf, .shx, .prj files)")
    
    response = input("\n❓ Do you want to continue anyway? (y/n): ")
    if response.lower() != 'y':
        print("\nExiting. Please add the data files and try again.")
        sys.exit(0)

# Step 2: Check dependencies
print("\n[Step 2] Checking dependencies...")

try:
    import geopandas as gpd
    print("  ✓ geopandas")
except ImportError:
    print("  ✗ geopandas - REQUIRED")
    print("    Install with: pip install geopandas")
    sys.exit(1)

try:
    import pandas as pd
    print("  ✓ pandas")
except ImportError:
    print("  ✗ pandas - REQUIRED")
    sys.exit(1)

try:
    import numpy as np
    print("  ✓ numpy")
except ImportError:
    print("  ✗ numpy - REQUIRED")
    sys.exit(1)

try:
    import matplotlib.pyplot as plt
    print("  ✓ matplotlib")
except ImportError:
    print("  ⚠️  matplotlib - optional (for visualizations)")

try:
    import folium
    print("  ✓ folium")
except ImportError:
    print("  ⚠️  folium - optional (for interactive maps)")

# Step 3: Test data loading
print("\n[Step 3] Testing data loader...")

try:
    from tree_priority_analysis.data_loader import DataLoader
    
    loader = DataLoader(verbose=True)
    
    # Try loading just the grid first
    print("\nTrying to load grid (CuttingGrids.shp)...")
    grid = loader.load_shapefile('grid', SHAPEFILES['grid'], required=False)
    
    if grid is not None:
        print(f"  ✓ Grid loaded: {len(grid)} cells")
        print(f"  ✓ CRS: {grid.crs}")
        print(f"  ✓ Geometry type: {grid.geometry.geom_type.iloc[0] if len(grid) > 0 else 'N/A'}")
    else:
        print("  ✗ Could not load grid")
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Ask to run full analysis
print("\n" + "=" * 70)
print("READY TO RUN FULL ANALYSIS")
print("=" * 70)

if len(found_files) < 5:
    print(f"\n⚠️  Warning: Only {len(found_files)} files found.")
    print("The analysis may fail if required layers are missing.")

response = input("\n❓ Run full analysis now? (y/n): ")

if response.lower() == 'y':
    print("\n" + "=" * 70)
    print("STARTING FULL ANALYSIS...")
    print("=" * 70 + "\n")
    
    try:
        from tree_priority_analysis.main import TreePriorityAnalysis
        
        # Create analysis instance
        analysis = TreePriorityAnalysis(verbose=True)
        
        # Run analysis
        result = analysis.run(
            export_results=True,
            create_visualizations=True
        )
        
        print("\n" + "🎉" * 35)
        print("SUCCESS! Analysis completed!")
        print("🎉" * 35)
        
        print(f"\nResults:")
        print(f"  - Grid cells processed: {len(result)}")
        print(f"  - Priority score range: {result['priority_score'].min():.2f} - {result['priority_score'].max():.2f}")
        print(f"  - High priority cells: {(result['priority_class'] == 'Very High').sum()}")
        
        # Show where outputs are
        from tree_priority_analysis.config import OUTPUT_DIR
        print(f"\n📁 Output files saved to: {OUTPUT_DIR}")
        
    except Exception as e:
        print("\n" + "❌" * 35)
        print(f"ERROR: {e}")
        print("❌" * 35)
        import traceback
        traceback.print_exc()
else:
    print("\nAnalysis cancelled. Run this script again when ready!")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)