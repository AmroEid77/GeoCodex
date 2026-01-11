# -*- coding: utf-8 -*-
"""
Utility modules for skiing resort analysis
"""

from .raster_utils import (
    create_empty_raster_like,
    calculate_slope,
    calculate_aspect,
    calculate_hillshade,
    normalize_array,
    reclassify_array
)

from .validation_metrics import (
    calculate_metrics,
    print_metrics,
    compare_methods
)

from .location_visualizer import (
    create_location_suitability_plot,
    create_location_detail_plots
)

__all__ = [
    'create_empty_raster_like',
    'calculate_slope',
    'calculate_aspect',
    'calculate_hillshade',
    'normalize_array',
    'reclassify_array',
    'calculate_metrics',
    'print_metrics',
    'compare_methods',
    'create_location_suitability_plot',
    'create_location_detail_plots',
]