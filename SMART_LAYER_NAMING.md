# Smart Layer Naming

## Overview

The GeoCodex plugin now automatically generates descriptive, unique names for each query result layer instead of using the generic "GeoCodex Query Result" for all layers. This makes it much easier to manage multiple query results in QGIS.

## How It Works

The system uses a three-tier naming strategy:

### 1. Natural Language Query Analysis (Priority 1)

When you ask a question in natural language, the system extracts key information:

**Examples:**

- "Find all cities with population over 100000" → `Cities_Pop_100000_1_145334`
- "Buffer roads by 500 meters" → `Roads_Buffer_500_2_145334`
- "Show counties in California" → `Counties_3_145334`
- "Find parks within 1km of downtown" → `Parks_Within_1k_4_145334`

**What it extracts:**

- **Entities**: cities, counties, roads, parks, buildings, parcels, rivers, lakes, etc.
- **Operations**: buffer, intersect, within, near, distance
- **Constraints**: Numbers with units (100k, 500m, 1km)

### 2. SQL Query Analysis (Priority 2)

If no natural language query is available, it analyzes the SQL:

**Examples:**

- `SELECT * FROM cities WHERE...` → `Cities_Query_5_145334`
- `SELECT ST_Buffer(geom, 100) FROM roads` → `Roads_Buffer_6_145334`
- `SELECT COUNT(*) FROM counties` → `Counties_Count_7_145334`
- `SELECT a.* FROM parcels WHERE ST_Intersects(...)` → `Parcels_Intersect_8_145334`

**What it detects:**

- **Table name**: Extracted from FROM clause (handles schema prefixes like `public.`)
- **Spatial operations**: ST_Buffer, ST_Intersects, ST_Within, ST_Distance
- **Aggregations**: COUNT, SUM, AVG → adds "\_Count" or "\_Stats" suffix

### 3. Fallback (Priority 3)

If neither natural language nor SQL provides meaningful information:

- Uses custom context if provided (e.g., "Image_Analysis")
- Falls back to generic `Query_X_timestamp`

## Uniqueness Guarantee

Each layer name is guaranteed to be unique using:

1. **Counter**: Increments for each query (1, 2, 3, ...)
2. **Timestamp**: Hour, minute, second (HHMMSS format)

Format: `{Descriptive_Name}_{Counter}_{Timestamp}`

Example: `Cities_Pop_100k_15_145334` means:

- **Cities_Pop_100k**: Descriptive name
- **15**: 15th query in this session
- **145334**: Created at 14:53:34 (2:53:34 PM)

## Usage Examples

### Scenario 1: Natural Language Workflow

```python
orchestrator = WorkflowOrchestrator(...)

# User asks: "Find all cities with population over 100000"
success, sql = orchestrator.run_nl_to_sql_workflow("Find all cities with population over 100000")

# Execute and load layer (no layer_name parameter needed)
success, msg = orchestrator.run_sql_to_layer_workflow(sql)
# Layer created: "Cities_Pop_100000_1_145501"
```

### Scenario 2: Direct SQL Execution

```python
sql = "SELECT * FROM roads WHERE ST_Buffer(geom, 500)"
success, msg = orchestrator.run_sql_to_layer_workflow(sql)
# Layer created: "Roads_Buffer_2_145502"
```

### Scenario 3: Custom Layer Name

```python
# You can still provide a custom name if needed
sql = "SELECT * FROM my_table"
success, msg = orchestrator.run_sql_to_layer_workflow(sql, layer_name="My_Custom_Layer")
# Layer created: "My_Custom_Layer"
```

### Scenario 4: Auto-Fix Workflow

```python
success, msg, final_sql = orchestrator.run_sql_with_auto_fix(
    sql_query="SELECT * FROM cities",
    user_query="Show me all cities"  # Optional but helps with naming
)
# Layer created: "Cities_Query_3_145503"
```

## Implementation Details

### Key Methods

#### `_generate_layer_name(sql_query=None, user_query=None, context=None)`

Main method that orchestrates the naming logic.

**Parameters:**

- `sql_query`: SQL being executed (optional)
- `user_query`: User's natural language query (optional)
- `context`: Additional context like "Image Analysis" (optional)

**Returns:** Unique, descriptive layer name

#### `_extract_name_from_nl_query(query)`

Parses natural language to extract entities, operations, and constraints.

**Recognized Keywords:**

- **Entities**: 40+ GIS-related terms (cities, roads, buildings, etc.)
- **Operations**: buffer, intersect, within, distance, area, population
- **Units**: k (thousand), m (meters), km (kilometers), mi (miles)

#### `_extract_name_from_sql(sql)`

Analyzes SQL structure to extract table names and operations.

**Handles:**

- Schema prefixes (`public.cities` → `Cities`)
- Common prefixes/suffixes (`tbl_cities` → `Cities`)
- Spatial functions (ST_Buffer, ST_Intersects, etc.)
- Aggregation functions (COUNT, SUM, AVG)

### Tracked State

The orchestrator maintains:

- `_layer_counter`: Incremental counter (resets on plugin reload)
- `_last_user_query`: Stores the most recent natural language query

## Benefits

### Before (Generic Naming)

```
Layers Panel:
├─ GeoCodex Query Result
├─ GeoCodex Query Result (2)
├─ GeoCodex Query Result (3)
└─ GeoCodex Query Result (4)
```

❌ Can't tell what each layer contains
❌ Hard to find specific results
❌ Need to manually rename each layer

### After (Smart Naming)

```
Layers Panel:
├─ Cities_Pop_100k_1_145501
├─ Roads_Buffer_500m_2_145502
├─ Parks_Within_1km_3_145503
└─ Counties_California_4_145504
```

✅ Immediately understand layer content
✅ Easy to find specific results
✅ No manual renaming needed
✅ Chronological ordering with timestamps

## Edge Cases Handled

### 1. Schema Prefixes

```sql
SELECT * FROM public.cities
```

→ `Cities_Query_1_145501` (not `Public_Query`)

### 2. Table Prefixes

```sql
SELECT * FROM tbl_parcels
```

→ `Parcels_Query_2_145502` (not `Tbl_parcels_Query`)

### 3. Multiple Tables

```sql
SELECT * FROM cities, counties WHERE ...
```

→ `Cities_Query_3_145503` (uses first table)

### 4. Complex Queries

```sql
SELECT c.name, p.pop
FROM (SELECT * FROM cities) c
JOIN population p ON c.id = p.city_id
```

→ `Cities_Query_4_145504` (extracts innermost table)

### 5. No Information Available

```sql
SELECT 1
```

→ `Query_5_145505` (fallback)

## Testing

Run the comprehensive test suite:

```bash
cd geo_codex
python test_layer_naming_simple.py
```

**Test Coverage:**

- Natural language extraction (✓)
- SQL parsing (✓)
- Uniqueness guarantee (✓)
- Schema prefix handling (✓)
- Fallback scenarios (✓)

## Future Enhancements

Potential improvements for future versions:

1. **User Preferences**: Allow users to configure naming patterns
2. **Entity Learning**: Learn project-specific table names and entities
3. **Abbreviation Support**: Configurable abbreviations (Population → Pop)
4. **Custom Templates**: Support for naming templates like `{table}_{date}_{time}`
5. **Layer Groups**: Auto-group related queries (e.g., all buffer operations)

## Backward Compatibility

The changes are **fully backward compatible**:

- `run_sql_to_layer_workflow(sql, layer_name)` still accepts custom layer names
- If `layer_name` is provided, smart naming is skipped
- Existing code continues to work without modification
- Smart naming is optional—only triggers when `layer_name=None`

## Migration Guide

### Old Code

```python
# Had to provide generic names
orchestrator.run_sql_to_layer_workflow(sql, "GeoCodex Query Result")
```

### New Code (Recommended)

```python
# Let the system generate smart names
orchestrator.run_sql_to_layer_workflow(sql)  # layer_name is optional now

# Or provide context for better naming
orchestrator.run_sql_with_auto_fix(
    sql_query=sql,
    user_query="Find all cities"  # Helps generate better names
)
```

## Configuration

Currently, smart naming is always enabled with default patterns. Future versions may add configuration options in `metadata.txt` or plugin settings.

---

**Version**: 1.0  
**Last Updated**: 2025  
**Related Files**:

- [orchestrator.py](geo_codex_logic/orchestrator.py)
- [test_layer_naming_simple.py](test_layer_naming_simple.py)
