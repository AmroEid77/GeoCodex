# -*- coding: utf-8 -*-
"""
Main Orchestrator for Skiing Resort Site Selection Analysis

This module coordinates two main tasks:
1. Snow depth interpolation comparison (IDW, Kriging, Spline)
2. Ski resort suitability analysis (slope, aspect, hillshade, weighted overlay)
"""
import os
import sys

# Fix Windows console encoding for Unicode characters and disable buffering
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
else:
    # For Unix-like systems, also disable buffering
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# Fix PROJ database conflict: Use conda environment's PROJ instead of PostgreSQL's
try:
    import pyproj
    correct_proj_dir = pyproj.datadir.get_data_dir()
    os.environ['PROJ_LIB'] = correct_proj_dir
except Exception:
    pass  # Silent fail if pyproj not available

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import rasterio
from rasterio.transform import from_bounds

from .config import (
    INPUT_FILES, OUTPUT_FILES, OUTPUT_DIR,
    SNOW_DEPTH_FIELD, TARGET_CRS, OPTIONS,
    COLORMAP_SNOW, COLORMAP_SLOPE, COLORMAP_ASPECT, COLORMAP_SUITABILITY,
    SNOW_DEPTH_CONSTRAINT
)
from .data_loader import DataLoader
from .interpolation import IDWInterpolator, KrigingInterpolator, SplineInterpolator
from .site_selection import SlopeAnalyzer, AspectAnalyzer, ShadingAnalyzer, SuitabilityModel
from .utils.validation_metrics import calculate_metrics, compare_methods
from .utils.qml_generator import (
    create_snow_depth_qml, create_slope_qml, 
    create_aspect_qml, create_suitability_qml
)
from .utils.map_generator import create_interactive_map


class SkiingResortAnalysis:
    """Main orchestrator for skiing resort site selection analysis"""
    
    def __init__(self, verbose: bool = None):
        """
        Initialize analysis
        
        Args:
            verbose: Print detailed progress (default: from config)
        """
        if verbose is None:
            verbose = OPTIONS['verbose']
        
        self.verbose = verbose
        self.loader = DataLoader(target_crs=TARGET_CRS)
        
        # Data containers
        self.dem_array = None
        self.transform = None
        self.meta = None
        self.snow_points = None
        self.cell_size = None
        
        # Interpolation results
        self.interpolators = {}
        self.snow_interpolated = {}
        
        # Terrain analysis results
        self.slope_analyzer = None
        self.aspect_analyzer = None
        self.shading_analyzer = None
        self.suitability_model = None
        
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print("="*70)
        print("SKI RESORT SITE SELECTION ANALYSIS")
        print("="*70)
    
    def load_data(self):
        """Load all required data"""
        print("\n" + "="*70)
        print("STEP 1: DATA LOADING")
        print("="*70)
        
        # Load DEM and snow points
        self.dem_array, self.transform, self.meta, self.snow_points = self.loader.load_all()
        
        # Calculate cell size
        self.cell_size = self.transform[0]  # Assuming square pixels
        
        print(f"\n✓ Data loading complete")
        print(f"  DEM: {self.dem_array.shape}")
        print(f"  Cell size: {self.cell_size}m")
        print(f"  Snow points: {len(self.snow_points)}")
    
    def task1_interpolate_snow(self):
        """
        Task 1: Compare snow depth interpolation methods
        
        Steps:
        1. Apply IDW, Kriging, and Spline interpolation
        2. Perform cross-validation
        3. Compare accuracy metrics
        4. Export results
        """
        print("\n" + "="*70)
        print("TASK 1: SNOW DEPTH INTERPOLATION COMPARISON")
        print("="*70)
        
        # Get DEM extent for interpolation grid
        extent = self.loader.get_dem_extent()
        
        # Initialize interpolators
        self.interpolators = {
            'IDW': IDWInterpolator(),
            'Kriging': KrigingInterpolator(),
            'Spline': SplineInterpolator(),
        }
        
        validation_results = []
        
        # Process each interpolation method
        for method_name, interpolator in self.interpolators.items():
            print(f"\n{'─'*70}")
            print(f"Method: {method_name}")
            print(f"{'─'*70}")
            
            # Fit model to all points
            interpolator.fit(self.snow_points, SNOW_DEPTH_FIELD)
            
            # Interpolate to DEM grid
            print(f"\nInterpolating to grid...")
            snow_grid, x_grid, y_grid = interpolator.interpolate_to_grid(
                extent['minx'], extent['maxx'],
                extent['miny'], extent['maxy'],
                self.cell_size
            )
            
            # Store result
            self.snow_interpolated[method_name] = snow_grid
            
            # Cross-validation
            print(f"\nCross-validation...")
            observed, predicted = interpolator.cross_validate(
                self.snow_points, SNOW_DEPTH_FIELD
            )
            
            # Calculate metrics
            metrics = calculate_metrics(observed, predicted)
            metrics['method'] = method_name
            validation_results.append(metrics)
            
            print(f"\n  Validation Metrics:")
            print(f"    RMSE: {metrics['rmse']:.4f}")
            print(f"    MAE: {metrics['mae']:.4f}")
            print(f"    R²: {metrics['r2']:.4f}")
            
            # Export interpolated raster if configured
            if OPTIONS['export_intermediate']:
                output_key = f'snow_{method_name.lower()}'
                if output_key in OUTPUT_FILES:
                    self._save_raster(
                        snow_grid,
                        OUTPUT_FILES[output_key],
                        extent
                    )
        
        # Compare methods
        print(f"\n{'─'*70}")
        print("INTERPOLATION COMPARISON")
        print(f"{'─'*70}")
        compare_methods(validation_results)
        
        # Save validation results to CSV
        df_validation = pd.DataFrame(validation_results)
        df_validation.to_csv(OUTPUT_FILES['validation_csv'], index=False)
        print(f"\n✓ Validation results saved to: {OUTPUT_FILES['validation_csv']}")
        
        # Create visualization
        if OPTIONS['create_visualizations']:
            self._visualize_interpolation_comparison()
        
        print(f"\n✓ Task 1 complete: Snow interpolation")
    
    def task2_suitability_analysis(self):
        """
        Task 2: Ski resort suitability analysis
        
        Steps:
        1. Calculate slope from DEM
        2. Calculate aspect from DEM
        3. Calculate hillshade from DEM
        4. Calculate suitability scores for each factor
        5. Weighted overlay to get overall suitability
        6. Extract suitable areas and best locations
        7. Export results
        """
        print("\n" + "="*70)
        print("TASK 2: SKI RESORT SUITABILITY ANALYSIS")
        print("="*70)
        
        # Initialize analyzers
        self.slope_analyzer = SlopeAnalyzer()
        self.aspect_analyzer = AspectAnalyzer()
        self.shading_analyzer = ShadingAnalyzer(azimuth=315, altitude=45)
        self.suitability_model = SuitabilityModel()
        
        # 1. Slope analysis
        slope = self.slope_analyzer.calculate_slope(self.dem_array, self.cell_size)
        slope_suitability = self.slope_analyzer.calculate_suitability(slope)
        
        if OPTIONS['export_intermediate']:
            self.slope_analyzer.save_slope(
                OUTPUT_FILES['slope'],
                self.transform,
                TARGET_CRS
            )
        
        # 2. Aspect analysis
        aspect = self.aspect_analyzer.calculate_aspect(self.dem_array, self.cell_size)
        aspect_suitability = self.aspect_analyzer.calculate_suitability(aspect)
        
        if OPTIONS['export_intermediate']:
            self.aspect_analyzer.save_aspect(
                OUTPUT_FILES['aspect'],
                self.transform,
                TARGET_CRS
            )
        
        # 3. Hillshade analysis
        hillshade = self.shading_analyzer.calculate_hillshade(self.dem_array, self.cell_size)
        hillshade_suitability = self.shading_analyzer.calculate_suitability(hillshade)
        
        if OPTIONS['export_intermediate']:
            self.shading_analyzer.save_hillshade(
                OUTPUT_FILES['hillshade'],
                self.transform,
                TARGET_CRS
            )
        
        # 4. Snow depth constraint (HARD THRESHOLD)
        print(f"\n{'='*60}")
        print("SNOW DEPTH CONSTRAINT (Hard Threshold)")
        print(f"{'='*60}")
        
        # Use Kriging interpolation (best R² = 0.770)
        snow_grid = self.snow_interpolated.get('Kriging')
        if snow_grid is None:
            print("⚠ Warning: Kriging interpolation not found, using IDW")
            snow_grid = self.snow_interpolated.get('IDW')
        
        if snow_grid is not None:
            # Resample snow grid to match DEM dimensions if needed
            if snow_grid.shape != slope_suitability.shape:
                print(f"  Resampling snow grid from {snow_grid.shape} to {slope_suitability.shape}...")
                from scipy.ndimage import zoom
                zoom_factors = (
                    slope_suitability.shape[0] / snow_grid.shape[0],
                    slope_suitability.shape[1] / snow_grid.shape[1]
                )
                snow_grid = zoom(snow_grid, zoom_factors, order=1)  # Bilinear interpolation
            
            min_snow = SNOW_DEPTH_CONSTRAINT['min_snow']
            print(f"  Snow depth range: {np.nanmin(snow_grid):.2f} - {np.nanmax(snow_grid):.2f} cm")
            print(f"  Minimum required: {min_snow:.1f} cm")
            
            cells_below_threshold = np.sum((snow_grid < min_snow) & ~np.isnan(snow_grid))
            total_cells = np.sum(~np.isnan(snow_grid))
            print(f"  Cells excluded: {cells_below_threshold}/{total_cells} ({cells_below_threshold/total_cells*100:.1f}%)")
        else:
            print("  ⚠ Warning: No snow interpolation available")
            print("  Proceeding without snow constraint (all areas allowed)")
        
        # 5. Overall suitability (weighted overlay with snow as hard constraint)
        overall_suitability = self.suitability_model.calculate_suitability(
            slope_suitability,
            aspect_suitability,
            hillshade_suitability,
            snow_depth=snow_grid,
            min_snow_threshold=SNOW_DEPTH_CONSTRAINT['min_snow']
        )
        
        # Diagnostic: Show what limits suitability
        print(f"\n{'='*60}")
        print("SUITABILITY LIMITING FACTORS ANALYSIS")
        print(f"{'='*60}")
        
        # Find cells with good terrain but excluded by snow constraint
        if snow_grid is not None:
            good_terrain = (slope_suitability > 70) & (aspect_suitability > 70)
            insufficient_snow = snow_grid < SNOW_DEPTH_CONSTRAINT['min_snow']
            excluded_by_snow = good_terrain & insufficient_snow
            
            if np.any(excluded_by_snow):
                n_cells = np.sum(excluded_by_snow)
                print(f"\n  Areas with good terrain but excluded by snow constraint: {n_cells} cells")
                print(f"    Average snow depth: {snow_grid[excluded_by_snow].mean():.1f} cm")
                print(f"    Required minimum: {SNOW_DEPTH_CONSTRAINT['min_snow']:.1f} cm")
                print(f"    → These areas have proper slope/aspect but insufficient snow coverage")
            
            # Find cells with sufficient snow but poor terrain
            sufficient_snow = snow_grid >= SNOW_DEPTH_CONSTRAINT['min_snow']
            poor_overall = overall_suitability < 50
            good_snow_poor_terrain = sufficient_snow & poor_overall & (overall_suitability > 0)
            
            if np.any(good_snow_poor_terrain):
                n_cells = np.sum(good_snow_poor_terrain)
                print(f"\n  Areas with sufficient snow (≥{SNOW_DEPTH_CONSTRAINT['min_snow']:.1f} cm) but poor terrain suitability: {n_cells} cells")
                
                # What's limiting them?
                poor_slope = slope_suitability[good_snow_poor_terrain].mean()
                poor_aspect = aspect_suitability[good_snow_poor_terrain].mean()
                poor_shade = hillshade_suitability[good_snow_poor_terrain].mean()
                
                print(f"    Average terrain scores:")
                print(f"      Slope: {poor_slope:.1f} (should be >70)")
                print(f"      Aspect: {poor_aspect:.1f} (should be >70)")
                print(f"      Hillshade: {poor_shade:.1f} (should be >70)")
                
                # Identify main limiting factor
                scores = {'Slope': poor_slope, 'Aspect': poor_aspect, 'Hillshade': poor_shade}
                limiting_factor = min(scores, key=scores.get)
                print(f"    → Main limiting factor: {limiting_factor} ({scores[limiting_factor]:.1f})")
        
        print(f"{'='*60}\n")
        
        # Save suitability raster
        self.suitability_model.save_suitability(
            OUTPUT_FILES['suitability'],
            self.transform,
            TARGET_CRS
        )
        
        # 5. Extract suitable areas
        suitable_areas = self.suitability_model.extract_suitable_areas(
            self.transform,
            TARGET_CRS
        )
        
        if len(suitable_areas) > 0:
            suitable_areas.to_file(OUTPUT_FILES['suitable_areas'])
            print(f"✓ Suitable areas saved to: {OUTPUT_FILES['suitable_areas']}")
        
        # 6. Find best locations (with 2km minimum separation for diversity)
        best_locations = self.suitability_model.find_best_locations(
            self.transform,
            TARGET_CRS,
            n_locations=5,
            min_distance=2000.0  # 2km separation
        )
        
        if len(best_locations) > 0:
            best_locations.to_file(OUTPUT_FILES['best_locations'], driver='GeoJSON')
            print(f"✓ Best locations saved to: {OUTPUT_FILES['best_locations']}")
        
        # 7. Create visualization
        if OPTIONS['create_visualizations']:
            self._visualize_suitability_analysis(
                slope, aspect, hillshade, overall_suitability
            )
        
        print(f"\n✓ Task 2 complete: Suitability analysis")
    
    def _save_raster(self, array: np.ndarray, output_path: str, extent: dict):
        """
        Save numpy array as GeoTIFF
        
        Args:
            array: Data array
            output_path: Output file path
            extent: Dictionary with minx, miny, maxx, maxy
        """
        height, width = array.shape
        
        # Create transform from extent
        transform = from_bounds(
            extent['minx'], extent['miny'],
            extent['maxx'], extent['maxy'],
            width, height
        )
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=array.dtype,
            crs=TARGET_CRS,
            transform=transform,
            nodata=np.nan
        ) as dst:
            dst.write(array, 1)
        
        print(f"  ✓ Saved: {output_path}")
    
    def _visualize_interpolation_comparison(self):
        """Create visualization comparing interpolation methods"""
        print("\nCreating interpolation comparison visualization...")
        
        n_methods = len(self.snow_interpolated)
        fig, axes = plt.subplots(1, n_methods, figsize=(6*n_methods, 5))
        
        if n_methods == 1:
            axes = [axes]
        
        for idx, (method_name, snow_grid) in enumerate(self.snow_interpolated.items()):
            ax = axes[idx]
            
            im = ax.imshow(
                snow_grid,
                cmap=COLORMAP_SNOW,
                origin='upper',
                interpolation='bilinear'
            )
            
            ax.set_title(f'{method_name} Interpolation', fontsize=14, fontweight='bold')
            ax.set_xlabel('Column')
            ax.set_ylabel('Row')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label('Snow Depth', rotation=270, labelpad=20)
        
        plt.tight_layout()
        plt.savefig(OUTPUT_FILES['interpolation_comparison'], dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Visualization saved to: {OUTPUT_FILES['interpolation_comparison']}")
    
    def _visualize_suitability_analysis(self, slope, aspect, hillshade, suitability):
        """Create visualization of suitability analysis"""
        print("\nCreating suitability analysis visualization...")
        
        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        # 1. Slope
        ax1 = fig.add_subplot(gs[0, 0])
        im1 = ax1.imshow(slope, cmap=COLORMAP_SLOPE, origin='upper')
        ax1.set_title('Slope (degrees)', fontsize=12, fontweight='bold')
        plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
        
        # 2. Aspect
        ax2 = fig.add_subplot(gs[0, 1])
        im2 = ax2.imshow(aspect, cmap=COLORMAP_ASPECT, origin='upper', vmin=0, vmax=360)
        ax2.set_title('Aspect (degrees)', fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
        
        # 3. Hillshade
        ax3 = fig.add_subplot(gs[0, 2])
        im3 = ax3.imshow(hillshade, cmap='gray', origin='upper')
        ax3.set_title('Hillshade', fontsize=12, fontweight='bold')
        plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
        
        # 4. Slope Suitability
        ax4 = fig.add_subplot(gs[1, 0])
        im4 = ax4.imshow(self.slope_analyzer.suitability_array, cmap=COLORMAP_SUITABILITY, origin='upper', vmin=0, vmax=100)
        ax4.set_title('Slope Suitability', fontsize=12, fontweight='bold')
        plt.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)
        
        # 5. Aspect Suitability
        ax5 = fig.add_subplot(gs[1, 1])
        im5 = ax5.imshow(self.aspect_analyzer.suitability_array, cmap=COLORMAP_SUITABILITY, origin='upper', vmin=0, vmax=100)
        ax5.set_title('Aspect Suitability', fontsize=12, fontweight='bold')
        plt.colorbar(im5, ax=ax5, fraction=0.046, pad=0.04)
        
        # 6. Overall Suitability
        ax6 = fig.add_subplot(gs[1, 2])
        im6 = ax6.imshow(suitability, cmap=COLORMAP_SUITABILITY, origin='upper', vmin=0, vmax=100)
        ax6.set_title('Overall Suitability', fontsize=12, fontweight='bold')
        plt.colorbar(im6, ax=ax6, fraction=0.046, pad=0.04)
        
        # Remove axis ticks
        for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
            ax.set_xticks([])
            ax.set_yticks([])
        
        plt.suptitle('Ski Resort Suitability Analysis', fontsize=16, fontweight='bold', y=0.98)
        plt.savefig(OUTPUT_FILES['suitability_map_png'], dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Visualization saved to: {OUTPUT_FILES['suitability_map_png']}")
    
    def _generate_qml_styles(self):
        """Generate QML style files for QGIS layers"""
        print("\n" + "="*70)
        print("GENERATING QML STYLE FILES FOR QGIS")
        print("="*70)
        
        # Snow depth style
        create_snow_depth_qml(OUTPUT_FILES['qml_snow'], min_val=0, max_val=28)
        
        # Slope style
        create_slope_qml(OUTPUT_FILES['qml_slope'], min_val=0, max_val=65)
        
        # Aspect style
        create_aspect_qml(OUTPUT_FILES['qml_aspect'], min_val=0, max_val=360)
        
        # Suitability style
        create_suitability_qml(OUTPUT_FILES['qml_suitability'], min_val=0, max_val=100)
        
        print("✓ All QML styles generated")
    
    def _generate_html_map(self):
        """Generate interactive HTML map"""
        print("\n" + "="*70)
        print("GENERATING INTERACTIVE HTML MAP")
        print("="*70)
        
        try:
            create_interactive_map(
                dem_path=INPUT_FILES['dem'],
                snow_raster=OUTPUT_FILES['snow_kriging'],
                suitability_raster=OUTPUT_FILES['suitability'],
                suitable_areas_shp=OUTPUT_FILES['suitable_areas'],
                best_locations_geojson=OUTPUT_FILES['best_locations'],
                dam_line_shp=INPUT_FILES['dam_line'],
                ridges_shp=INPUT_FILES['ridges'],
                output_html=OUTPUT_FILES['interactive_map']
            )
            print("✓ HTML map generation complete")
        except Exception as e:
            print(f"⚠ Warning: HTML map generation failed: {e}")
            print("  (This is optional - other outputs are still valid)")
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        try:
            # Load data
            self.load_data()
            
            # Task 1: Interpolation
            self.task1_interpolate_snow()
            
            # Task 2: Suitability
            self.task2_suitability_analysis()
            
            # Generate QML style files for QGIS
            self._generate_qml_styles()
            
            # Generate interactive HTML map
            self._generate_html_map()
            
            print("\n" + "="*70)
            print("ANALYSIS COMPLETE")
            print("="*70)
            print(f"\nAll outputs saved to: {OUTPUT_DIR}")
            print("\nOutput files:")
            for key, path in OUTPUT_FILES.items():
                if os.path.exists(path):
                    print(f"  ✓ {key}: {os.path.basename(path)}")
            
            return True
            
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    analysis = SkiingResortAnalysis(verbose=True)
    success = analysis.run_full_analysis()
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())