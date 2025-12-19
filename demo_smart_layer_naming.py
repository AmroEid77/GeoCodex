"""
Visual Demonstration: Smart Layer Naming in Action
Shows the before/after comparison of layer naming
"""

print("=" * 80)
print("GeoCodex Smart Layer Naming - Visual Demo")
print("=" * 80)

# Scenario: A user runs multiple queries during a QGIS session

queries = [
    {
        "user_query": "Find all cities with population over 100000",
        "sql": "SELECT * FROM cities WHERE population > 100000",
    },
    {
        "user_query": "Buffer roads by 500 meters",
        "sql": "SELECT ST_Buffer(geom, 500) as geom, name FROM roads",
    },
    {
        "user_query": "Show me all parks within 1km of downtown",
        "sql": "SELECT * FROM parks WHERE ST_DWithin(geom, (SELECT geom FROM poi WHERE name='Downtown'), 1000)",
    },
    {
        "user_query": "Calculate area of all parcels in California",
        "sql": "SELECT id, name, ST_Area(geom) as area FROM parcels WHERE state = 'CA'",
    },
    {
        "user_query": None,  # Direct SQL execution
        "sql": "SELECT COUNT(*) as total, county FROM buildings GROUP BY county",
    }
]

print("\n" + "=" * 80)
print("BEFORE: Generic Layer Names")
print("=" * 80)
print("""
QGIS Layers Panel:
├─ 📊 GeoCodex Query Result
├─ 📊 GeoCodex Query Result (2)
├─ 📊 GeoCodex Query Result (3)
├─ 📊 GeoCodex Query Result (4)
└─ 📊 GeoCodex Query Result (5)

Problems:
❌ Can't identify layer contents without opening attribute table
❌ Manual renaming required for organization
❌ Time-consuming to find specific results
❌ Easy to accidentally remove wrong layer
""")

print("\n" + "=" * 80)
print("AFTER: Smart Layer Names")
print("=" * 80)
print("""
QGIS Layers Panel:
├─ 📊 Cities_Pop_100000_1_145501
├─ 📊 Roads_Buffer_500_2_145502
├─ 📊 Parks_Within_1k_3_145503
├─ 📊 Parcels_Area_4_145504
└─ 📊 Buildings_Count_5_145505

Benefits:
✅ Instantly understand layer contents
✅ No manual renaming needed
✅ Easy to find specific results
✅ Chronological order visible (timestamps)
✅ Unique names prevent conflicts
""")

print("\n" + "=" * 80)
print("Query-by-Query Breakdown")
print("=" * 80)

for i, q in enumerate(queries, 1):
    print(f"\n{'─' * 80}")
    print(f"Query #{i}")
    print(f"{'─' * 80}")
    
    if q['user_query']:
        print(f"📝 User Asked: \"{q['user_query']}\"")
    else:
        print(f"📝 User Asked: (Direct SQL execution)")
    
    print(f"\n💻 Generated SQL:")
    print(f"   {q['sql'][:70]}{'...' if len(q['sql']) > 70 else ''}")
    
    # Simulate what the old system would create
    old_name = f"GeoCodex Query Result{f' ({i})' if i > 1 else ''}"
    
    # Simulate what the new system creates
    if i == 1:
        new_name = "Cities_Pop_100000_1_145501"
    elif i == 2:
        new_name = "Roads_Buffer_500_2_145502"
    elif i == 3:
        new_name = "Parks_Within_1k_3_145503"
    elif i == 4:
        new_name = "Parcels_Area_4_145504"
    else:
        new_name = "Buildings_Count_5_145505"
    
    print(f"\n📊 Layer Created:")
    print(f"   OLD: {old_name}")
    print(f"   NEW: {new_name}")
    
    print(f"\n✨ Improvements:")
    if i == 1:
        print("   • 'Cities' - Clearly shows entity type")
        print("   • 'Pop_100000' - Shows population constraint")
        print("   • Immediately searchable by name")
    elif i == 2:
        print("   • 'Roads' - Entity type visible")
        print("   • 'Buffer_500' - Shows operation and parameter")
        print("   • No confusion with other buffer operations")
    elif i == 3:
        print("   • 'Parks' - Clear entity identification")
        print("   • 'Within_1k' - Distance operation obvious")
        print("   • Easy to locate spatial analysis results")
    elif i == 4:
        print("   • 'Parcels' - Table name extracted")
        print("   • 'Area' - Calculation type shown")
        print("   • Distinguishable from other parcel queries")
    else:
        print("   • 'Buildings_Count' - Even without user query!")
        print("   • SQL analysis detected COUNT operation")
        print("   • Smart fallback still provides context")

print("\n" + "=" * 80)
print("Real-World Scenario: Complex Analysis Session")
print("=" * 80)

print("""
A GIS analyst is preparing a report on urban development. They run:

1. "Find all commercial buildings in the city center"
   → Commercial_Buildings_1_091500

2. "Buffer these buildings by 100 meters"
   → Commercial_Buildings_Buffer_100m_2_091502

3. "Find residential parcels that intersect with buffered commercial zones"
   → Residential_Parcels_Intersect_3_091505

4. "Calculate total area of affected residential zones"
   → Residential_Parcels_Area_4_091507

5. "Show all schools within 500m of commercial zones"
   → Schools_Within_500m_5_091510

Result in QGIS:
├─ 📊 Commercial_Buildings_1_091500
├─ 📊 Commercial_Buildings_Buffer_100m_2_091502
├─ 📊 Residential_Parcels_Intersect_3_091505
├─ 📊 Residential_Parcels_Area_4_091507
└─ 📊 Schools_Within_500m_5_091510

The analyst can:
✅ Clearly see the analysis workflow
✅ Identify intermediate results (buffer layer)
✅ Find final outputs (schools layer)
✅ Share the project with colleagues who can understand layer purpose
✅ Resume work later without confusion
""")

print("\n" + "=" * 80)
print("Edge Case Handling")
print("=" * 80)

edge_cases = [
    ("Multiple tables", "SELECT * FROM cities, counties WHERE...", "Cities_Query_1_120000"),
    ("Schema prefix", "SELECT * FROM public.roads", "Roads_Query_2_120001"),
    ("Table prefix", "SELECT * FROM tbl_parcels", "Parcels_Query_3_120002"),
    ("Complex subquery", "SELECT * FROM (SELECT * FROM buildings) b", "Buildings_Query_4_120003"),
    ("No extractable info", "SELECT 1 + 1", "Query_5_120004"),
]

print("\nThe system gracefully handles edge cases:\n")
for scenario, sql, result in edge_cases:
    print(f"Scenario: {scenario}")
    print(f"  SQL: {sql}")
    print(f"  Result: {result} ✅")
    print()

print("=" * 80)
print("Summary")
print("=" * 80)

print("""
Smart Layer Naming transforms the GeoCodex user experience:

FROM: Generic, confusing layer names requiring manual work
TO:   Descriptive, automatic names that enhance productivity

Key Features:
• 🎯 Context-aware: Uses natural language query when available
• 🔄 Fallback-safe: Always generates a valid name
• 🆔 Unique: Combines counter + timestamp
• ⚡ Automatic: Zero configuration needed
• 📚 Informative: Extracts entities, operations, constraints
• 🔧 Flexible: Supports custom names when needed

Impact:
• ⏱️ Saves time: No manual renaming
• 🧠 Reduces cognitive load: Clear layer identification
• 📊 Improves organization: Chronological + descriptive
• 🤝 Better collaboration: Colleagues understand layer purpose
• 🔍 Enhanced discoverability: Searchable, meaningful names

Result: A more professional, efficient GIS workflow! 🚀
""")

print("=" * 80)
print("Demo Complete!")
print("=" * 80)
