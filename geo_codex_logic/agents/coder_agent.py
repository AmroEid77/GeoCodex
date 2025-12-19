# -*- coding: utf-8 -*-
"""
CoderAgent - Specialized agent for SQL code generation and fixing
Handles SQL generation, error correction, and code optimization
"""

import re
from typing import Tuple, Dict, List, Optional

try:
    from qgis.core import QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
except ImportError:
    log = print


class CoderAgent:
    """
    Agent specialized in SQL code generation and fixing.
    
    Responsibilities:
    - Generate SQL queries from natural language
    - Generate SQL from structured workflow steps
    - Fix SQL queries based on error messages
    - Optimize SQL queries for PostGIS/PostgreSQL
    """
    
    def __init__(self, llm_client):
        """
        Initialize the Coder Agent.
        
        Args:
            llm_client: An LLMClient instance configured for code generation
        """
        self.llm_client = llm_client
        log("CoderAgent initialized")
    
    def generate_sql_from_nl(self, user_query: str, schema_info: str) -> Tuple[bool, str]:
        """
        Generate SQL from a natural language query.
        
        Args:
            user_query: Natural language query from user
            schema_info: Database schema information
            
        Returns:
            Tuple of (success, sql_query or error_message)
        """
        log(f"CoderAgent: Generating SQL from NL query: {user_query[:100]}...")
        
        try:
            prompt = self._build_nl_to_sql_prompt(user_query, schema_info)
            response = self.llm_client.generate_response(prompt)
            
            if "Error:" in response:
                return False, response
            
            # Extract and clean SQL
            clean_sql = self._extract_sql(response)
            if clean_sql:
                return True, clean_sql
            else:
                return False, "Could not extract valid SQL from response"
                
        except Exception as e:
            error_msg = f"SQL generation error: {e}"
            log(error_msg)
            return False, error_msg
    
    def generate_sql_from_steps(self, workflow_steps: str, schema_info: str) -> Tuple[bool, str]:
        """
        Generate SQL from structured workflow steps (e.g., from image analysis).
        
        Args:
            workflow_steps: Structured workflow description
            schema_info: Database schema information
            
        Returns:
            Tuple of (success, sql_query or error_message)
        """
        log("CoderAgent: Generating SQL from workflow steps")
        
        try:
            prompt = self._build_steps_to_sql_prompt(workflow_steps, schema_info)
            response = self.llm_client.generate_response(prompt)
            
            if "Error:" in response:
                return False, response
            
            # Extract and clean SQL
            clean_sql = self._extract_sql(response)
            if clean_sql:
                return True, clean_sql
            else:
                return False, "Could not extract valid SQL from response"
                
        except Exception as e:
            error_msg = f"SQL generation from steps error: {e}"
            log(error_msg)
            return False, error_msg
    
    def fix_sql(self, 
                failed_sql: str, 
                error_msg: str, 
                schema_info: str,
                error_history: Optional[List[Dict]] = None,
                full_error_context: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Fix a failed SQL query based on error message with full observability.
        
        Args:
            failed_sql: The SQL query that failed
            error_msg: The error message from execution
            schema_info: Database schema information
            error_history: List of previous failed attempts (optional)
            full_error_context: Full error context including:
                - error_type: Type of error (layer_invalid, syntax, execution, etc.)
                - full_traceback: Complete error traceback if available
                - error_details: Detailed error information from QGIS/PostgreSQL
                - execution_context: Where/how the query was executed
            
        Returns:
            Tuple of (success, fixed_sql or error_message)
        """
        log(f"CoderAgent: Fixing SQL error with full context: {error_msg[:100]}...")
        
        try:
            # Build prompt with full error context - LLM will analyze it
            prompt = self._build_sql_fix_prompt(
                failed_sql, error_msg, schema_info, error_history, full_error_context
            )
            response = self.llm_client.generate_response(prompt)
            
            if "Error:" in response:
                return False, response
            
            # Extract fixed SQL
            fixed_sql = self._extract_sql(response)
            if fixed_sql:
                log("CoderAgent: SQL fix generated successfully")
                return True, fixed_sql
            else:
                return False, "Could not extract valid SQL from fix response"
                
        except Exception as e:
            error_msg = f"SQL fix error: {e}"
            log(error_msg)
            return False, error_msg
    
    def _extract_sql(self, response: str) -> Optional[str]:
        """
        Extract SQL query from LLM response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned SQL query or None
        """
        # Try to extract from SQL code blocks
        sql_matches = re.findall(r'```sql\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
        if sql_matches:
            return sql_matches[-1].strip()
        
        # Try plain code blocks
        code_matches = re.findall(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_matches:
            potential_sql = code_matches[-1].strip()
            if potential_sql.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')):
                return potential_sql
        
        # Last resort - check if response itself starts with SQL keywords
        cleaned = response.strip()
        if cleaned.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')):
            return cleaned
        
        return None
    

    
    def _build_nl_to_sql_prompt(self, user_query: str, schema_info: str) -> str:
        """
        Build expert-level prompt for natural language to SQL conversion.
        """
        return f"""You are a MASTER-LEVEL PostGIS/PostgreSQL/Spatial Database expert with deep knowledge of:
• SQL optimization and query planning
• PostGIS spatial functions (ST_*, geometry operations, topology)
• DE-9IM spatial relationship model
• Coordinate reference systems (CRS/SRID) and projections
• Spatial indexing (GiST, BRIN) and performance tuning
• Common PostgreSQL/PostGIS pitfalls and error patterns

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA:
═══════════════════════════════════════════════════════════════════════════════
{schema_info}

═══════════════════════════════════════════════════════════════════════════════
USER REQUEST:
===============================================================================
{user_query}

===============================================================================
[STRATEGIC THINKING PROCESS] - Think Before Coding:
===============================================================================

1. UNDERSTAND: What is the user really asking for?
2. IDENTIFY: Which tables/columns from the schema are needed?
3. PLAN: What spatial operations are required? (buffer, intersection, distance, etc.)
4. VALIDATE: Do column names EXACTLY match the schema? (case-sensitive!)
5. OPTIMIZE: Can this query be more efficient? (indexes, limits, subqueries)
6. VERIFY: Does the result include 'geom' for QGIS visualization?

===============================================================================
[CRITICAL REQUIREMENTS] - MUST FOLLOW:
===============================================================================

1. >> GEOMETRY COLUMN: MANDATORY 'geom' in final SELECT (for QGIS display)
   - Even for attribute queries: SELECT name, population, geom FROM...
   - If geometry transform needed: SELECT name, ST_Transform(geom, 4326) as geom FROM...

2. >> EXACT SCHEMA MATCH:
   - Copy table/column names EXACTLY from schema (case matters!)
   - Check spelling twice - typos cause "column does not exist" errors
   - Use schema prefix if shown: public.tablename

   >> POSTGRESQL CASE SENSITIVITY (CRITICAL!):
   - Unquoted identifiers: Automatically lowercased (city = CITY = City)
   - Quoted identifiers: Case-sensitive ("CITY" != "city" != city)
   - If schema shows uppercase/mixed case → USE DOUBLE QUOTES!
   
   Examples:
   [X] SELECT ColumnName FROM table          (fails if column is "ColumnName")
   [OK] SELECT "ColumnName" FROM table        (correct for mixed/uppercase columns)
   [X] SELECT name FROM "TableName"           (fails if column is lowercase)
   [OK] SELECT "name" FROM "TableName"        (or just: name if lowercase)
   
   Rule: If schema shows UPPERCASE or MixedCase → quote it: "UPPERCASE", "MixedCase"
         If schema shows lowercase → no quotes needed: lowercase

3. >> SPATIAL OPERATIONS:
   - Distance queries: ST_DWithin(geom, geom, distance) for indexed queries
   - Buffer: ST_Buffer(geom, distance) - distance in CRS units
   - Intersection: ST_Intersects(a.geom, b.geom) for boolean check
   - Containment: ST_Contains, ST_Within, ST_Covers
   - Relationships: ST_Relate for DE-9IM patterns

4. >> CRS/PROJECTION HANDLING:
   - Check SRID in schema (ST_SRID(geom))
   - For accurate distance: Transform to projected CRS
     * USA: ST_Transform(geom, 2163) Albers Equal Area
     * Meters needed: ST_Transform(geom, 3857) Web Mercator
   - Distance units match CRS: degrees vs meters vs feet

5. >> PERFORMANCE OPTIMIZATION:
   - Use spatial index operators: && (bounding box overlap)
   - Combine with ST_* functions: WHERE geom && bbox AND ST_Intersects(...)
   - LIMIT results for large datasets
   - Use ST_DWithin instead of ST_Distance < x for indexed queries

6. >> COMMON PATTERNS:
   - Buffer analysis: SELECT ST_Buffer(geom, distance) as geom FROM...
   - Find nearby: WHERE ST_DWithin(a.geom, b.geom, distance)
   - Spatial join: FROM a JOIN b ON ST_Intersects(a.geom, b.geom)
   - Aggregate geometry: ST_Union, ST_Collect, ST_ConvexHull

===============================================================================
[EXPERT TIPS] - Avoid Common Errors:
===============================================================================

* String values need single quotes: WHERE name = 'California'
* Numeric comparisons no quotes: WHERE population > 100000
* NULL handling: Use IS NULL / IS NOT NULL (not = NULL)
* Array containment: Use ANY(array) or = ANY(ARRAY[...])
* Case-insensitive search: LOWER(column) = LOWER('value') or ILIKE
* Date/time: Use proper casting: '2024-01-01'::date
* Avoid SELECT * if not needed - specify columns for performance
* Use table aliases for readability: FROM cities c, counties co WHERE...

===============================================================================
[OUTPUT FORMAT - STRICT]
===============================================================================

Return ONLY the SQL query wrapped in ```sql``` code blocks.
NO explanations, NO comments, NO thinking text - JUST THE QUERY.

Example:
```sql
SELECT name, population, geom 
FROM cities 
WHERE population > 100000
```

Now generate the perfect SQL query:
"""
    
    def _build_steps_to_sql_prompt(self, workflow_steps: str, schema_info: str) -> str:
        """
        Build expert-level prompt for workflow steps to SQL conversion.
        """
        return f"""You are a MASTER-LEVEL PostGIS/PostgreSQL expert specializing in complex multi-step spatial workflows.
You excel at translating image-extracted workflows into optimized, production-ready SQL.

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA (Your Reference):
═══════════════════════════════════════════════════════════════════════════════
{schema_info}

===============================================================================
WORKFLOW STEPS (From Image Analysis):
===============================================================================
{workflow_steps}

===============================================================================
[STRATEGIC WORKFLOW IMPLEMENTATION]
===============================================================================

STEP 1: UNDERSTAND THE WORKFLOW
  * Read each step carefully
  * Identify data flow: input -> transformation -> output
  * Note spatial operations required at each step
  * Determine if steps can be chained or need CTEs

STEP 2: MAP TO DATABASE SCHEMA
  * Match workflow entities to actual table names (EXACT spelling!)
  * Identify required columns from schema
  * Verify geometry column names
  * Check for any intermediate calculations needed
  * CHECK CASE SENSITIVITY: If schema shows UPPERCASE or MixedCase → quote them!

STEP 3: PLAN SQL STRUCTURE
  * Single query or CTEs? (Use CTEs for clarity in multi-step workflows)
  * Which PostGIS functions for each spatial operation?
  * CRS transformations needed?
  * Performance considerations (indexes, order of operations)

STEP 4: IMPLEMENT WITH PRECISION
  * Follow workflow step order
  * Use descriptive CTE names (step1_buffer, step2_intersect, etc.)
  * Maintain geometry through all steps
  * Apply transformations correctly

===============================================================================
[CRITICAL REQUIREMENTS]
===============================================================================

1. >> FINAL OUTPUT MUST INCLUDE 'geom':
   - The last SELECT must have a geometry column named 'geom'
   - This is essential for QGIS map visualization
   
2. >> MULTI-STEP WORKFLOWS USE CTEs:
   Example structure:
   ```sql
   WITH step1 AS (
     SELECT ..., geom FROM table WHERE ...
   ),
   step2 AS (
     SELECT ..., ST_Buffer(geom, 100) as geom FROM step1
   ),
   step3 AS (
     SELECT ..., geom FROM step2 WHERE ST_Intersects(...)
   )
   SELECT * FROM step3
   ```

3. >> SPATIAL OPERATIONS PATTERNS:
   * Buffer: ST_Buffer(geom, distance)
   * Intersection: ST_Intersection(a.geom, b.geom) for geometry
                   ST_Intersects(a.geom, b.geom) for boolean check
   * Within/Contains: ST_Within, ST_Contains, ST_Covers
   * Distance: ST_DWithin for indexed queries, ST_Distance for measurement
   * Union: ST_Union for aggregating geometries
   * Clip: ST_Intersection(input.geom, boundary.geom)

4. >> CRS/PROJECTION HANDLING:
   * Check if distance measurements needed -> transform to projected CRS
   * USA data: ST_Transform(geom, 2163) for accurate meters
   * Keep consistent SRID throughout workflow
   * Final output can be in original CRS or 4326 for web display

5. >> WORKFLOW STEP PATTERNS:

   "Select features where..." -> WHERE clause with criteria
   "Buffer by X meters" -> ST_Buffer(ST_Transform(geom, projected_srid), X)
   "Find features within..." -> ST_DWithin or WHERE ST_Within
   "Intersect with..." -> ST_Intersection for geometry, ST_Intersects for filter
   "Calculate area/length" -> ST_Area, ST_Length (ensure projected CRS!)
   "Merge/combine" -> ST_Union in GROUP BY or aggregate
   "Count features" -> COUNT(*) or COUNT(geom)
   "Filter by attribute" -> WHERE column = value

===============================================================================
[EXPERT WORKFLOW TIPS]
===============================================================================

* Name CTEs descriptively: step1_parks, step2_buffered, step3_intersected
* Pass geometry through each CTE: Always include geom in SELECT
* Use table aliases for readability: FROM parks p, boundaries b
* Optimize order: Filter early, spatial ops later
* Comment complex steps inline if helpful for debugging
* For "find X near Y": Use ST_DWithin (indexed) not ST_Distance < 
* For "get geometry": Use ST_Intersection
* For "boolean check": Use ST_Intersects, ST_Within, ST_Contains

===============================================================================
[OUTPUT FORMAT - STRICT]
===============================================================================

Return ONLY the SQL query wrapped in ```sql``` code blocks.
NO explanations, NO thinking text - JUST THE QUERY.

For multi-step workflows, use this structure:
```sql
WITH step1_descriptive_name AS (
  -- First operation
  SELECT columns, geom FROM table WHERE criteria
),
step2_descriptive_name AS (
  -- Second operation  
  SELECT columns, ST_SomeFunction(geom) as geom FROM step1_descriptive_name
)
SELECT * FROM step2_descriptive_name
```

Now translate the workflow into perfect SQL:
"""
    
    def _build_sql_fix_prompt(self, 
                              failed_sql: str, 
                              error_msg: str, 
                              schema_info: str,
                              error_history: Optional[List[Dict]] = None,
                              full_error_context: Optional[Dict] = None) -> str:
        """
        Build prompt for SQL error fixing - pass full error context to LLM.
        """
        # Build context from error history
        history_context = ""
        if error_history and len(error_history) > 1:
            history_context = "\n\n**Previous failed attempts:**\n"
            for h in error_history[:-1]:  # All but current
                history_context += f"- Attempt {h['attempt']}: Error was '{h['error'][:200]}'\n"
        
        # Build full error context - pass everything to the LLM
        full_context = ""
        if full_error_context:
            full_context = "\n\n═══════════════════════════════════════════════════════════════════════════════\nFULL ERROR CONTEXT (Complete Details):\n═══════════════════════════════════════════════════════════════════════════════\n"
            if 'error_type' in full_error_context:
                full_context += f"Error Type: {full_error_context['error_type']}\n"
            if 'execution_context' in full_error_context:
                full_context += f"Execution Context: {full_error_context['execution_context']}\n"
            if 'full_traceback' in full_error_context:
                full_context += f"\nFull Traceback:\n{full_error_context['full_traceback']}\n"
            if 'error_details' in full_error_context:
                full_context += f"\nDetailed Error Info:\n{full_error_context['error_details']}\n"
            if 'wrapped_sql' in full_error_context:
                full_context += f"\nWrapped SQL (actual executed):\n{full_error_context['wrapped_sql']}\n"
            if 'uri' in full_error_context:
                full_context += f"\nConnection URI info: {full_error_context['uri']}\n"
        
        return f"""You are a MASTER-LEVEL PostGIS/PostgreSQL debugging expert with years of experience fixing spatial SQL errors.

You have COMPLETE ERROR CONTEXT including traceback, PostgreSQL hints, execution details, and error history.
Your mission: Analyze deeply, think strategically, fix precisely.

IMPORTANT: You CANNOT execute SQL queries to test solutions. You must fix the query based on error analysis alone.
Generate the corrected SQL directly without suggesting intermediate test queries.

===============================================================================
DATABASE SCHEMA (Your Ground Truth):
===============================================================================
{schema_info}

===============================================================================
FAILED SQL QUERY:
===============================================================================
```sql
{failed_sql}
```

===============================================================================
COMPLETE ERROR INFORMATION:
===============================================================================
{error_msg}
{history_context}
{full_context}

===============================================================================
[SYSTEMATIC DEBUGGING PROCESS] - Think Through Each Step:
===============================================================================

STEP 1: IDENTIFY ERROR TYPE
  [ ] Schema/column name mismatch? -> Check exact spelling in schema
  [ ] Missing geometry column? -> Add 'geom' to SELECT
  [ ] Syntax error? -> Find the specific syntax issue (comma, quote, parenthesis)
  [ ] Type mismatch? -> Check data types and add explicit casting
  [ ] Spatial function error? -> Verify function signature and CRS compatibility
  [ ] Permission/connection error? -> Usually unfixable via SQL change

STEP 2: LOCATE EXACT PROBLEM
  * Read PostgreSQL error message carefully - it tells you EXACTLY what's wrong
  * Line numbers and "near" indicators point to problem location
  * "column does not exist" -> Typo in column name or wrong table
  * "relation does not exist" -> Typo in table name or missing schema prefix
  * "function does not exist" -> Wrong function name, wrong parameter types, or missing PostGIS
  * "layer is invalid" or "layer invalid" -> MISSING 'geom' in final SELECT
  * "cannot cast" -> Data type mismatch, need explicit ::type casting

STEP 3: CROSS-REFERENCE WITH SCHEMA
  * Compare EVERY table name in query with schema (exact match!)
  * Compare EVERY column name with schema columns (case-sensitive!)
  * Verify geometry column name (usually 'geom', 'geometry', 'the_geom')
  * Check if schema prefix needed (public.tablename vs tablename)

STEP 4: CHECK PREVIOUS ATTEMPTS
  * If this is attempt 2+, what was tried before?
  * Don't repeat the same mistake
  * If previous attempt added 'geom' but still failed, look deeper
  * Learn from error history pattern

STEP 5: APPLY THE FIX
  * Make MINIMAL changes - fix ONLY the error
  * Preserve original query intent and logic
  * Don't over-engineer - simple fix is best fix
  * Test logic mentally before outputting

===============================================================================
[CRITICAL ERROR PATTERNS] - Expert Knowledge:
===============================================================================

1. MISSING GEOMETRY (Most Common!):
   [X] SELECT name, population FROM cities
   [OK] SELECT name, population, geom FROM cities
   -> QGIS requires geometry column for map visualization

2. COLUMN NAME TYPO:
   [X] SELECT populaton FROM cities  (typo: populaton)
   [OK] SELECT population FROM cities
   -> Copy exact spelling from schema

2b. CASE SENSITIVITY ERROR (PostgreSQL!):
   [X] SELECT ColumnName, MyColumn FROM table  (if schema shows "ColumnName", "MyColumn")
   [OK] SELECT "ColumnName", "MyColumn" FROM table
   -> PostgreSQL: Uppercase/mixed case columns MUST be quoted with double quotes!
   -> Unquoted = lowercased automatically
   -> Check schema carefully: compare exact case shown in schema

3. TABLE NAME TYPO/SCHEMA:
   [X] SELECT * FROM Counties  (wrong case or missing schema)
   [OK] SELECT * FROM public.counties
   -> Use exact table name from schema with schema prefix if needed

4. GEOMETRY COLUMN NAME WRONG:
   [X] SELECT name, geometry FROM cities  (column might be 'geom')
   [OK] SELECT name, geom FROM cities
   -> Check schema for exact geometry column name

5. STRING QUOTING:
   [X] WHERE name = California  (missing quotes)
   [OK] WHERE name = 'California'
   -> Strings need single quotes in SQL

6. DATA TYPE MISMATCH:
   [X] WHERE ST_Area(geom) = '1000'  (comparing number to string)
   [OK] WHERE ST_Area(geom) = 1000
   -> Remove quotes from numbers, or use explicit casting

7. SPATIAL FUNCTION ERRORS:
   [X] ST_Buffer(geom, '100m')  (distance as string)
   [OK] ST_Buffer(geom, 100)  (distance as number)
   -> Function parameters must be correct type

8. CRS/SRID MISMATCH:
   [X] ST_Distance(geom1, geom2) < 100  (different SRIDs)
   [OK] ST_Distance(ST_Transform(geom1, 3857), ST_Transform(geom2, 3857)) < 100
   -> Ensure same CRS for spatial operations

9. MISSING AGGREGATION:
   [X] SELECT county, name FROM cities GROUP BY county  (name not aggregated)
   [OK] SELECT county, array_agg(name) FROM cities GROUP BY county
   -> All non-grouped columns need aggregation

10. SUBQUERY ALIAS MISSING:
    [X] SELECT * FROM (SELECT geom FROM cities)  (no alias)
    [OK] SELECT * FROM (SELECT geom FROM cities) AS subq
    -> Subqueries need AS alias

===============================================================================
[ADVANCED DEBUGGING STRATEGIES]
===============================================================================

NOTE: You CANNOT execute SQL queries to test solutions. You must fix based on analysis alone.

Breaking Down Complex Issues:
  * Is the geometry valid? Consider ST_IsValid(geom) in your fix
  * What's the SRID? Consider ST_SRID(geom) if CRS issues detected
  * Does bounding box work? Use geom && other_geom for performance
  
DE-9IM Spatial Relationships:
  * ST_Relate(a.geom, b.geom) returns 9-character matrix
  * Common patterns: 'T********' (touches), '2********' (overlaps)
  * Use predefined predicates when possible (ST_Intersects, ST_Within, etc.)
  
Performance Optimization:
  * Check if spatial index exists in schema (GiST indexes)
  * Use && for bounding box before ST_* functions
  * Add LIMIT if result set might be huge
  * Consider ST_SimplifyPreserveTopology for complex geometries

===============================================================================
[YOUR MISSION]
===============================================================================

1. Read ENTIRE error context (don't skip traceback or details)
2. THINK through the debugging steps above
3. Identify ROOT CAUSE (not just symptoms)
4. Fix PRECISELY (minimal change, maximum impact)
5. VERIFY mentally that fix addresses the exact error
6. Output ONLY the corrected SQL

DO NOT:
  [X] Make random changes hoping something works
  [X] Repeat same mistake from error history
  [X] Change query logic beyond fixing the error
  [X] Add unnecessary complexity
  [X] Forget to include 'geom' in SELECT

DO:
  [OK] Think systematically through the debugging process
  [OK] Cross-reference everything with schema
  [OK] Make surgical, precise fixes
  [OK] Learn from previous failed attempts
  [OK] Always include geometry column for QGIS

===============================================================================
[OUTPUT FORMAT - STRICT]
===============================================================================

Return ONLY the corrected SQL wrapped in ```sql``` code blocks.
NO explanations, NO thinking text, NO comments - JUST THE FIXED QUERY.

Example:
```sql
SELECT name, population, geom FROM cities WHERE population > 100000
```

Now apply your expert debugging skills and fix this query:
"""
