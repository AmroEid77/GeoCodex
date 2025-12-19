"""
Simple test for smart layer naming functionality
Tests the naming logic without requiring QGIS/database dependencies
"""

import re
from datetime import datetime
from typing import Optional


class LayerNamingTester:
    """Simplified version of the layer naming logic for testing"""
    
    def __init__(self):
        self._layer_counter = 0
    
    def _generate_layer_name(self, sql_query: str = None, user_query: str = None, context: str = None) -> str:
        """Generate a smart, descriptive layer name based on the query."""
        self._layer_counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Combine counter and timestamp for better uniqueness
        unique_suffix = f"{self._layer_counter}_{timestamp}"
        
        # Try to extract a meaningful name from user query first
        if user_query:
            name = self._extract_name_from_nl_query(user_query)
            if name:
                return f"{name}_{unique_suffix}"
        
        # Fall back to SQL analysis
        if sql_query:
            name = self._extract_name_from_sql(sql_query)
            if name:
                return f"{name}_{unique_suffix}"
        
        # Use context if provided
        if context:
            return f"{context}_{unique_suffix}"
        
        # Final fallback
        return f"Query_{unique_suffix}"
    
    def _extract_name_from_nl_query(self, query: str) -> Optional[str]:
        """Extract a descriptive name from natural language query."""
        query_lower = query.lower()
        
        entities = []
        operations = []
        
        # Common GIS entities
        entity_keywords = {
            'cities': 'Cities', 'city': 'Cities',
            'counties': 'Counties', 'county': 'Counties',
            'states': 'States', 'state': 'States',
            'roads': 'Roads', 'road': 'Roads',
            'highways': 'Highways', 'highway': 'Highways',
            'rivers': 'Rivers', 'river': 'Rivers',
            'lakes': 'Lakes', 'lake': 'Lakes',
            'parks': 'Parks', 'park': 'Parks',
            'buildings': 'Buildings', 'building': 'Buildings',
            'parcels': 'Parcels', 'parcel': 'Parcels',
            'points': 'Points', 'point': 'Points',
            'polygons': 'Polygons', 'polygon': 'Polygons',
            'lines': 'Lines', 'line': 'Lines'
        }
        
        # Find entities
        for keyword, name in entity_keywords.items():
            if keyword in query_lower:
                if name not in entities:
                    entities.append(name)
        
        # Extract operations
        if any(kw in query_lower for kw in ['buffer', 'buffered']):
            operations.append('Buffer')
        if any(kw in query_lower for kw in ['intersect', 'intersection']):
            operations.append('Intersect')
        if any(kw in query_lower for kw in ['within', 'inside']):
            operations.append('Within')
        if any(kw in query_lower for kw in ['near', 'close', 'distance']):
            operations.append('Near')
        if any(kw in query_lower for kw in ['population', 'pop']):
            operations.append('Pop')
        if any(kw in query_lower for kw in ['area', 'size']):
            operations.append('Area')
        
        # Extract numbers
        numbers = re.findall(r'\b(\d+(?:k|m|km|mi|miles|meters)?)', query_lower)
        
        # Build name
        parts = []
        
        if entities:
            parts.append('_'.join(entities[:2]))
        
        if operations:
            parts.extend(operations[:2])
        
        if numbers:
            num_str = numbers[0].replace('k', 'k').replace('m', 'm')
            parts.append(num_str)
        
        if parts:
            return '_'.join(parts)
        
        return None
    
    def _extract_name_from_sql(self, sql: str) -> Optional[str]:
        """Extract a descriptive name from SQL query."""
        sql_upper = sql.upper()
        
        # Extract table names from FROM clause (handle schema prefix)
        from_match = re.search(r'FROM\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)', sql_upper, re.IGNORECASE)
        if from_match:
            table_name = from_match.group(1).lower()
            # Clean up common prefixes/suffixes
            table_name = table_name.replace('tbl_', '').replace('_tbl', '')
            # Capitalize
            table_name = table_name.capitalize()
            
            # Determine operation type
            if 'ST_BUFFER' in sql_upper:
                return f"{table_name}_Buffer"
            elif 'ST_INTERSECTS' in sql_upper or 'ST_INTERSECTION' in sql_upper:
                return f"{table_name}_Intersect"
            elif 'ST_WITHIN' in sql_upper or 'ST_DWITHIN' in sql_upper:
                return f"{table_name}_Within"
            elif 'ST_DISTANCE' in sql_upper:
                return f"{table_name}_Distance"
            elif 'COUNT' in sql_upper:
                return f"{table_name}_Count"
            elif 'SUM' in sql_upper or 'AVG' in sql_upper:
                return f"{table_name}_Stats"
            else:
                return f"{table_name}_Query"
        
        return None


def test_layer_naming():
    """Test the smart layer naming functionality"""
    
    print("=" * 80)
    print("Testing Smart Layer Naming")
    print("=" * 80)
    
    tester = LayerNamingTester()
    
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
            'user_query': None,
            'sql_query': 'SELECT * FROM counties WHERE state = \'TX\'',
            'expected_contains': ['Counties']
        }
    ]
    
    print("\n" + "=" * 80)
    print("Natural Language Query → Layer Name")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        layer_name = tester._generate_layer_name(
            sql_query=test['sql_query'],
            user_query=test['user_query']
        )
        
        print(f"\nTest {i}:")
        print(f"  User Query: {test['user_query'] or 'None'}")
        print(f"  SQL: {test['sql_query'][:60]}...")
        print(f"  Generated Name: {layer_name}")
        
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
        layer_name = tester._generate_layer_name(sql_query=test['sql'])
        
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
        name = tester._generate_layer_name(
            user_query='Find all cities',
            sql_query='SELECT * FROM cities'
        )
        names.append(name)
        print(f"  Layer {i+1}: {name}")
    
    unique_names = len(set(names)) == len(names)
    print(f"\n  All names unique: {'✓ PASS' if unique_names else '✗ FAIL'}")
    
    print("\n" + "=" * 80)
    print("All Tests Complete!")
    print("=" * 80)


if __name__ == '__main__':
    test_layer_naming()
