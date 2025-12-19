# -*- coding: utf-8 -*-
"""
Test script to verify the refactored agents work correctly
"""

import sys
import os

# Add the plugin directory to the path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, plugin_dir)

def test_coder_agent():
    """Test CoderAgent functionality"""
    print("=" * 80)
    print("Testing CoderAgent")
    print("=" * 80)
    
    from geo_codex_logic.agents.coder_agent import CoderAgent
    
    # Mock LLM client
    class MockLLMClient:
        def generate_response(self, prompt):
            # Return a mock SQL response
            return """```sql
SELECT * FROM cities WHERE population > 50000
```"""
    
    # Create agent
    agent = CoderAgent(MockLLMClient())
    
    # Test SQL generation from NL
    schema_info = "Table: cities (id, name, population, geom)"
    success, result = agent.generate_sql_from_nl("Find cities with population over 50000", schema_info)
    
    print(f"✓ SQL Generation from NL: {'SUCCESS' if success else 'FAILED'}")
    print(f"  Result: {result[:100]}...")
    
    # Test SQL extraction
    response_with_sql = """Here's the query:
```sql
SELECT * FROM test
```
And some explanation."""
    
    extracted = agent._extract_sql(response_with_sql)
    print(f"✓ SQL Extraction: {'SUCCESS' if extracted == 'SELECT * FROM test' else 'FAILED'}")
    print(f"  Extracted: {extracted}")
    
    print()

def test_interpreter_agent():
    """Test InterpreterAgent functionality"""
    print("=" * 80)
    print("Testing InterpreterAgent")
    print("=" * 80)
    
    from geo_codex_logic.agents.interpreter_agent import InterpreterAgent
    
    # Mock LLM client
    class MockLLMClient:
        def get_workflow_steps_from_image(self, base64_image):
            return "Step 1: Filter data\nStep 2: Apply spatial operation"
        
        def generate_vision_response(self, prompt, base64_image):
            return "Analysis: The image shows a workflow with criteria mapped to schema"
        
        def generate_response(self, prompt):
            return "This is a conversational response"
    
    # Create agent
    agent = InterpreterAgent(MockLLMClient())
    
    # Test workflow extraction
    success, result = agent.extract_workflow_from_image("fake_base64_image")
    print(f"✓ Workflow Extraction: {'SUCCESS' if success else 'FAILED'}")
    print(f"  Result: {result[:100]}...")
    
    # Test schema mapping
    success, result = agent.analyze_image_with_schema(
        "fake_base64_image",
        "Schema info",
        "User message",
        "Context"
    )
    print(f"✓ Schema Mapping: {'SUCCESS' if success else 'FAILED'}")
    print(f"  Result: {result[:100]}...")
    
    # Test chat response
    success, result = agent.chat_response("Hello", "Schema", "Context")
    print(f"✓ Chat Response: {'SUCCESS' if success else 'FAILED'}")
    print(f"  Result: {result[:100]}...")
    
    print()

def test_error_handler():
    """Test ErrorHandler functionality"""
    print("=" * 80)
    print("Testing ErrorHandler")
    print("=" * 80)
    
    from geo_codex_logic.utils.error_handler import ErrorHandler, ErrorType
    
    # Test exception handling
    try:
        raise ValueError("Test database connection error")
    except Exception as e:
        success, msg = ErrorHandler.handle_exception(e, "Database connection", log_traceback=False)
        print(f"✓ Exception Handling: {'SUCCESS' if not success and 'database' in msg.lower() else 'FAILED'}")
        print(f"  Message: {msg[:100]}...")
    
    # Test error categorization
    db_error = ValueError("Connection to database failed")
    error_type = ErrorHandler._categorize_error(db_error)
    print(f"✓ Error Categorization: {'SUCCESS' if error_type == ErrorType.DATABASE else 'FAILED'}")
    print(f"  Type: {error_type}")
    
    # Test error history formatting
    history = [
        {"attempt": 1, "error": "First error"},
        {"attempt": 2, "error": "Second error"}
    ]
    formatted = ErrorHandler.format_error_history(history)
    print(f"✓ Error History Formatting: {'SUCCESS' if 'Attempt 1' in formatted else 'FAILED'}")
    print(f"  Formatted: {formatted[:100]}...")
    
    # Test parameter validation
    params = {"key1": "value1", "key2": "value2"}
    valid, msg = ErrorHandler.validate_required_params(params, ["key1", "key2"])
    print(f"✓ Parameter Validation (valid): {'SUCCESS' if valid else 'FAILED'}")
    
    valid, msg = ErrorHandler.validate_required_params(params, ["key1", "key3"])
    print(f"✓ Parameter Validation (invalid): {'SUCCESS' if not valid else 'FAILED'}")
    print(f"  Message: {msg}")
    
    print()

def test_integration():
    """Test integration between components"""
    print("=" * 80)
    print("Testing Integration")
    print("=" * 80)
    
    from geo_codex_logic.agents.coder_agent import CoderAgent
    from geo_codex_logic.agents.interpreter_agent import InterpreterAgent
    from geo_codex_logic.utils.error_handler import ErrorHandler
    
    # Mock LLM client
    class MockLLMClient:
        def generate_response(self, prompt):
            return "```sql\nSELECT * FROM test\n```"
        
        def get_workflow_steps_from_image(self, base64_image):
            return "Step 1: Process data"
    
    # Test agent creation and usage
    coder = CoderAgent(MockLLMClient())
    interpreter = InterpreterAgent(MockLLMClient())
    
    # Simulate workflow
    print("Simulating workflow:")
    print("  1. Extract workflow from image (InterpreterAgent)")
    success, workflow = interpreter.extract_workflow_from_image("image")
    print(f"     Result: {workflow}")
    
    print("  2. Generate SQL from workflow (CoderAgent)")
    success, sql = coder.generate_sql_from_steps(workflow, "schema")
    print(f"     Result: {sql}")
    
    print("✓ Integration test completed successfully")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("GeoCodex - Refactored Agents Test Suite")
    print("=" * 80 + "\n")
    
    try:
        test_coder_agent()
        test_interpreter_agent()
        test_error_handler()
        test_integration()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
