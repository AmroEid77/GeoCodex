# -*- coding: utf-8 -*-
"""
Test Script for Skiing Resort Analysis

Quick test run to verify the analysis pipeline works correctly.
"""
import os
import sys

# Fix PROJ database conflict: Use conda environment's PROJ instead of PostgreSQL's
try:
    import pyproj
    correct_proj_dir = pyproj.datadir.get_data_dir()
    os.environ['PROJ_LIB'] = correct_proj_dir
    print(f"OK - PROJ_LIB set to: {correct_proj_dir}\n")
except Exception as e:
    print(f"Warning: Could not set PROJ_LIB: {e}\n")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skiing_resort_analysis.main import SkiingResortAnalysis


def test_data_loading():
    """Test data loading"""
    print("\n" + "="*70)
    print("TEST 1: DATA LOADING")
    print("="*70)
    
    try:
        analysis = SkiingResortAnalysis(verbose=True)
        analysis.load_data()
        
        assert analysis.dem_array is not None, "DEM not loaded"
        assert analysis.snow_points is not None, "Snow points not loaded"
        assert len(analysis.snow_points) > 0, "No snow points found"
        
        print("\n✓ TEST PASSED: Data loading successful")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_interpolation():
    """Test snow interpolation"""
    print("\n" + "="*70)
    print("TEST 2: SNOW INTERPOLATION")
    print("="*70)
    
    try:
        analysis = SkiingResortAnalysis(verbose=True)
        analysis.load_data()
        analysis.task1_interpolate_snow()
        
        assert len(analysis.interpolators) == 3, "Not all interpolators created"
        assert len(analysis.snow_interpolated) == 3, "Not all interpolations completed"
        
        print("\n✓ TEST PASSED: Interpolation successful")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_suitability():
    """Test suitability analysis"""
    print("\n" + "="*70)
    print("TEST 3: SUITABILITY ANALYSIS")
    print("="*70)
    
    try:
        analysis = SkiingResortAnalysis(verbose=True)
        analysis.load_data()
        analysis.task2_suitability_analysis()
        
        assert analysis.slope_analyzer is not None, "Slope analyzer not created"
        assert analysis.aspect_analyzer is not None, "Aspect analyzer not created"
        assert analysis.suitability_model is not None, "Suitability model not created"
        
        print("\n✓ TEST PASSED: Suitability analysis successful")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test complete analysis pipeline"""
    print("\n" + "="*70)
    print("TEST 4: FULL PIPELINE")
    print("="*70)
    
    try:
        analysis = SkiingResortAnalysis(verbose=True)
        success = analysis.run_full_analysis()
        
        assert success, "Full analysis failed"
        
        print("\n✓ TEST PASSED: Full pipeline successful")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("SKIING RESORT ANALYSIS - TEST SUITE")
    print("="*70)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Snow Interpolation", test_interpolation),
        ("Suitability Analysis", test_suitability),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"{'='*70}")
        
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)