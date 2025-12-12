# -*- coding: utf-8 -*-
"""
Tree Priority Workflow - Preset workflow for tree cutting priority analysis
Integrates the tree_priority_analysis module with GeoCodex
"""

import os
import sys
from typing import Dict, Tuple, Optional

# Add tree_priority_analysis to path
plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, plugin_dir)

try:
    from tree_priority_analysis.main import TreePriorityAnalysis
    from tree_priority_analysis.config import WEIGHTS, DATA_DIR, OUTPUT_SHAPEFILE
    TREE_PRIORITY_AVAILABLE = True
except ImportError as e:
    TREE_PRIORITY_AVAILABLE = False
    IMPORT_ERROR = str(e)

try:
    from qgis.core import QgsVectorLayer, QgsProject, QgsMessageLog, Qgis
    log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex', Qgis.Info)
except ImportError:
    log = print


class TreePriorityWorkflow:
    """
    Preset workflow for tree cutting priority analysis.
    
    Triggered by natural language queries like:
    - "run tree priority analysis"
    - "calculate tree cutting priorities"
    - "analyze tree removal priorities for fire creek"
    """
    
    # Keywords that trigger this workflow
    TRIGGER_KEYWORDS = [
        'tree priority',
        'tree cutting',
        'tree removal',
        'cutting priority',
        'tree analysis',
        'fire creek tree',
    ]
    
    def __init__(self, data_dir: str = None, custom_weights: Dict[str, float] = None):
        """
        Initialize tree priority workflow
        
        Args:
            data_dir: Custom data directory (overrides default)
            custom_weights: Custom factor weights
        """
        if not TREE_PRIORITY_AVAILABLE:
            raise ImportError(f"Tree priority analysis not available: {IMPORT_ERROR}")
        
        self.data_dir = data_dir
        self.custom_weights = custom_weights
        self.analysis = None
    
    @classmethod
    def should_trigger(cls, user_query: str) -> bool:
        """
        Check if user query should trigger this workflow
        
        Args:
            user_query: The user's natural language query
            
        Returns:
            True if workflow should be triggered
        """
        query_lower = user_query.lower()
        return any(keyword in query_lower for keyword in cls.TRIGGER_KEYWORDS)
    
    def run(self, user_query: str = None, load_to_qgis: bool = True) -> Tuple[bool, str]:
        """
        Execute the tree priority analysis workflow
        
        Args:
            user_query: Optional - natural language query (for parsing parameters)
            load_to_qgis: Whether to load results as QGIS layer
            
        Returns:
            Tuple of (success, message)
        """
        log("=" * 70)
        log("Tree Priority Workflow: Starting analysis...")
        log("=" * 70)
        
        try:
            # Parse any custom parameters from query
            weights = self._parse_weights_from_query(user_query) if user_query else None
            
            # Create analysis instance
            self.analysis = TreePriorityAnalysis(
                data_dir=self.data_dir,
                weights=weights or self.custom_weights,
                verbose=True
            )
            
            # Run analysis
            log("Executing tree priority analysis...")
            result = self.analysis.run(
                export_results=True,
                create_visualizations=True
            )
            
            # Load to QGIS if requested
            if load_to_qgis:
                success, msg = self._load_to_qgis(result)
                if not success:
                    return False, f"Analysis completed but layer loading failed: {msg}"
            
            # Generate summary message
            summary = self._generate_summary(result)
            
            log("Tree Priority Workflow: COMPLETE")
            return True, summary
            
        except FileNotFoundError as e:
            error_msg = (
                f"Data files not found: {e}\n\n"
                f"Please ensure shapefiles are in: {DATA_DIR}\n"
                f"Required files:\n"
                f"  - CuttingGrids.shp\n"
                f"  - SBNFMortalityt.shp\n"
                f"  - Communityfeatures.shp\n"
                f"  - EgressRoutes.shp\n"
                f"  - PopulatedAreast.shp\n"
                f"  - Transmission.shp (and related utility layers)"
            )
            log(f"ERROR: {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Tree priority analysis failed: {e}"
            log(f"ERROR: {error_msg}")
            import traceback
            log(traceback.format_exc())
            return False, error_msg
    
    def _parse_weights_from_query(self, query: str) -> Optional[Dict[str, float]]:
        """
        Parse custom weights from natural language query
        
        Examples:
        - "prioritize mortality at 40%"
        - "focus more on utilities"
        - "equal weights for all factors"
        
        Returns:
            Dictionary of weights or None if using defaults
        """
        # TODO: Implement LLM-based parameter extraction
        # For now, return None to use default weights
        return None
    
    def _load_to_qgis(self, result) -> Tuple[bool, str]:
        """
        Load analysis results as QGIS layer
        
        Args:
            result: GeoDataFrame with analysis results
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # The results are already saved to shapefile by the analysis
            shapefile_path = OUTPUT_SHAPEFILE
            
            if not os.path.exists(shapefile_path):
                return False, f"Output shapefile not found: {shapefile_path}"
            
            # Load as vector layer
            layer = QgsVectorLayer(shapefile_path, "Tree Cutting Priority", "ogr")
            
            if not layer.isValid():
                return False, f"Failed to load layer: {layer.error().summary()}"
            
            # Add to QGIS project
            QgsProject.instance().addMapLayer(layer)
            
            # Apply styling (optional - can be enhanced)
            self._apply_priority_styling(layer)
            
            msg = f"Layer 'Tree Cutting Priority' added with {layer.featureCount()} zones"
            log(msg)
            return True, msg
            
        except Exception as e:
            return False, f"Error loading to QGIS: {e}"
    
    def _apply_priority_styling(self, layer):
        """
        Apply graduated color styling based on priority class
        
        Args:
            layer: QgsVectorLayer to style
        """
        try:
            from qgis.core import (
                QgsGraduatedSymbolRenderer, 
                QgsRendererRange,
                QgsSymbol,
                QgsStyle
            )
            from PyQt5.QtGui import QColor
            
            # Define priority colors (matching config.COLOR_MAP)
            priority_ranges = [
                (0, 2, 'Very Low', QColor('#1a9850')),    # Dark green
                (2, 4, 'Low', QColor('#91cf60')),         # Light green
                (4, 6, 'Medium', QColor('#fee08b')),      # Yellow
                (6, 8, 'High', QColor('#fc8d59')),        # Orange
                (8, 10, 'Very High', QColor('#d73027')),  # Red
            ]
            
            ranges = []
            for min_val, max_val, label, color in priority_ranges:
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.setColor(color)
                symbol.setOpacity(0.7)
                
                ranges.append(QgsRendererRange(min_val, max_val, symbol, label))
            
            # Create renderer
            renderer = QgsGraduatedSymbolRenderer('prior_scr', ranges)  # 'prior_scr' = priority_score (shortened)
            layer.setRenderer(renderer)
            layer.triggerRepaint()
            
            log("Applied priority styling to layer")
            
        except Exception as e:
            log(f"Warning: Could not apply styling: {e}")
            # Non-critical error - layer still loads without styling
    
    def _generate_summary(self, result) -> str:
        """
        Generate human-readable summary of results
        
        Args:
            result: GeoDataFrame with analysis results
            
        Returns:
            Summary message string
        """
        total_cells = len(result)
        mean_score = result['priority_score'].mean()
        
        # Count by priority class
        class_counts = result['priority_class'].value_counts()
        
        very_high = class_counts.get('Very High', 0)
        high = class_counts.get('High', 0)
        medium = class_counts.get('Medium', 0)
        low = class_counts.get('Low', 0)
        very_low = class_counts.get('Very Low', 0)
        
        # Find top priority cell
        top_cell = result.nlargest(1, 'priority_score').iloc[0]
        top_score = top_cell['priority_score']
        top_rank = int(top_cell['priority_rank'])
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════════╗
║           TREE CUTTING PRIORITY ANALYSIS - COMPLETE                 ║
╚══════════════════════════════════════════════════════════════════════╝

📊 ANALYSIS RESULTS:
   • Total Grid Cells: {total_cells}
   • Average Priority Score: {mean_score:.2f}/10
   • Highest Priority Score: {top_score:.2f}

🎯 PRIORITY DISTRIBUTION:
   • Very High Priority: {very_high} cells ({very_high/total_cells*100:.1f}%)
   • High Priority: {high} cells ({high/total_cells*100:.1f}%)
   • Medium Priority: {medium} cells ({medium/total_cells*100:.1f}%)
   • Low Priority: {low} cells ({low/total_cells*100:.1f}%)
   • Very Low Priority: {very_low} cells ({very_low/total_cells*100:.1f}%)

🌳 RECOMMENDATIONS:
   • Focus on {very_high + high} high-priority zones first
   • Top priority cell has score of {top_score:.2f}
   
📁 OUTPUT FILES:
   • Shapefile: output/tree_priority_result.shp
   • CSV: output/tree_priority_result.csv
   • Map: output/tree_priority_map.html
   • Visualization: output/tree_priority_map.png

✅ Results loaded to QGIS as 'Tree Cutting Priority' layer
"""
        
        return summary


def is_available() -> bool:
    """Check if tree priority workflow is available"""
    return TREE_PRIORITY_AVAILABLE


def get_error() -> str:
    """Get import error message if not available"""
    return IMPORT_ERROR if not TREE_PRIORITY_AVAILABLE else ""
