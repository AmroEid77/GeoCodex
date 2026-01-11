# -*- coding: utf-8 -*-
"""
Top Locations and Suitability Visualizer
Creates detailed visualizations of best ski resort locations
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.gridspec import GridSpec
import geopandas as gpd


def create_location_suitability_plot(suitability_array, best_locations_gdf, 
                                     suitable_areas_gdf, transform, 
                                     output_path, title="Top Ski Resort Locations"):
    """
    Create detailed visualization showing top locations on suitability map
    
    Args:
        suitability_array: 2D numpy array of suitability scores
        best_locations_gdf: GeoDataFrame with best location points
        suitable_areas_gdf: GeoDataFrame with suitable area polygons
        transform: Raster affine transform
        output_path: Path to save the figure
        title: Plot title
    """
    
    print(f"\nCreating top locations visualization...")
    
    # Create figure with multiple panels
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(2, 3, figure=fig, hspace=0.25, wspace=0.3, 
                  height_ratios=[1.2, 1], width_ratios=[1.5, 1, 1])
    
    # ========== MAIN MAP: Suitability with Top Locations ==========
    ax_main = fig.add_subplot(gs[:, 0])
    
    # Plot suitability
    im = ax_main.imshow(suitability_array, cmap='RdYlGn', origin='upper', 
                        vmin=0, vmax=100, aspect='auto')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax_main, fraction=0.046, pad=0.04)
    cbar.set_label('Suitability Score (0-100)', rotation=270, labelpad=25, fontsize=12)
    
    # Overlay best locations
    if not best_locations_gdf.empty:
        for idx, location in best_locations_gdf.iterrows():
            # Convert real-world coords to pixel coords
            x, y = location.geometry.x, location.geometry.y
            col = (x - transform.c) / transform.a
            row = (y - transform.f) / transform.e
            
            rank = location['rank']
            score = location['suitability']
            
            # Draw marker
            color = 'red' if rank <= 3 else 'orange'
            marker_size = 300 if rank <= 3 else 200
            
            ax_main.scatter(col, row, c=color, s=marker_size, 
                          marker='*', edgecolors='white', linewidths=2,
                          zorder=10, label=f"Rank {rank}" if idx < 3 else "")
            
            # Add rank label
            ax_main.text(col, row - 15, f"#{rank}\n{score:.1f}", 
                        ha='center', va='top', fontsize=10, fontweight='bold',
                        color='white', bbox=dict(boxstyle='round,pad=0.3', 
                        facecolor=color, alpha=0.8, edgecolor='white'))
    
    ax_main.set_title(f'{title}\nTop Locations Overlay', 
                     fontsize=16, fontweight='bold', pad=15)
    ax_main.set_xlabel('Column (Easting)', fontsize=11)
    ax_main.set_ylabel('Row (Northing)', fontsize=11)
    ax_main.grid(True, alpha=0.3, linestyle='--')
    
    # Add legend for top 3
    if len(best_locations_gdf) >= 3:
        handles = [
            plt.scatter([], [], c='red', s=300, marker='*', 
                       edgecolors='white', linewidths=2, label='Top 3 Locations'),
            plt.scatter([], [], c='orange', s=200, marker='*', 
                       edgecolors='white', linewidths=2, label='Other Locations')
        ]
        ax_main.legend(handles=handles, loc='upper right', fontsize=10, 
                      framealpha=0.9, edgecolor='black')
    
    # ========== PANEL: Location Rankings Table ==========
    ax_table = fig.add_subplot(gs[0, 1:])
    ax_table.axis('off')
    
    # Create ranking table
    if not best_locations_gdf.empty:
        table_data = []
        headers = ['Rank', 'Suitability', 'Coordinates (X, Y)']
        
        for idx, location in best_locations_gdf.iterrows():
            rank = location['rank']
            score = location['suitability']
            x = location.geometry.x
            y = location.geometry.y
            
            table_data.append([
                f"#{rank}",
                f"{score:.2f}",
                f"({x:.0f}, {y:.0f})"
            ])
        
        # Create table
        table = ax_table.table(cellText=table_data, colLabels=headers,
                              cellLoc='center', loc='center',
                              colWidths=[0.15, 0.25, 0.6])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        
        # Style header
        for i in range(len(headers)):
            cell = table[(0, i)]
            cell.set_facecolor('#4CAF50')
            cell.set_text_props(weight='bold', color='white')
        
        # Color code rows by rank
        for i, row_data in enumerate(table_data, 1):
            rank = int(row_data[0].strip('#'))
            if rank <= 3:
                color = '#ffebee'  # Light red
            elif rank <= 5:
                color = '#fff3e0'  # Light orange
            else:
                color = '#f5f5f5'  # Light grey
            
            for j in range(len(headers)):
                table[(i, j)].set_facecolor(color)
        
        ax_table.set_title('Location Rankings', fontsize=14, 
                          fontweight='bold', pad=15)
    
    # ========== PANEL: Suitability Distribution Histogram ==========
    ax_hist = fig.add_subplot(gs[1, 1])
    
    # Flatten and remove NaN
    suit_flat = suitability_array[~np.isnan(suitability_array)]
    
    # Create histogram
    counts, bins, patches = ax_hist.hist(suit_flat, bins=50, color='skyblue', 
                                         edgecolor='black', alpha=0.7)
    
    # Color bars by suitability class
    for i, patch in enumerate(patches):
        bin_center = (bins[i] + bins[i+1]) / 2
        if bin_center >= 80:
            patch.set_facecolor('#4CAF50')  # Green - High
        elif bin_center >= 60:
            patch.set_facecolor('#FFC107')  # Yellow - Moderate
        else:
            patch.set_facecolor('#F44336')  # Red - Low
    
    # Mark mean and median
    mean_val = np.nanmean(suitability_array)
    median_val = np.nanmedian(suitability_array)
    
    ax_hist.axvline(mean_val, color='blue', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_val:.1f}')
    ax_hist.axvline(median_val, color='purple', linestyle='--', linewidth=2, 
                   label=f'Median: {median_val:.1f}')
    
    # Mark threshold
    ax_hist.axvline(70, color='red', linestyle='-', linewidth=2, 
                   label='Threshold: 70', alpha=0.7)
    
    ax_hist.set_xlabel('Suitability Score', fontsize=11)
    ax_hist.set_ylabel('Frequency (cells)', fontsize=11)
    ax_hist.set_title('Suitability Distribution', fontsize=13, fontweight='bold')
    ax_hist.legend(loc='upper left', fontsize=9)
    ax_hist.grid(True, alpha=0.3, axis='y')
    
    # ========== PANEL: Statistics Summary ==========
    ax_stats = fig.add_subplot(gs[1, 2])
    ax_stats.axis('off')
    
    # Calculate statistics
    total_cells = (~np.isnan(suitability_array)).sum()
    high_suit = (suitability_array >= 80).sum()
    moderate_suit = ((suitability_array >= 60) & (suitability_array < 80)).sum()
    low_suit = (suitability_array < 60).sum()
    
    suitable_cells = (suitability_array >= 70).sum()
    num_regions = len(suitable_areas_gdf) if suitable_areas_gdf is not None else 0
    
    # Statistics text
    stats_text = f"""
    ANALYSIS SUMMARY
    {'='*30}
    
    Total Area:
      • {total_cells:,} cells analyzed
      • {suitable_cells:,} suitable (≥70)
      • {(suitable_cells/total_cells*100):.1f}% suitable
    
    Suitability Classes:
      • High (≥80): {high_suit:,} cells
        ({(high_suit/total_cells*100):.1f}%)
      • Moderate (60-80): {moderate_suit:,} cells
        ({(moderate_suit/total_cells*100):.1f}%)
      • Low (<60): {low_suit:,} cells
        ({(low_suit/total_cells*100):.1f}%)
    
    Regions Identified:
      • {num_regions:,} suitable regions
      • {len(best_locations_gdf)} top locations
    
    Best Location:
      • Rank #1
      • Score: {best_locations_gdf.iloc[0]['suitability']:.2f}
      • Coordinates: ({best_locations_gdf.iloc[0].geometry.x:.0f}, 
        {best_locations_gdf.iloc[0].geometry.y:.0f})
    """
    
    ax_stats.text(0.1, 0.95, stats_text, transform=ax_stats.transAxes,
                 fontsize=10, verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax_stats.set_title('Statistics', fontsize=13, fontweight='bold', pad=10)
    
    # Overall title
    fig.suptitle('Ski Resort Site Selection - Top Locations Analysis', 
                fontsize=18, fontweight='bold', y=0.98)
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Top locations visualization saved to: {output_path}")


def create_location_detail_plots(suitability_array, best_locations_gdf, transform,
                                 slope_array, aspect_array, hillshade_array, 
                                 snow_array, output_path, zoom_size=50):
    """
    Create detailed zoom-in plots for each top location showing all factors
    
    Args:
        suitability_array: 2D numpy array of suitability scores
        best_locations_gdf: GeoDataFrame with best location points
        transform: Raster affine transform
        slope_array: Slope data
        aspect_array: Aspect data
        hillshade_array: Hillshade data
        snow_array: Snow depth data
        output_path: Path to save the figure
        zoom_size: Size of zoom window (pixels)
    """
    
    print(f"\nCreating detailed location zoom plots...")
    
    # Show top 5 locations
    n_locations = min(5, len(best_locations_gdf))
    
    fig = plt.figure(figsize=(20, 4 * n_locations))
    gs = GridSpec(n_locations, 5, figure=fig, hspace=0.3, wspace=0.3)
    
    for loc_idx in range(n_locations):
        location = best_locations_gdf.iloc[loc_idx]
        
        # Convert to pixel coordinates
        x, y = location.geometry.x, location.geometry.y
        col = int((x - transform.c) / transform.a)
        row = int((y - transform.f) / transform.e)
        
        # Define zoom window
        row_min = max(0, row - zoom_size)
        row_max = min(suitability_array.shape[0], row + zoom_size)
        col_min = max(0, col - zoom_size)
        col_max = min(suitability_array.shape[1], col + zoom_size)
        
        # Extract subsets
        suit_zoom = suitability_array[row_min:row_max, col_min:col_max]
        slope_zoom = slope_array[row_min:row_max, col_min:col_max] if slope_array is not None else None
        aspect_zoom = aspect_array[row_min:row_max, col_min:col_max] if aspect_array is not None else None
        shade_zoom = hillshade_array[row_min:row_max, col_min:col_max] if hillshade_array is not None else None
        snow_zoom = snow_array[row_min:row_max, col_min:col_max] if snow_array is not None else None
        
        # Center point in zoom
        center_row = row - row_min
        center_col = col - col_min
        
        # Plot 1: Suitability
        ax1 = fig.add_subplot(gs[loc_idx, 0])
        im1 = ax1.imshow(suit_zoom, cmap='RdYlGn', vmin=0, vmax=100, origin='upper')
        ax1.plot(center_col, center_row, '*', color='red', markersize=20, 
                markeredgecolor='white', markeredgewidth=2)
        ax1.set_title(f"Rank #{location['rank']}: Suitability {location['suitability']:.1f}", 
                     fontweight='bold')
        plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
        ax1.set_xticks([])
        ax1.set_yticks([])
        
        # Plot 2: Slope
        if slope_zoom is not None:
            ax2 = fig.add_subplot(gs[loc_idx, 1])
            im2 = ax2.imshow(slope_zoom, cmap='terrain', origin='upper')
            ax2.plot(center_col, center_row, '*', color='red', markersize=15,
                    markeredgecolor='white', markeredgewidth=2)
            ax2.set_title('Slope (degrees)', fontweight='bold')
            plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
            ax2.set_xticks([])
            ax2.set_yticks([])
        
        # Plot 3: Aspect
        if aspect_zoom is not None:
            ax3 = fig.add_subplot(gs[loc_idx, 2])
            im3 = ax3.imshow(aspect_zoom, cmap='hsv', vmin=0, vmax=360, origin='upper')
            ax3.plot(center_col, center_row, '*', color='red', markersize=15,
                    markeredgecolor='white', markeredgewidth=2)
            ax3.set_title('Aspect (degrees)', fontweight='bold')
            plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
            ax3.set_xticks([])
            ax3.set_yticks([])
        
        # Plot 4: Hillshade
        if shade_zoom is not None:
            ax4 = fig.add_subplot(gs[loc_idx, 3])
            im4 = ax4.imshow(shade_zoom, cmap='gray', origin='upper')
            ax4.plot(center_col, center_row, '*', color='red', markersize=15,
                    markeredgecolor='white', markeredgewidth=2)
            ax4.set_title('Hillshade', fontweight='bold')
            plt.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)
            ax4.set_xticks([])
            ax4.set_yticks([])
        
        # Plot 5: Snow Depth
        if snow_zoom is not None:
            ax5 = fig.add_subplot(gs[loc_idx, 4])
            im5 = ax5.imshow(snow_zoom, cmap='Blues', origin='upper')
            ax5.plot(center_col, center_row, '*', color='red', markersize=15,
                    markeredgecolor='white', markeredgewidth=2)
            ax5.set_title('Snow Depth (cm)', fontweight='bold')
            plt.colorbar(im5, ax=ax5, fraction=0.046, pad=0.04)
            ax5.set_xticks([])
            ax5.set_yticks([])
    
    fig.suptitle('Detailed View of Top 5 Locations - All Factors', 
                fontsize=18, fontweight='bold', y=0.995)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Detailed location plots saved to: {output_path}")
