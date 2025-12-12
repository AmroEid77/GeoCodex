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

## 🏗️ System Architecture

### Entity-Relationship Diagram

```mermaid
erDiagram
    DEM ||--o{ SNOW_POINTS : "spatial_reference"
    DEM ||--|| SLOPE : derives
    DEM ||--|| ASPECT : derives
    DEM ||--|| HILLSHADE : derives
    SNOW_POINTS ||--o{ INTERPOLATION_MODEL : "trains"
    INTERPOLATION_MODEL ||--|| SNOW_SURFACE : "generates"
    SLOPE ||--|| SLOPE_SUITABILITY : "evaluates"
    ASPECT ||--|| ASPECT_SUITABILITY : "evaluates"
    HILLSHADE ||--|| SHADE_SUITABILITY : "evaluates"
    SNOW_SURFACE ||--|| SNOW_SUITABILITY : "evaluates"
    SLOPE_SUITABILITY ||--|| SUITABILITY_MAP : "combines_weighted"
    ASPECT_SUITABILITY ||--|| SUITABILITY_MAP : "combines_weighted"
    SHADE_SUITABILITY ||--|| SUITABILITY_MAP : "combines_weighted"
    SNOW_SUITABILITY ||--|| SUITABILITY_MAP : "combines_weighted"
    SUITABILITY_MAP ||--o{ SUITABLE_AREAS : "extracts_threshold"
    SUITABLE_AREAS ||--o{ BEST_LOCATIONS : "identifies_maxima"
    SUITABILITY_MAP ||--|| QML_STYLES : "visualizes"
    SUITABLE_AREAS ||--|| HTML_MAP : "displays"
    BEST_LOCATIONS ||--|| HTML_MAP : "displays"

    DEM {
        int rows PK "948"
        int cols PK "752"
        float resolution "30m"
        string crs "EPSG_26710"
        float nodata "-32768"
        float elevation_values "array"
    }

    SNOW_POINTS {
        int point_id PK
        float x_coord "UTM_easting"
        float y_coord "UTM_northing"
        float snow_depth "measured_cm"
        string crs "EPSG_26710"
    }

    INTERPOLATION_MODEL {
        string method PK "IDW_Kriging_Spline"
        dict parameters "power_variogram_smooth"
        float rmse "validation_metric"
        float mae "validation_metric"
        float r_squared "validation_metric"
    }

    SNOW_SURFACE {
        string method FK
        array values "interpolated_depths"
        float min_value "cm"
        float max_value "cm"
    }

    SLOPE {
        array values "degrees"
        float min_slope "0"
        float max_slope "65"
        string calculation "numpy_gradient"
    }

    ASPECT {
        array values "azimuth_0_360"
        string calculation "arctan2"
        string reference "north_0_clockwise"
    }

    HILLSHADE {
        array values "0_255"
        float azimuth "315"
        float altitude "45"
        string calculation "terrain_shading"
    }

    SLOPE_SUITABILITY {
        array scores "0_100"
        float weight "0.40"
        float min_threshold "15_degrees"
        float max_threshold "40_degrees"
        float optimal_min "20_degrees"
        float optimal_max "30_degrees"
    }

    ASPECT_SUITABILITY {
        array scores "0_100"
        float weight "0.35"
        string preference "north_facing"
        string avoided "south_facing"
    }

    SHADE_SUITABILITY {
        array scores "0_100"
        float weight "0.15"
        string preference "moderate_shading"
    }

    SNOW_SUITABILITY {
        array scores "0_100"
        float weight "0.10"
        string preference "deeper_snow"
    }

    SUITABILITY_MAP {
        array scores "0_100"
        float min_score "23.33"
        float max_score "99.07"
        int total_cells "710976"
        string formula "weighted_overlay"
    }

    SUITABLE_AREAS {
        int region_id PK
        float suitability_score "70_100"
        float area_m2 "calculated"
        geometry polygon "multipolygon"
        int total_regions "2749"
    }

    BEST_LOCATIONS {
        int rank PK "1_5"
        float x_coord "UTM_easting"
        float y_coord "UTM_northing"
        float suitability_score "90_99"
        string type "local_maxima"
    }

    QML_STYLES {
        string layer_name PK
        string color_ramp "gradient"
        float min_value "range_start"
        float max_value "range_end"
        string format "QGIS_XML"
    }

    HTML_MAP {
        string format "Folium_Leaflet"
        array base_layers "OSM_Topo_Satellite"
        array overlays "markers_polygons_lines"
        bool interactive "true"
    }
```

### Process Flow Diagram

```mermaid
flowchart TD
    Start([Start Analysis]) --> Init[Initialize Configuration]
    Init --> LoadData{Load Input Data}
    
    LoadData --> DEM[Load DEM Raster<br/>arelev1.tif<br/>948x752, 30m]
    LoadData --> Snow[Load Snow Points<br/>snowpoint.shp<br/>271 stations]
    LoadData --> Dam[Load Dam Line<br/>DamLine.shp]
    LoadData --> Ridge[Load Ridges<br/>ridges.shp]
    
    DEM --> Validate{Validate CRS<br/>& Spatial Overlap}
    Snow --> Validate
    Dam --> Validate
    Ridge --> Validate
    
    Validate -->|Invalid| Error1[Report Error<br/>& Exit]
    Validate -->|Valid| Task1[TASK 1:<br/>Snow Interpolation]
    
    Task1 --> IDW[IDW Interpolation<br/>Power=2.0]
    Task1 --> Kriging[Kriging Interpolation<br/>Spherical Variogram]
    Task1 --> Spline[Spline Interpolation<br/>Thin Plate RBF]
    
    IDW --> CV1[Cross-Validation<br/>Leave-One-Out<br/>271 iterations]
    Kriging --> CV2[Cross-Validation<br/>Leave-One-Out<br/>271 iterations]
    Spline --> CV3[Cross-Validation<br/>Leave-One-Out<br/>271 iterations]
    
    CV1 --> Metrics1[Calculate Metrics<br/>RMSE: 4.437<br/>MAE: 3.275<br/>R²: 0.708]
    CV2 --> Metrics2[Calculate Metrics<br/>RMSE: 3.941<br/>MAE: 2.758<br/>R²: 0.770]
    CV3 --> Metrics3[Calculate Metrics<br/>RMSE: 4.290<br/>MAE: 2.956<br/>R²: 0.727]
    
    Metrics1 --> Compare{Compare<br/>Methods}
    Metrics2 --> Compare
    Metrics3 --> Compare
    
    Compare --> Best[Select Best Method<br/>KRIGING - Lowest RMSE]
    Best --> SaveSnow[Save Snow Surfaces<br/>3 GeoTIFF files]
    SaveSnow --> SaveMetrics[Save Validation CSV<br/>& Comparison PNG]
    
    SaveMetrics --> Task2[TASK 2:<br/>Suitability Analysis]
    
    Task2 --> CalcSlope[Calculate Slope<br/>numpy.gradient<br/>Range: 0-65°]
    Task2 --> CalcAspect[Calculate Aspect<br/>arctan2 dy/dx<br/>Range: 0-360°]
    Task2 --> CalcShade[Calculate Hillshade<br/>Azimuth: 315°<br/>Altitude: 45°]
    
    CalcSlope --> ScoreSlope[Score Slope Suitability<br/>Optimal: 20-30°<br/>Range: 15-40°<br/>Weight: 40%]
    CalcAspect --> ScoreAspect[Score Aspect Suitability<br/>Prefer: North-facing<br/>Avoid: South-facing<br/>Weight: 35%]
    CalcShade --> ScoreShade[Score Shade Suitability<br/>Prefer: Moderate<br/>Weight: 15%]
    Best --> ScoreSnow[Score Snow Suitability<br/>Prefer: Deeper snow<br/>Weight: 10%]
    
    ScoreSlope --> Overlay[Weighted Overlay<br/>Suitability = 0.40×Slope +<br/>0.35×Aspect + 0.15×Shade +<br/>0.10×Snow]
    ScoreAspect --> Overlay
    ScoreShade --> Overlay
    ScoreSnow --> Overlay
    
    Overlay --> Extract[Extract Suitable Areas<br/>Threshold ≥ 70<br/>Vectorize Regions]
    Extract --> Count[Count Regions<br/>Total: 2,749]
    
    Count --> FindBest[Identify Best Locations<br/>Local Maxima<br/>Top 5 Sites]
    
    FindBest --> SaveTask2[Save Suitability Outputs<br/>4 Rasters + 2 Vectors]
    SaveTask2 --> SaveViz[Save Visualization<br/>Multi-panel PNG]
    
    SaveViz --> GenQML[Generate QML Styles<br/>4 Style Files]
    GenQML --> QMLSnow[snow_depth_style.qml<br/>Blue-White Gradient]
    GenQML --> QMLSlope[slope_style.qml<br/>Green-Yellow-Red]
    GenQML --> QMLAspect[aspect_style.qml<br/>Directional Colors]
    GenQML --> QMLSuit[suitability_style.qml<br/>Red-Green Gradient]
    
    QMLSnow --> GenMap[Generate HTML Map]
    QMLSlope --> GenMap
    QMLAspect --> GenMap
    QMLSuit --> GenMap
    
    GenMap --> AddBase[Add Base Layers<br/>OSM, Topo, Satellite]
    AddBase --> AddMarkers[Add Best Location Markers<br/>Red Stars with Popups]
    AddMarkers --> AddAreas[Add Suitable Area Polygons<br/>Color-coded by Score]
    AddAreas --> AddRef[Add Reference Layers<br/>Dam Line, Ridges]
    AddRef --> AddControls[Add Interactive Controls<br/>Layer Toggle, Measure, Fullscreen]
    
    AddControls --> SaveMap[Save HTML Map<br/>skiing_resort_analysis.html<br/>471 KB]
    
    SaveMap --> Summary[Generate Summary Report<br/>17 Output Files]
    Summary --> End([Analysis Complete])
    
    style Task1 fill:#e1f5ff
    style Task2 fill:#fff4e1
    style Best fill:#d4edda
    style Compare fill:#fff3cd
    style Validate fill:#fff3cd
    style Error1 fill:#f8d7da
    style End fill:#d4edda
```

### Class Hierarchy Diagram

```mermaid
classDiagram
    class BaseInterpolator {
        <<abstract>>
        +fit(x, y, values)
        +predict(x, y)
        +interpolate_to_grid(transform, shape)
        +cross_validate(x, y, values)*
        -_fit_model()*
        -_predict_value()*
    }

    class IDWInterpolator {
        -power: float
        -tree: cKDTree
        +_fit_model()
        +_predict_value()
    }

    class KrigingInterpolator {
        -variogram_model: str
        -ok_model: OrdinaryKriging
        +_fit_model()
        +_predict_value()
    }

    class SplineInterpolator {
        -smooth: float
        -rbf_model: RBFInterpolator
        +_fit_model()
        +_predict_value()
    }

    class SlopeAnalyzer {
        -dem: ndarray
        -transform: Affine
        -resolution: float
        +calculate_slope()
        +score_slope_suitability()
        -_normalize_slope()
    }

    class AspectAnalyzer {
        -dem: ndarray
        -transform: Affine
        +calculate_aspect()
        +score_aspect_suitability()
        -_aspect_to_radians()
    }

    class ShadingAnalyzer {
        -dem: ndarray
        -azimuth: float
        -altitude: float
        +calculate_hillshade()
        +score_shading_suitability()
    }

    class SuitabilityModel {
        -slope_score: ndarray
        -aspect_score: ndarray
        -shade_score: ndarray
        -snow_score: ndarray
        -weights: dict
        +calculate_suitability()
        +extract_suitable_areas()
        +identify_best_locations()
        -_weighted_overlay()
        -_vectorize_regions()
    }

    class DataLoader {
        +load_dem()
        +load_snow_points()
        +validate_spatial_overlap()
        +load_all()
    }

    class RasterUtils {
        +normalize_array()
        +save_geotiff()
        +read_geotiff()
        +apply_mask()
    }

    class ValidationMetrics {
        +calculate_rmse()
        +calculate_mae()
        +calculate_r2()
        +compare_methods()
    }

    class QMLGenerator {
        +create_qml_raster_style()
        +create_snow_depth_qml()
        +create_slope_qml()
        +create_aspect_qml()
        +create_suitability_qml()
    }

    class MapGenerator {
        +create_interactive_map()
        -_add_base_layers()
        -_add_best_locations()
        -_add_suitable_areas()
        -_add_reference_layers()
    }

    class SkiingResortAnalysis {
        -config: Config
        -data_loader: DataLoader
        +run_task1()
        +run_task2()
        +generate_outputs()
    }

    BaseInterpolator <|-- IDWInterpolator
    BaseInterpolator <|-- KrigingInterpolator
    BaseInterpolator <|-- SplineInterpolator
    
    SkiingResortAnalysis --> DataLoader
    SkiingResortAnalysis --> IDWInterpolator
    SkiingResortAnalysis --> KrigingInterpolator
    SkiingResortAnalysis --> SplineInterpolator
    SkiingResortAnalysis --> SlopeAnalyzer
    SkiingResortAnalysis --> AspectAnalyzer
    SkiingResortAnalysis --> ShadingAnalyzer
    SkiingResortAnalysis --> SuitabilityModel
    SkiingResortAnalysis --> QMLGenerator
    SkiingResortAnalysis --> MapGenerator
    
    SlopeAnalyzer --> RasterUtils
    AspectAnalyzer --> RasterUtils
    ShadingAnalyzer --> RasterUtils
    SuitabilityModel --> RasterUtils
    
    BaseInterpolator --> ValidationMetrics
```

### Data Processing Pipeline

```mermaid
graph LR
    subgraph Input["Input Data Layer"]
        A1[DEM Raster<br/>948x752x30m]
        A2[Snow Points<br/>271 stations]
        A3[Dam Line<br/>Vector]
        A4[Ridges<br/>Vector]
    end

    subgraph Processing["Processing Layer"]
        B1[Data Validation<br/>CRS Check]
        B2[Interpolation<br/>3 Methods]
        B3[Terrain Analysis<br/>Slope/Aspect/Shade]
        B4[Suitability Scoring<br/>4 Factors]
        B5[Weighted Overlay<br/>40/35/15/10%]
        B6[Region Extraction<br/>Threshold ≥70]
    end

    subgraph Output["Output Layer"]
        C1[Snow Surfaces<br/>3 GeoTIFFs]
        C2[Validation Metrics<br/>CSV + PNG]
        C3[Terrain Maps<br/>3 GeoTIFFs]
        C4[Suitability Map<br/>GeoTIFF]
        C5[Suitable Areas<br/>Shapefile + GeoJSON]
        C6[QML Styles<br/>4 Files]
        C7[HTML Map<br/>Interactive]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    
    B1 --> B2
    B1 --> B3
    
    B2 --> B4
    B3 --> B4
    
    B4 --> B5
    B5 --> B6
    
    B2 --> C1
    B2 --> C2
    B3 --> C3
    B5 --> C4
    B6 --> C5
    B6 --> C6
    B6 --> C7

    style Input fill:#e3f2fd
    style Processing fill:#fff3e0
    style Output fill:#e8f5e9
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

## 📐 Algorithm Details

### 1. IDW (Inverse Distance Weighting)

```mermaid
graph TD
    A[Input: Points x,y,z] --> B[Build KD-Tree]
    B --> C[For each grid cell]
    C --> D[Find k nearest neighbors]
    D --> E[Calculate distances d_i]
    E --> F["Calculate weights: w_i = 1/d_i^p"]
    F --> G["Normalize weights: w_i / Σw_i"]
    G --> H["Interpolate: z = Σ(w_i × z_i)"]
    H --> I{More cells?}
    I -->|Yes| C
    I -->|No| J[Output Grid]
    
    style A fill:#e3f2fd
    style J fill:#e8f5e9
```

**Formula:**
$$
z(x,y) = \frac{\sum_{i=1}^{n} w_i \cdot z_i}{\sum_{i=1}^{n} w_i}
$$

where $w_i = \frac{1}{d_i^p}$ and $d_i = \sqrt{(x-x_i)^2 + (y-y_i)^2}$

**Parameters:**
- Power ($p$): 2.0 (inverse square distance)
- Neighbors: All points (weighted by distance)

### 2. Kriging (Ordinary Kriging)

```mermaid
graph TD
    A[Input: Points x,y,z] --> B[Calculate Experimental Variogram]
    B --> C[Fit Theoretical Model<br/>Spherical/Gaussian/Exponential]
    C --> D[For each grid cell]
    D --> E[Form Kriging System<br/>Matrix Equations]
    E --> F[Solve for Weights λ_i]
    F --> G["Interpolate: z = Σ(λ_i × z_i)"]
    G --> H[Calculate Variance σ²]
    H --> I{More cells?}
    I -->|Yes| D
    I -->|No| J[Output Grid + Variance]
    
    style A fill:#e3f2fd
    style J fill:#e8f5e9
```

**Variogram Model (Spherical):**
$$
\gamma(h) = \begin{cases}
C_0 + C \left[\frac{3h}{2a} - \frac{h^3}{2a^3}\right] & \text{if } h \leq a \\
C_0 + C & \text{if } h > a
\end{cases}
$$

where:
- $h$: lag distance
- $C_0$: nugget effect
- $C$: sill
- $a$: range

### 3. Spline (Thin Plate)

```mermaid
graph TD
    A[Input: Points x,y,z] --> B[Form RBF Matrix]
    B --> C["Calculate basis: φ(r) = r² log(r)"]
    C --> D[Solve Linear System<br/>Ax = b]
    D --> E[Get Coefficients w_i]
    E --> F[For each grid cell]
    F --> G["Sum: z = Σ(w_i × φ(||x-x_i||))"]
    G --> H{More cells?}
    H -->|Yes| F
    H -->|No| I[Output Grid]
    
    style A fill:#e3f2fd
    style I fill:#e8f5e9
```

**Radial Basis Function:**
$$
z(x,y) = \sum_{i=1}^{n} w_i \cdot \phi(\|r_i\|)
$$

where $\phi(r) = r^2 \log(r)$ (thin plate) and $r_i = \sqrt{(x-x_i)^2 + (y-y_i)^2}$

### 4. Cross-Validation (Leave-One-Out)

```mermaid
sequenceDiagram
    participant P as Points (n=271)
    participant M as Model
    participant V as Validator
    
    loop For each point i
        P->>M: Train with points except i
        M->>M: Fit interpolation model
        P->>M: Predict value at point i
        M->>V: Predicted value ẑ_i
        P->>V: Actual value z_i
        V->>V: Calculate error: e_i = z_i - ẑ_i
    end
    
    V->>V: RMSE = √(Σe_i² / n)
    V->>V: MAE = Σ|e_i| / n
    V->>V: R² = 1 - (Σe_i² / Σ(z_i - z̄)²)
```

**Validation Metrics:**
- **RMSE**: Root Mean Square Error
  $$RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(z_i - \hat{z}_i)^2}$$

- **MAE**: Mean Absolute Error
  $$MAE = \frac{1}{n}\sum_{i=1}^{n}|z_i - \hat{z}_i|$$

- **R²**: Coefficient of Determination
  $$R^2 = 1 - \frac{\sum_{i=1}^{n}(z_i - \hat{z}_i)^2}{\sum_{i=1}^{n}(z_i - \bar{z})^2}$$

### 5. Slope Calculation

```mermaid
graph LR
    A[DEM Grid] --> B[Calculate dz/dx<br/>Horizontal Gradient]
    A --> C[Calculate dz/dy<br/>Vertical Gradient]
    B --> D["Slope = arctan(√((dz/dx)² + (dz/dy)²))"]
    C --> D
    D --> E[Convert to Degrees]
    E --> F[Slope Map 0-65°]
    
    style A fill:#e3f2fd
    style F fill:#e8f5e9
```

**Formula:**
$$
\text{slope} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right) \times \frac{180}{\pi}
$$

### 6. Aspect Calculation

```mermaid
graph LR
    A[DEM Grid] --> B[Calculate dz/dx]
    A --> C[Calculate dz/dy]
    B --> D["Aspect = arctan2(-dz/dy, -dz/dx)"]
    C --> D
    D --> E[Convert to Azimuth<br/>0° = North, Clockwise]
    E --> F[Aspect Map 0-360°]
    
    style A fill:#e3f2fd
    style F fill:#e8f5e9
```

**Formula:**
$$
\text{aspect} = \arctan2\left(-\frac{\partial z}{\partial y}, -\frac{\partial z}{\partial x}\right) \times \frac{180}{\pi} \mod 360
$$

### 7. Hillshade Calculation

```mermaid
graph TD
    A[DEM + Slope + Aspect] --> B[Set Sun Position<br/>Azimuth=315° Altitude=45°]
    B --> C[Calculate Zenith<br/>90° - Altitude]
    C --> D["Hillshade = cos(Zenith)×cos(Slope)<br/>+ sin(Zenith)×sin(Slope)×cos(Azimuth-Aspect)"]
    D --> E[Scale to 0-255]
    E --> F[Hillshade Map]
    
    style A fill:#e3f2fd
    style F fill:#e8f5e9
```

**Formula:**
$$
H = 255 \times \left[\cos(Z) \cos(S) + \sin(Z) \sin(S) \cos(A_z - A)\right]
$$

where:
- $Z$: zenith angle (90° - altitude)
- $S$: slope angle
- $A_z$: sun azimuth
- $A$: terrain aspect

### 8. Suitability Scoring

```mermaid
graph TD
    subgraph Slope_Scoring["Slope Suitability (40%)"]
        S1[Slope Value] --> S2{Range Check}
        S2 -->|"< 15°"| S3[Score = 0]
        S2 -->|"15-20°"| S4["Linear: (s-15)/5 × 80"]
        S2 -->|"20-30°"| S5[Score = 100]
        S2 -->|"30-40°"| S6["Linear: (40-s)/10 × 80"]
        S2 -->|"> 40°"| S7[Score = 0]
    end
    
    subgraph Aspect_Scoring["Aspect Suitability (35%)"]
        A1[Aspect Value 0-360°] --> A2["Deviation from North"]
        A2 --> A3["Score = 100 × (1 - deviation/180)"]
    end
    
    subgraph Shade_Scoring["Hillshade Suitability (15%)"]
        H1[Hillshade 0-255] --> H2[Normalize to 0-1]
        H2 --> H3["Prefer moderate: 1 - |h - 0.5| × 2"]
        H3 --> H4[Score = value × 100]
    end
    
    subgraph Snow_Scoring["Snow Suitability (10%)"]
        N1[Snow Depth cm] --> N2[Normalize by Max]
        N2 --> N3[Score = normalized × 100]
    end
    
    S3 --> W[Weighted Sum]
    S4 --> W
    S5 --> W
    S6 --> W
    S7 --> W
    A3 --> W
    H4 --> W
    N3 --> W
    
    W --> Final["Suitability = 0.40×Slope +<br/>0.35×Aspect + 0.15×Shade + 0.10×Snow"]
    
    style Final fill:#e8f5e9
```

**Weighted Overlay Formula:**
$$
\text{Suitability} = w_s \cdot S_{\text{slope}} + w_a \cdot S_{\text{aspect}} + w_h \cdot S_{\text{shade}} + w_n \cdot S_{\text{snow}}
$$

where $w_s = 0.40$, $w_a = 0.35$, $w_h = 0.15$, $w_n = 0.10$

### 9. Region Extraction & Best Location

```mermaid
graph TD
    A[Suitability Map] --> B{Threshold ≥ 70}
    B -->|"< 70"| C[Exclude]
    B -->|"≥ 70"| D[Include in Mask]
    D --> E[Connected Components Analysis]
    E --> F[Label Regions<br/>2,749 polygons]
    F --> G[Calculate Region Stats<br/>Area, Mean Score, Max Score]
    G --> H[For each region]
    H --> I[Find Local Maxima<br/>Highest suitability points]
    I --> J[Rank by Score]
    J --> K[Select Top 5 Locations]
    K --> L[Export Best Locations]
    
    style A fill:#e3f2fd
    style L fill:#e8f5e9
```

## 🎨 Visualization Components

### QML Style Generation

```mermaid
graph LR
    A[Raster Data] --> B{Layer Type}
    B -->|Snow Depth| C[Blue-White Gradient<br/>0-60 cm]
    B -->|Slope| D[Green-Yellow-Red<br/>0-65°]
    B -->|Aspect| E[Directional HSV<br/>0-360°]
    B -->|Suitability| F[Red-Orange-Green<br/>0-100]
    
    C --> G[Generate XML QML]
    D --> G
    E --> G
    F --> G
    
    G --> H[QGIS Compatible<br/>Version 3.34+]
    
    style A fill:#e3f2fd
    style H fill:#e8f5e9
```

### Interactive Map Layers

```mermaid
graph TD
    A[Folium Map Object] --> B[Add Base Layers]
    B --> B1[OpenStreetMap]
    B --> B2[Stamen Terrain]
    B --> B3[Esri WorldImagery]
    
    B1 --> C[Add Data Overlays]
    B2 --> C
    B3 --> C
    
    C --> C1[Best Locations<br/>Red Star Markers]
    C --> C2[Suitable Areas<br/>Colored Polygons]
    C --> C3[Dam Line<br/>Blue Line]
    C --> C4[Ridges<br/>Brown Line]
    
    C1 --> D[Add Controls]
    C2 --> D
    C3 --> D
    C4 --> D
    
    D --> D1[Layer Control<br/>Toggle visibility]
    D --> D2[Measure Tool<br/>Distance/Area]
    D --> D3[Fullscreen<br/>Maximize view]
    D --> D4[Mouse Position<br/>Coordinates]
    
    D1 --> E[Export HTML<br/>Self-contained]
    D2 --> E
    D3 --> E
    D4 --> E
    
    style A fill:#e3f2fd
    style E fill:#e8f5e9
```

## 📊 Statistical Analysis

### Interpolation Performance Comparison

| Metric | IDW | Kriging | Spline | Best |
|--------|-----|---------|--------|------|
| **RMSE** | 4.437 | **3.941** ✓ | 4.290 | Kriging |
| **MAE** | 3.275 | **2.758** ✓ | 2.956 | Kriging |
| **R²** | 0.708 | **0.770** ✓ | 0.727 | Kriging |
| **Computation Time** | Fast | Moderate | Fast | - |
| **Smoothness** | Moderate | High | Very High | - |

**Interpretation:**
- **Kriging** provides the best fit (highest R², lowest errors)
- **IDW** is fastest but less accurate
- **Spline** over-smooths some variations

### Suitability Statistics

```
Total Cells: 710,976
Suitable Cells (≥70): 123,240 (17.3%)
Regions Identified: 2,749

Score Distribution:
  Mean: 52.67
  Median: 48.22
  Std Dev: 18.45
  Min: 23.33
  Max: 99.07

Percentiles:
  25th: 39.15
  50th: 48.22
  75th: 64.88
  90th: 76.34
  95th: 82.57
  99th: 91.23
```

### Factor Contribution Analysis

```mermaid
pie title Suitability Weight Distribution
    "Slope (Most Important)" : 40
    "Aspect (North-facing)" : 35
    "Hillshade (Shading)" : 15
    "Snow Depth" : 10
```

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
