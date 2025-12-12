# -*- coding: utf-8 -*-
"""
Generate QGIS Style File for Tree Priority Results
Run this after analysis to create matching QGIS styling
"""

import os

# Output path
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
QML_PATH = os.path.join(OUTPUT_DIR, 'tree_priority_style.qml')

# Color mapping (matching visualizations)
COLOR_MAP = {
    'Very High': '#d73027',    # Red
    'High': '#fc8d59',         # Orange
    'Medium': '#fee08b',       # Yellow
    'Low': '#91cf60',          # Light green
    'Very Low': '#1a9850',     # Dark green
}

def create_qgis_style():
    """Create QML style file for QGIS"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    qml_content = '''<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.28" styleCategories="Symbology">
  <renderer-v2 type="categorizedSymbol" attr="prior_cls" forceraster="0" enableorderby="0">
    <categories>
'''
    
    priority_order = ['Very High', 'High', 'Medium', 'Low', 'Very Low']
    for idx, priority_class in enumerate(priority_order):
        qml_content += f'      <category render="true" symbol="{idx}" value="{priority_class}" label="{priority_class}"/>\n'
    
    qml_content += '''    </categories>
    <symbols>
'''
    
    for idx, priority_class in enumerate(priority_order):
        color = COLOR_MAP[priority_class]
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        
        qml_content += f'''      <symbol type="fill" name="{idx}" alpha="0.7" force_rhr="0" clip_to_extent="1">
        <layer pass="0" locked="0" enabled="1" class="SimpleFill">
          <prop k="color" v="{rgb[0]},{rgb[1]},{rgb[2]},178"/>
          <prop k="outline_color" v="50,50,50,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.5"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>
'''
    
    qml_content += '''    </symbols>
  </renderer-v2>
</qgis>
'''
    
    with open(QML_PATH, 'w') as f:
        f.write(qml_content)
    
    print(f"✓ QGIS style file created: {QML_PATH}")
    print("\nTo use in QGIS:")
    print("  1. Load: output/tree_priority_result.shp")
    print("  2. Right-click layer → Properties → Style")
    print("  3. Click 'Style' (bottom left) → Load Style")
    print(f"  4. Select: {QML_PATH}")
    
    return QML_PATH

if __name__ == '__main__':
    create_qgis_style()