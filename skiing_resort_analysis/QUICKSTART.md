# Skiing Resort Site Selection Analysis

Comprehensive spatial analysis for optimal ski resort location selection using Python and GIS techniques.

## 📋 Project Overview

This analysis addresses two main tasks:

### Task 1: Snow Depth Interpolation & Validation
Create continuous surface representing snow depth distribution using spatial interpolation methods:
- **IDW (Inverse Distance Weighting)**
- **Kriging (Ordinary Kriging)**
- **Spline (Radial Basis Function)**

Cross-validation with leave-one-out method to determine the best interpolation technique.

### Task 2: Ski Resort Suitability Analysis
Identify optimal locations for ski resort development based on:
- **Slope**: 15-40° (optimal: 20-30°)
- **Aspect/Orientation**: North-facing preferred (avoids direct sun exposure)
- **Hillshade/Shading**: Moderate shading optimal for snow preservation

## 📊 Input Data

| Dataset | Type | Description |
|---------|------|-------------|
| `arelev1.tif` | Raster | Digital Elevation Model (DEM) - 30m resolution |
| `snowpoint.shp` | Vector | Snow measurement stations (271 points) |
| `DamLine.shp` | Vector | Proposed dam location (reference) |
| `ridges.shp` | Vector | Ridge lines (reference) |

**Coordinate System**: NAD27 UTM Zone 10N (EPSG:26710)

## 🚀 Installation & Setup

### 1. Create Conda Environment
```bash
conda create -n skiing-resort python=3.10
conda activate skiing-resort
```

### 2. Install Dependencies
```bash
cd skiing_resort_analysis
pip install -r requirements.txt
```

**Required Packages**:
- geopandas >= 0.14.0
- rasterio >= 1.3.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- scikit-learn >= 1.3.0
- pykrige >= 1.7.0
- matplotlib >= 3.7.0
- pandas >= 2.0.0
- folium >= 0.14.0
- branca >= 0.6.0
- pillow >= 10.0.0

## 📁 Project Structure

```
skiing_resort_analysis/
├── __init__.py
├── config.py                   # Configuration and parameters
├── data_loader.py              # Data loading and validation
├── main.py                     # Main orchestrator
├── requirements.txt            # Python dependencies
├── test_run.py                 # Test suite
├── README.md                   # This file
├── interpolation/
│   ├── base_interpolator.py   # Abstract base class
│   ├── idw_interpolator.py    # IDW implementation
│   ├── kriging_interpolator.py # Kriging implementation
│   └── spline_interpolator.py  # Spline implementation
├── site_selection/
│   ├── slope_analyzer.py       # Slope analysis
│   ├── aspect_analyzer.py      # Aspect/orientation analysis
│   ├── shading_analyzer.py     # Hillshade analysis
│   └── suitability_model.py    # Weighted overlay model
└── utils/
    ├── raster_utils.py         # Raster operations
    ├── validation_metrics.py   # Cross-validation metrics
    ├── qml_generator.py        # QGIS style files
    └── map_generator.py        # Interactive HTML maps
```

## 🎯 Usage

### Run Full Analysis
```bash
python -m skiing_resort_analysis.main
```

### Run Tests
```bash
python -m skiing_resort_analysis.test_run
```

## 📤 Outputs

All outputs are saved to `output/skiing_resort/`

### Task 1: Interpolation Results
| File | Description |
|------|-------------|
| `snow_interpolated_idw.tif` | IDW interpolation result |
| `snow_interpolated_kriging.tif` | Kriging interpolation (BEST METHOD ✓) |
| `snow_interpolated_spline.tif` | Spline interpolation result |
| `validation_results.csv` | Cross-validation metrics comparison |
| `interpolation_comparison.png` | Visual comparison plot |

**Validation Results**:
```
Method     RMSE    MAE     R²
-------------------------------
IDW        4.437   3.275   0.708
Kriging    3.941   2.758   0.770  ← BEST
Spline     4.290   2.956   0.727
```

### Task 2: Suitability Analysis
| File | Description |
|------|-------------|
| `slope_map.tif` | Terrain slope (0-65°) |
| `aspect_map.tif` | Terrain orientation (0-360°) |
| `hillshade_map.tif` | Shading analysis (0-255) |
| `suitability_map.tif` | Overall suitability score (0-100) |
| `suitable_areas.shp` | Suitable regions (threshold ≥70) |
| `best_locations.geojson` | Top 5 optimal locations |
| `suitability_map.png` | Multi-panel visualization |

### QGIS Style Files (.qml)
Ready-to-use QGIS layer styles:
- `snow_depth_style.qml` - Blue to white gradient
- `slope_style.qml` - Green (good) to red (steep) 
- `aspect_style.qml` - Directional colors (blue=north)
- `suitability_style.qml` - Red (poor) to green (optimal)

**How to use in QGIS**:
1. Load raster layer (e.g., `suitability_map.tif`)
2. Right-click → Properties → Symbology
3. Click "Style" → "Load Style"
4. Select corresponding `.qml` file

### Interactive HTML Map
`skiing_resort_analysis.html` - Web-based interactive map featuring:
- ✨ Multiple base maps (OpenStreetMap, Topographic, Satellite)
- 📍 Best location markers (ranked by suitability)
- 🗺️ Suitable areas polygons (color-coded)
- 📏 Measurement tools
- 🔄 Dam line and ridges overlay
- 📊 Interactive legend

**Open in browser**: Double-click `skiing_resort_analysis.html`

## ⚙️ Configuration

Edit `config.py` to customize analysis parameters:

### Interpolation Settings
```python
IDW_POWER = 2.0                  # IDW distance decay
KRIGING_VARIOGRAM = 'spherical'  # Kriging model
SPLINE_SMOOTH = 0.0              # Spline smoothing
```

### Suitability Criteria
```python
# Slope ranges (degrees)
MIN_SLOPE = 15               # Minimum viable slope
OPTIMAL_SLOPE_MIN = 20       # Optimal range start
OPTIMAL_SLOPE_MAX = 30       # Optimal range end
MAX_SLOPE = 40               # Maximum viable slope

# Weights for overlay
WEIGHT_SLOPE = 0.40          # 40%
WEIGHT_ASPECT = 0.35         # 35%
WEIGHT_HILLSHADE = 0.15      # 15%
WEIGHT_SNOW = 0.10           # 10%
```

## 📈 Analysis Results Summary

### Key Findings
1. **Best Interpolation Method**: Kriging (R² = 0.770)
2. **Suitable Area**: 123,240 cells (~111 km² at 30m resolution)
3. **Number of Suitable Regions**: 2,749
4. **Top Suitability Score**: 99.07/100
5. **Mean Terrain Slope**: 9.77°

### Suitability Distribution
- **High Suitability (≥80)**: 65,106 cells (9.7%)
- **Moderate (60-80)**: 108,741 cells (16.2%)
- **Low (<60)**: 491,195 cells (74.1%)

## 🔧 Methodology

### Interpolation Workflow
1. Load snow point measurements
2. Fit interpolation models (IDW, Kriging, Spline)
3. Interpolate to DEM grid
4. Perform leave-one-out cross-validation
5. Calculate RMSE, MAE, R² metrics
6. Select best method based on lowest RMSE

### Suitability Workflow
1. Calculate slope from DEM using gradient
2. Calculate aspect using arctan2
3. Calculate hillshade using sun position (azimuth=315°, altitude=45°)
4. Score each factor (0-100 scale)
5. Apply weighted overlay: `Suitability = 0.40×Slope + 0.35×Aspect + 0.15×Hillshade + 0.10×Snow`
6. Extract regions with suitability ≥ 70
7. Identify local maxima as best locations

## 🧪 Testing

The project includes comprehensive tests:
```bash
python -m skiing_resort_analysis.test_run
```

**Test Coverage**:
- ✓ Data loading and validation
- ✓ Snow interpolation (all 3 methods)
- ✓ Suitability analysis pipeline
- ✓ Full end-to-end workflow

## 📝 Notes

- **DEM Nodata Value**: -32768 represents no data (masked in calculations)
- **Shapefile Field Limitations**: Field names truncated to 10 characters
- **Processing Time**: ~30 seconds for full analysis (271 cross-validation iterations)

## 🐛 Troubleshooting

### PROJ Database Error
If you see "PROJ: proj_create_from_database" error:
```python
# Already fixed in main.py and test_run.py
import os
import pyproj
os.environ['PROJ_LIB'] = pyproj.datadir.get_data_dir()
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

## 📚 References

- **Kriging**: Ordinary Kriging with spherical variogram model
- **IDW**: Inverse distance weighting with power=2
- **Slope Calculation**: Gradient-based using numpy
- **Aspect**: arctan2(dy/dx) converted to 0-360° azimuth

## 👥 Author

GeoCodex QGIS Plugin - Skiing Resort Analysis Module

## 📄 License

Part of the GeoCodex QGIS Plugin project.
