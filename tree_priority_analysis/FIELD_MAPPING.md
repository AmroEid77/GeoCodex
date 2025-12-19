# Fire Creek PostGIS Field Mapping Reference

## Complete Schema Mapping

### Table 1: CuttingGrids (Base Grid for Analysis)
```sql
SELECT * FROM "public"."CuttingGrids"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | Polygon geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `GRID` | Grid cell identifier | `GRID_FIELDS['grid_id']` |
| `SHAPE_Leng` | Perimeter | Not used |
| `SHAPE_Area` | Area | `GRID_FIELDS['area']` |

### Table 2: SBNFMortalityt (Tree Mortality Data)
```sql
SELECT * FROM "public"."SBNFMortalityt"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | Point/Polygon geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | `MORTALITY_FIELDS['tree_count']` (proxy) |
| `SHAPE_Leng` | Perimeter | Not used |
| `SHAPE_Area` | Area | Not used |
| `Tot_mortal` | **Total mortality %** | `MORTALITY_FIELDS['mortality_percent']` ✓ |

### Table 3: Communityfeatures (Buildings, Parks, Schools)
```sql
SELECT * FROM "public"."Communityfeatures"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | Point/Polygon geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `NAME` | Feature name | `COMMUNITY_FIELDS['name']` |
| `weight` | Optional weight | `COMMUNITY_FIELDS['weight']` |

### Table 4: EgressRoutes (Evacuation Routes)
```sql
SELECT * FROM "public"."EgressRoutes"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | LineString geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `weight` | Optional weight | `EGRESS_FIELDS['weight']` |
| `SHAPE_Leng` | Length | Not used |

### Table 5: PopulatedAreast (Population Zones)
```sql
SELECT * FROM "public"."PopulatedAreast"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | Polygon geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `PLACE_NAME` | Place name | Not used |
| `POP` | **Population count** | `POPULATION_FIELDS['population']` ✓ |
| `pop_per_sq` | **Pop per sq mile** | `POPULATION_FIELDS['density']` ✓ |
| `area_sqmi` | Area in sq miles | `POPULATION_FIELDS['area']` ✓ |
| `Shape_Leng` | Perimeter | Not used |
| `Shape_Area` | Area | Not used |

### Table 6: Transmission (High Voltage Lines)
```sql
SELECT * FROM "public"."Transmission"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | LineString geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `CIRCUIT_NO` | Circuit number | `UTILITY_FIELDS['transmission']['circuit']` |
| `NAME` | Line name | `UTILITY_FIELDS['transmission']['name']` |
| `KV` | Voltage (kilovolts) | `UTILITY_FIELDS['transmission']['voltage']` |
| `STATUS` | Operational status | Not used |
| `CENTER` | Center point | Not used |
| `CIRCUIT` | Circuit info | Not used |
| `MILES` | Length in miles | Not used |
| `weight` | Optional weight | `UTILITY_FIELDS['transmission']['weight']` |
| `value1` | Custom value | Not used |
| `value2` | Custom value | Not used |
| `SHAPE_Leng` | Length | Not used |

### Table 7: SubTransmission (Medium Voltage Lines)
```sql
SELECT * FROM "public"."SubTransmission"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | LineString geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `NAME` | Line name | `UTILITY_FIELDS['subtransmission']['name']` |
| `CA` | CA identifier | Not used |
| `Priority` | Priority level | `UTILITY_FIELDS['subtransmission']['priority']` |
| `SHAPE_Leng` | Length | Not used |

### Table 8: DistCircuits (Distribution Lines)
```sql
SELECT * FROM "public"."DistCircuits"
```
| PostGIS Field | Purpose | Config Mapping |
|---------------|---------|----------------|
| `id` | Primary key | Auto (index) |
| `geom` | LineString geometry | Auto (geometry column) |
| `OBJECTID` | Object ID | Not used |
| `SHAPE_Leng` | Length | Not used |

## Critical Fields for Analysis

### ✓ Required Fields (Must be present)
1. **Mortality**: `Tot_mortal` (SBNFMortalityt)
2. **Population**: `POP` (PopulatedAreast)
3. **Grid ID**: `GRID` (CuttingGrids)

### ⚠️ Optional Fields (Enhance analysis if present)
1. **Population Density**: `pop_per_sq` (PopulatedAreast)
2. **Community Weight**: `weight` (Communityfeatures)
3. **Egress Weight**: `weight` (EgressRoutes)
4. **Transmission Voltage**: `KV` (Transmission)

## Auto-Detection Priority

The code tries fields in this order:

### Mortality Field Detection:
1. `Tot_mortal` (Fire Creek)
2. `MORTALITY`
3. `mort_pct`
4. First numeric column

### Population Field Detection:
1. `POP` (Fire Creek)
2. `POPULATION`
3. `POP_TOTAL`
4. First numeric column

### Density Field Detection:
1. `pop_per_sq` (Fire Creek)
2. `POP_DENSITY`
3. `DENSITY`
4. Not used if not found

## Validation Command

Run this before the main analysis:
```bash
cd tree_priority_analysis
python check_fields.py
```

This will verify all field mappings are correct!
