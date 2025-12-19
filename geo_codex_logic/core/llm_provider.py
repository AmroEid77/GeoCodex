# -*- coding: utf-8 -*-
"""
Unified LLM Provider Factory
Supports: OpenAI, Anthropic, Google Gemini, NVIDIA, OpenRouter, Ollama
"""

import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# Ensure vendor path is set up
plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
vendor_dir = os.path.join(plugin_dir, 'vendor')
if vendor_dir not in sys.path:
    sys.path.insert(0, vendor_dir)

try:
    from qgis.core import QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex-LLM', Qgis.Info)
except ImportError:
    log = print

# Fix langchain initialization issues
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


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


@dataclass
class ModelConfig:
    """Configuration for an LLM model"""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 8192


# Default models for each provider
PROVIDER_DEFAULTS = {
    LLMProvider.OPENAI: {
        "vision_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "code_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_vision": "gpt-4o",
        "default_code": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
    },
    LLMProvider.ANTHROPIC: {
        "vision_models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "code_models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        "default_vision": "claude-sonnet-4-20250514",
        "default_code": "claude-sonnet-4-20250514",
        "base_url": "https://api.anthropic.com",
    },
    LLMProvider.GEMINI: {
        "vision_models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "code_models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "default_vision": "gemini-2.0-flash",
        "default_code": "gemini-2.0-flash",
        "base_url": None,
    },
    LLMProvider.NVIDIA: {
        "vision_models": ["mistralai/mistral-medium-3-instruct", "microsoft/phi-3.5-vision-instruct", "meta/llama-3.2-90b-vision-instruct"],
        "code_models": ["deepseek-ai/deepseek-v3.1", "meta/llama-3.3-70b-instruct", "qwen/qwen2.5-coder-32b-instruct"],
        "default_vision": "mistralai/mistral-medium-3-instruct",
        "default_code": "deepseek-ai/deepseek-v3.1",
        "base_url": "https://integrate.api.nvidia.com/v1",
    },
    LLMProvider.OPENROUTER: {
        "vision_models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-pro-vision"],
        "code_models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "deepseek/deepseek-chat", "meta-llama/llama-3.3-70b-instruct"],
        "default_vision": "openai/gpt-4o",
        "default_code": "deepseek/deepseek-chat",
        "base_url": "https://openrouter.ai/api/v1",
    },
    LLMProvider.OLLAMA: {
        "vision_models": ["llava", "llava:13b", "bakllava", "moondream"],
        "code_models": ["codellama", "deepseek-coder", "qwen2.5-coder", "llama3.2", "mistral"],
        "default_vision": "llava",
        "default_code": "deepseek-coder",
        "base_url": "http://localhost:11434",
    },
}


def get_provider_from_string(provider_str: str) -> LLMProvider:
    """Convert UI string to LLMProvider enum"""
    mapping = {
        "OpenAI (ChatGPT)": LLMProvider.OPENAI,
        "Anthropic (Claude)": LLMProvider.ANTHROPIC,
        "Google (Gemini)": LLMProvider.GEMINI,
        "NVIDIA AI": LLMProvider.NVIDIA,
        "OpenRouter": LLMProvider.OPENROUTER,
        "Ollama (Local)": LLMProvider.OLLAMA,
    }
    return mapping.get(provider_str, LLMProvider.OPENAI)


def get_models_for_provider(provider: LLMProvider, for_vision: bool = False) -> List[str]:
    """Get available models for a provider"""
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    if for_vision:
        return defaults.get("vision_models", [])
    return defaults.get("code_models", [])


def get_default_model(provider: LLMProvider, for_vision: bool = False) -> str:
    """Get default model for a provider"""
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    if for_vision:
        return defaults.get("default_vision", "")
    return defaults.get("default_code", "")


def get_default_base_url(provider: LLMProvider) -> Optional[str]:
    """Get default base URL for a provider"""
    return PROVIDER_DEFAULTS.get(provider, {}).get("base_url")


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
    
    @abstractmethod
    def initialize(self) -> Tuple[bool, str]:
        """Initialize the client. Returns (success, message)"""
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a text response"""
        pass
    
    @abstractmethod
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        """Generate a response from an image"""
        pass
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to the API"""
        try:
            response = self.generate_response("Hello. Respond with one word: ready.")
            if response and "Error:" not in response:
                return True, "Connection successful!"
            
            # Check for common error patterns and provide helpful messages
            if "403" in response or "Forbidden" in response or "authorization" in response.lower():
                return False, "Error: [403] Forbidden - Invalid API key or insufficient permissions. Please check your API key."
            elif "401" in response or "Unauthorized" in response:
                return False, "Error: [401] Unauthorized - Invalid API key. Please verify your API key."
            elif "404" in response:
                return False, "Error: [404] Not Found - Check your base URL and model name."
            elif "429" in response:
                return False, "Error: [429] Rate limit exceeded. Please try again later."
            
            return False, response
        except Exception as e:
            error_msg = str(e)
            # Extract meaningful error from exception
            if "403" in error_msg or "Forbidden" in error_msg:
                return False, "Error: [403] Forbidden - Invalid API key or insufficient permissions. Please check your API key."
            elif "401" in error_msg or "Unauthorized" in error_msg:
                return False, "Error: [401] Unauthorized - Invalid API key. Please verify your API key."
            elif "404" in error_msg:
                return False, "Error: [404] Not Found - Check your base URL and model name."
            elif "429" in error_msg:
                return False, "Error: [429] Rate limit exceeded. Please try again later."
            return False, f"Connection failed: {error_msg}"


class OpenAIClient(BaseLLMClient):
    """OpenAI API client (ChatGPT)"""
    
    def initialize(self) -> Tuple[bool, str]:
        try:
            from langchain_openai import ChatOpenAI
            
            self.client = ChatOpenAI(
                model=self.config.model_name,
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://api.openai.com/v1",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            log(f"OpenAI client initialized with model: {self.config.model_name}")
            return True, "OpenAI client initialized"
        except Exception as e:
            log(f"Failed to initialize OpenAI client: {e}")
            return False, str(e)
    
    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            response = self.client.invoke(prompt)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
            response = self.client.invoke(messages)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"


class AnthropicClient(BaseLLMClient):
    """Anthropic API client (Claude)"""
    
    def initialize(self) -> Tuple[bool, str]:
        try:
            from langchain_anthropic import ChatAnthropic
            
            self.client = ChatAnthropic(
                model=self.config.model_name,
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            log(f"Anthropic client initialized with model: {self.config.model_name}")
            return True, "Anthropic client initialized"
        except Exception as e:
            log(f"Failed to initialize Anthropic client: {e}")
            return False, str(e)
    
    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            response = self.client.invoke(prompt)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            error_msg = str(e)
            # Provide more specific error messages for common issues
            if "403" in error_msg or "Forbidden" in error_msg:
                return f"Error: [403] Forbidden - Authorization failed. Please verify your Anthropic API key is valid and has the required permissions."
            elif "401" in error_msg:
                return f"Error: [401] Unauthorized - Invalid Anthropic API key."
            elif "429" in error_msg:
                return f"Error: [429] Rate limit exceeded."
            return f"Error: {e}"
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
            response = self.client.invoke([message])
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"


class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""
    
    def initialize(self) -> Tuple[bool, str]:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            self.client = ChatGoogleGenerativeAI(
                model=self.config.model_name,
                google_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )
            log(f"Gemini client initialized with model: {self.config.model_name}")
            return True, "Gemini client initialized"
        except Exception as e:
            log(f"Failed to initialize Gemini client: {e}")
            return False, str(e)
    
    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            response = self.client.invoke(prompt)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
            response = self.client.invoke([message])
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"


class NVIDIAClient(BaseLLMClient):
    """NVIDIA AI Endpoints client"""
    
    def initialize(self) -> Tuple[bool, str]:
        try:
            import certifi
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
            
            cert_path = certifi.where()
            log(f"Using certificate bundle from: {cert_path}")
            
            # Handle SSL environment variables
            ssl_env_vars = {}
            for var_name in ['SSL_CERT_FILE', 'SSL_CERT_DIR', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE']:
                if var_name in os.environ:
                    ssl_env_vars[var_name] = os.environ.pop(var_name)
            
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            
            try:
                self.client = ChatNVIDIA(
                    model=self.config.model_name,
                    api_key=self.config.api_key,
                    verify_ssl=cert_path,
                    temperature=self.config.temperature,
                    top_p=0.7,
                    max_completion_tokens=self.config.max_tokens,
                )
                log(f"NVIDIA client initialized with model: {self.config.model_name}")
                return True, "NVIDIA client initialized"
            finally:
                for var_name, var_value in ssl_env_vars.items():
                    os.environ[var_name] = var_value
                    
        except Exception as e:
            log(f"Failed to initialize NVIDIA client: {e}")
            return False, str(e)
    
    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            response = self.client.invoke(prompt)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
            response = self.client.invoke(messages)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client"""
    
    def initialize(self) -> Tuple[bool, str]:
        try:
            from langchain_openai import ChatOpenAI
            
            self.client = ChatOpenAI(
                model=self.config.model_name,
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://openrouter.ai/api/v1",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                default_headers={
                    "HTTP-Referer": "https://github.com/AmroEid77/GeoCodex",
                    "X-Title": "GeoCodex QGIS Plugin"
                }
            )
            log(f"OpenRouter client initialized with model: {self.config.model_name}")
            return True, "OpenRouter client initialized"
        except Exception as e:
            log(f"Failed to initialize OpenRouter client: {e}")
            return False, str(e)
    
    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            response = self.client.invoke(prompt)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
            response = self.client.invoke(messages)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"


class OllamaClient(BaseLLMClient):
    """Ollama local client"""
    
    def initialize(self) -> Tuple[bool, str]:
        try:
            # Debug: Log which langchain_core is being used
            import langchain_core
            log(f"DEBUG: langchain_core loaded from: {langchain_core.__file__}")
            
            # Check if ensure_id exists in our vendor version
            try:
                from langchain_core.utils.utils import ensure_id
                log(f"DEBUG: ensure_id successfully imported")
            except ImportError as ie:
                log(f"DEBUG: Cannot import ensure_id: {ie}")
                # Try to check what's in utils
                from langchain_core.utils import utils as utils_module
                log(f"DEBUG: utils module has: {[x for x in dir(utils_module) if not x.startswith('_')][:20]}")
            
            from langchain_ollama import ChatOllama
            
            base_url = self.config.base_url or "http://localhost:11434"
            log(f"Attempting to create Ollama client with model: {self.config.model_name} at {base_url}")
            
            self.client = ChatOllama(
                model=self.config.model_name,
                base_url=base_url,
                temperature=self.config.temperature,
            )
            
            if self.client is None:
                log("Ollama client creation returned None")
                return False, "Ollama client creation failed - returned None"
            
            log(f"Ollama client initialized with model: {self.config.model_name} at {base_url}")
            return True, "Ollama client initialized"
        except ImportError as e:
            log(f"Failed to import langchain_ollama: {e}")
            return False, f"langchain_ollama not installed: {e}"
        except Exception as e:
            import traceback
            log(f"Failed to initialize Ollama client: {e}")
            log(traceback.format_exc())
            return False, str(e)
    
    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            response = self.client.invoke(prompt)
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"
    
    def generate_vision_response(self, prompt: str, base64_image: str) -> str:
        if not self.client:
            return "Error: Client not initialized"
        try:
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
            response = self.client.invoke([message])
            return response.content.strip() if response and response.content else "Error: Empty response"
        except Exception as e:
            return f"Error: {e}"


def create_llm_client(config: ModelConfig) -> BaseLLMClient:
    """Factory function to create the appropriate LLM client"""
    client_map = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.ANTHROPIC: AnthropicClient,
        LLMProvider.GEMINI: GeminiClient,
        LLMProvider.NVIDIA: NVIDIAClient,
        LLMProvider.OPENROUTER: OpenRouterClient,
        LLMProvider.OLLAMA: OllamaClient,
    }
    
    client_class = client_map.get(config.provider)
    if not client_class:
        raise ValueError(f"Unsupported provider: {config.provider}")
    
    client = client_class(config)
    success, message = client.initialize()
    
    if not success:
        log(f"Warning: Client initialization failed: {message}")
    
    return client
