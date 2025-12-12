# Quick Start Guide - Skiing Resort Analysis

## 🎯 What You Have

All analysis outputs are in: `output/skiing_resort/`

### ✅ Completed Requirements

1. **✓ Task 1: Snow Surface Prediction**
   - 3 interpolation methods (IDW, Kriging, Spline)
   - Validation with cross-validation metrics
   - **Best method identified: Kriging (R² = 0.770)**

2. **✓ Task 2: Best Location for Ski Resort**
   - Proper slope analysis (15-40°)
   - Proper shading (hillshade)
   - Proper orientation (north-facing, not toward sun)
   - Weighted overlay model

3. **✓ Interactive HTML Map** (`skiing_resort_analysis.html`)
   - Multiple base maps
   - Best locations marked
   - Suitable areas shown
   - Dam & ridges included

4. **✓ QML Style Files** (4 files for QGIS)
   - Ready to import
   - Optimized color schemes

## 🚀 How to Use in QGIS

### Step 1: Load Suitability Map
```
1. Open QGIS
2. Layer → Add Raster Layer
3. Select: output/skiing_resort/suitability_map.tif
```

### Step 2: Apply QML Style
```
1. Right-click the layer → Properties
2. Go to Symbology tab
3. Click "Style" button (bottom) → "Load Style"
4. Select: output/skiing_resort/suitability_style.qml
5. Click "OK"
```

The map will now show:
- 🟢 Green = Optimal locations (90-100)
- 🟡 Yellow = Good locations (70-90)
- 🟠 Orange = Moderate (50-70)
- 🔴 Red = Poor (0-50)

### Step 3: Load Other Layers

**Snow Depth (Kriging - Best Method)**:
- File: `snow_interpolated_kriging.tif`
- Style: `snow_depth_style.qml`

**Slope**:
- File: `slope_map.tif`
- Style: `slope_style.qml`

**Aspect/Orientation**:
- File: `aspect_map.tif`
- Style: `aspect_style.qml`

### Step 4: Load Vector Layers

**Best Locations** (Top 5 spots):
```
1. Layer → Add Vector Layer
2. Select: output/skiing_resort/best_locations.geojson
3. Style it with star symbols or pins
```

**Suitable Areas** (All regions ≥70 score):
```
1. Layer → Add Vector Layer
2. Select: output/skiing_resort/suitable_areas.shp
3. Color by 'mean_suita' field
```

## 🗺️ Interactive HTML Map

### Open the Map
Double-click: `output/skiing_resort/skiing_resort_analysis.html`

### Features
- 🗺️ **Base Maps**: Switch between OSM, Topographic, Satellite
- ⭐ **Best Locations**: Red star markers (ranked 1-5)
- 🎨 **Suitable Areas**: Color-coded polygons (green=best)
- 📏 **Measure Tool**: Click ruler icon to measure distances
- 🔍 **Zoom Controls**: Navigate the area
- 📊 **Legend**: Shows color coding and features
- 🔳 **Fullscreen**: Click expand button

### Reference Layers
- **Blue Line**: Dam location
- **Brown Line**: Ridge lines

## 📊 Understanding the Results

### Interpolation Validation (CSV)
File: `validation_results.csv`

```
Method      RMSE    MAE     R²      Best?
----------------------------------------
IDW         4.437   3.275   0.708   
Kriging     3.941   2.758   0.770   ✓ YES
Spline      4.290   2.956   0.727
```

**Interpretation**: Lower RMSE + Higher R² = Better
→ Use Kriging results for snow depth!

### Suitability Scores

**Score Range**: 0-100

| Score | Category | Interpretation |
|-------|----------|----------------|
| 90-100 | Optimal | Perfect conditions |
| 80-90 | Excellent | Very suitable |
| 70-80 | Good | Suitable with minor issues |
| 60-70 | Moderate | May need adjustments |
| <60 | Poor | Not recommended |

### Criteria Weights
The suitability score is calculated as:
```
Suitability = 40% × Slope Score 
            + 35% × Aspect Score
            + 15% × Hillshade Score
            + 10% × Snow Score
```

## 📈 Analysis Summary

### Coverage
- **Total Area Analyzed**: 948 × 752 cells (30m resolution)
- **Suitable Areas Found**: 2,749 regions
- **Total Suitable Area**: 123,240 cells (~111 km²)

### Top Results
- **Best Suitability Score**: 99.07/100
- **Best Interpolation**: Kriging (RMSE: 3.941)
- **Mean Slope**: 9.77° (mostly gentle terrain)

### Suitability Distribution
- High (≥80): 9.7% of area
- Moderate (60-80): 16.2% of area
- Low (<60): 74.1% of area

## 🎨 Color Schemes

### Suitability Map
- 🟢 Dark Green (100): Perfect location
- 🟢 Light Green (80-100): Excellent
- 🟡 Yellow (60-80): Good
- 🟠 Orange (40-60): Moderate
- 🔴 Red (0-40): Poor

### Snow Depth Map
- ⚪ White (0): No snow
- 🔵 Light Blue (0-7): Light snow
- 🔵 Blue (7-14): Moderate snow
- 🔵 Dark Blue (14-21): Heavy snow
- 🔵 Navy (21-28): Very heavy snow

### Slope Map
- 🟢 Green (<15°): Too flat
- 🟡 Yellow (15-20°): Marginal
- 🟢 Light Green (20-30°): Optimal
- 🟠 Orange (30-40°): Marginal steep
- 🔴 Red (>40°): Too steep

## 💡 Tips

### For Best Results in QGIS:
1. Load layers in this order:
   - Base: Suitability map
   - Add: Slope, Aspect, Snow
   - Top: Best locations, Suitable areas
   
2. Adjust layer transparency (30-70%) to see overlap

3. Use "Identify Features" tool to click and see exact values

### For Presentations:
1. Use the HTML map for interactive demos
2. Use the PNG files for static reports
3. Export QGIS layouts with QML styles applied

## 🔧 Re-run Analysis

If you need to adjust parameters:

1. Edit: `skiing_resort_analysis/config.py`
2. Change weights, thresholds, or ranges
3. Run: `python -m skiing_resort_analysis.main`
4. New outputs overwrite old ones

## ❓ Common Questions

**Q: Which snow map should I use?**
A: Use `snow_interpolated_kriging.tif` - it has the best validation scores.

**Q: What does "mean_suita" mean in suitable_areas.shp?**
A: Average suitability score for that polygon (truncated to 10 chars).

**Q: Can I change the suitability threshold?**
A: Yes! Edit `SUITABILITY_THRESHOLD` in `config.py` (default: 70).

**Q: Why are some areas not suitable?**
A: Usually because slope is too flat (<15°) or too steep (>40°).

**Q: How do I share results?**
A: Share the HTML map file - it's self-contained and works in any browser!

## 📞 Support

For issues or questions about the analysis, check:
- `README.md` - Full technical documentation
- `test_run.py` - Run tests to verify setup
- Output logs in terminal

---

**Ready to explore!** 🎿⛷️
