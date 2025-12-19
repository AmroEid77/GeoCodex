# -*- coding: utf-8 -*-
"""
WorkflowOrchestrator - Manages the execution of the plugin's core workflows
Supports dual-model configuration: Interpreter (vision) and Coder (SQL generation)
"""

import re
from datetime import datetime
from typing import Dict, Tuple, Optional
from .core.llm_client import LLMClient
from .core.db_connector import DBConnector
from .utils import prompt_builder
from .utils import image_utils
from .utils.error_handler import ErrorHandler
from .agents.coder_agent import CoderAgent
from .agents.interpreter_agent import InterpreterAgent

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
        self._layer_counter = 0  # Counter for unique layer names
        
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
    
    def _get_coder_agent(self) -> CoderAgent:
        """Get or create a Coder Agent instance"""
        if not hasattr(self, '_coder_agent'):
            coder_client = self._create_coder_client()
            self._coder_agent = CoderAgent(coder_client)
        return self._coder_agent
    
    def _get_interpreter_agent(self) -> InterpreterAgent:
        """Get or create an Interpreter Agent instance"""
        if not hasattr(self, '_interpreter_agent'):
            interpreter_client = self._create_interpreter_client()
            self._interpreter_agent = InterpreterAgent(interpreter_client)
        return self._interpreter_agent
    
    def _generate_layer_name(self, sql_query: str = None, user_query: str = None, context: str = None) -> str:
        """
        Generate a smart, descriptive layer name based on the query.
        
        Args:
            sql_query: The SQL query being executed (optional)
            user_query: The original user's natural language query (optional)
            context: Additional context (e.g., 'Image Analysis', 'Chat') (optional)
            
        Returns:
            A unique, descriptive layer name
        """
        self._layer_counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Combine counter and timestamp for better uniqueness
        unique_suffix = f"{self._layer_counter}_{timestamp}"
        
        # Try to extract a meaningful name from user query first
        if user_query:
            name = self._extract_name_from_nl_query(user_query)
            if name:
                return f"{name}_{unique_suffix}"
        
        # Fall back to SQL analysis
        if sql_query:
            name = self._extract_name_from_sql(sql_query)
            if name:
                return f"{name}_{unique_suffix}"
        
        # Use context if provided
        if context:
            return f"{context}_{unique_suffix}"
        
        # Final fallback
        return f"Query_{unique_suffix}"
    
    def _extract_name_from_nl_query(self, query: str) -> Optional[str]:
        """
        Extract a descriptive name from natural language query.
        
        Examples:
        - "Find all cities with population over 100000" → "Cities_Pop_Over_100k"
        - "Show me counties in California" → "Counties_California"
        - "Buffer roads by 500 meters" → "Roads_Buffer_500m"
        """
        query_lower = query.lower()
        
        # Extract key entities and operations
        entities = []
        operations = []
        
        # Common GIS entities
        entity_keywords = {
            'cities': 'Cities', 'city': 'Cities',
            'counties': 'Counties', 'county': 'Counties',
            'states': 'States', 'state': 'States',
            'roads': 'Roads', 'road': 'Roads',
            'highways': 'Highways', 'highway': 'Highways',
            'rivers': 'Rivers', 'river': 'Rivers',
            'lakes': 'Lakes', 'lake': 'Lakes',
            'parks': 'Parks', 'park': 'Parks',
            'buildings': 'Buildings', 'building': 'Buildings',
            'parcels': 'Parcels', 'parcel': 'Parcels',
            'points': 'Points', 'point': 'Points',
            'polygons': 'Polygons', 'polygon': 'Polygons',
            'lines': 'Lines', 'line': 'Lines'
        }
        
        # Find entities
        for keyword, name in entity_keywords.items():
            if keyword in query_lower:
                if name not in entities:
                    entities.append(name)
        
        # Extract operations
        if any(kw in query_lower for kw in ['buffer', 'buffered']):
            operations.append('Buffer')
        if any(kw in query_lower for kw in ['intersect', 'intersection']):
            operations.append('Intersect')
        if any(kw in query_lower for kw in ['within', 'inside']):
            operations.append('Within')
        if any(kw in query_lower for kw in ['near', 'close', 'distance']):
            operations.append('Near')
        if any(kw in query_lower for kw in ['population', 'pop']):
            operations.append('Pop')
        if any(kw in query_lower for kw in ['area', 'size']):
            operations.append('Area')
        
        # Extract numbers (for constraints)
        numbers = re.findall(r'\b(\d+(?:k|m|km|mi|miles|meters)?)', query_lower)
        
        # Build name
        parts = []
        
        # Add entities
        if entities:
            parts.append('_'.join(entities[:2]))  # Max 2 entities
        
        # Add operations
        if operations:
            parts.extend(operations[:2])  # Max 2 operations
        
        # Add significant numbers
        if numbers:
            # Clean up numbers
            num_str = numbers[0].replace('k', 'k').replace('m', 'm')
            parts.append(num_str)
        
        if parts:
            return '_'.join(parts)
        
        return None
    
    def _extract_name_from_sql(self, sql: str) -> Optional[str]:
        """
        Extract a descriptive name from SQL query.
        
        Examples:
        - "SELECT * FROM cities WHERE..." → "Cities_Query"
        - "SELECT name, pop FROM counties..." → "Counties_Data"
        """
        sql_upper = sql.upper()
        
        # Extract table names from FROM clause (handle schema prefix)
        from_match = re.search(r'FROM\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)', sql_upper, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1).lower()
            # Clean up common prefixes/suffixes
            table_name = table_name.replace('tbl_', '').replace('_tbl', '')
            # Capitalize
            table_name = table_name.capitalize()
            
            # Determine operation type
            if 'ST_BUFFER' in sql_upper:
                return f"{table_name}_Buffer"
            elif 'ST_INTERSECTS' in sql_upper or 'ST_INTERSECTION' in sql_upper:
                return f"{table_name}_Intersect"
            elif 'ST_WITHIN' in sql_upper or 'ST_DWITHIN' in sql_upper:
                return f"{table_name}_Within"
            elif 'ST_DISTANCE' in sql_upper:
                return f"{table_name}_Distance"
            elif 'COUNT' in sql_upper:
                return f"{table_name}_Count"
            elif 'SUM' in sql_upper or 'AVG' in sql_upper:
                return f"{table_name}_Stats"
            else:
                return f"{table_name}_Query"
        
        return None

    # --- V2 Methods ---
    def run_nl_to_sql_workflow(self, user_query: str) -> Tuple[bool, str]:
        """
        Convert natural language query to SQL.
        Uses the Coder model for SQL generation.
        """
        log("--- Orchestrator: Starting NL-to-SQL workflow ---")
        
        try:
            # Store user query for layer naming
            self._last_user_query = user_query
            
            # Get database schema for context
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            if "Error:" in schema_info:
                return False, schema_info
            
            # Use the CoderAgent for SQL generation
            coder_agent = self._get_coder_agent()
            success, sql_query = coder_agent.generate_sql_from_nl(user_query, schema_info)
            
            if not success:
                return False, sql_query
            
            return True, sql_query
            
        except Exception as e:
            return ErrorHandler.handle_exception(e, "NL-to-SQL workflow")

    def run_sql_to_layer_workflow(self, sql_query: str, layer_name: str = None) -> Tuple[bool, str]:
        """
        Execute SQL query and load results as a QGIS layer.
        
        Args:
            sql_query: SQL query to execute
            layer_name: Optional custom layer name. If None, generates a smart name.
        """
        log("--- Orchestrator: Starting SQL-to-Layer workflow ---")
        
        try:
            sql_query = sql_query.strip().rstrip(';')
            
            # Generate smart layer name if not provided
            if not layer_name:
                user_query = getattr(self, '_last_user_query', None)
                layer_name = self._generate_layer_name(
                    sql_query=sql_query,
                    user_query=user_query
                )
                log(f"Generated layer name: {layer_name}")
            
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

    def run_sql_with_auto_fix(self, sql_query: str, layer_name: str = None, max_retries: int = 3, user_query: str = None) -> Tuple[bool, str, str]:
        """
        Execute SQL with automatic error correction.
        
        If execution fails, sends the error back to the Coder LLM to fix the SQL.
        Retries up to max_retries times.
        
        Args:
            sql_query: SQL query to execute
            layer_name: Optional custom layer name. If None, generates a smart name.
            max_retries: Maximum number of retry attempts
            user_query: Original user's natural language query (for better layer naming)
        
        Returns:
            Tuple of (success, message, final_sql)
        """
        log(f"--- Orchestrator: SQL execution with auto-fix (max {max_retries} retries) ---")
        
        # Store user query for layer naming
        if user_query:
            self._last_user_query = user_query
        
        # Generate smart layer name if not provided
        if not layer_name:
            layer_name = self._generate_layer_name(
                sql_query=sql_query,
                user_query=user_query or getattr(self, '_last_user_query', None)
            )
            log(f"Generated layer name: {layer_name}")
        
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
            success, result, error_context = self._try_execute_sql(current_sql, layer_name)
            
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
                "error": error_msg,
                "error_context": error_context
            })
            
            log(f"Attempt {attempt} failed: {error_msg}")
            if error_context:
                log(f"Error type: {error_context.get('error_type', 'unknown')}")
            
            # If we've exhausted retries, return failure
            if attempt > max_retries:
                log(f"All {max_retries + 1} attempts failed. Giving up.")
                break
            
            # Try to fix the SQL using LLM with full error context
            log(f"Sending error with full context to Coder Agent for correction...")
            fix_success, fixed_sql = self._fix_sql_with_llm(
                current_sql, error_msg, schema_info, error_history, error_context
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
    
    def _try_execute_sql(self, sql_query: str, layer_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Try to execute SQL and load as layer. Returns (success, message/error, error_context).
        """
        error_context = None
        
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
                # Build comprehensive error context
                error_context = {
                    "error_type": "layer_invalid",
                    "execution_context": "QGIS Vector Layer creation",
                    "error_details": layer.error().message() if layer.error() else "No detailed error available",
                    "uri": uri.uri(False),
                    "wrapped_sql": wrapped_sql
                }
                
                # Try to get more detailed error
                if not error_msg:
                    error_msg = "Layer is invalid (unknown error)"
                else:
                    # Include full error details in context
                    error_context["full_error_message"] = error_msg
                
                return False, error_msg, error_context
            
            # Check if layer has features
            feature_count = layer.featureCount()
            
            QgsProject.instance().addMapLayer(layer)
            return True, f"Layer '{layer_name}' added ({feature_count} features).", None
            
        except Exception as e:
            import traceback
            # Build comprehensive error context for exceptions
            error_context = {
                "error_type": "execution_exception",
                "execution_context": "SQL execution and layer creation",
                "exception_type": type(e).__name__,
                "error_details": str(e),
                "full_traceback": traceback.format_exc()
            }
            return False, str(e), error_context
    
    def _fix_sql_with_llm(
        self, 
        failed_sql: str, 
        error_msg: str, 
        schema_info: str,
        error_history: list,
        full_error_context: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Use the Coder Agent to fix a failed SQL query with full error context.
        
        Returns (success, fixed_sql or error_message)
        """
        try:
            # Use the CoderAgent for SQL fixing with full observability
            coder_agent = self._get_coder_agent()
            success, fixed_sql = coder_agent.fix_sql(
                failed_sql, error_msg, schema_info, error_history, full_error_context
            )
            
            if not success:
                return False, fixed_sql
            
            return True, fixed_sql
            
        except Exception as e:
            return ErrorHandler.handle_exception(e, "SQL fixing")
    
    def _format_error_history(self, error_history: list) -> str:
        """Format error history for display to user"""
        return ErrorHandler.format_error_history(error_history)

    # --- V3 Method ---
    def run_image_to_sql_workflow(self, image_path: str) -> Tuple[bool, str]:
        """
        Execute the Image-to-SQL pipeline.
        
        Uses two models:
        1. Interpreter (vision) model to extract workflow steps from image
        2. Coder model to generate SQL from the workflow steps
        """
        log("--- Orchestrator: Starting Image-to-SQL Pipeline (Dual Model) ---")
        
        # Mark this as image-based for layer naming
        self._last_user_query = "Image Analysis Workflow"
        
        try:
            # Part 1: Image to Text (Interpreter Agent)
            log(f"Step 1: Encoding image at {image_path}")
            base64_image = image_utils.encode_image_to_base64(image_path)
            if "Error:" in base64_image:
                return False, base64_image
            
            log("Step 2: Using Interpreter agent to extract workflow steps...")
            interpreter_agent = self._get_interpreter_agent()
            success, workflow_steps = interpreter_agent.extract_workflow_from_image(base64_image)

            if not success:
                return False, workflow_steps
            log(f"Received workflow steps:\n{workflow_steps}")

            # Part 2: Text to SQL (Coder Agent)
            log("Step 3: Using Coder agent to generate SQL...")
            
            # Get database schema for context
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            if "Error:" in schema_info:
                return False, schema_info
            
            # Use CoderAgent for SQL generation
            coder_agent = self._get_coder_agent()
            success, sql_query = coder_agent.generate_sql_from_steps(workflow_steps, schema_info)

            if not success:
                return False, sql_query

            log(f"Generated Final SQL Query:\n{sql_query}")
            return True, sql_query

        except Exception as e:
            return ErrorHandler.handle_exception(e, "Image-to-SQL workflow")

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
                # Use the CoderAgent with the full SQL prompt (same as Ask Data tab)
                log("Chat message requires SQL - using Coder agent")
                
                # Build the full query with conversation context
                full_query = message
                if conversation_context:
                    full_query = f"Previous conversation context:\n{conversation_context}\n\nCurrent request: {message}"
                
                # Use CoderAgent for SQL generation
                coder_agent = self._get_coder_agent()
                success, sql_response = coder_agent.generate_sql_from_nl(full_query, schema_info)
                
                if not success:
                    return False, sql_response
                
                # Wrap in conversational response with SQL block
                response = f"Based on your request, here's the SQL query:\n\n```sql\n{sql_response}\n```\n\nYou can execute this query to see the results on the map."
                return True, response
            else:
                # General conversation - use interpreter for conversational response
                log("Chat message is conversational - using Interpreter agent")
                interpreter_agent = self._get_interpreter_agent()
                success, response = interpreter_agent.chat_response(
                    message, schema_info, conversation_context
                )
                
                if not success:
                    return False, response
                
                return True, response
            
        except Exception as e:
            return ErrorHandler.handle_exception(e, "Chat processing")
    
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
            log("Step 1: Using Interpreter agent to analyze image WITH schema context...")
            
            interpreter_agent = self._get_interpreter_agent()
            success, image_analysis = interpreter_agent.analyze_image_with_schema(
                base64_image, schema_info, message, conversation_context
            )
            
            if not success:
                return False, image_analysis
            
            log(f"Interpreter analysis (with schema mapping):\n{image_analysis[:500]}...")
            
            # Check if SQL generation is needed
            needs_sql = self._message_needs_sql(message) or self._analysis_suggests_sql(image_analysis)
            
            if needs_sql:
                # ═══════════════════════════════════════════════════════════════
                # STEP 2: CODER AGENT - Generate SQL from schema-mapped analysis
                # ═══════════════════════════════════════════════════════════════
                log("Step 2: Using Coder agent to generate SQL from schema-mapped analysis...")
                
                # Build prompt for SQL generation from image analysis
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

                # Use CoderAgent for SQL generation
                coder_agent = self._get_coder_agent()
                success, sql_response = coder_agent.generate_sql_from_nl(
                    sql_query_from_image, schema_info
                )
                
                if not success:
                    return False, sql_response
                
                # Combine interpreter analysis with SQL in response
                response = f"""**Image Analysis (Schema-Mapped):**
{image_analysis}

---

**Generated SQL Query:**
```sql
{sql_response}
```

Click "Execute SQL" to run this query and see the results on the map."""
                
                return True, response
            else:
                # No SQL needed - just return the image analysis
                return True, image_analysis
            
        except Exception as e:
            return ErrorHandler.handle_exception(e, "Vision chat")
    
    def _build_conversation_context(self, chat_history: list) -> str:
        """
        Build a string representation of FULL chat history for context.
        No truncation - pass everything until provider token limit is hit.
        """
        if not chat_history:
            return ""
        
        # Pass ALL chat history - no artificial limits
        # Let the LLM provider handle token limits naturally
        context_parts = []
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")  # Full content, no truncation
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