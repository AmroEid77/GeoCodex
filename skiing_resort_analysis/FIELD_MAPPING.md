# Skiing Resort Analysis - PostGIS Field Mapping Reference

## Complete Schema Mapping

### Raster Tables (All have same structure)

#### Tables: aspect_map, dem, hillshade_map, hillshade_suitable, slope_map, slope_suitable
```sql
SELECT * FROM "public"."aspect_map" LIMIT 10
SELECT * FROM "public"."dem" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Used In Analysis |
|---------------|-----------|---------|------------------|
| `rid` | Integer | Raster tile ID | Auto (internal) |
| `rast` | Raster | Raster data block | Auto (rasterio reads this) |

**Note**: These are PostGIS raster tables. Python code reads them as GeoTIFF files, not directly from database.

#### Table: snow_surface_raster (Interpolation Output)
```sql
SELECT * FROM "public"."snow_surface_raster" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Used In Analysis |
|---------------|-----------|---------|------------------|
| `rast` | Raster | Interpolated snow surface | Output only |

### Vector Tables (Point/Line/Polygon Data)

#### Table 1: snowpoint (Snow Measurement Stations) ⚠️ CRITICAL
```sql
SELECT * FROM "public"."snowpoint" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Config Mapping |
|---------------|-----------|---------|----------------|
| `id` | Integer | Primary key | Auto (index) |
| `geom` | Point | Station location | Auto (geometry) |
| `station` | String | Station identifier | `STATION_ID_FIELD` ✓ |
| `snowdepth` | Float | **Snow depth (cm)** | `SNOW_DEPTH_FIELD` ✓ |

**Auto-Detection**: Code tries: `snowdepth` → `SNOWDEPTH` → `snow_depth` → `SNOW_DEPTH`

#### Table 2: cont (Contour Lines)
```sql
SELECT * FROM "public"."cont" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Config Mapping |
|---------------|-----------|---------|----------------|
| `id` | Integer | Primary key | Auto (index) |
| `geom` | LineString | Contour line | Auto (geometry) |
| `contour` | Float | Elevation value (m) | `CONTOUR_FIELD` ✓ |

#### Table 3: DamLine (Dam Reference Line)
```sql
SELECT * FROM "public"."DamLine" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Config Mapping |
|---------------|-----------|---------|----------------|
| `id` | Integer | Primary key | Auto (index) |
| `geom` | LineString | Dam centerline | Auto (geometry) |

**Note**: No attribute fields required - used for spatial reference only.

#### Table 4: ridges (Ridge Lines)
```sql
SELECT * FROM "public"."ridges" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Config Mapping |
|---------------|-----------|---------|----------------|
| `id` | Integer | Primary key | Auto (index) |
| `geom` | LineString | Ridge line | Auto (geometry) |
| `fnode_` | Integer | From node ID | Not used |
| `tnode_` | Integer | To node ID | Not used |
| `lpoly_` | Integer | Left polygon | Not used |
| `rpoly_` | Integer | Right polygon | Not used |
| `length` | Float | Ridge length | Not used |
| `ridges_` | Integer | Ridge ID | Not used |
| `ridges_id` | Integer | Ridge identifier | Not used |
| `rcov2_` | Integer | Coverage ID | Not used |
| `rcov2_id` | Integer | Coverage identifier | Not used |

**Note**: Legacy topology fields not used in current analysis - used for spatial reference only.

#### Table 5: interpolation_grid (Interpolation Grid Points)
```sql
SELECT * FROM "public"."interpolation_grid" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Config Mapping |
|---------------|-----------|---------|----------------|
| `gid` | Integer | Grid point ID | Auto (index) |
| `geom` | Point | Grid point location | Auto (geometry) |
| `x` | Float | X coordinate | Auto (extracted from geom) |
| `y` | Float | Y coordinate | Auto (extracted from geom) |

**Note**: Grid created during interpolation process for validation.

#### Table 6: snow_interpolated_idw (IDW Interpolation Result)
```sql
SELECT * FROM "public"."snow_interpolated_idw" LIMIT 10
```
| PostGIS Field | Data Type | Purpose | Config Mapping |
|---------------|-----------|---------|----------------|
| `gid` | Integer | Grid point ID | Auto (index) |
| `geom` | Point | Point location | Auto (geometry) |
| `snow_depth_idw` | Float | IDW interpolated snow depth | Output field |

**Note**: Similar tables exist for Kriging and Spline methods (not listed in schema but may exist).

### System Tables (PostGIS Metadata)

#### Table: raster_columns (PostGIS Catalog)
```sql
SELECT * FROM "public"."raster_columns" LIMIT 10
```
| PostGIS Field | Purpose |
|---------------|---------|
| `r_table_catalog` | Database name |
| `r_table_schema` | Schema name (public) |
| `r_table_name` | Raster table name |
| `r_raster_column` | Raster column name (usually 'rast') |
| `srid` | Spatial reference ID |
| `scale_x` | Pixel size X |
| `scale_y` | Pixel size Y |
| `blocksize_x` | Tile width |
| `blocksize_y` | Tile height |
| `same_alignment` | Alignment flag |
| `regular_blocking` | Blocking flag |
| `num_bands` | Number of bands |
| `pixel_types` | Pixel data types |
| `nodata_values` | NoData values |
| `out_db` | Out-of-database storage |
| `extent` | Spatial extent |
| `spatial_index` | Spatial index status |

**Note**: System catalog - not directly accessed by analysis code.

## Critical Fields for Analysis

### ✓ Required Fields (Must be present)
1. **Snow Depth**: `snowdepth` (snowpoint table) - Used for all 3 interpolation methods
2. **Station ID**: `station` (snowpoint table) - Used for validation and reporting

### ⚠️ Optional Fields (Enhance visualization if present)
1. **Contour Elevation**: `contour` (cont table) - Used in interactive map
2. **Grid Coordinates**: `x`, `y` (interpolation_grid) - Auto-generated during analysis

## Field Name Detection Logic

The code uses **case-insensitive auto-detection** with fallback options:

### Snow Depth Field Detection (Priority Order):
1. `snowdepth` (PostGIS schema - lowercase) ✓
2. `SNOWDEPTH` (shapefile - uppercase)
3. `snow_depth` (alternative)
4. `SNOW_DEPTH` (alternative)

### Station ID Field Detection:
1. `station` (PostGIS schema)
2. `STATION` (shapefile)
3. First string column if not found

**Auto-Rename**: If a different case variant is found, the code automatically renames it to the expected field name (`snowdepth`) for consistent processing.

## Data Flow: PostGIS → Python

### Input Process:
1. **PostGIS Export** (if needed):
   ```sql
   -- Export snow points to shapefile
   pgsql2shp -f snowpoint.shp -u username -P password dbname "SELECT * FROM snowpoint"
   ```

2. **Python Reading**:
   ```python
   gdf = gpd.read_file('snowpoint.shp')  # Reads as GeoDataFrame
   # Auto-detects 'snowdepth' field
   # Renames to SNOW_DEPTH_FIELD if needed
   ```

### Output Process:
1. **Python Writing**:
   ```python
   # Rasters saved as GeoTIFF
   rasterio.write('snow_interpolated_idw.tif', data)
   
   # Vectors saved as GeoJSON/Shapefile
   gdf.to_file('suitable_areas.shp')
   ```

2. **PostGIS Import** (if needed):
   ```sql
   -- Import raster to PostGIS
   raster2pgsql -s 26710 -I -C -M snow_interpolated_idw.tif public.snow_surface_raster | psql -d dbname
   
   -- Import vector to PostGIS
   shp2pgsql -s 26710 -I suitable_areas.shp public.suitable_areas | psql -d dbname
   ```

## Configuration File Reference

Current settings in `config.py`:

```python
# Field names (matches PostGIS lowercase schema)
SNOW_DEPTH_FIELD = 'snowdepth'  # Snow measurement field
STATION_ID_FIELD = 'station'     # Station identifier
CONTOUR_FIELD = 'contour'        # Contour elevation

# Input files (shapefiles exported from PostGIS)
INPUT_FILES = {
    'dem': 'arelev1.tif',
    'snow_points': 'snowpoint.shp',
    'dam_line': 'DamLine.shp',
    'ridges': 'ridges.shp',
    'contours': 'cont.shp',
}
```

## Validation Command

Run this before the main analysis to verify all field mappings:

```bash
cd skiing_resort_analysis
python check_fields.py
```

Expected output:
```
======================================================================
LAYER: Snow Measurement Points
======================================================================
File: ../data/skiing_resort/snowpoint.shp

Actual fields in shapefile:
  - id
  - station
  - snowdepth

Expected fields:
  ✓ Snow Depth: 'snowdepth' FOUND
  ✓ Station ID: 'station' FOUND

======================================================================
VALIDATION SUMMARY
======================================================================
✓ snow_points: PASS
✓ contours: PASS
✓ dam_line: PASS
✓ ridges: PASS

Result: 4/4 layers passed validation

✓ All field names are correct!
You can safely run the main analysis.
```

## Common Issues & Solutions

### Issue 1: "Field 'SNOWDEPTH' not found"
**Cause**: PostGIS exports lowercase field names, but code expected uppercase.

**Solution**: ✅ FIXED - Code now auto-detects case variants and renames.

### Issue 2: "No snow depth values found"
**Cause**: Field exists but contains NULL values.

**Solution**: Check data quality:
```sql
SELECT COUNT(*) FROM snowpoint WHERE snowdepth IS NULL;
```

### Issue 3: CRS mismatch warnings
**Cause**: PostGIS table has different SRID than expected.

**Solution**: Code auto-transforms to EPSG:26710 (NAD27 UTM 10N).

## Schema Update History

| Date | Change | Reason |
|------|--------|--------|
| 2024-12-19 | Changed `SNOWDEPTH` → `snowdepth` | Match PostGIS lowercase schema |
| 2024-12-19 | Added auto-detection logic | Support both shapefile and PostGIS exports |
| 2024-12-19 | Added `CONTOUR_FIELD` config | Support contour visualization |

## Notes

- **Raster Tables**: Python code reads rasters as GeoTIFF files, not directly from PostGIS raster tables
- **Case Sensitivity**: PostGIS field names are lowercase; shapefiles often uppercase
- **Auto-Detection**: Code handles both cases automatically
- **Field Renaming**: Internal normalization ensures consistent field names during processing
- **Validation**: Always run `check_fields.py` before main analysis
