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
    <rasterrenderer type="singlebandpseudocolor" opacity="1" band="1" nodataColor="" alphaBand="-1" classificationMin="0" classificationMax="28">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>MinMax</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="Continuous" maximumValue="28" minimumValue="0" clip="0" classificationMode="1" labelPrecision="2">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option type="QString" name="color1" value="0,0,255,255"/>
              <Option type="QString" name="color2" value="255,0,0,255"/>
              <Option type="QString" name="stops"/>
            </Option>
          </colorramp>
        <item value="0" label="0.0 (No Snow)" color="#ffffff" alpha="255"/>
        <item value="7.0" label="7.0 (Light)" color="#b3e2ff" alpha="255"/>
        <item value="14.0" label="14.0 (Moderate)" color="#66b2ff" alpha="255"/>
        <item value="21.0" label="21.0 (Heavy)" color="#1966ff" alpha="255"/>
        <item value="28" label="28.0 (Very Heavy)" color="#002699" alpha="255"/>
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
