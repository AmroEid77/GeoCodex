import os
import sys
from qgis.core import QgsMessageLog, Qgis

# We MUST ensure our vendor path is set up before importing our vendored libraries.
# This makes sure we import the versions we bundled with the plugin.
plugin_dir = os.path.dirname(os.path.dirname(__file__))
vendor_dir = os.path.join(plugin_dir, 'vendor')
if vendor_dir not in sys.path:
    sys.path.insert(0, vendor_dir)

# Now we can safely import our vendored libraries
from dotenv import load_dotenv
import certifi
import httpx
from langchain_nvidia_ai_endpoints import ChatNVIDIA


# Smart .env Loading (remains the same)
if 'qgis' in sys.modules:
    project_root = os.path.dirname(plugin_dir)
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()


class LLMClient:
    """ A client to handle all interactions with the NVIDIA AI Endpoints API. """
    def __init__(self, api_key=None, model_name="deepseek-ai/deepseek-v3.1"):
        log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
        log("--- LLMClient.__init__ started (v3 - Forceful Injection) ---")

        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        log(f"API Key being used: '{self.api_key}'")

        if not self.api_key:
            log("API Key is MISSING. Raising ValueError.")
            raise ValueError("API Key is missing. Not passed and not in environment.")
        
        # Store model_name before using it
        self.model_name = model_name
        
        # --- THE DEFINITIVE FIX ---
        # 1. Get the path to the trusted certificate bundle from our vendored certifi library.
        cert_path = certifi.where()
        log(f"Explicitly using certificate bundle from: {cert_path}")

        # 2. Temporarily remove ALL SSL-related env vars to prevent requests from using them
        ssl_env_vars = {}
        for var_name in ['SSL_CERT_FILE', 'SSL_CERT_DIR', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']:
            if var_name in os.environ:
                ssl_env_vars[var_name] = os.environ.pop(var_name)
                log(f"Temporarily removing {var_name} env var (was set to: {ssl_env_vars[var_name]})")

        # 3. Set REQUESTS_CA_BUNDLE to our certificate path so requests library uses it
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        log(f"Setting REQUESTS_CA_BUNDLE to: {cert_path}")

        try:
            # 4. Create ChatNVIDIA client with explicit certificate path via verify_ssl parameter
            log("Attempting to initialize ChatNVIDIA client with verify_ssl parameter...")
            self.client = ChatNVIDIA(
                model=self.model_name,
                api_key=self.api_key,
                verify_ssl=cert_path,  # Pass certificate bundle path directly
                temperature=0.1,
                top_p=0.7,
                max_completion_tokens=8192,
            )
            log("ChatNVIDIA client initialized SUCCESSFULLY.")
        except Exception as e:
            log(f"CRITICAL: Error initializing ChatNVIDIA client: {e}")
            self.client = None
        finally:
            # Restore the original env var values
            for var_name, var_value in ssl_env_vars.items():
                os.environ[var_name] = var_value

    # ... the rest of the class is unchanged ...
    def test_connection(self):
        # ... this method will now work because self.client will be initialized correctly ...
        log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
        
        if not self.client:
            log("test_connection failed because self.client is None.")
            return False, "Client not initialized."
        
        try:
            log("Attempting to invoke model for connection test...")
            response = self.client.invoke("Hello. Respond with one word: ready.")
            
            if response and response.content:
                log(f"Connection test successful. Response: {response.content}")
                return True, "Connection successful!"
            else:
                log("Connection test failed: Received an empty response.")
                return False, "Received an empty response from the API."
        except Exception as e:
            log(f"Connection test CRITICAL failure: {e}")
            return False, f"Connection failed: {str(e)}"