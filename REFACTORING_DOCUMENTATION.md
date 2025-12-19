# GeoCodex Refactoring - Agent Architecture Documentation

## Overview

This document describes the refactored agent architecture for the GeoCodex QGIS plugin. The refactoring separates concerns into specialized agents and utilities, making the codebase more maintainable, testable, and extensible.

## Architecture

### 1. Agent Pattern

The plugin now uses a **dual-agent architecture**:

- **CoderAgent**: Specialized in SQL code generation, fixing, and optimization
- **InterpreterAgent**: Specialized in image analysis, natural language understanding, and conversational AI

Both agents are managed by the `WorkflowOrchestrator`, which coordinates their activities.

### 2. File Structure

```
geo_codex_logic/
├── agents/
│   ├── __init__.py          # Exports CoderAgent, InterpreterAgent
│   ├── coder_agent.py       # SQL generation and fixing
│   └── interpreter_agent.py # Image analysis and NLU
├── utils/
│   ├── __init__.py          # Exports ErrorHandler, ErrorType
│   └── error_handler.py     # Centralized error handling
└── orchestrator.py          # Workflow coordination
```

## Component Details

### CoderAgent (`agents/coder_agent.py`)

**Purpose**: Handle all SQL-related tasks including generation, fixing, and optimization.

**Key Methods**:

```python
class CoderAgent:
    def __init__(self, llm_client):
        """Initialize with an LLM client configured for code generation"""

    def generate_sql_from_nl(self, user_query: str, schema_info: str) -> Tuple[bool, str]:
        """Generate SQL from natural language query"""

    def generate_sql_from_steps(self, workflow_steps: str, schema_info: str) -> Tuple[bool, str]:
        """Generate SQL from structured workflow steps (e.g., from image analysis)"""

    def fix_sql(self, failed_sql: str, error_msg: str, schema_info: str,
                error_history: Optional[List[Dict]] = None) -> Tuple[bool, str]:
        """Fix a failed SQL query based on error message"""
```

**Features**:

- Automatic SQL extraction from LLM responses (handles code blocks, plain text)
- Context-aware prompt building for different scenarios
- Error history tracking for iterative fixes
- PostGIS/PostgreSQL optimization

**Usage Example**:

```python
from geo_codex_logic.agents.coder_agent import CoderAgent
from geo_codex_logic.core.llm_client import LLMClient

# Create LLM client
llm_client = LLMClient(provider="openai", api_key="your-key", model_name="gpt-4")

# Create agent
coder = CoderAgent(llm_client)

# Generate SQL
success, sql = coder.generate_sql_from_nl(
    "Find all cities with population over 100000",
    schema_info
)

if success:
    print(f"Generated SQL: {sql}")
```

### InterpreterAgent (`agents/interpreter_agent.py`)

**Purpose**: Handle image analysis, natural language understanding, and conversational interactions.

**Key Methods**:

```python
class InterpreterAgent:
    def __init__(self, llm_client):
        """Initialize with a vision-capable LLM client"""

    def extract_workflow_from_image(self, base64_image: str) -> Tuple[bool, str]:
        """Extract workflow steps from an image (diagram, flowchart, etc.)"""

    def analyze_image_with_schema(self, base64_image: str, schema_info: str,
                                   user_message: str = "",
                                   conversation_context: str = "") -> Tuple[bool, str]:
        """Analyze image and map contents to database schema"""

    def chat_response(self, message: str, schema_info: Optional[str] = None,
                     conversation_context: Optional[str] = None) -> Tuple[bool, str]:
        """Generate conversational response"""
```

**Features**:

- Vision-based workflow extraction
- Schema-aware image analysis
- Conversational context management
- Multi-modal understanding (text + images)

**Usage Example**:

```python
from geo_codex_logic.agents.interpreter_agent import InterpreterAgent
from geo_codex_logic.core.llm_client import LLMClient

# Create vision-capable LLM client
llm_client = LLMClient(provider="openai", api_key="your-key", model_name="gpt-4-vision")

# Create agent
interpreter = InterpreterAgent(llm_client)

# Analyze image with schema context
success, analysis = interpreter.analyze_image_with_schema(
    base64_image,
    schema_info,
    user_message="What does this workflow show?",
    conversation_context="Previous discussion..."
)

if success:
    print(f"Analysis: {analysis}")
```

### ErrorHandler (`utils/error_handler.py`)

**Purpose**: Centralized error handling, categorization, and user-friendly messaging.

**Key Features**:

```python
class ErrorType(Enum):
    """Error categorization"""
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
    @staticmethod
    def handle_exception(e: Exception, context: str = "",
                        log_traceback: bool = True) -> Tuple[bool, str]:
        """Handle exception and return formatted error message"""

    @staticmethod
    def format_error_history(error_history: List[Dict]) -> str:
        """Format error history for user display"""

    @staticmethod
    def wrap_operation(operation_name: str, func, *args, **kwargs) -> Tuple[bool, any]:
        """Wrap an operation with error handling"""

    @staticmethod
    def validate_required_params(params: Dict, required_keys: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate required parameters"""
```

**Features**:

- Automatic error categorization
- Context-aware error messages
- User-friendly suggestions
- Error history tracking
- Parameter validation

**Usage Example**:

```python
from geo_codex_logic.utils.error_handler import ErrorHandler

# Handle exceptions
try:
    # Some operation
    result = risky_operation()
except Exception as e:
    success, msg = ErrorHandler.handle_exception(e, "Database connection")
    print(msg)  # User-friendly message with suggestions

# Validate parameters
params = {"host": "localhost", "port": 5432}
valid, error_msg = ErrorHandler.validate_required_params(
    params, ["host", "port", "dbname"]
)
if not valid:
    print(error_msg)  # "Missing required parameters: dbname"
```

### WorkflowOrchestrator (Refactored)

The orchestrator has been refactored to use the new agents:

**Changes**:

- Removed inline SQL generation/fixing logic
- Delegates to `CoderAgent` for all SQL operations
- Delegates to `InterpreterAgent` for image analysis
- Uses `ErrorHandler` for consistent error handling
- Maintains agent instances (singleton pattern)

**New Helper Methods**:

```python
def _get_coder_agent(self) -> CoderAgent:
    """Get or create a Coder Agent instance"""

def _get_interpreter_agent(self) -> InterpreterAgent:
    """Get or create an Interpreter Agent instance"""
```

**Workflow Methods Updated**:

- `run_nl_to_sql_workflow()` - Uses CoderAgent
- `run_image_to_sql_workflow()` - Uses both agents
- `run_sql_with_auto_fix()` - Uses CoderAgent for fixes
- `run_chat_message()` - Uses appropriate agent based on context
- `run_chat_with_image()` - Uses dual-agent flow

## Benefits of Refactoring

### 1. Separation of Concerns

- **CoderAgent**: Only SQL-related logic
- **InterpreterAgent**: Only interpretation/analysis logic
- **ErrorHandler**: Only error handling logic
- **Orchestrator**: Only workflow coordination

### 2. Testability

- Each agent can be tested independently with mock LLM clients
- Error handling can be tested in isolation
- Unit tests included (`test_refactored_agents.py`)

### 3. Maintainability

- Changes to SQL generation logic only affect CoderAgent
- Changes to image analysis only affect InterpreterAgent
- Error handling improvements benefit all components
- Clear responsibilities for each class

### 4. Extensibility

- Easy to add new agent types (e.g., ValidatorAgent, OptimizerAgent)
- Simple to add new error types and handling strategies
- Straightforward to enhance existing agents with new capabilities

### 5. Reusability

- Agents can be used independently of orchestrator
- Error handler can be used across the entire plugin
- Prompt building logic encapsulated in agents

## Migration Guide

### For Developers

If you were using orchestrator methods directly, **no changes needed**. The public API remains the same:

```python
# This still works exactly the same
orchestrator = WorkflowOrchestrator(interpreter_config, coder_config, db_params)
success, sql = orchestrator.run_nl_to_sql_workflow("Find cities...")
```

### Adding New Features

**To add a new SQL generation capability**:

1. Add method to `CoderAgent`
2. Update orchestrator to call it if needed
3. No changes to other components

**To add new image analysis capability**:

1. Add method to `InterpreterAgent`
2. Update orchestrator to call it if needed
3. No changes to other components

**To add new error type**:

1. Add to `ErrorType` enum
2. Add categorization logic in `ErrorHandler._categorize_error()`
3. Add guidance in `ErrorHandler._get_error_guidance()`

## Testing

Run the test suite:

```bash
python test_refactored_agents.py
```

**Test Coverage**:

- ✅ CoderAgent: SQL generation, extraction, fixing
- ✅ InterpreterAgent: Workflow extraction, schema mapping, chat
- ✅ ErrorHandler: Exception handling, categorization, validation
- ✅ Integration: Agent coordination and workflow

## Performance Considerations

### Agent Instance Caching

Agents are created once and reused:

```python
def _get_coder_agent(self) -> CoderAgent:
    if not hasattr(self, '_coder_agent'):
        coder_client = self._create_coder_client()
        self._coder_agent = CoderAgent(coder_client)
    return self._coder_agent
```

This prevents recreating agents on every operation, improving performance.

### Error Handling Overhead

ErrorHandler operations are lightweight (string operations, dictionary lookups). No performance impact.

## Future Enhancements

Potential additions to the architecture:

1. **CacheAgent**: Cache frequently used SQL queries and results
2. **ValidatorAgent**: Validate SQL before execution
3. **OptimizerAgent**: Optimize generated SQL queries
4. **MonitoringAgent**: Track performance metrics and usage patterns
5. **ContextManager**: Enhanced conversation context management

## Conclusion

The refactored architecture provides a solid foundation for future development while maintaining backward compatibility. The separation into specialized agents makes the codebase easier to understand, test, and extend.

---

**Last Updated**: December 19, 2025  
**Version**: 1.0  
**Author**: GeoCodex Development Team
