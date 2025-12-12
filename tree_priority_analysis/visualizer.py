# -*- coding: utf-8 -*-
"""
Visualizer - Export and visualize results
Supports shapefile, CSV, and HTML map outputs
"""

import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Optional
from .config import OUTPUT_SHAPEFILE, OUTPUT_CSV, OUTPUT_HTML_MAP, COLOR_MAP, OUTPUT_DIR


class Visualizer:
    """Handle visualization and export of tree priority analysis results"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def log(self, message: str):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[Visualizer] {message}")
    
    def export_shapefile(
        self,
        result: gpd.GeoDataFrame,
        output_path: str = None
    ) -> str:
        """
        Export results to shapefile
        
        Args:
            result: GeoDataFrame with priority analysis results
            output_path: Output shapefile path (defaults to config)
            
        Returns:
            Path to created shapefile
        """
        output_path = output_path or OUTPUT_SHAPEFILE
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.log(f"Exporting to shapefile: {output_path}")
        
        # Shapefile has column name length limit (10 chars)
        # Rename columns to fit
        export_df = result.copy()
        column_mapping = {
            'mortality_score': 'mort_scr',
            'community_score': 'comm_scr',
            'egress_score': 'egrs_scr',
            'population_score': 'pop_scr',
            'utility_score': 'util_scr',
            'priority_score': 'prior_scr',
            'priority_class': 'prior_cls',
            'priority_rank': 'prior_rnk',
        }
        
        export_df = export_df.rename(columns=column_mapping)
        
        # Export
        export_df.to_file(output_path)
        
        self.log(f"✓ Shapefile exported: {len(export_df)} features")
        return output_path
    
    def export_csv(
        self,
        result: gpd.GeoDataFrame,
        output_path: str = None,
        include_geometry: bool = False
    ) -> str:
        """
        Export results to CSV
        
        Args:
            result: GeoDataFrame with priority analysis results
            output_path: Output CSV path (defaults to config)
            include_geometry: Include WKT geometry in CSV
            
        Returns:
            Path to created CSV
        """
        output_path = output_path or OUTPUT_CSV
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.log(f"Exporting to CSV: {output_path}")
        
        # Prepare dataframe
        export_df = result.copy()
        
        if include_geometry:
            export_df['geometry_wkt'] = export_df.geometry.to_wkt()
        
        # Drop geometry column for CSV
        export_df = export_df.drop(columns=['geometry'])
        
        # Export
        export_df.to_csv(output_path, index=False)
        
        self.log(f"✓ CSV exported: {len(export_df)} rows")
        return output_path
    
    def create_static_map(
        self,
        result: gpd.GeoDataFrame,
        output_path: str = None,
        figsize: tuple = (15, 12),
        title: str = "Tree Cutting Priority Analysis - Fire Creek"
    ) -> str:
        """
        Create a static map visualization using matplotlib
        
        Args:
            result: GeoDataFrame with priority analysis results
            output_path: Output image path
            figsize: Figure size (width, height)
            title: Map title
            
        Returns:
            Path to created image
        """
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, 'tree_priority_map.png')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.log(f"Creating static map: {output_path}")
        
        # Create color mapping
        colors = [COLOR_MAP[cls] for cls in result['priority_class']]
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot grid with priority colors
        result.plot(
            ax=ax,
            color=colors,
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7
        )
        
        # Add title
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.axis('off')
        
        # Create legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=COLOR_MAP[cls], edgecolor='black', label=cls)
            for cls in ['Very High', 'High', 'Medium', 'Low', 'Very Low']
        ]
        ax.legend(
            handles=legend_elements,
            loc='lower right',
            title='Priority Class',
            fontsize=10,
            title_fontsize=12,
            framealpha=0.9
        )
        
        # Add statistics text
        stats_text = (
            f"Total Cells: {len(result)}\n"
            f"Mean Score: {result['priority_score'].mean():.2f}\n"
            f"Very High: {(result['priority_class'] == 'Very High').sum()} cells"
        )
        ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.log(f"✓ Static map created")
        return output_path
    
    def create_interactive_map(
        self,
        result: gpd.GeoDataFrame,
        output_path: str = None
    ) -> str:
        """
        Create an interactive HTML map using folium
        
        Args:
            result: GeoDataFrame with priority analysis results
            output_path: Output HTML path
            
        Returns:
            Path to created HTML file
        """
        try:
            import folium
            from folium import plugins
        except ImportError:
            self.log("⚠ Folium not installed, skipping interactive map")
            self.log("  Install with: pip install folium")
            return None
        
        output_path = output_path or OUTPUT_HTML_MAP
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.log(f"Creating interactive map: {output_path}")
        
        # Convert to WGS84 for web mapping
        result_wgs84 = result.to_crs("EPSG:4326")
        
        # Calculate map center
        bounds = result_wgs84.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=13,
            tiles='OpenStreetMap'
        )
        
        # Add choropleth layer
        folium.Choropleth(
            geo_data=result_wgs84,
            data=result_wgs84,
            columns=['priority_rank', 'priority_score'],
            key_on='feature.id',
            fill_color='RdYlGn_r',  # Red-Yellow-Green reversed
            fill_opacity=0.7,
            line_opacity=0.5,
            legend_name='Priority Score',
            name='Priority Zones'
        ).add_to(m)
        
        # Add popup information for each cell
        style_function = lambda x: {
            'fillColor': COLOR_MAP.get(x['properties']['priority_class'], '#gray'),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.6
        }
        
        folium.GeoJson(
            result_wgs84,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['priority_score', 'priority_class', 'priority_rank'],
                aliases=['Priority Score:', 'Class:', 'Rank:'],
                localize=True
            ),
            popup=folium.GeoJsonPopup(
                fields=['priority_score', 'priority_class', 'mortality_score', 
                        'community_score', 'egress_score', 'population_score', 'utility_score'],
                aliases=['Priority:', 'Class:', 'Mortality:', 'Community:', 
                         'Egress:', 'Population:', 'Utility:'],
                localize=True
            )
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add title
        title_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 400px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Tree Cutting Priority Analysis - Fire Creek</h4>
        <p>Interactive map showing priority zones for tree removal</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save map
        m.save(output_path)
        
        self.log(f"✓ Interactive map created")
        return output_path
    
    def create_factor_comparison_plot(
        self,
        result: gpd.GeoDataFrame,
        output_path: str = None
    ) -> str:
        """
        Create a comparison plot of all factor scores
        
        Args:
            result: GeoDataFrame with all factor scores
            output_path: Output image path
            
        Returns:
            Path to created image
        """
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, 'factor_comparison.png')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.log(f"Creating factor comparison plot: {output_path}")
        
        # Extract factor scores
        factor_columns = [col for col in result.columns if col.endswith('_score') and col != 'priority_score']
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()
        
        # Plot each factor
        for idx, col in enumerate(factor_columns):
            if idx < len(axes):
                ax = axes[idx]
                result.plot(
                    column=col,
                    ax=ax,
                    cmap='RdYlGn',
                    edgecolor='black',
                    linewidth=0.3,
                    legend=True,
                    vmin=0,
                    vmax=10
                )
                ax.set_title(col.replace('_score', '').title(), fontsize=12, fontweight='bold')
                ax.axis('off')
        
        # Plot final priority in the last subplot
        if len(factor_columns) < len(axes):
            ax = axes[-1]
            result.plot(
                column='priority_score',
                ax=ax,
                cmap='RdYlGn',
                edgecolor='black',
                linewidth=0.3,
                legend=True,
                vmin=0,
                vmax=10
            )
            ax.set_title('Final Priority Score', fontsize=12, fontweight='bold')
            ax.axis('off')
        
        plt.suptitle('Factor Score Comparison', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.log(f"✓ Factor comparison plot created")
        return output_path
    
    def export_all(
        self,
        result: gpd.GeoDataFrame,
        create_maps: bool = True
    ) -> dict:
        """
        Export all outputs (shapefile, CSV, maps)
        
        Args:
            result: GeoDataFrame with analysis results
            create_maps: Whether to create map visualizations
            
        Returns:
            Dictionary of created file paths
        """
        self.log("=" * 70)
        self.log("Exporting all outputs...")
        self.log("=" * 70)
        
        outputs = {}
        
        # Export shapefile
        outputs['shapefile'] = self.export_shapefile(result)
        
        # Export CSV
        outputs['csv'] = self.export_csv(result)
        
        if create_maps:
            # Create static map
            outputs['static_map'] = self.create_static_map(result)
            
            # Create factor comparison
            outputs['factor_plot'] = self.create_factor_comparison_plot(result)
            
            # Create interactive map
            interactive = self.create_interactive_map(result)
            if interactive:
                outputs['interactive_map'] = interactive
        
        self.log("\n✓ All outputs exported successfully!")
        self.log("\nOutput files:")
        for output_type, path in outputs.items():
            self.log(f"  {output_type:15} : {path}")
        
        return outputs