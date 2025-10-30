def build_sql_prompt(user_query: str, schema_info: str) -> str:
    """
    Constructs a detailed and structured prompt for the LLM to generate SQL.

    Args:
        user_query (str): The natural language question from the user.
        schema_info (str): The database schema information from DBConnector.

    Returns:
        str: The fully formatted prompt.
    """
    
    prompt = f"""
You are an expert PostGIS data analyst. Your task is to convert the user's request into a single, executable SQL query for a PostgreSQL database with the PostGIS extension.

Follow these rules STRICTLY:
1.  Analyze the database schema provided to understand the available tables and columns.
2.  Pay close attention to column names and data types. Assume geometry columns are named 'geom' or 'geometry' if not specified.
3.  ALWAYS include the geometry column in your SELECT statement if the table has one. Use "geom" or "geometry" as appropriate.
4.  For queries that don't require spatial analysis, still include the geometry column so results can be displayed on the map.
5.  Use PostGIS spatial functions like ST_DWithin, ST_Intersects, ST_Buffer, ST_Area, ST_Length, etc., for any spatial analysis.
6.  Provide ONLY the raw SQL code as your response. Do not include any explanations, comments, or markdown formatting like ```sql.
7.  Do not add a semicolon at the end of your query.

EXAMPLES:
- User asks: "Show me all states"
  Correct: SELECT geom, name FROM usa.states
  Wrong: SELECT name FROM usa.states

- User asks: "Find states with area > 1000000"
  Correct: SELECT geom, name, ST_Area(geom) as area FROM usa.states WHERE ST_Area(geom) > 1000000
  
- User asks: "Get state names"
  Correct: SELECT geom, name FROM usa.states
  Wrong: SELECT name FROM usa.states

---
DATABASE SCHEMA CONTEXT:
{schema_info}
---
USER'S REQUEST:
"{user_query}"
---

SQL QUERY:
"""
    return prompt


def build_sql_from_steps_prompt(workflow_steps: str, schema_info: str) -> str:
    """
    Constructs a prompt for the LLM to generate a single SQL query from a list of steps.

    Args:
        workflow_steps (str): The textual workflow steps from the vision model (Agent 1).
        schema_info (str): The database schema for context.

    Returns:
        str: The fully formatted prompt for the SQL generation model (Agent 2).
    """
    
    prompt = f"""
You are an expert PostGIS data analyst. Your task is to convert a sequence of workflow steps into a SINGLE, consolidated, and executable SQL query. You may need to use Common Table Expressions (CTEs) with the `WITH` clause to chain operations together.

Follow these rules STRICTLY:
1.  Analyze the database schema provided to understand the available tables and columns.
2.  Read all the workflow steps first to understand the final goal.
3.  Combine the steps into a single SQL query. For example, a "buffer" step followed by an "intersect" step should be a single query like `SELECT ... FROM table_a, table_b WHERE ST_Intersects(ST_Buffer(table_a.geom, 100), table_b.geom)`.
4.  ALWAYS include the geometry column in the final SELECT statement so the result can be mapped.
5.  Provide ONLY the raw SQL code as your response. Do not include any explanations or markdown formatting.
6.  Do not add a semicolon at the end of your query.

---
DATABASE SCHEMA CONTEXT:
{schema_info}
---
WORKFLOW STEPS TO IMPLEMENT:
{workflow_steps}
---

SINGLE CONSOLIDATED SQL QUERY:
"""
    return prompt