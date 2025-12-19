# -*- coding: utf-8 -*-
"""
InterpreterAgent - Specialized agent for image analysis and natural language understanding
Handles vision-based workflows, image interpretation, and conversational AI
"""

from typing import Tuple, Optional

try:
    from qgis.core import QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
except ImportError:
    log = print


class InterpreterAgent:
    """
    Agent specialized in image interpretation and natural language understanding.
    
    Responsibilities:
    - Extract workflow steps from images (diagrams, flowcharts, maps)
    - Analyze images with schema context for database mapping
    - Handle conversational interactions
    - Provide explanations and contextual responses
    """
    
    def __init__(self, llm_client):
        """
        Initialize the Interpreter Agent.
        
        Args:
            llm_client: An LLMClient instance with vision capabilities
        """
        self.llm_client = llm_client
        log("InterpreterAgent initialized")
    
    def extract_workflow_from_image(self, base64_image: str) -> Tuple[bool, str]:
        """
        Extract workflow steps from an image (diagram, flowchart, etc.).
        
        Args:
            base64_image: Base64 encoded image string
            
        Returns:
            Tuple of (success, workflow_steps or error_message)
        """
        log("InterpreterAgent: Extracting workflow from image")
        
        try:
            response = self.llm_client.get_workflow_steps_from_image(base64_image)
            
            if "Error:" in response:
                return False, response
            
            log(f"InterpreterAgent: Workflow extracted successfully")
            return True, response
            
        except Exception as e:
            error_msg = f"Workflow extraction error: {e}"
            log(error_msg)
            return False, error_msg
    
    def analyze_image_with_schema(self, 
                                   base64_image: str, 
                                   schema_info: str,
                                   user_message: str = "",
                                   conversation_context: str = "") -> Tuple[bool, str]:
        """
        Analyze an image with database schema context to map visual elements to schema.
        
        Args:
            base64_image: Base64 encoded image string
            schema_info: Database schema information
            user_message: User's accompanying message (optional)
            conversation_context: Previous conversation context (optional)
            
        Returns:
            Tuple of (success, schema_mapped_analysis or error_message)
        """
        log("InterpreterAgent: Analyzing image with schema context")
        
        try:
            prompt = self._build_schema_mapping_prompt(
                schema_info, user_message, conversation_context
            )
            response = self.llm_client.generate_vision_response(prompt, base64_image)
            
            if "Error:" in response:
                return False, response
            
            log("InterpreterAgent: Schema-mapped analysis complete")
            return True, response
            
        except Exception as e:
            error_msg = f"Schema mapping error: {e}"
            log(error_msg)
            return False, error_msg
    
    def chat_response(self, 
                     message: str, 
                     schema_info: Optional[str] = None,
                     conversation_context: Optional[str] = None) -> Tuple[bool, str]:
        """
        Generate a conversational response.
        
        Args:
            message: User's message
            schema_info: Optional database schema for context
            conversation_context: Optional previous conversation
            
        Returns:
            Tuple of (success, response or error_message)
        """
        log("InterpreterAgent: Generating chat response")
        
        try:
            prompt = self._build_chat_prompt(message, schema_info, conversation_context)
            response = self.llm_client.generate_response(prompt)
            
            if "Error:" in response:
                return False, response
            
            return True, response
            
        except Exception as e:
            error_msg = f"Chat response error: {e}"
            log(error_msg)
            return False, error_msg
    
    def _build_workflow_extraction_prompt(self) -> str:
        """
        Build prompt for extracting workflow steps from images.
        """
        return """Analyze this image and extract the workflow or process it describes.

The image may contain:
- Flowcharts or process diagrams
- Workflow steps
- Criteria or conditions
- Spatial analysis workflows
- GIS operations

Your task:
1. Identify all steps in the workflow
2. Extract any criteria, conditions, or thresholds
3. Note the sequence and dependencies
4. Describe any spatial operations or relationships
5. Present the workflow in a clear, structured format

Provide a detailed, step-by-step description of what you see."""
    
    def _build_schema_mapping_prompt(self, 
                                      schema_info: str,
                                      user_message: str,
                                      conversation_context: str) -> str:
        """
        Build prompt for analyzing image with schema mapping.
        """
        context_section = f"""
═══════════════════════════════════════════════════════════════════════════════
PREVIOUS CONVERSATION:
═══════════════════════════════════════════════════════════════════════════════
{conversation_context}
""" if conversation_context else ""
        
        message_section = f"""
═══════════════════════════════════════════════════════════════════════════════
USER'S MESSAGE: {user_message}
═══════════════════════════════════════════════════════════════════════════════
""" if user_message else ""
        
        return f"""You are an expert GIS/PostGIS analyst. Analyze this image and map its contents to the available database schema.

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA (Use these EXACT table and column names):
═══════════════════════════════════════════════════════════════════════════════
{schema_info}
{context_section}
{message_section}

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
   - Order of operations (filter first, then spatial, etc.)
   - How criteria combine (AND/OR)
   - Expected intermediate and final results

BE PRECISE - use the EXACT table and column names from the schema above.
If a criterion mentions something not clearly in the schema, note the closest match or flag it as unclear."""
    
    def _build_chat_prompt(self, 
                           message: str,
                           schema_info: Optional[str],
                           conversation_context: Optional[str]) -> str:
        """
        Build prompt for conversational chat.
        """
        schema_section = f"""
═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA:
═══════════════════════════════════════════════════════════════════════════════
{schema_info}
""" if schema_info else ""
        
        context_section = f"""
═══════════════════════════════════════════════════════════════════════════════
PREVIOUS CONVERSATION:
═══════════════════════════════════════════════════════════════════════════════
{conversation_context}
""" if conversation_context else ""
        
        return f"""You are a helpful GIS/PostGIS assistant. Provide a clear, informative response to the user's message.
{schema_section}
{context_section}
═══════════════════════════════════════════════════════════════════════════════
USER'S MESSAGE:
═══════════════════════════════════════════════════════════════════════════════
{message}

Provide a helpful, conversational response. If the question relates to data analysis or querying,
explain the approach clearly."""
