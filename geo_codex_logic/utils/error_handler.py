# -*- coding: utf-8 -*-
"""
ErrorHandler - Centralized error handling and formatting utility
Provides consistent error handling across the plugin
"""

import traceback
from typing import Tuple, Optional, Dict, List
from enum import Enum

try:
    from qgis.core import QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
    log_error = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Critical)
except ImportError:
    log = print
    log_error = print


class ErrorType(Enum):
    """Error types for categorization"""
    DATABASE = "database"
    SQL_SYNTAX = "sql_syntax"
    SQL_EXECUTION = "sql_execution"
    LLM_API = "llm_api"
    IMAGE_PROCESSING = "image_processing"
    VALIDATION = "validation"
    NETWORK = "network"
    FILE_IO = "file_io"
    UNKNOWN = "unknown"


class ErrorHandler:
    """
    Centralized error handling utility.
    
    Provides:
    - Error categorization
    - Error message formatting
    - Error history tracking
    - User-friendly error descriptions
    """
    
    @staticmethod
    def handle_exception(e: Exception, 
                        context: str = "",
                        log_traceback: bool = True) -> Tuple[bool, str]:
        """
        Handle an exception and return a formatted error message.
        
        Args:
            e: The exception to handle
            context: Context description (e.g., "SQL generation", "Database connection")
            log_traceback: Whether to log the full traceback
            
        Returns:
            Tuple of (False, formatted_error_message)
        """
        error_type = ErrorHandler._categorize_error(e)
        error_msg = ErrorHandler._format_error(e, error_type, context)
        
        # Log the error
        log_error(f"{context}: {error_msg}")
        
        if log_traceback:
            log_error(traceback.format_exc())
        
        return False, error_msg
    
    @staticmethod
    def _categorize_error(e: Exception) -> ErrorType:
        """Categorize error by type."""
        error_str = str(e).lower()
        exception_type = type(e).__name__.lower()
        
        # Database errors
        if any(kw in error_str for kw in ['connection', 'database', 'postgresql', 'postgis']):
            return ErrorType.DATABASE
        
        # SQL errors
        if any(kw in error_str for kw in ['syntax error', 'column', 'table', 'relation']):
            return ErrorType.SQL_SYNTAX
        
        if any(kw in error_str for kw in ['query', 'execute', 'invalid']):
            return ErrorType.SQL_EXECUTION
        
        # LLM/API errors
        if any(kw in error_str for kw in ['api', 'authentication', 'unauthorized', 'rate limit']):
            return ErrorType.LLM_API
        
        # Image processing
        if any(kw in error_str for kw in ['image', 'base64', 'encoding', 'vision']):
            return ErrorType.IMAGE_PROCESSING
        
        # Network errors
        if any(kw in exception_type for kw in ['connection', 'timeout', 'network']):
            return ErrorType.NETWORK
        
        # File I/O
        if any(kw in exception_type for kw in ['ioerror', 'filenotfound']):
            return ErrorType.FILE_IO
        
        return ErrorType.UNKNOWN
    
    @staticmethod
    def _format_error(e: Exception, error_type: ErrorType, context: str) -> str:
        """Format error message for user display."""
        base_msg = str(e)
        
        # Add context if provided
        if context:
            prefix = f"Error during {context}: "
        else:
            prefix = "Error: "
        
        # Add type-specific guidance
        guidance = ErrorHandler._get_error_guidance(error_type, base_msg)
        
        if guidance:
            return f"{prefix}{base_msg}\n\nSuggestion: {guidance}"
        else:
            return f"{prefix}{base_msg}"
    
    @staticmethod
    def _get_error_guidance(error_type: ErrorType, error_msg: str) -> Optional[str]:
        """Get user-friendly guidance based on error type."""
        guidance_map = {
            ErrorType.DATABASE: "Check your database connection settings (host, port, credentials). Ensure the database is running and accessible.",
            ErrorType.SQL_SYNTAX: "There may be a syntax error in the generated SQL. Try regenerating the query or check table/column names.",
            ErrorType.SQL_EXECUTION: "The SQL query is valid but failed to execute. Check data types, constraints, and geometry validity.",
            ErrorType.LLM_API: "Check your API key and network connection. You may have reached rate limits or the service may be unavailable.",
            ErrorType.IMAGE_PROCESSING: "Check that the image file exists and is in a supported format (PNG, JPG, etc.).",
            ErrorType.NETWORK: "Check your internet connection. The LLM service may be temporarily unavailable.",
            ErrorType.FILE_IO: "Check that the file path is correct and you have read/write permissions."
        }
        
        return guidance_map.get(error_type)
    
    @staticmethod
    def format_error_history(error_history: List[Dict]) -> str:
        """
        Format error history for display to user.
        
        Args:
            error_history: List of error dictionaries with 'attempt', 'sql', 'error' keys
            
        Returns:
            Formatted error history string
        """
        if not error_history:
            return "No error history available."
        
        parts = ["**Error History:**\n"]
        
        for h in error_history:
            attempt = h.get('attempt', '?')
            error = h.get('error', 'Unknown error')
            
            # Truncate long errors
            if len(error) > 300:
                error = error[:300] + "..."
            
            parts.append(f"**Attempt {attempt}:**")
            parts.append(f"Error: {error}")
            parts.append("")
        
        return "\n".join(parts)
    
    @staticmethod
    def wrap_operation(operation_name: str, func, *args, **kwargs) -> Tuple[bool, any]:
        """
        Wrap an operation with error handling.
        
        Args:
            operation_name: Name of the operation for context
            func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Tuple of (success, result_or_error_message)
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            return ErrorHandler.handle_exception(e, operation_name)
    
    @staticmethod
    def validate_required_params(params: Dict, required_keys: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that required parameters are present.
        
        Args:
            params: Dictionary of parameters
            required_keys: List of required key names
            
        Returns:
            Tuple of (valid, error_message or None)
        """
        missing = [key for key in required_keys if key not in params or not params[key]]
        
        if missing:
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            log_error(error_msg)
            return False, error_msg
        
        return True, None
