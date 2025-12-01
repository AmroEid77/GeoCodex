# -*- coding: utf-8 -*-
"""
WorkflowOrchestrator - Manages the execution of the plugin's core workflows
Supports dual-model configuration: Interpreter (vision) and Coder (SQL generation)
"""

from typing import Dict, Tuple, Optional
from .core.llm_client import LLMClient
from .core.db_connector import DBConnector
from .utils import prompt_builder
from .utils import image_utils

try:
    from qgis.core import QgsVectorLayer, QgsProject, QgsDataSourceUri, QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
except ImportError:
    log = print


class WorkflowOrchestrator:
    """
    Manages the execution of the plugin's core workflows.
    
    Supports two LLM configurations:
    - Interpreter: Vision-capable model for image analysis
    - Coder: Model optimized for SQL code generation
    
    Can use the same model for both or different models/providers.
    """
    
    def __init__(
        self, 
        interpreter_config: Optional[Dict] = None,
        coder_config: Optional[Dict] = None,
        db_params: Optional[Dict] = None,
        # Legacy parameters for backward compatibility
        api_key: Optional[str] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            interpreter_config: Dict with keys: provider, api_key, model_name, base_url
            coder_config: Dict with keys: provider, api_key, model_name, base_url
            db_params: Database connection parameters
            api_key: Legacy parameter - if provided, uses NVIDIA with this key
        """
        # Handle legacy initialization (single api_key)
        if api_key and not interpreter_config:
            interpreter_config = {
                "provider": "nvidia",
                "api_key": api_key,
                "model_name": "mistralai/mistral-medium-3-instruct",
                "base_url": None
            }
            coder_config = {
                "provider": "nvidia", 
                "api_key": api_key,
                "model_name": "deepseek-ai/deepseek-v3.1",
                "base_url": None
            }
        
        self.interpreter_config = interpreter_config or {}
        self.coder_config = coder_config or {}
        self.db_params = db_params or {}
        
        log(f"Orchestrator initialized with interpreter: {self.interpreter_config.get('provider', 'N/A')}, "
            f"coder: {self.coder_config.get('provider', 'N/A')}")

    def _create_interpreter_client(self) -> LLMClient:
        """Create an LLM client for the interpreter (vision) model"""
        return LLMClient(
            provider=self.interpreter_config.get("provider", "nvidia"),
            api_key=self.interpreter_config.get("api_key"),
            model_name=self.interpreter_config.get("model_name"),
            base_url=self.interpreter_config.get("base_url")
        )
    
    def _create_coder_client(self) -> LLMClient:
        """Create an LLM client for the coder (SQL generation) model"""
        return LLMClient(
            provider=self.coder_config.get("provider", "nvidia"),
            api_key=self.coder_config.get("api_key"),
            model_name=self.coder_config.get("model_name"),
            base_url=self.coder_config.get("base_url")
        )

    # --- V2 Methods ---
    def run_nl_to_sql_workflow(self, user_query: str) -> Tuple[bool, str]:
        """
        Convert natural language query to SQL.
        Uses the Coder model for SQL generation.
        """
        log("--- Orchestrator: Starting NL-to-SQL workflow ---")
        
        try:
            # Get database schema for context
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            if "Error:" in schema_info:
                return False, schema_info
            
            # Build the SQL generation prompt
            final_prompt = prompt_builder.build_sql_prompt(user_query, schema_info)
            
            # Use the coder model for SQL generation
            coder_client = self._create_coder_client()
            sql_response = coder_client.generate_response(final_prompt)
            
            if "Error:" in sql_response:
                return False, sql_response
            
            # Clean up the response
            clean_sql = sql_response.replace("```sql", "").replace("```", "").strip()
            return True, clean_sql
            
        except Exception as e:
            error_msg = f"NL-to-SQL workflow error: {e}"
            log(error_msg)
            return False, error_msg

    def run_sql_to_layer_workflow(self, sql_query: str, layer_name: str) -> Tuple[bool, str]:
        """
        Execute SQL query and load results as a QGIS layer.
        """
        log("--- Orchestrator: Starting SQL-to-Layer workflow ---")
        
        try:
            sql_query = sql_query.strip().rstrip(';')
            
            uri = QgsDataSourceUri()
            uri.setConnection(
                self.db_params['host'], 
                self.db_params['port'], 
                self.db_params['dbname'], 
                self.db_params['user'], 
                self.db_params['password']
            )
            
            # Wrap query to ensure it has a unique ID column
            # Use checkPrimaryKeyUnicity=0 to avoid pg_get_serial_sequence warning on subqueries
            wrapped_sql = f"SELECT ROW_NUMBER() OVER() AS gid, * FROM ({sql_query}) AS subquery"
            uri.setDataSource("", f"({wrapped_sql})", "geom", "", "gid")
            uri.setParam("checkPrimaryKeyUnicity", "0")
            
            layer = QgsVectorLayer(uri.uri(False), layer_name, "postgres")
            
            if not layer.isValid():
                error_msg = f"Layer failed to load: {layer.error().summary()}"
                log(error_msg)
                return False, error_msg
            
            QgsProject.instance().addMapLayer(layer)
            msg = f"Success! Layer '{layer_name}' added ({layer.featureCount()} features)."
            log(msg)
            return True, msg
            
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            log(error_msg)
            return False, error_msg

    def run_sql_with_auto_fix(self, sql_query: str, layer_name: str, max_retries: int = 3) -> Tuple[bool, str, str]:
        """
        Execute SQL with automatic error correction.
        
        If execution fails, sends the error back to the Coder LLM to fix the SQL.
        Retries up to max_retries times.
        
        Returns:
            Tuple of (success, message, final_sql)
        """
        log(f"--- Orchestrator: SQL execution with auto-fix (max {max_retries} retries) ---")
        
        current_sql = sql_query.strip().rstrip(';')
        attempt = 0
        error_history = []
        
        # Get schema for context in fix attempts
        try:
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
        except Exception as e:
            return False, f"Failed to get schema: {e}", current_sql
        
        while attempt <= max_retries:
            attempt += 1
            log(f"Attempt {attempt}/{max_retries + 1}: Executing SQL...")
            
            # Try to execute the SQL
            success, result = self._try_execute_sql(current_sql, layer_name)
            
            if success:
                if attempt > 1:
                    log(f"SQL fixed successfully after {attempt} attempts!")
                    return True, f"Success after {attempt} attempts! {result}", current_sql
                else:
                    return True, result, current_sql
            
            # Execution failed
            error_msg = result
            error_history.append({
                "attempt": attempt,
                "sql": current_sql,
                "error": error_msg
            })
            
            log(f"Attempt {attempt} failed: {error_msg}")
            
            # If we've exhausted retries, return failure
            if attempt > max_retries:
                log(f"All {max_retries + 1} attempts failed. Giving up.")
                break
            
            # Try to fix the SQL using LLM
            log(f"Sending error to Coder LLM for correction...")
            fix_success, fixed_sql = self._fix_sql_with_llm(
                current_sql, error_msg, schema_info, error_history
            )
            
            if not fix_success:
                log(f"LLM failed to generate fix: {fixed_sql}")
                break
            
            # Update SQL for next attempt
            current_sql = fixed_sql
            log(f"Received fixed SQL, retrying...")
        
        # All attempts failed - return the error history
        error_summary = self._format_error_history(error_history)
        return False, f"Failed after {attempt} attempts.\n\n{error_summary}", current_sql
    
    def _try_execute_sql(self, sql_query: str, layer_name: str) -> Tuple[bool, str]:
        """
        Try to execute SQL and load as layer. Returns (success, message/error).
        """
        try:
            uri = QgsDataSourceUri()
            uri.setConnection(
                self.db_params['host'], 
                self.db_params['port'], 
                self.db_params['dbname'], 
                self.db_params['user'], 
                self.db_params['password']
            )
            
            # Wrap query to ensure it has a unique ID column
            # Use checkPrimaryKeyUnicity=false to avoid pg_get_serial_sequence warning
            wrapped_sql = f"SELECT ROW_NUMBER() OVER() AS gid, * FROM ({sql_query}) AS subquery"
            uri.setDataSource("", f"({wrapped_sql})", "geom", "", "gid")
            uri.setParam("checkPrimaryKeyUnicity", "0")
            
            layer = QgsVectorLayer(uri.uri(False), layer_name, "postgres")
            
            if not layer.isValid():
                error_msg = layer.error().summary()
                # Try to get more detailed error
                if not error_msg:
                    error_msg = "Layer is invalid (unknown error)"
                return False, error_msg
            
            # Check if layer has features
            feature_count = layer.featureCount()
            
            QgsProject.instance().addMapLayer(layer)
            return True, f"Layer '{layer_name}' added ({feature_count} features)."
            
        except Exception as e:
            return False, str(e)
    
    def _fix_sql_with_llm(
        self, 
        failed_sql: str, 
        error_msg: str, 
        schema_info: str,
        error_history: list
    ) -> Tuple[bool, str]:
        """
        Use the Coder LLM to fix a failed SQL query.
        
        Returns (success, fixed_sql or error_message)
        """
        try:
            # Build context from error history if there were multiple failures
            history_context = ""
            if len(error_history) > 1:
                history_context = "\n\n**Previous failed attempts:**\n"
                for h in error_history[:-1]:  # All but the current one
                    history_context += f"- Attempt {h['attempt']}: Error was '{h['error'][:200]}'\n"
            
            fix_prompt = f"""You are a PostGIS/PostgreSQL expert. Fix the following SQL query that produced an error.

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA:
═══════════════════════════════════════════════════════════════════════════════
{schema_info}

═══════════════════════════════════════════════════════════════════════════════
FAILED SQL QUERY:
═══════════════════════════════════════════════════════════════════════════════
```sql
{failed_sql}
```

═══════════════════════════════════════════════════════════════════════════════
ERROR MESSAGE:
═══════════════════════════════════════════════════════════════════════════════
{error_msg}
{history_context}

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK:
═══════════════════════════════════════════════════════════════════════════════
1. Analyze the error message carefully
2. Identify the root cause (syntax error, wrong column name, missing table, type mismatch, etc.)
3. Fix ONLY the issue - preserve the original query intent
4. Verify column and table names against the schema above
5. Return ONLY the corrected SQL query

CRITICAL REQUIREMENTS:
- The query MUST include a geometry column named 'geom' in the final SELECT
- If the query is for attribute-only data (like DE-9IM matrices, counts, etc.), 
  STILL include the geometry column so it can be displayed on the map
- Example: SELECT name, ST_Relate(a.geom, b.geom) as de9im, a.geom FROM ...

COMMON FIXES TO CONSIDER:
- "Layer is invalid" or "unknown error" = MISSING GEOMETRY COLUMN - add 'geom' to SELECT
- Column name typos (check schema for correct names)
- Missing schema prefix (e.g., public.tablename)
- Wrong geometry column name (check schema for actual geometry column)
- Data type mismatches (casting may be needed)
- Missing quotes around string values
- Incorrect function names or parameters
- CRS/SRID issues with spatial functions
- Referencing temporary results like "GeoCodex Query Result" - rebuild the full query

OUTPUT FORMAT:
Return ONLY the corrected SQL query wrapped in ```sql``` code blocks.
Do NOT include any explanation - just the fixed SQL.

```sql
-- Your corrected SQL here
```"""

            coder_client = self._create_coder_client()
            response = coder_client.generate_response(fix_prompt)
            
            if "Error:" in response:
                return False, response
            
            # Extract SQL from response
            import re
            sql_matches = re.findall(r'```sql\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
            
            if sql_matches:
                fixed_sql = sql_matches[-1].strip()
                return True, fixed_sql
            
            # Try plain code blocks
            code_matches = re.findall(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if code_matches:
                fixed_sql = code_matches[-1].strip()
                return True, fixed_sql
            
            # Last resort - clean the response
            fixed_sql = response.strip()
            if fixed_sql.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')):
                return True, fixed_sql
            
            return False, "Could not extract SQL from LLM response"
            
        except Exception as e:
            return False, f"LLM fix error: {e}"
    
    def _format_error_history(self, error_history: list) -> str:
        """Format error history for display to user"""
        parts = ["**Error History:**\n"]
        for h in error_history:
            parts.append(f"**Attempt {h['attempt']}:**")
            parts.append(f"Error: {h['error'][:300]}...")
            parts.append("")
        return "\n".join(parts)

    # --- V3 Method ---
    def run_image_to_sql_workflow(self, image_path: str) -> Tuple[bool, str]:
        """
        Execute the Image-to-SQL pipeline.
        
        Uses two models:
        1. Interpreter (vision) model to extract workflow steps from image
        2. Coder model to generate SQL from the workflow steps
        """
        log("--- Orchestrator: Starting Image-to-SQL Pipeline (Dual Model) ---")
        
        try:
            # Part 1: Image to Text (Interpreter Agent)
            log(f"Step 1: Encoding image at {image_path}")
            base64_image = image_utils.encode_image_to_base64(image_path)
            if "Error:" in base64_image:
                return False, base64_image
            
            log("Step 2: Using Interpreter model to extract workflow steps...")
            interpreter_client = self._create_interpreter_client()
            workflow_steps = interpreter_client.get_workflow_steps_from_image(base64_image)

            if "Error:" in workflow_steps:
                return False, workflow_steps
            log(f"Received workflow steps:\n{workflow_steps}")

            # Part 2: Text to SQL (Coder Agent)
            log("Step 3: Using Coder model to generate SQL...")
            
            # Get database schema for context
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            if "Error:" in schema_info:
                return False, schema_info
            
            # Build the SQL generation prompt
            sql_prompt = prompt_builder.build_sql_from_steps_prompt(workflow_steps, schema_info)
            
            # Use coder model for SQL generation
            coder_client = self._create_coder_client()
            sql_query = coder_client.generate_response(sql_prompt)

            if "Error:" in sql_query:
                return False, sql_query

            clean_sql = sql_query.replace("```sql", "").replace("```", "").strip()
            log(f"Generated Final SQL Query:\n{clean_sql}")
            return True, clean_sql

        except Exception as e:
            import traceback
            error_msg = f"Image-to-SQL workflow error: {e}"
            log(error_msg)
            log(traceback.format_exc())
            return False, error_msg

    # --- Chat Methods (V4) ---
    def run_chat_message(self, message: str, chat_history: list = None) -> Tuple[bool, str]:
        """
        Process a text-only chat message.
        Uses the Coder model for SQL generation (same as Ask Data tab).
        Includes chat history for context.
        """
        log("--- Orchestrator: Processing chat message ---")
        
        try:
            # Get database schema for context
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            
            # Build conversation context from history
            conversation_context = self._build_conversation_context(chat_history)
            
            # Check if the message is asking for SQL/data analysis
            needs_sql = self._message_needs_sql(message)
            
            if needs_sql:
                # Use the CODER model with the strong SQL prompt (same as Ask Data tab)
                log("Chat message requires SQL - using Coder agent with full SQL prompt")
                
                # Build the enhanced SQL prompt with conversation context
                full_query = message
                if conversation_context:
                    full_query = f"Previous conversation context:\n{conversation_context}\n\nCurrent request: {message}"
                
                sql_prompt = prompt_builder.build_sql_prompt(full_query, schema_info)
                
                # Use CODER model for SQL generation
                coder_client = self._create_coder_client()
                sql_response = coder_client.generate_response(sql_prompt)
                
                if "Error:" in sql_response:
                    return False, sql_response
                
                # Clean and format the response
                clean_sql = sql_response.replace("```sql", "").replace("```", "").strip()
                
                # Wrap in conversational response with SQL block
                response = f"Based on your request, here's the SQL query:\n\n```sql\n{clean_sql}\n```\n\nYou can execute this query to see the results on the map."
                return True, response
            else:
                # General conversation - use interpreter for conversational response
                log("Chat message is conversational - using Interpreter agent")
                chat_prompt = prompt_builder.build_chat_sql_prompt(message, schema_info, conversation_context)
                
                interpreter_client = self._create_interpreter_client()
                response = interpreter_client.generate_response(chat_prompt)
                
                if "Error:" in response:
                    return False, response
                
                return True, response
            
        except Exception as e:
            error_msg = f"Chat error: {e}"
            log(error_msg)
            return False, error_msg
    
    def run_chat_with_image(self, message: str, image_path: str, chat_history: list = None) -> Tuple[bool, str]:
        """
        Process a chat message with an attached image.
        Uses DUAL-AGENT flow:
        1. Interpreter (vision) model extracts workflow/criteria from image WITH schema context
        2. Coder model generates SQL from the extracted information
        """
        log(f"--- Orchestrator: Processing chat with image (Dual-Agent): {image_path} ---")
        
        try:
            # Encode image
            base64_image = image_utils.encode_image_to_base64(image_path)
            if "Error:" in base64_image:
                return False, base64_image
            
            # Get database schema for context - CRITICAL for both agents
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            
            if "Error:" in schema_info:
                return False, f"Database error: {schema_info}"
            
            # Build conversation context from history
            conversation_context = self._build_conversation_context(chat_history)
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 1: INTERPRETER AGENT - Extract information from image
            #         WITH SCHEMA CONTEXT so it maps to actual tables/columns
            # ═══════════════════════════════════════════════════════════════
            log("Step 1: Using Interpreter (vision) model to analyze image WITH schema context...")
            
            interpreter_prompt = f"""You are an expert GIS/PostGIS analyst. Analyze this image and map its contents to the available database schema.

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA (Use these EXACT table and column names):
═══════════════════════════════════════════════════════════════════════════════
{schema_info}

═══════════════════════════════════════════════════════════════════════════════
{f"PREVIOUS CONVERSATION:{chr(10)}{conversation_context}{chr(10)}" if conversation_context else ""}
USER'S MESSAGE: {message}
═══════════════════════════════════════════════════════════════════════════════

YOUR TASK - Analyze the image and create a DETAILED MAPPING:

1. **IDENTIFY WHAT THE IMAGE SHOWS:**
   - Workflow diagram, flowchart, map, criteria list, etc.

2. **EXTRACT ALL CRITERIA AND MAP TO SCHEMA:**
   For EACH criterion in the image, specify:
   - The criterion as stated in the image
   - Which TABLE from the schema it applies to
   - Which COLUMN(s) to use
   - The comparison operator and value
   - Whether it's ATTRIBUTE-based or SPATIAL

   Example format:
   ```
   Criterion: "population greater than 50,000"
   → Table: schema.counties
   → Column: pop_total (or similar from schema)
   → Condition: pop_total > 50000
   → Type: ATTRIBUTE
   ```

3. **IDENTIFY SPATIAL OPERATIONS:**
   For any distance/proximity criteria:
   - Source layer (from schema)
   - Target layer (from schema)
   - Distance value and units
   - Spatial relationship (within, intersects, etc.)

   Example:
   ```
   Criterion: "within 10 miles of interstate"
   → Source: schema.cities (geometry column: geom)
   → Target: schema.interstates (geometry column: geom)
   → Distance: 10 miles = 16093.4 meters
   → Operation: ST_DWithin with ST_Transform to projected CRS
   ```

4. **DETERMINE LOGICAL FLOW:**
   - Order of operations (filter counties first, then cities, then spatial)
   - How criteria combine (AND/OR)
   - Expected intermediate and final results

BE PRECISE - use the EXACT table and column names from the schema above.
If a criterion mentions something not clearly in the schema, note the closest match or flag it as unclear."""

            interpreter_client = self._create_interpreter_client()
            image_analysis = interpreter_client.generate_vision_response(interpreter_prompt, base64_image)
            
            if "Error:" in image_analysis:
                return False, image_analysis
            
            log(f"Interpreter analysis (with schema mapping):\n{image_analysis[:500]}...")
            
            # Check if SQL generation is needed
            needs_sql = self._message_needs_sql(message) or self._analysis_suggests_sql(image_analysis)
            
            if needs_sql:
                # ═══════════════════════════════════════════════════════════════
                # STEP 2: CODER AGENT - Generate SQL from schema-mapped analysis
                # ═══════════════════════════════════════════════════════════════
                log("Step 2: Using Coder model to generate SQL from schema-mapped analysis...")
                
                # Build SQL prompt with the detailed schema-mapped analysis
                sql_query_from_image = f"""Generate SQL based on this detailed image analysis that has been mapped to the database schema.

═══════════════════════════════════════════════════════════════════════════════
IMAGE ANALYSIS WITH SCHEMA MAPPING:
═══════════════════════════════════════════════════════════════════════════════
{image_analysis}

═══════════════════════════════════════════════════════════════════════════════
USER'S REQUEST: {message}
═══════════════════════════════════════════════════════════════════════════════

IMPORTANT:
- Use the EXACT table and column names identified in the analysis above
- Follow the logical flow/order of operations specified
- Include ALL criteria - do not skip any
- Use CTEs for multi-step operations
- For distance calculations, use ST_Transform to projected CRS (EPSG:2163 for USA)
- Include geometry column in final SELECT"""

                sql_prompt = prompt_builder.build_sql_prompt(sql_query_from_image, schema_info)
                
                # Use CODER model for SQL generation
                coder_client = self._create_coder_client()
                sql_response = coder_client.generate_response(sql_prompt)
                
                if "Error:" in sql_response:
                    return False, sql_response
                
                # Clean the SQL
                clean_sql = sql_response.replace("```sql", "").replace("```", "").strip()
                
                # Combine interpreter analysis with SQL in response
                response = f"""**Image Analysis (Schema-Mapped):**
{image_analysis}

---

**Generated SQL Query:**
```sql
{clean_sql}
```

Click "Execute SQL" to run this query and see the results on the map."""
                
                return True, response
            else:
                # No SQL needed - just return the image analysis
                return True, image_analysis
            
        except Exception as e:
            import traceback
            error_msg = f"Vision chat error: {e}"
            log(error_msg)
            log(traceback.format_exc())
            return False, error_msg
    
    def _build_conversation_context(self, chat_history: list) -> str:
        """Build a string representation of recent chat history for context"""
        if not chat_history:
            return ""
        
        # Take last 6 messages (3 exchanges) for context
        recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
        
        context_parts = []
        for msg in recent_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:500]  # Truncate long messages
            if msg.get("image"):
                context_parts.append(f"{role}: [Image attached] {content}")
            else:
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def _message_needs_sql(self, message: str) -> bool:
        """Determine if a message is asking for SQL/data analysis"""
        message_lower = message.lower()
        
        sql_keywords = [
            'find', 'show', 'get', 'select', 'query', 'search',
            'where', 'which', 'what', 'how many', 'count', 'list',
            'filter', 'within', 'near', 'distance', 'buffer',
            'intersect', 'overlap', 'contain', 'inside',
            'greater than', 'less than', 'between', 'equal',
            'sql', 'database', 'table', 'layer',
            'analyze', 'analysis', 'criteria', 'condition'
        ]
        
        return any(keyword in message_lower for keyword in sql_keywords)
    
    def _analysis_suggests_sql(self, analysis: str) -> bool:
        """Check if the image analysis suggests SQL should be generated"""
        analysis_lower = analysis.lower()
        
        sql_indicators = [
            'workflow', 'criteria', 'condition', 'threshold',
            'filter', 'select', 'query', 'distance', 'buffer',
            'greater than', 'less than', 'within', 'near',
            'step 1', 'step 2', 'process', 'sequence'
        ]
        
        return any(indicator in analysis_lower for indicator in sql_indicators)