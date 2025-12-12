# -*- coding: utf-8 -*-
"""
Configuration for Tree Cutting Priority Analysis
Centralized settings for weights, thresholds, and paths
"""
import os

# ═══════════════════════════════════════════════════════════════
# PROJECT PATHS
# ═══════════════════════════════════════════════════════════════
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'fire_creek')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output', 'tree_cutting_priority_analysis')

# ═══════════════════════════════════════════════════════════════
# INPUT DATA PATHS
# ═══════════════════════════════════════════════════════════════
SHAPEFILES = {
    'grid': os.path.join(DATA_DIR, 'CuttingGrids.shp'),
    'mortality': os.path.join(DATA_DIR, 'SBNFMortalityt.shp'),
    'community': os.path.join(DATA_DIR, 'Communityfeatures.shp'),
    'egress': os.path.join(DATA_DIR, 'EgressRoutes.shp'),
    'population': os.path.join(DATA_DIR, 'PopulatedAreast.shp'),
    'transmission': os.path.join(DATA_DIR, 'Transmission.shp'),
    'sub_transmission': os.path.join(DATA_DIR, 'SubTransmission.shp'),
    'dist_circuits': os.path.join(DATA_DIR, 'DistCircuits.shp'),
    'substations': os.path.join(DATA_DIR, 'Substations.shp'),
    'pole_subs': os.path.join(DATA_DIR, 'PoleTopSubs.shp'),
    'boundary': os.path.join(DATA_DIR, 'TownBoundary.shp'),
}

# ═══════════════════════════════════════════════════════════════
# OUTPUT PATHS
# ═══════════════════════════════════════════════════════════════
OUTPUT_SHAPEFILE = os.path.join(OUTPUT_DIR, 'tree_priority_result.shp')
OUTPUT_CSV = os.path.join(OUTPUT_DIR, 'tree_priority_result.csv')
OUTPUT_HTML_MAP = os.path.join(OUTPUT_DIR, 'tree_priority_map.html')

# ═══════════════════════════════════════════════════════════════
# COORDINATE REFERENCE SYSTEM
# ═══════════════════════════════════════════════════════════════
# Target CRS for distance calculations (meters)
# Adjust based on your data's location
# For US data, use appropriate State Plane or UTM zone
TARGET_CRS = "EPSG:2163"  # US National Atlas Equal Area

# ═══════════════════════════════════════════════════════════════
# FACTOR WEIGHTS (must sum to 1.0)
# ═══════════════════════════════════════════════════════════════
WEIGHTS = {
    'mortality': 0.30,      # 30% - Tree mortality (highest priority)
    'community': 0.25,      # 25% - Proximity to community features
    'egress': 0.20,         # 20% - Proximity to egress routes
    'population': 0.15,     # 15% - Population density
    'utility': 0.10,        # 10% - Proximity to utilities
}

# Validate weights sum to 1.0
assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001, "Weights must sum to 1.0"

# ═══════════════════════════════════════════════════════════════
# SCORING PARAMETERS
# ═══════════════════════════════════════════════════════════════
SCORE_RANGE = (0, 10)  # Min and max score for each factor

# Distance thresholds (in meters, after CRS transformation)
DISTANCE_THRESHOLDS = {
    'community_max': 1000,      # 1km - beyond this, score = 0
    'egress_max': 2000,          # 2km
    'utility_max': 500,          # 500m - utilities are dangerous closer
}

# ═══════════════════════════════════════════════════════════════
# MORTALITY FIELD MAPPING
# ═══════════════════════════════════════════════════════════════
# Adjust these based on actual field names in your shapefile
MORTALITY_FIELDS = {
    'mortality_percent': 'MORTALITY',  # Field containing mortality %
    'tree_count': 'TREE_COUNT',        # Optional: number of trees
}

POPULATION_FIELDS = {
    'population': 'POPULATION',        # Field containing population count
    'density': 'POP_DENSITY',          # Optional: pre-calculated density
}

# ═══════════════════════════════════════════════════════════════
# PRIORITY CLASSIFICATION
# ═══════════════════════════════════════════════════════════════
PRIORITY_CLASSES = {
    'Very High': (8, 10),
    'High': (6, 8),
    'Medium': (4, 6),
    'Low': (2, 4),
    'Very Low': (0, 2),
}

# ═══════════════════════════════════════════════════════════════
# VISUALIZATION SETTINGS
# ═══════════════════════════════════════════════════════════════
COLOR_MAP = {
    'Very High': '#d73027',    # Red
    'High': '#fc8d59',         # Orange
    'Medium': '#fee08b',       # Yellow
    'Low': '#91cf60',          # Light green
    'Very Low': '#1a9850',     # Dark green
}

# ═══════════════════════════════════════════════════════════════
# ANALYSIS OPTIONS
# ═══════════════════════════════════════════════════════════════
OPTIONS = {
    'verbose': True,                    # Print progress messages
    'validate_geometries': True,        # Check for invalid geometries
    'use_spatial_index': True,          # Use spatial index for faster queries
    'combine_utilities': True,          # Merge all utility layers into one
    'normalize_scores': True,           # Normalize to 0-10 range
}