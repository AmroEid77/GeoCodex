# -*- coding: utf-8 -*-
"""
Interactive HTML Map Generator
Creates interactive HTML maps using Folium library
"""
import folium
from folium import plugins
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import os
from branca.colormap import LinearColormap


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
    suitability_layer = folium.FeatureGroup(name='Suitability Heatmap', show=True)
    areas_layer = folium.FeatureGroup(name='Suitable Areas (Polygons)', show=False)
    locations_layer = folium.FeatureGroup(name='🌟 Best Locations', show=True)
    reference_layer = folium.FeatureGroup(name='Reference (Dam & Ridges)', show=True)
    
    # Add suitability raster as image overlay
    try:
        if os.path.exists(suitability_raster):
            print("  Adding suitability heatmap overlay...")
            with rasterio.open(suitability_raster) as src:
                suitability_data = src.read(1)
                bounds_proj = src.bounds
                crs_proj = src.crs
                
                # Transform bounds to WGS84
                if crs_proj.to_epsg() != 4326:
                    from pyproj import Transformer
                    transformer = Transformer.from_crs(crs_proj, "EPSG:4326", always_xy=True)
                    
                    # Get corner coordinates
                    sw_lon, sw_lat = transformer.transform(bounds_proj.left, bounds_proj.bottom)
                    ne_lon, ne_lat = transformer.transform(bounds_proj.right, bounds_proj.top)
                    bounds_wgs84 = [[sw_lat, sw_lon], [ne_lat, ne_lon]]
                else:
                    bounds_wgs84 = [[bounds_proj.bottom, bounds_proj.left], 
                                   [bounds_proj.top, bounds_proj.right]]
                
                # Normalize and create colored overlay
                suit_normalized = np.nan_to_num(suitability_data, nan=0)
                suit_normalized = np.clip(suit_normalized, 0, 100) / 100.0
                
                # Create color map (Red -> Yellow -> Green)
                from matplotlib import cm
                from matplotlib.colors import Normalize
                import matplotlib.pyplot as plt
                
                # Use RdYlGn colormap
                norm = Normalize(vmin=0, vmax=100)
                cmap = cm.get_cmap('RdYlGn')
                
                # Apply colormap
                colored = cmap(suit_normalized)
                colored = (colored[:, :, :3] * 255).astype(np.uint8)
                
                # Mask low suitability areas (make transparent)
                mask = suitability_data < 50
                colored[mask] = [0, 0, 0, 0]
                
                # Save temporary PNG
                import tempfile
                from PIL import Image
                temp_dir = tempfile.gettempdir()
                temp_img = os.path.join(temp_dir, 'suitability_overlay.png')
                
                # Create RGBA image with transparency
                img_array = np.zeros((colored.shape[0], colored.shape[1], 4), dtype=np.uint8)
                img_array[:, :, :3] = colored
                img_array[:, :, 3] = np.where(mask, 0, 180)  # Alpha channel (180 = semi-transparent)
                
                img = Image.fromarray(img_array, mode='RGBA')
                img.save(temp_img)
                
                # Add as image overlay
                folium.raster_layers.ImageOverlay(
                    image=temp_img,
                    bounds=bounds_wgs84,
                    opacity=0.6,
                    interactive=False,
                    cross_origin=False,
                    zindex=1,
                ).add_to(suitability_layer)
                
                print("  ✓ Suitability heatmap added")
    except Exception as e:
        print(f"  ⚠ Could not add suitability overlay: {e}")
    
    # Add best locations with custom star icons and circles
    try:
        if os.path.exists(best_locations_geojson):
            best_locs = gpd.read_file(best_locations_geojson)
            if not best_locs.empty:
                # Reproject to WGS84 if needed
                if best_locs.crs.to_epsg() != 4326:
                    best_locs = best_locs.to_crs(epsg=4326)
                
                print(f"  Adding {len(best_locs)} best locations...")
                
                for idx, row in best_locs.iterrows():
                    rank = row['rank']
                    score = row['suitability']
                    
                    # Color based on rank
                    if rank == 1:
                        color = 'red'
                        icon_color = 'white'
                        size = 'large'
                    elif rank <= 3:
                        color = 'darkred'
                        icon_color = 'white'
                        size = 'medium'
                    else:
                        color = 'orange'
                        icon_color = 'white'
                        size = 'small'
                    
                    # Add circular highlight around location
                    folium.Circle(
                        location=[row.geometry.y, row.geometry.x],
                        radius=500,  # 500 meters
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.15,
                        weight=2,
                        opacity=0.8,
                        popup=None,
                        tooltip=None
                    ).add_to(locations_layer)
                    
                    # Custom HTML icon with star
                    star_html = f"""
                    <div style="text-align: center;">
                        <div style="font-size: 32px; color: {color}; 
                                    text-shadow: 2px 2px 4px rgba(0,0,0,0.7),
                                               -1px -1px 2px white,
                                                1px -1px 2px white,
                                               -1px 1px 2px white,
                                                1px 1px 2px white;">
                            ⭐
                        </div>
                        <div style="background: {color}; color: white; 
                                    border-radius: 50%; width: 24px; height: 24px; 
                                    display: flex; align-items: center; justify-content: center;
                                    font-weight: bold; font-size: 14px;
                                    border: 2px solid white;
                                    box-shadow: 0 0 5px rgba(0,0,0,0.5);
                                    margin: -10px auto 0 auto;">
                            {rank}
                        </div>
                    </div>
                    """
                    
                    # Detailed popup
                    popup_html = f"""
                    <div style="font-family: Arial; min-width: 200px;">
                        <h3 style="margin: 0 0 10px 0; color: {color}; border-bottom: 2px solid {color};">
                            🏔️ Location #{rank}
                        </h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="background: #f0f0f0;">
                                <td style="padding: 5px; font-weight: bold;">Suitability:</td>
                                <td style="padding: 5px; text-align: right;">
                                    <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">
                                        {score:.2f}/100
                                    </span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 5px; font-weight: bold;">Rank:</td>
                                <td style="padding: 5px; text-align: right;">#{rank}</td>
                            </tr>
                            <tr style="background: #f0f0f0;">
                                <td style="padding: 5px; font-weight: bold;">Longitude:</td>
                                <td style="padding: 5px; text-align: right;">{row.geometry.x:.6f}°</td>
                            </tr>
                            <tr>
                                <td style="padding: 5px; font-weight: bold;">Latitude:</td>
                                <td style="padding: 5px; text-align: right;">{row.geometry.y:.6f}°</td>
                            </tr>
                        </table>
                        <p style="margin: 10px 0 0 0; padding: 8px; background: #fffacd; border-radius: 3px; font-size: 11px;">
                            <b>💡 Tip:</b> This location scored highest based on slope, aspect, hillshade, and snow depth.
                        </p>
                    </div>
                    """
                    
                    # Add marker with custom icon
                    folium.Marker(
                        location=[row.geometry.y, row.geometry.x],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"<b>Rank #{rank}</b><br>Score: {score:.1f}/100<br>Click for details",
                        icon=folium.DivIcon(html=star_html)
                    ).add_to(locations_layer)
                
                print(f"  ✓ Added {len(best_locs)} best locations")
    except Exception as e:
        print(f"  ⚠ Could not add best locations: {e}")
        import traceback
        traceback.print_exc()
    
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
    suitability_layer.add_to(m)
    areas_layer.add_to(m)
    locations_layer.add_to(m)
    reference_layer.add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    
    # Add custom title with better styling
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 520px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none; z-index: 9999; 
                font-size: 16px; padding: 15px; border-radius: 10px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                color: white;">
        <h3 style="margin: 0 0 10px 0; color: white; font-size: 20px;">
            ⛷️ Skiing Resort Site Selection Analysis
        </h3>
        <p style="margin: 5px 0; font-size: 13px; opacity: 0.95;">
            <b>📊 Task 1:</b> Snow depth interpolation using Kriging<br>
            <b>🗺️ Task 2:</b> Multi-criteria suitability analysis<br>
            <b>🌟 Top Locations:</b> Click stars to see detailed information
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Enhanced legend with better styling
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; right: 30px; width: 240px; 
                background-color: white; 
                border: none;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                z-index: 9999; 
                font-size: 13px; padding: 15px; border-radius: 10px;">
        <h4 style="margin: 0 0 12px 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
            📍 Map Legend
        </h4>
        
        <div style="margin-bottom: 12px;">
            <h5 style="margin: 0 0 6px 0; color: #555; font-size: 12px;">Suitability Score:</h5>
            <div style="margin: 3px 0;">
                <span style="background: linear-gradient(to right, #26964B, #4CAF50); 
                            width: 30px; height: 18px; display: inline-block; 
                            border-radius: 3px; vertical-align: middle;"></span>
                <span style="margin-left: 8px;">90-100 (Optimal)</span>
            </div>
            <div style="margin: 3px 0;">
                <span style="background: linear-gradient(to right, #9ACD32, #CDDC39); 
                            width: 30px; height: 18px; display: inline-block; 
                            border-radius: 3px; vertical-align: middle;"></span>
                <span style="margin-left: 8px;">70-90 (Good)</span>
            </div>
            <div style="margin: 3px 0;">
                <span style="background: linear-gradient(to right, #FFC107, #FFD54F); 
                            width: 30px; height: 18px; display: inline-block; 
                            border-radius: 3px; vertical-align: middle;"></span>
                <span style="margin-left: 8px;">50-70 (Moderate)</span>
            </div>
            <div style="margin: 3px 0;">
                <span style="background: linear-gradient(to right, #F44336, #EF5350); 
                            width: 30px; height: 18px; display: inline-block; 
                            border-radius: 3px; vertical-align: middle;"></span>
                <span style="margin-left: 8px;">0-50 (Poor)</span>
            </div>
        </div>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 10px 0;">
        
        <div style="margin-bottom: 8px;">
            <h5 style="margin: 0 0 6px 0; color: #555; font-size: 12px;">Best Locations:</h5>
            <div style="margin: 3px 0;">
                <span style="font-size: 20px; color: red;">⭐</span>
                <span style="background: red; color: white; padding: 2px 6px; 
                            border-radius: 50%; font-weight: bold; font-size: 11px; 
                            margin: 0 5px;">1</span>
                <span>Top Location</span>
            </div>
            <div style="margin: 3px 0;">
                <span style="font-size: 20px; color: #8B0000;">⭐</span>
                <span style="background: #8B0000; color: white; padding: 2px 6px; 
                            border-radius: 50%; font-weight: bold; font-size: 11px; 
                            margin: 0 5px;">2-3</span>
                <span>Top 3</span>
            </div>
            <div style="margin: 3px 0;">
                <span style="font-size: 20px; color: orange;">⭐</span>
                <span style="background: orange; color: white; padding: 2px 6px; 
                            border-radius: 50%; font-weight: bold; font-size: 11px; 
                            margin: 0 5px;">4+</span>
                <span>Other Locations</span>
            </div>
        </div>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 10px 0;">
        
        <div>
            <h5 style="margin: 0 0 6px 0; color: #555; font-size: 12px;">Reference Layers:</h5>
            <div style="margin: 3px 0;">
                <span style="border-left: 4px solid blue; padding-left: 8px; margin-left: 4px;">Dam Line</span>
            </div>
            <div style="margin: 3px 0;">
                <span style="border-left: 4px solid brown; padding-left: 8px; margin-left: 4px;">Ridge Lines</span>
            </div>
        </div>
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
