# -*- coding: utf-8 -*-
"""
Configuration for Skiing Resort Site Selection Analysis
"""
import os

# ═══════════════════════════════════════════════════════════════
# PROJECT PATHS
# ═══════════════════════════════════════════════════════════════
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'skiing_resort')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output', 'skiing_resort')

# ═══════════════════════════════════════════════════════════════
# INPUT DATA PATHS
# ═══════════════════════════════════════════════════════════════
INPUT_FILES = {
    'dem': os.path.join(DATA_DIR, 'arelev1.tif'),
    'snow_points': os.path.join(DATA_DIR, 'snowpoint.shp'),
    'dam_line': os.path.join(DATA_DIR, 'DamLine.shp'),
    'ridges': os.path.join(DATA_DIR, 'ridges.shp'),
    'contours': os.path.join(DATA_DIR, 'cont.shp'),
}

# ═══════════════════════════════════════════════════════════════
# OUTPUT PATHS
# ═══════════════════════════════════════════════════════════════
OUTPUT_FILES = {
    # Task 1: Interpolation outputs
    'snow_idw': os.path.join(OUTPUT_DIR, 'snow_interpolated_idw.tif'),
    'snow_kriging': os.path.join(OUTPUT_DIR, 'snow_interpolated_kriging.tif'),
    'snow_spline': os.path.join(OUTPUT_DIR, 'snow_interpolated_spline.tif'),
    'validation_csv': os.path.join(OUTPUT_DIR, 'validation_results.csv'),
    
    # Task 2: Terrain analysis outputs
    'slope': os.path.join(OUTPUT_DIR, 'slope_map.tif'),
    'aspect': os.path.join(OUTPUT_DIR, 'aspect_map.tif'),
    'hillshade': os.path.join(OUTPUT_DIR, 'hillshade_map.tif'),
    
    # Task 2: Suitability outputs
    'suitability': os.path.join(OUTPUT_DIR, 'suitability_map.tif'),
    'suitable_areas': os.path.join(OUTPUT_DIR, 'suitable_areas.shp'),
    'best_locations': os.path.join(OUTPUT_DIR, 'best_locations.geojson'),
    
    # Visualizations
    'interpolation_comparison': os.path.join(OUTPUT_DIR, 'interpolation_comparison.png'),
    'suitability_map_png': os.path.join(OUTPUT_DIR, 'suitability_map.png'),
    'top_locations_viz': os.path.join(OUTPUT_DIR, 'top_locations_analysis.png'),
    'location_details_viz': os.path.join(OUTPUT_DIR, 'location_details.png'),
    'interactive_map': os.path.join(OUTPUT_DIR, 'skiing_resort_analysis.html'),
    
    # QML Style Files for QGIS
    'qml_snow': os.path.join(OUTPUT_DIR, 'snow_depth_style.qml'),
    'qml_slope': os.path.join(OUTPUT_DIR, 'slope_style.qml'),
    'qml_aspect': os.path.join(OUTPUT_DIR, 'aspect_style.qml'),
    'qml_suitability': os.path.join(OUTPUT_DIR, 'suitability_style.qml'),
}

# ═══════════════════════════════════════════════════════════════
# FIELD NAMES (Shapefile schema - uppercase, auto-detected)
# ═══════════════════════════════════════════════════════════════
SNOW_DEPTH_FIELD = 'SNOWDEPTH'  # Field name in snowpoint shapefile
STATION_ID_FIELD = 'STATION'     # Station ID field
CONTOUR_FIELD = 'CONTOUR'        # Contour elevation field

# ═══════════════════════════════════════════════════════════════
# INTERPOLATION PARAMETERS
# ═══════════════════════════════════════════════════════════════
INTERPOLATION_PARAMS = {
    'idw': {
        'power': 2.0,           # IDW power parameter
        'radius': 5000,         # Search radius in meters
    },
    'kriging': {
        'variogram_model': 'spherical',  # 'linear', 'power', 'gaussian', 'spherical'
        'nlags': 12,
    },
    'spline': {
        'smoothing': 0.5,       # Spline smoothing factor
    }
}

# ═══════════════════════════════════════════════════════════════
# SKI RESORT SUITABILITY CRITERIA
# ═══════════════════════════════════════════════════════════════

# Slope criteria (in degrees)
# Stricter criteria for quality ski resort terrain
SLOPE_CRITERIA = {
    'min_slope': 15,        # Minimum slope for skiing
    'optimal_min': 20,      # Optimal range start
    'optimal_max': 30,      # Optimal range end
    'max_slope': 40,        # Maximum safe slope
}

# Aspect criteria (in degrees, 0 = North)
# North-facing slopes (0-45, 315-360) are preferred (less sun)
ASPECT_CRITERIA = {
    'preferred_min': 315,   # Northwest
    'preferred_max': 45,    # Northeast
    'acceptable_min': 270,  # West
    'acceptable_max': 90,   # East
}

# Hillshade criteria (0-255)
HILLSHADE_CRITERIA = {
    'min_shade': 100,       # Minimum shading
    'optimal_shade': 150,   # Optimal shading
}

# Snow depth criteria (soft constraint in cm)
# Based on actual data range: 0-28 cm
# Note: Snow is now a SOFT weighted factor, not a hard exclusion
SNOW_DEPTH_CONSTRAINT = {
    'min_snow': 5.0,        # Minimal exclusion threshold (cm) - very low to avoid temporal bias
    'optimal_snow': 20.0,   # Optimal snow depth (cm)
    'poor_snow': 10.0,      # Poor snow threshold (cm)
}

# Weights for suitability calculation (must sum to 1.0)
# Adjusted to reduce slope dominance and include snow as soft factor
# This reduces bias from temporal snow variability and steep terrain over-selection
SUITABILITY_WEIGHTS = {
    'slope': 0.45,         # 45% - Important but not dominating
    'aspect': 0.30,        # 30% - Sun exposure critical for snow retention
    'hillshade': 0.15,     # 15% - Terrain shading
    'snow': 0.10,          # 10% - Snow depth as soft factor (temporal awareness)
}

assert abs(sum(SUITABILITY_WEIGHTS.values()) - 1.0) < 0.001, "Weights must sum to 1.0"

# Minimum suitability score threshold (0-100)
SUITABILITY_THRESHOLD = 70

# ═══════════════════════════════════════════════════════════════
# COORDINATE REFERENCE SYSTEM
# ═══════════════════════════════════════════════════════════════
TARGET_CRS = "EPSG:26710"  # NAD27 / UTM zone 10N

# ═══════════════════════════════════════════════════════════════
# ANALYSIS OPTIONS
# ═══════════════════════════════════════════════════════════════
OPTIONS = {
    'verbose': True,
    'validation_method': 'loo',  # 'loo' (leave-one-out) or 'kfold'
    'k_folds': 5,                # For k-fold cross-validation
    'create_visualizations': True,
    'export_intermediate': True,  # Export intermediate results
}

# ═══════════════════════════════════════════════════════════════
# VISUALIZATION SETTINGS
# ═══════════════════════════════════════════════════════════════
COLORMAP_SNOW = 'Blues'
COLORMAP_SLOPE = 'YlOrRd'
COLORMAP_ASPECT = 'twilight'
COLORMAP_SUITABILITY = 'RdYlGn'