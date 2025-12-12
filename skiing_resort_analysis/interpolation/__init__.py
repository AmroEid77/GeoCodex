# -*- coding: utf-8 -*-
"""
Interpolation methods for snow depth data
"""
from .base_interpolator import BaseInterpolator
from .idw_interpolator import IDWInterpolator
from .kriging_interpolator import KrigingInterpolator
from .spline_interpolator import SplineInterpolator

__all__ = [
    'BaseInterpolator',
    'IDWInterpolator',
    'KrigingInterpolator',
    'SplineInterpolator',
]