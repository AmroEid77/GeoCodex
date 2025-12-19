"""
Test smart layer naming functionality
"""

import sys
import os

# Add vendor path for dependencies
vendor_path = os.path.join(os.path.dirname(__file__), 'vendor')
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

from geo_codex_logic.orchestrator import WorkflowOrchestrator


def test_layer_naming():
    """Test the smart layer naming functionality"""
    
    print("=" * 80)
    print("Testing Smart Layer Naming")
    print("=" * 80)
    
    # Create orchestrator (no actual DB connection needed for naming tests)
    orchestrator = WorkflowOrchestrator(
        interpreter_config={'provider': 'openai'},
        coder_config={'provider': 'openai'},
        db_params={}
    )
    
    # Test cases for natural language queries
    test_cases = [
        {
            'user_query': 'Find all cities with population over 100000',
            'sql_query': 'SELECT * FROM cities WHERE population > 100000',
            'expected_contains': ['Cities', 'Pop']
        },
        {
            'user_query': 'Show me counties in California',
            'sql_query': 'SELECT * FROM counties WHERE state = \'CA\'',
            'expected_contains': ['Counties']
        },
        {
            'user_query': 'Buffer roads by 500 meters',
            'sql_query': 'SELECT ST_BUFFER(geom, 500) FROM roads',
            'expected_contains': ['Roads', 'Buffer']
        },
        {
            'user_query': 'Find parks within 1km of downtown',
            'sql_query': 'SELECT * FROM parks WHERE ST_DWithin(geom, downtown.geom, 1000)',
            'expected_contains': ['Parks', 'Within']
        },
        {
            'user_query': 'Calculate area of all polygons',
            'sql_query': 'SELECT id, ST_Area(geom) FROM polygons',
            'expected_contains': ['Polygons', 'Area']
        },
        {
            'user_query': None,  # No user query
            'sql_query': 'SELECT * FROM counties WHERE state = \'TX\'',
            'expected_contains': ['Counties']
        },
        {
            'user_query': 'Some complex query',
            'sql_query': 'SELECT a.id, b.name FROM table_a a JOIN table_b b ON a.id = b.id',
            'expected_contains': ['Table_a']  # Falls back to SQL parsing
        }
    ]
    
    print("\n" + "=" * 80)
    print("Natural Language Query → Layer Name")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        user_query = test['user_query']
        sql_query = test['sql_query']
        
        # Set user query if provided
        if user_query:
            orchestrator._last_user_query = user_query
        else:
            if hasattr(orchestrator, '_last_user_query'):
                delattr(orchestrator, '_last_user_query')
        
        layer_name = orchestrator._generate_layer_name(
            sql_query=sql_query,
            user_query=user_query
        )
        
        print(f"\nTest {i}:")
        print(f"  User Query: {user_query or 'None'}")
        print(f"  SQL: {sql_query[:60]}...")
        print(f"  Generated Name: {layer_name}")
        
        # Verify expected components
        passed = any(exp.lower() in layer_name.lower() for exp in test['expected_contains'])
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  Expected: {', '.join(test['expected_contains'])}")
        print(f"  Status: {status}")
    
    # Test SQL-only parsing
    print("\n" + "=" * 80)
    print("SQL-Only Parsing → Layer Name")
    print("=" * 80)
    
    sql_tests = [
        {
            'sql': 'SELECT * FROM public.cities WHERE population > 50000',
            'expected': 'Cities_Query'
        },
        {
            'sql': 'SELECT ST_Buffer(geom, 100) FROM roads',
            'expected': 'Roads_Buffer'
        },
        {
            'sql': 'SELECT a.*, b.name FROM parcels a, buildings b WHERE ST_Intersects(a.geom, b.geom)',
            'expected': 'Parcels_Intersect'
        },
        {
            'sql': 'SELECT COUNT(*) FROM counties',
            'expected': 'Counties_Count'
        },
        {
            'sql': 'SELECT AVG(area) FROM polygons',
            'expected': 'Polygons_Stats'
        }
    ]
    
    for i, test in enumerate(sql_tests, 1):
        # Clear user query
        if hasattr(orchestrator, '_last_user_query'):
            delattr(orchestrator, '_last_user_query')
        
        layer_name = orchestrator._generate_layer_name(sql_query=test['sql'])
        
        print(f"\nTest {i}:")
        print(f"  SQL: {test['sql'][:60]}...")
        print(f"  Generated Name: {layer_name}")
        print(f"  Expected Pattern: {test['expected']}")
        
        passed = test['expected'].lower() in layer_name.lower()
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  Status: {status}")
    
    # Test uniqueness
    print("\n" + "=" * 80)
    print("Testing Uniqueness")
    print("=" * 80)
    
    names = []
    for i in range(5):
        name = orchestrator._generate_layer_name(
            user_query='Find all cities',
            sql_query='SELECT * FROM cities'
        )
        names.append(name)
        print(f"  Layer {i+1}: {name}")
    
    unique_names = len(set(names)) == len(names)
    print(f"\n  All names unique: {'✓ PASS' if unique_names else '✗ FAIL'}")
    
    # Test fallback scenarios
    print("\n" + "=" * 80)
    print("Testing Fallback Scenarios")
    print("=" * 80)
    
    fallback_tests = [
        {
            'user_query': None,
            'sql_query': None,
            'context': 'Custom_Context',
            'desc': 'Only context provided'
        },
        {
            'user_query': None,
            'sql_query': None,
            'context': None,
            'desc': 'Nothing provided (ultimate fallback)'
        },
        {
            'user_query': 'Random text with no keywords',
            'sql_query': 'SELECT 1',
            'context': None,
            'desc': 'No extractable information'
        }
    ]
    
    for i, test in enumerate(fallback_tests, 1):
        if test['user_query']:
            orchestrator._last_user_query = test['user_query']
        else:
            if hasattr(orchestrator, '_last_user_query'):
                delattr(orchestrator, '_last_user_query')
        
        name = orchestrator._generate_layer_name(
            sql_query=test['sql_query'],
            user_query=test['user_query'],
            context=test['context']
        )
        
        print(f"\nFallback Test {i}: {test['desc']}")
        print(f"  Generated Name: {name}")
        print(f"  Has timestamp: {'✓ PASS' if any(c.isdigit() for c in name) else '✗ FAIL'}")
    
    print("\n" + "=" * 80)
    print("All Tests Complete!")
    print("=" * 80)


if __name__ == '__main__':
    test_layer_naming()
