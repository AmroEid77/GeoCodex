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
]