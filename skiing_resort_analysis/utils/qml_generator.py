# -*- coding: utf-8 -*-
"""
QML Style File Generator for QGIS
Generates QGIS Layer Style (.qml) files for raster layers
"""


def create_qml_raster_style(output_path, layer_name, color_ramp, min_val, max_val, 
                             mode='Continuous', units='', description=''):
    """
    Create QML style file for raster layer
    
    Args:
        output_path (str): Path to save .qml file
        layer_name (str): Name of the layer
        color_ramp (list): List of (value, r, g, b, alpha, label) tuples
        min_val (float): Minimum value
        max_val (float): Maximum value
        mode (str): 'Continuous' or 'Discrete'
        units (str): Units for legend
        description (str): Layer description
    """
    
    # Build color ramp items
    ramp_items = []
    for value, r, g, b, alpha, label in color_ramp:
        ramp_items.append(f'''        <item value="{value}" label="{label}" color="#{r:02x}{g:02x}{b:02x}" alpha="{alpha}"/>''')
    
    ramp_xml = '\n'.join(ramp_items)
    
    qml_content = f'''<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <customproperties>
    <Option type="Map">
      <Option type="QString" name="identify/format" value="Value"/>
    </Option>
  </customproperties>
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option type="QString" name="name" value=""/>
      <Option name="properties"/>
      <Option type="QString" name="type" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling enabled="false" maxOversampling="2" zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer type="singlebandpseudocolor" opacity="1" band="1" nodataColor="" alphaBand="-1" classificationMin="{min_val}" classificationMax="{max_val}">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>MinMax</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="{mode}" maximumValue="{max_val}" minimumValue="{min_val}" clip="0" classificationMode="1" labelPrecision="2">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option type="QString" name="color1" value="0,0,255,255"/>
              <Option type="QString" name="color2" value="255,0,0,255"/>
              <Option type="QString" name="stops"/>
            </Option>
          </colorramp>
{ramp_xml}
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" gamma="1" contrast="0"/>
    <huesaturation colorizeRed="255" grayscaleMode="0" colorizeStrength="100" colorizeBlue="128" colorizeOn="0" saturation="0" invertColors="0" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(qml_content)
    
    print(f"OK - QML style saved: {output_path}")


def create_snow_depth_qml(output_path, min_val=0, max_val=28):
    """Create QML for snow depth (blue to white gradient)"""
    color_ramp = [
        (min_val, 255, 255, 255, 255, f"{min_val:.1f} (No Snow)"),
        (max_val * 0.25, 179, 226, 255, 255, f"{max_val * 0.25:.1f} (Light)"),
        (max_val * 0.5, 102, 178, 255, 255, f"{max_val * 0.5:.1f} (Moderate)"),
        (max_val * 0.75, 25, 102, 255, 255, f"{max_val * 0.75:.1f} (Heavy)"),
        (max_val, 0, 38, 153, 255, f"{max_val:.1f} (Very Heavy)"),
    ]
    create_qml_raster_style(output_path, "Snow Depth", color_ramp, min_val, max_val, 
                           'Continuous', 'units', 'Interpolated snow depth')


def create_slope_qml(output_path, min_val=0, max_val=65):
    """Create QML for slope (green to red gradient)"""
    color_ramp = [
        (0, 26, 150, 65, 255, "0 deg (Flat - Unsuitable)"),
        (15, 166, 217, 106, 255, "15 deg (Min - Marginal)"),
        (20, 255, 255, 191, 255, "20 deg (Good)"),
        (25, 253, 174, 97, 255, "25 deg (Optimal)"),
        (30, 244, 109, 67, 255, "30 deg (Good)"),
        (40, 215, 48, 39, 255, "40 deg (Max - Marginal)"),
        (max_val, 165, 0, 38, 255, f"{max_val:.0f} deg (Too Steep)"),
    ]
    create_qml_raster_style(output_path, "Slope", color_ramp, min_val, max_val, 
                           'Continuous', 'degrees', 'Terrain slope analysis')


def create_aspect_qml(output_path, min_val=0, max_val=360):
    """Create QML for aspect (directional colors)"""
    color_ramp = [
        (0, 68, 137, 255, 255, "North (Optimal)"),
        (45, 102, 178, 255, 255, "NE (Good)"),
        (90, 255, 255, 191, 255, "East (Moderate)"),
        (135, 253, 174, 97, 255, "SE (Poor)"),
        (180, 244, 109, 67, 255, "South (Worst)"),
        (225, 215, 48, 39, 255, "SW (Poor)"),
        (270, 255, 255, 191, 255, "West (Moderate)"),
        (315, 102, 178, 255, 255, "NW (Good)"),
        (360, 68, 137, 255, 255, "North (Optimal)"),
    ]
    create_qml_raster_style(output_path, "Aspect", color_ramp, min_val, max_val, 
                           'Continuous', 'degrees', 'Terrain orientation')


def create_suitability_qml(output_path, min_val=0, max_val=100):
    """Create QML for suitability (red to green gradient)"""
    color_ramp = [
        (0, 165, 0, 38, 255, "0 (Unsuitable)"),
        (20, 215, 48, 39, 255, "20 (Poor)"),
        (40, 244, 109, 67, 255, "40 (Low)"),
        (60, 253, 174, 97, 255, "60 (Moderate)"),
        (70, 255, 255, 191, 255, "70 (Good)"),
        (80, 166, 217, 106, 255, "80 (Very Good)"),
        (90, 102, 189, 99, 255, "90 (Excellent)"),
        (100, 26, 150, 65, 255, "100 (Optimal)"),
    ]
    create_qml_raster_style(output_path, "Suitability", color_ramp, min_val, max_val, 
                           'Continuous', 'score', 'Ski resort suitability score')
