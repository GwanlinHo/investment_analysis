import pytest
import pandas as pd
import numpy as np
import investment_analysis
from investment_analysis import calculate_all_indicators, determine_trend, get_color_class

def test_calculate_all_indicators():
    # Create a dummy DataFrame with 100 rows to ensure enough data for windows (up to 60)
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = {
        'Open': np.linspace(100, 200, 100),
        'High': np.linspace(102, 202, 100),
        'Low': np.linspace(98, 198, 100),
        'Close': np.linspace(101, 201, 100),
        'Volume': np.linspace(1000, 2000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    
    result_df = calculate_all_indicators(df)
    
    # Check if key indicators are present
    assert 'K' in result_df.columns
    assert 'D' in result_df.columns
    assert 'BIAS_5' in result_df.columns
    assert 'BIAS_20' in result_df.columns
    assert 'BIAS_60' in result_df.columns
    assert 'ADX' in result_df.columns
    
    # Check some specific values (approximate)
    # Since prices are linearly increasing, BIAS should be positive
    assert result_df['BIAS_20'].iloc[-1] > 0
    assert not pd.isna(result_df['K'].iloc[-1])
    assert not pd.isna(result_df['D'].iloc[-1])

def test_determine_trend():
    # Strong Bullish: k > d and bias_signal_val > threshold (0)
    assert determine_trend(85, 80, 2) == ("多頭排列", "bullish-strong")
    # Weak Bullish (Rebound): k > d but bias_signal_val < 0
    assert determine_trend(30, 25, -2) == ("反彈", "bullish-weak")
    # Strong Bearish: k < d and bias_signal_val < 0
    assert determine_trend(15, 20, -2) == ("空頭修正", "bearish-strong")
    # Pullback: k < d but bias_signal_val > 0
    assert determine_trend(75, 80, 2) == ("回檔整理", "bearish-weak")

def test_get_color_class():
    # Normal case: value > high -> text-up, value < low -> text-down
    assert get_color_class(5, 0, 0) == "text-up"
    assert get_color_class(-5, 0, 0) == "text-down"
    assert get_color_class(0, 0, 0) == ""
    
    # Inverse case (e.g., VIX): value > high -> text-down, value < low -> text-up
    assert get_color_class(5, 0, 0, inverse=True) == "text-down"
    assert get_color_class(-5, 0, 0, inverse=True) == "text-up"
    
    # Thresholds
    assert get_color_class(85, 80, 20) == "text-up"
    assert get_color_class(15, 80, 20) == "text-down"
    assert get_color_class(50, 80, 20) == ""

    # None/NaN handling
    assert get_color_class(None, 80, 20) == ""
    assert get_color_class(np.nan, 80, 20) == ""
