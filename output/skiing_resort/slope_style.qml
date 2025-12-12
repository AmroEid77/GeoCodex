<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
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
    <rasterrenderer type="singlebandpseudocolor" opacity="1" band="1" nodataColor="" alphaBand="-1" classificationMin="0" classificationMax="65">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>MinMax</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="Continuous" maximumValue="65" minimumValue="0" clip="0" classificationMode="1" labelPrecision="2">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option type="QString" name="color1" value="0,0,255,255"/>
              <Option type="QString" name="color2" value="255,0,0,255"/>
              <Option type="QString" name="stops"/>
            </Option>
          </colorramp>
        <item value="0" label="0 deg (Flat - Unsuitable)" color="#1a9641" alpha="255"/>
        <item value="15" label="15 deg (Min - Marginal)" color="#a6d96a" alpha="255"/>
        <item value="20" label="20 deg (Good)" color="#ffffbf" alpha="255"/>
        <item value="25" label="25 deg (Optimal)" color="#fdae61" alpha="255"/>
        <item value="30" label="30 deg (Good)" color="#f46d43" alpha="255"/>
        <item value="40" label="40 deg (Max - Marginal)" color="#d73027" alpha="255"/>
        <item value="65" label="65 deg (Too Steep)" color="#a50026" alpha="255"/>
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
