# -*- coding: utf-8 -*-
"""
Base Factor - Abstract base class for all factor calculators
Defines the interface that all factors must implement
"""

from abc import ABC, abstractmethod
import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Tuple
from ..config import SCORE_RANGE


class BaseFactor(ABC):
    """
    Abstract base class for factor calculators
    
    All factor implementations must:
    1. Inherit from this class
    2. Implement the calculate() method
    3. Return scores in the range defined by SCORE_RANGE
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.factor_name = self.__class__.__name__.replace('Factor', '')
        self.min_score, self.max_score = SCORE_RANGE
    
    def log(self, message: str):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[{self.factor_name}Factor] {message}")
    
    @abstractmethod
    def calculate(
        self, 
        grid: gpd.GeoDataFrame,
        source_data: gpd.GeoDataFrame,
        **kwargs
    ) -> pd.Series:
        """
        Calculate factor scores for each grid cell
        
        Args:
            grid: GeoDataFrame of grid cells to score
            source_data: GeoDataFrame of source features (trees, roads, etc.)
            **kwargs: Additional parameters specific to the factor
            
        Returns:
            pandas Series with scores indexed by grid cell index
        """
        pass
    
    def normalize_score(
        self, 
        values: pd.Series, 
        inverse: bool = False,
        custom_range: Tuple[float, float] = None
    ) -> pd.Series:
        """
        Normalize values to the score range (0-10 by default)
        
        Args:
            values: Raw values to normalize
            inverse: If True, lower values get higher scores
            custom_range: Override the default score range
            
        Returns:
            Normalized scores
        """
        min_val, max_val = values.min(), values.max()
        
        if max_val == min_val:
            # All values are the same, return middle score
            return pd.Series(
                (self.min_score + self.max_score) / 2,
                index=values.index
            )
        
        # Normalize to 0-1
        normalized = (values - min_val) / (max_val - min_val)
        
        # Inverse if needed (for distance: closer = higher score)
        if inverse:
            normalized = 1 - normalized
        
        # Scale to score range
        score_min, score_max = custom_range or (self.min_score, self.max_score)
        scores = score_min + normalized * (score_max - score_min)
        
        return scores
    
    def calculate_distance_score(
        self,
        distances: pd.Series,
        max_distance: float,
        decay_type: str = 'linear'
    ) -> pd.Series:
        """
        Convert distances to scores (closer = higher score)
        
        Args:
            distances: Series of distances in meters
            max_distance: Distance beyond which score = 0
            decay_type: 'linear', 'inverse', or 'exponential'
            
        Returns:
            Scores based on distance decay
        """
        # Clip distances to max
        clipped = distances.clip(upper=max_distance)
        
        if decay_type == 'linear':
            # Linear decay: score = max * (1 - distance/max_distance)
            normalized = 1 - (clipped / max_distance)
        
        elif decay_type == 'inverse':
            # Inverse distance: score = max / (1 + distance)
            normalized = 1 / (1 + clipped / 100)  # Scale by 100m
            normalized = (normalized - normalized.min()) / (normalized.max() - normalized.min())
        
        elif decay_type == 'exponential':
            # Exponential decay: score = max * exp(-distance/scale)
            scale = max_distance / 3  # Decay constant
            normalized = np.exp(-clipped / scale)
        
        else:
            raise ValueError(f"Unknown decay type: {decay_type}")
        
        # Scale to score range
        scores = self.min_score + normalized * (self.max_score - self.min_score)
        
        return scores
    
    def get_summary_stats(self, scores: pd.Series) -> str:
        """Generate summary statistics for calculated scores"""
        return (
            f"\n  Score Range: [{scores.min():.2f}, {scores.max():.2f}] | "
            f"Mean: {scores.mean():.2f} | "
            f"Std: {scores.std():.2f}"
        )