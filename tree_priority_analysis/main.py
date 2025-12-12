# -*- coding: utf-8 -*-
"""
Main Orchestrator - Run the complete tree priority analysis pipeline
Entry point for the analysis
"""

import os
import sys
import time
from typing import Optional, Dict
import geopandas as gpd

from .config import SHAPEFILES, WEIGHTS, OPTIONS
from .data_loader import DataLoader
from .factors import (
    MortalityFactor,
    CommunityFactor,
    EgressFactor,
    PopulationFactor,
    UtilityFactor
)
from .priority_calculator import PriorityCalculator
from .visualizer import Visualizer


class TreePriorityAnalysis:
    """
    Main orchestrator for tree cutting priority analysis
    
    Complete pipeline:
    1. Load data
    2. Calculate factor scores
    3. Combine into priority scores
    4. Export results and visualizations
    """
    
    def __init__(
        self,
        data_dir: str = None,
        weights: Dict[str, float] = None,
        verbose: bool = True
    ):
        """
        Initialize analysis
        
        Args:
            data_dir: Directory containing shapefiles (overrides config)
            weights: Custom factor weights (overrides config)
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.weights = weights or WEIGHTS
        self.start_time = None
        self.end_time = None
        
        # Override data directory if provided
        if data_dir:
            for key in SHAPEFILES:
                filename = os.path.basename(SHAPEFILES[key])
                SHAPEFILES[key] = os.path.join(data_dir, filename)
        
        # Initialize components
        self.data_loader = DataLoader(verbose=verbose)
        self.calculator = PriorityCalculator(weights=self.weights, verbose=verbose)
        self.visualizer = Visualizer(verbose=verbose)
        
        # Storage for intermediate results
        self.data = None
        self.grid = None
        self.factor_scores = {}
        self.result = None
    
    def log(self, message: str):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[TreePriorityAnalysis] {message}")
    
    def run(
        self,
        export_results: bool = True,
        create_visualizations: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Run the complete analysis pipeline
        
        Args:
            export_results: Whether to export results to files
            create_visualizations: Whether to create map visualizations
            
        Returns:
            GeoDataFrame with final priority results
        """
        self.start_time = time.time()
        
        self.log("=" * 70)
        self.log("TREE CUTTING PRIORITY ANALYSIS - FIRE CREEK")
        self.log("=" * 70)
        self.log(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # Step 1: Load data
            self.log("\n" + "█" * 70)
            self.log("STEP 1: LOADING DATA")
            self.log("█" * 70)
            self.data = self.data_loader.load_all()
            self.grid = self.data['grid']
            self.log(self.data_loader.get_summary())
            
            # Step 2: Calculate factor scores
            self.log("\n" + "█" * 70)
            self.log("STEP 2: CALCULATING FACTOR SCORES")
            self.log("█" * 70)
            self._calculate_all_factors()
            
            # Step 3: Combine factors into final priority
            self.log("\n" + "█" * 70)
            self.log("STEP 3: CALCULATING FINAL PRIORITY")
            self.log("█" * 70)
            self.result = self.calculator.calculate(self.grid, self.factor_scores)
            
            # Step 4: Export results
            if export_results:
                self.log("\n" + "█" * 70)
                self.log("STEP 4: EXPORTING RESULTS")
                self.log("█" * 70)
                self.visualizer.export_all(self.result, create_maps=create_visualizations)
            
            # Summary
            self.end_time = time.time()
            elapsed = self.end_time - self.start_time
            
            self.log("\n" + "=" * 70)
            self.log("ANALYSIS COMPLETE!")
            self.log("=" * 70)
            self.log(f"Total time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
            self.log(f"Grid cells processed: {len(self.result)}")
            self.log(f"Factors calculated: {len(self.factor_scores)}")
            
            # Top priority cells
            top_5 = self.result.nlargest(5, 'priority_score')
            self.log("\nTop 5 Priority Cells:")
            for idx, row in top_5.iterrows():
                self.log(f"  Rank {int(row['priority_rank']):3d}: Score {row['priority_score']:.2f} ({row['priority_class']})")
            
            self.log("\n" + "=" * 70 + "\n")
            
            return self.result
            
        except Exception as e:
            self.log(f"\n❌ ERROR: Analysis failed!")
            self.log(f"Error message: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _calculate_all_factors(self):
        """Calculate all five factor scores"""
        
        # Factor 1: Tree Mortality
        self.log("\n[1/5] Tree Mortality Factor...")
        mortality_calc = MortalityFactor(verbose=self.verbose)
        self.factor_scores['mortality'] = mortality_calc.calculate(
            self.grid,
            self.data['mortality'],
            method='weighted'  # weight by tree count
        )
        
        # Factor 2: Community Features
        self.log("\n[2/5] Community Proximity Factor...")
        community_calc = CommunityFactor(verbose=self.verbose)
        self.factor_scores['community'] = community_calc.calculate(
            self.grid,
            self.data['community'],
            decay_type='linear'
        )
        
        # Factor 3: Egress Routes
        self.log("\n[3/5] Egress Route Proximity Factor...")
        egress_calc = EgressFactor(verbose=self.verbose)
        self.factor_scores['egress'] = egress_calc.calculate(
            self.grid,
            self.data['egress'],
            decay_type='linear'
        )
        
        # Factor 4: Population
        self.log("\n[4/5] Population Density Factor...")
        population_calc = PopulationFactor(verbose=self.verbose)
        self.factor_scores['population'] = population_calc.calculate(
            self.grid,
            self.data['population'],
            method='sum'
        )
        
        # Factor 5: Electric Utilities
        self.log("\n[5/5] Utility Proximity Factor...")
        utility_calc = UtilityFactor(verbose=self.verbose)
        
        # Combine utility layers
        if OPTIONS['combine_utilities']:
            utilities = self.data_loader.combine_utility_layers()
        else:
            utilities = self.data['transmission']  # Use primary layer
        
        self.factor_scores['utility'] = utility_calc.calculate(
            self.grid,
            utilities,
            decay_type='exponential'
        )
        
        self.log("\n✓ All factor scores calculated successfully!")


def main():
    """Command-line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Tree Cutting Priority Analysis for Fire Creek'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Directory containing input shapefiles'
    )
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Skip exporting results to files'
    )
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip creating visualizations'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    # Run analysis
    analysis = TreePriorityAnalysis(
        data_dir=args.data_dir,
        verbose=not args.quiet
    )
    
    result = analysis.run(
        export_results=not args.no_export,
        create_visualizations=not args.no_viz
    )
    
    print(f"\n✓ Analysis complete! Results saved to output directory.")
    print(f"  Total cells: {len(result)}")
    print(f"  High priority cells: {(result['priority_class'].isin(['Very High', 'High'])).sum()}")


if __name__ == '__main__':
    main()