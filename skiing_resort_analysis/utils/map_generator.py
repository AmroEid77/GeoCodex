# -*- coding: utf-8 -*-
"""
Interactive HTML Map Generator
Creates interactive HTML maps using Folium library
"""
import folium
from folium import plugins
import geopandas as gpd
import os


def create_interactive_map(dem_path, snow_raster, suitability_raster, 
                          suitable_areas_shp, best_locations_geojson,
                          dam_line_shp, ridges_shp, output_html):
    """
    Create interactive HTML map with all analysis layers
    
    Args:
        dem_path (str): Path to DEM raster
        snow_raster (str): Path to snow interpolation raster (kriging)
        suitability_raster (str): Path to suitability raster
        suitable_areas_shp (str): Path to suitable areas shapefile
        best_locations_geojson (str): Path to best locations GeoJSON
        dam_line_shp (str): Path to dam line shapefile
        ridges_shp (str): Path to ridges shapefile
        output_html (str): Output HTML file path
    """
    
    print("\nCreating interactive HTML map...")
    
    # Read DEM to get center coordinates
    import rasterio
    with rasterio.open(dem_path) as src:
        bounds = src.bounds
        center_lat = (bounds.top + bounds.bottom) / 2
        center_lon = (bounds.left + bounds.right) / 2
        
        # Transform to lat/lon if needed
        if src.crs.to_epsg() != 4326:
            from pyproj import Transformer
            transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
            center_lon, center_lat = transformer.transform(
                (bounds.left + bounds.right) / 2,
                (bounds.bottom + bounds.top) / 2
            )
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add different base maps
    folium.TileLayer('OpenTopoMap', name='Topographic', attr='Map data: &copy; OpenTopoMap contributors').add_to(m)
    folium.TileLayer(
        tiles='https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png',
        attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL',
        name='Terrain',
        overlay=False,
        control=True
    ).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add layer groups
    areas_layer = folium.FeatureGroup(name='Suitable Areas', show=True)
    locations_layer = folium.FeatureGroup(name='Best Locations', show=True)
    reference_layer = folium.FeatureGroup(name='Reference (Dam & Ridges)', show=False)
    
    # Add best locations as markers
    try:
        if os.path.exists(best_locations_geojson):
            best_locs = gpd.read_file(best_locations_geojson)
            if not best_locs.empty:
                # Reproject to WGS84 if needed
                if best_locs.crs.to_epsg() != 4326:
                    best_locs = best_locs.to_crs(epsg=4326)
                
                for idx, row in best_locs.iterrows():
                    folium.Marker(
                        location=[row.geometry.y, row.geometry.x],
                        popup=f"""
                        <b>Best Location #{row['rank']}</b><br>
                        Suitability: {row['suitability']:.2f}/100<br>
                        Coordinates: ({row.geometry.x:.2f}, {row.geometry.y:.2f})
                        """,
                        tooltip=f"Rank {row['rank']} - Score: {row['suitability']:.1f}",
                        icon=folium.Icon(color='red', icon='star', prefix='fa')
                    ).add_to(locations_layer)
    except Exception as e:
        print(f"  Warning: Could not add best locations: {e}")
    
    # Add suitable areas as polygons
    try:
        if os.path.exists(suitable_areas_shp):
            suitable = gpd.read_file(suitable_areas_shp)
            if not suitable.empty:
                # Reproject to WGS84 if needed
                if suitable.crs.to_epsg() != 4326:
                    suitable = suitable.to_crs(epsg=4326)
                
                # Only show larger areas (top 10% by size)
                suitable = suitable.nlargest(max(10, len(suitable) // 10), 'area_cells')
                
                for idx, row in suitable.iterrows():
                    # Color based on suitability
                    if row['mean_suita'] >= 85:
                        color = '#26964B'  # Dark green
                    elif row['mean_suita'] >= 75:
                        color = '#66D966'  # Light green
                    else:
                        color = '#FFFF9D'  # Yellow
                    
                    folium.GeoJson(
                        row.geometry,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.5
                        },
                        tooltip=f"Area: {row['area_cells']} cells, Avg Suitability: {row['mean_suita']:.1f}"
                    ).add_to(areas_layer)
    except Exception as e:
        print(f"  Warning: Could not add suitable areas: {e}")
    
    # Add dam line
    try:
        if os.path.exists(dam_line_shp):
            dam = gpd.read_file(dam_line_shp)
            if not dam.empty:
                if dam.crs.to_epsg() != 4326:
                    dam = dam.to_crs(epsg=4326)
                folium.GeoJson(
                    dam,
                    style_function=lambda x: {
                        'color': 'blue',
                        'weight': 3,
                        'opacity': 0.8
                    },
                    tooltip='Dam Line'
                ).add_to(reference_layer)
    except Exception as e:
        print(f"  Warning: Could not add dam line: {e}")
    
    # Add ridges
    try:
        if os.path.exists(ridges_shp):
            ridges = gpd.read_file(ridges_shp)
            if not ridges.empty:
                if ridges.crs.to_epsg() != 4326:
                    ridges = ridges.to_crs(epsg=4326)
                folium.GeoJson(
                    ridges,
                    style_function=lambda x: {
                        'color': 'brown',
                        'weight': 2,
                        'opacity': 0.7
                    },
                    tooltip='Ridge Line'
                ).add_to(reference_layer)
    except Exception as e:
        print(f"  Warning: Could not add ridges: {e}")
    
    # Add all layers to map
    areas_layer.add_to(m)
    locations_layer.add_to(m)
    reference_layer.add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px; border-radius: 5px; opacity: 0.9;">
        <h3 style="margin: 0; color: #2c3e50;">Skiing Resort Site Selection Analysis</h3>
        <p style="margin: 5px 0; font-size: 12px; color: #555;">
            <b>Task 1:</b> Snow depth interpolation (Kriging method)<br>
            <b>Task 2:</b> Suitability based on slope, orientation & shading
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend for suitability
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; border-radius: 5px; opacity: 0.9;">
        <h4 style="margin: 0 0 10px 0;">Suitability Score</h4>
        <div><span style="background:#26964B; width:20px; height:15px; display:inline-block;"></span> 90-100 Optimal</div>
        <div><span style="background:#66D966; width:20px; height:15px; display:inline-block;"></span> 70-90 Good</div>
        <div><span style="background:#FFFF9D; width:20px; height:15px; display:inline-block;"></span> 50-70 Moderate</div>
        <div><span style="background:#F44336; width:20px; height:15px; display:inline-block;"></span> 0-50 Poor</div>
        <hr>
        <div><i class="fa fa-star" style="color:red"></i> Best Locations</div>
        <div style="border-left: 3px solid blue; padding-left: 5px; margin-top: 5px;">Dam Line</div>
        <div style="border-left: 3px solid brown; padding-left: 5px; margin-top: 5px;">Ridges</div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add fullscreen button
    plugins.Fullscreen(
        position='topleft',
        title='Full Screen',
        title_cancel='Exit Full Screen',
        force_separate_button=True
    ).add_to(m)
    
    # Add measure control
    plugins.MeasureControl(position='topleft', primary_length_unit='meters').add_to(m)
    
    # Save map
    m.save(output_html)
    print(f"OK - Interactive map saved: {output_html}")
