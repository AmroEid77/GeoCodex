# -*- coding: utf-8 -*-
"""
LLMClient - Unified interface for all LLM providers
Supports: OpenAI, Anthropic, Google Gemini, NVIDIA, OpenRouter, Ollama
"""

import os
import sys
from typing import Optional, Tuple

try:
    from qgis.core import QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
except ImportError:
    log = print

# We MUST ensure our vendor path is set up before importing our vendored libraries.
plugin_dir = os.path.dirname(os.path.dirname(__file__))
vendor_dir = os.path.join(plugin_dir, 'vendor')
if vendor_dir not in sys.path:
    sys.path.insert(0, vendor_dir)

try:
    import langchain as _lc
    if not hasattr(_lc, "verbose"):
        _lc.verbose = False
    if not hasattr(_lc, "debug"):
        _lc.debug = False
    if not hasattr(_lc, "llm_cache"):
        _lc.llm_cache = None
except Exception:
    pass

# Import from our provider module
from .llm_provider import (
    LLMProvider, ModelConfig, BaseLLMClient, 
    create_llm_client, get_provider_from_string,
    get_default_model, get_default_base_url
)

# Try to load .env for backward compatibility
try:
    from dotenv import load_dotenv
    if 'qgis' in sys.modules:
        project_root = os.path.dirname(plugin_dir)
        dotenv_path = os.path.join(project_root, '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path)
    else:
        load_dotenv()
except ImportError:
    pass


class LLMClient:
    """
    Unified LLM client that supports multiple providers.
    
    Can be initialized in two ways:
    1. Legacy mode (backward compatible): LLMClient(api_key="...", model_name="...")
    2. New mode with provider: LLMClient(provider="openai", api_key="...", model_name="...")
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: Optional[str] = None,
        provider: str = "nvidia",  # Default to NVIDIA for backward compatibility
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192
    ):
        log("--- LLMClient.__init__ started (v4 - Multi-Provider) ---")
        
        # Convert provider string to enum
        if isinstance(provider, str):
            # Check if it's a UI string like "OpenAI (ChatGPT)"
            if "(" in provider:
                self.provider = get_provider_from_string(provider)
            else:
                # Try to match directly
                provider_map = {
                    "openai": LLMProvider.OPENAI,
                    "anthropic": LLMProvider.ANTHROPIC,
                    "gemini": LLMProvider.GEMINI,
                    "nvidia": LLMProvider.NVIDIA,
                    "openrouter": LLMProvider.OPENROUTER,
                    "ollama": LLMProvider.OLLAMA,
                }
                self.provider = provider_map.get(provider.lower(), LLMProvider.NVIDIA)
        else:
            self.provider = provider
        
        log(f"Provider: {self.provider.value}")
        
        # Handle API key - Ollama doesn't need one
        if self.provider == LLMProvider.OLLAMA:
            self.api_key = None
        else:
            self.api_key = api_key or self._get_env_api_key()
            if not self.api_key:
                log("API Key is MISSING. Raising ValueError.")
                raise ValueError(f"API Key is missing for provider {self.provider.value}")
        
        # Set model name - use default if not provided
        self.model_name = model_name or get_default_model(self.provider, for_vision=False)
        log(f"Model: {self.model_name}")
        
        # Set base URL
        self.base_url = base_url or get_default_base_url(self.provider)
        
        # Create the configuration
        config = ModelConfig(
            provider=self.provider,
            model_name=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Create the underlying client
        try:
            self._client: BaseLLMClient = create_llm_client(config)
            self.client = self._client.client  # For backward compatibility
            
            # Check if the underlying client was actually created
            if self._client.client is None:
                log(f"WARNING: Provider client created but underlying client is None")
                # Don't set _client to None - keep it so we can get better error messages
            else:
                log(f"LLMClient initialized successfully with {self.provider.value}")
        except Exception as e:
            log(f"CRITICAL: Error initializing LLM client: {e}")
            import traceback
            log(traceback.format_exc())
            self._client = None
            self.client = None
    
    def _get_env_api_key(self) -> Optional[str]:
        """Get API key from environment variables based on provider"""
        env_var_map = {
            LLMProvider.OPENAI: ["OPENAI_API_KEY"],
            LLMProvider.ANTHROPIC: ["ANTHROPIC_API_KEY"],
            LLMProvider.GEMINI: ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            LLMProvider.NVIDIA: ["NVIDIA_API_KEY"],
            LLMProvider.OPENROUTER: ["OPENROUTER_API_KEY"],
            LLMProvider.OLLAMA: [],
        }
        
        for env_var in env_var_map.get(self.provider, []):
            key = os.getenv(env_var)
            if key:
                log(f"Found API key in environment variable: {env_var}")
                return key
        return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to the LLM provider"""
        log("Testing connection...")
        
        if not self._client:
            log("test_connection failed because _client wrapper is None.")
            return False, "Client wrapper not initialized."
        
        if not self._client.client:
            log("test_connection failed because underlying client is None.")
            return False, f"Underlying {self.provider.value} client not initialized. Check if the service is running."
        
        return self._client.test_connection()

    def generate_response(self, prompt_text: str) -> str:
        """
        Sends a single prompt to the LLM and gets a complete response.

        Args:
            prompt_text (str): The full prompt to send to the model.

        Returns:
            str: The LLM's response content, or an error message.
        """
        if not self._client:
            log("generate_response failed because client is None.")
            return "Error: Client not initialized."
        
        return self._client.generate_response(prompt_text)
    
    def get_workflow_steps_from_image(self, base64_image: str) -> str:
        """
        Sends an image to the vision model and asks it to generate workflow steps.
        
        Args:
            base64_image: A Base64 encoded string of the workflow image.

        Returns:
            A string containing the textual workflow steps, or an error message.
        """
        if not self._client:
            return "Error: Vision client not initialized."

        prompt = """You are a GIS workflow expert. Analyze this image and describe the sequence of QGIS operations shown.
Break it down into a numbered list of simple, unambiguous actions.
For example:
1. Load the 'rivers' shapefile.
2. Apply a 100-meter buffer to the 'rivers' layer.
3. Intersect the 'buffered rivers' layer with the 'land parcels' layer."""

        return self._client.generate_vision_response(prompt, base64_image)
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        """
        Send a prompt with an image to the vision model.
        
        Args:
            prompt: The text prompt to send with the image.
            base64_image: A Base64 encoded string of the image.

        Returns:
            The LLM's response content, or an error message.
        """
        if not self._client:
            return "Error: Vision client not initialized."
        
        return self._client.generate_vision_response(prompt, base64_image)