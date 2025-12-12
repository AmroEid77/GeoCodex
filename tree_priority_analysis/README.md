# Tree Cutting Priority Analysis

## 🎯 Overview

A GeoPandas-based spatial analysis tool for determining tree cutting priorities in Fire Creek. This module calculates priority scores based on five weighted factors: tree mortality, proximity to community features, egress routes, populated areas, and electric utilities.

---

## 🚀 Quick Start

### **Installation**

```bash
# Clone the repository
git clone https://github.com/AmroEid77/GeoCodex.git
cd GeoCodex/tree_priority_analysis

# Create conda environment
conda create -n tree_priority python=3.10 -y
conda activate tree_priority

# Install dependencies
pip install -r requirements.txt
# OR
conda install -c conda-forge geopandas pandas numpy matplotlib folium
```

### **Prepare Data**

Copy your shapefiles to `data/fire_creek/`:
```
data/fire_creek/
  ├── CuttingGrids.shp
  ├── SBNFMortalityt.shp
  ├── Communityfeatures.shp
  ├── EgressRoutes.shp
  ├── PopulatedAreast.shp
  ├── Transmission.shp
  ├── SubTransmission.shp
  └── DistCircuits.shp
```

### **Run Analysis**

```bash
# Run with test script (recommended for first time)
python test_run.py

# Or run directly
python -m tree_priority_analysis.main
```

---

## 📊 What It Does

### **The 5 Priority Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| **Mortality** | 30% | Tree mortality/damage level |
| **Community** | 25% | Proximity to buildings, parks, schools |
| **Egress Routes** | 20% | Distance to evacuation routes |
| **Population** | 15% | Population density |
| **Utilities** | 10% | Proximity to power lines |

### **Output:**

- **Shapefile**: `output/tree_priority_result.shp` (load in QGIS)
- **CSV**: `output/tree_priority_result.csv` (analysis in Excel)
- **Interactive Map**: `output/tree_priority_map.html` (open in browser)
- **Static Map**: `output/tree_priority_map.png` (for reports)
- **Factor Comparison**: `output/factor_comparison.png`

---

## 🔧 Configuration

### **Custom Weights**

Edit `tree_priority_analysis/config.py`:

```python
WEIGHTS = {
    'mortality': 0.35,      # Increase mortality importance
    'community': 0.25,
    'egress': 0.20,
    'population': 0.15,
    'utility': 0.05,        # Decrease utility importance
}
```

### **Distance Thresholds**

```python
DISTANCE_THRESHOLDS = {
    'community_max': 1500,      # Increase from 1km to 1.5km
    'egress_max': 2000,
    'utility_max': 500,
}
```

### **Field Name Mapping**

If your shapefiles have different field names:

```python
MORTALITY_FIELDS = {
    'mortality_percent': 'YOUR_MORTALITY_FIELD',
    'tree_count': 'YOUR_TREE_COUNT_FIELD',
}

POPULATION_FIELDS = {
    'population': 'YOUR_POP_FIELD',
}
```

---

## 🎨 Results Interpretation

### **Priority Classes:**

- 🔴 **Very High (8-10)**: Immediate action required
- 🟠 **High (6-8)**: Priority within 1 month
- 🟡 **Medium (4-6)**: Address within 3 months
- 🟢 **Low (2-4)**: Monitor, address within 6 months
- 🟢 **Very Low (0-2)**: Routine maintenance

### **Example Output:**

```
📊 ANALYSIS RESULTS:
   • Total Grid Cells: 80
   • Average Priority Score: 5.43/10
   • Highest Priority Score: 9.86

🎯 PRIORITY DISTRIBUTION:
   • Very High Priority: 12 cells (15.0%)
   • High Priority: 18 cells (22.5%)
   • Medium Priority: 25 cells (31.3%)
   • Low Priority: 15 cells (18.8%)
   • Very Low Priority: 10 cells (12.5%)
```

---

## 🛠️ Troubleshooting

### **"Data files not found"**

**Solution:** Ensure all shapefiles are in `data/fire_creek/`:
```
data/fire_creek/
  ├── CuttingGrids.shp (and .dbf, .shx, .prj, etc.)
  ├── SBNFMortalityt.shp
  ├── Communityfeatures.shp
  ├── EgressRoutes.shp
  ├── PopulatedAreast.shp
  ├── Transmission.shp
  ├── SubTransmission.shp
  └── DistCircuits.shp
```

### **"Field not found"**

**Solution:** Check field names in your shapefiles and update `config.py`:
```bash
# View fields in a shapefile
ogrinfo -al -so CuttingGrids.shp
```

### **"Module not found: geopandas"**

**Solution:** Install dependencies:
```bash
conda activate tree_priority
conda install -c conda-forge geopandas
```

### **No trees matched to grid cells**

**Possible causes:**
1. Mortality shapefile is polygon-based, not point-based
2. Trees and grid are in different coordinate systems
3. Spatial join predicate needs adjustment

**Solution:** Change to intersection-based join in `mortality_factor.py`:
```python
joined = gpd.sjoin(
    source_data,
    grid[['grid_id', 'geometry']],
    how='inner',
    predicate='intersects'  # Changed from 'within'
)
```

---

## 🔮 Future Enhancements

- **LLM Integration**: Natural language parameter extraction via GeoCodex
- **Custom AOI**: Analysis for specific geographic areas
- **Real-Time Updates**: Recalculate based on new data
- **Web Interface**: Interactive dashboard for results exploration
- **Temporal Analysis**: Track priority changes over time

---

## 📚 API Reference

### **TreePriorityAnalysis**

Main class for running the analysis.

```python
from tree_priority_analysis.main import TreePriorityAnalysis

# Initialize
analysis = TreePriorityAnalysis(
    data_dir=None,          # Custom data directory
    weights=None,           # Custom factor weights
    verbose=True            # Enable logging
)

# Run analysis
result = analysis.run(
    export_results=True,          # Export shapefiles, CSV, maps
    create_visualizations=True    # Create HTML/PNG visualizations
)

# Access results
print(result['priority_score'].describe())
top_10 = result.nlargest(10, 'priority_score')
```

---

## 📖 Technical Details

### **Architecture**

```
TreePriorityAnalysis (main.py)
    ↓
├── DataLoader (data_loader.py)
│   └── Load & validate shapefiles
├── Factor Calculators (factors/)
│   ├── MortalityFactor
│   ├── CommunityFactor
│   ├── EgressFactor
│   ├── PopulationFactor
│   └── UtilityFactor
├── PriorityCalculator (priority_calculator.py)
│   └── Weighted sum & classification
└── Visualizer (visualizer.py)
    └── Export results & maps
```

### **Performance**

- **80 cells**: ~10-15 seconds
- **500 cells**: ~1-2 minutes
- **2000+ cells**: ~5-10 minutes

Bottleneck: Distance calculations (optimized with spatial indexing)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is part of the GeoCodex QGIS plugin.

---

## 👥 Credits

**Developed for:** Fire Creek Tree Cutting Priority Analysis  
**Part of:** [GeoCodex](https://github.com/AmroEid77/GeoCodex) - AI-Powered QGIS Plugin  
**Framework:** GeoPandas spatial analysis  
**Authors:** Amro Eid, Ahmad

---

## ❓ Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/AmroEid77/GeoCodex/issues)
- Check the [GeoCodex documentation](../README.md)
- Contact: amro.eidd@gmail.com
