from .core.llm_client import LLMClient
from .core.db_connector import DBConnector
from .utils import prompt_builder
from qgis.core import QgsVectorLayer, QgsProject, QgsDataSourceUri, QgsMessageLog, Qgis

class WorkflowOrchestrator:
    """ Manages the execution of the plugin's core workflows. """
    
    def __init__(self, api_key, db_params):
        """
        Initializes the orchestrator with credentials.
        db_params should be a dictionary with host, port, dbname, user, pass.
        """
        self.api_key = api_key
        self.db_params = db_params
        self.log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)

    def run_nl_to_sql_workflow(self, user_query):
        """
        Executes the full Natural Language to SQL generation workflow.
        Returns: (bool, str) -> (success, result_message_or_sql_code)
        """
        self.log("--- Orchestrator: Starting NL-to-SQL workflow ---")
        
        # 1. Get DB Schema
        db_connector = DBConnector(**self.db_params)
        schema_info = db_connector.get_schema_info()
        if "Error:" in schema_info:
            return False, schema_info

        # 2. Build Prompt
        final_prompt = prompt_builder.build_sql_prompt(user_query, schema_info)
        
        # 3. Call LLM
        llm_client = LLMClient(api_key=self.api_key)
        sql_response = llm_client.generate_response(final_prompt)
        
        if "Error:" in sql_response:
            return False, sql_response
            
        clean_sql = sql_response.replace("```sql", "").replace("```", "").strip()
        return True, clean_sql

    def run_sql_to_layer_workflow(self, sql_query, layer_name):
        """
        Executes a SQL query and loads the result as a QGIS layer.
        Returns: (bool, str) -> (success, result_message)
        """
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