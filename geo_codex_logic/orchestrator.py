from .core.llm_client import LLMClient
from .core.db_connector import DBConnector
from .utils import prompt_builder
from .utils import image_utils
from qgis.core import QgsVectorLayer, QgsProject, QgsDataSourceUri, QgsMessageLog, Qgis

class WorkflowOrchestrator:
    """ Manages the execution of the plugin's core workflows. """
    
    def __init__(self, api_key, db_params):
        self.api_key = api_key
        self.db_params = db_params
        self.log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)

    # --- V2 Methods
    def run_nl_to_sql_workflow(self, user_query):
        
        self.log("--- Orchestrator: Starting NL-to-SQL workflow ---")
        db_connector = DBConnector(**self.db_params)
        schema_info = db_connector.get_schema_info()
        if "Error:" in schema_info: return False, schema_info
        final_prompt = prompt_builder.build_sql_prompt(user_query, schema_info)
        llm_client = LLMClient(api_key=self.api_key)
        sql_response = llm_client.generate_response(final_prompt)
        if "Error:" in sql_response: return False, sql_response
        clean_sql = sql_response.replace("```sql", "").replace("```", "").strip()
        return True, clean_sql

    def run_sql_to_layer_workflow(self, sql_query, layer_name):
        # ... (this method remains exactly the same) ...
        self.log("--- Orchestrator: Starting SQL-to-Layer workflow ---")
        try:
            sql_query = sql_query.strip().rstrip(';')
            uri = QgsDataSourceUri()
            uri.setConnection(self.db_params['host'], self.db_params['port'], self.db_params['dbname'], self.db_params['user'], self.db_params['password'])
            wrapped_sql = f"SELECT ROW_NUMBER() OVER() AS gid, * FROM ({sql_query}) AS subquery"
            uri.setDataSource("", f"({wrapped_sql})", "geom", "", "gid")
            layer = QgsVectorLayer(uri.uri(False), layer_name, "postgres")
            if not layer.isValid():
                error_msg = f"Layer failed to load: {layer.error().summary()}"
                self.log(error_msg)
                return False, error_msg
            QgsProject.instance().addMapLayer(layer)
            msg = f"Success! Layer '{layer_name}' added ({layer.featureCount()} features)."
            self.log(msg)
            return True, msg
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            self.log(error_msg)
            return False, error_msg

    # --- V3 Method---
    def run_image_to_sql_workflow(self, image_path):
        """
        Executes the Image-to-SQL pipeline using direct LangChain calls.
        """
        self.log("--- Orchestrator: Starting Image-to-SQL Pipeline (Pure LangChain) ---")
        try:
            # Part 1: Image to Text (Agent 1: Interpreter)
            self.log(f"Step 1: Encoding image at {image_path}")
            base64_image = image_utils.encode_image_to_base64(image_path)
            if "Error:" in base64_image:
                return False, base64_image
            
            self.log("Step 2: Calling Vision LLM to get workflow steps...")
            vision_llm = LLMClient(api_key=self.api_key, model_name="mistralai/mistral-medium-3-instruct")
            workflow_steps = vision_llm.get_workflow_steps_from_image(base64_image)

            if "Error:" in workflow_steps:
                return False, workflow_steps
            self.log(f"Received workflow steps:\n{workflow_steps}")

            # Part 2: Text to SQL (Agent 2: SQL Coder)
            self.log("Step 3: Calling SQL Code LLM to generate the final query...")
            
            # We need the database schema for context, just like in V2
            db_connector = DBConnector(**self.db_params)
            schema_info = db_connector.get_schema_info()
            if "Error:" in schema_info:
                return False, schema_info
            
            # Build the dedicated prompt for turning steps into SQL
            sql_prompt = prompt_builder.build_sql_from_steps_prompt(workflow_steps, schema_info)
            
            # Use a strong model for complex SQL generation
            code_llm = LLMClient(api_key=self.api_key, model_name="deepseek-ai/deepseek-v3.1")
            
            # Get the final SQL query directly
            sql_query = code_llm.generate_response(sql_prompt)

            if "Error:" in sql_query:
                return False, sql_query

            clean_sql = sql_query.replace("```sql", "").replace("```", "").strip()
            self.log(f"Generated Final SQL Query:\n{clean_sql}")
            return True, clean_sql

        except Exception as e:
            import traceback
            error_msg = f"A workflow error occurred: {e}"
            self.log(error_msg)
            self.log(traceback.format_exc())
            return False, error_msg