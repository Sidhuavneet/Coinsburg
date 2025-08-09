import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import talib

class PatternDetector:
    """
    A class to detect Cup and Handle patterns in OHLCV data based on a strict
    set of validation rules.
    """
    def __init__(self, config=None):
        if config is None:
            self.config = {
                "cup_duration": (30, 300),
                "handle_duration": (5, 50),
                "rim_level_diff_max": 0.10,
                "cup_depth_min_factor": 2.0,
                "handle_retrace_max": 0.40,
                "r_squared_min": 0.85,
                "breakout_atr_factor": 1.5,
                "volume_spike_factor": 1.5
            }
        else:
            self.config = config
        
        self.patterns = []

    def _calculate_r_squared(self, y_true, y_pred):
        """Calculates the R-squared value for the parabolic fit."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        if ss_tot == 0:
            return 0.0
        return 1 - (ss_res / ss_tot)

    def find_patterns(self, df: pd.DataFrame):
        """
        Main method to find all valid Cup and Handle patterns in the dataframe.
        """
        print("Starting pattern detection...")
        # Ensure dataframe has integer index for easier iloc access
        df = df.reset_index(drop=True)
        # Assume 'timestamp' column exists; if not, adjust accordingly
        if 'timestamp' not in df.columns:
            df['timestamp'] = df.index  # Fallback to index if no timestamp

        df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        avg_candle_size = (df['high'] - df['low']).mean()
        print(f"Average candle size: {avg_candle_size:.2f}")
        
        # Find swing highs and lows using prominence based on avg candle size
        swing_highs, _ = find_peaks(df['high'], prominence=avg_candle_size * 0.5, distance=5)
        swing_lows, _ = find_peaks(-df['low'], prominence=avg_candle_size * 0.5, distance=5)
        
        print(f"Found {len(swing_highs)} swing highs and {len(swing_lows)} swing lows.")

        # To avoid duplicates, track covered ranges
        covered_ranges = []

        for low_idx in swing_lows:
            possible_left_rims = swing_highs[swing_highs < low_idx]
            if len(possible_left_rims) == 0:
                continue
            
            left_rim_idx = possible_left_rims[-1]  # Most recent swing high before bottom
            left_rim_price = df['high'].iloc[left_rim_idx]

            possible_right_rims = swing_highs[swing_highs > low_idx]
            if len(possible_right_rims) == 0:
                continue

            for right_rim_idx in possible_right_rims:
                cup_duration = right_rim_idx - left_rim_idx
                if not (self.config["cup_duration"][0] <= cup_duration <= self.config["cup_duration"][1]):
                    continue
                
                right_rim_price = df['high'].iloc[right_rim_idx]
                
                # Use average rim price for calculations
                avg_rim_price = (left_rim_price + right_rim_price) / 2
                rim_level_diff = abs(left_rim_price - right_rim_price) / max(left_rim_price, right_rim_price)
                if rim_level_diff > self.config["rim_level_diff_max"]:
                    continue
                
                cup_bottom_price = df['low'].iloc[low_idx]
                cup_depth = avg_rim_price - cup_bottom_price
                if cup_depth < self.config["cup_depth_min_factor"] * avg_candle_size:
                    continue

                # Cup data for fitting: use lows for bottom shape
                cup_data = df.iloc[left_rim_idx: right_rim_idx + 1]
                x_cup = np.arange(len(cup_data))
                y_cup = cup_data['low'].values
                
                # Fit parabola (degree 2)
                coeffs = np.polyfit(x_cup, y_cup, 2)
                if coeffs[0] <= 0:  # Ensure upward opening for U-shape
                    continue
                    
                p = np.poly1d(coeffs)
                y_pred = p(x_cup)
                r_squared = self._calculate_r_squared(y_cup, y_pred)
                
                if r_squared < self.config["r_squared_min"]:
                    continue

                # Find next swing low after right rim for handle bottom
                possible_handle_lows = swing_lows[swing_lows > right_rim_idx]
                if len(possible_handle_lows) == 0:
                    continue
                
                handle_low_idx = possible_handle_lows[0]  # Next swing low
                handle_duration = handle_low_idx - right_rim_idx
                if not (self.config["handle_duration"][0] <= handle_duration <= self.config["handle_duration"][1]):
                    continue

                # Handle high: max high between right rim (exclusive) and handle low (inclusive)
                handle_slice = df.iloc[right_rim_idx + 1: handle_low_idx + 1]
                if handle_slice.empty:
                    continue
                handle_high_idx = handle_slice['high'].idxmax()
                handle_high = df['high'].iloc[handle_high_idx]
                
                # Check handle high <= max rim
                if handle_high > max(left_rim_price, right_rim_price):
                    continue

                handle_low = df['low'].iloc[handle_low_idx]

                # Check handle low > cup bottom
                if handle_low < cup_bottom_price:
                    continue

                # Handle retrace using avg rim
                handle_retrace = (avg_rim_price - handle_low) / cup_depth
                if handle_retrace > self.config["handle_retrace_max"]:
                    continue

                # Search for breakout after handle low
                breakout_search_start_idx = handle_low_idx + 1
                if breakout_search_start_idx >= len(df):
                    continue
                breakout_search_area = df.iloc[breakout_search_start_idx: breakout_search_start_idx + 60]
                
                breakout_candle_idx = None
                for i in range(len(breakout_search_area)):
                    candle_idx = breakout_search_start_idx + i
                    candle = df.iloc[candle_idx]
                    atr_val = candle['ATR']
                    if np.isnan(atr_val):
                        continue
                    if candle['high'] > handle_high + self.config["breakout_atr_factor"] * atr_val:
                        breakout_candle_idx = candle_idx
                        break
                
                if breakout_candle_idx is None:
                    continue

                # Volume spike check (bonus)
                avg_volume_cup_handle = df.iloc[left_rim_idx:breakout_candle_idx]['volume'].mean()
                volume_spike = df['volume'].iloc[breakout_candle_idx] > (avg_volume_cup_handle * self.config["volume_spike_factor"])

                # Check for overlap with previous patterns to avoid duplicates
                pattern_range = (left_rim_idx, breakout_candle_idx)
                if any(max(start, left_rim_idx) < min(end, breakout_candle_idx) for start, end in covered_ranges):
                    continue  # Skip if overlaps with previous
                covered_ranges.append(pattern_range)

                # All checks passed
                pattern_info = {
                    "pattern_id": len(self.patterns) + 1,
                    "status": "valid",
                    "reason": "All rules passed",
                    "start_time": df.iloc[left_rim_idx]['timestamp'],
                    "end_time": df.iloc[breakout_candle_idx]['timestamp'],
                    "cup_depth": cup_depth,
                    "cup_duration": cup_duration,
                    "handle_depth": avg_rim_price - handle_low,
                    "handle_duration": handle_duration,
                    "r_squared_fit": r_squared,
                    "breakout_candle_timestamp": df.iloc[breakout_candle_idx]['timestamp'],
                    "volume_spike": volume_spike,
                    "indices": {
                        "left_rim": left_rim_idx,
                        "cup_bottom": low_idx,
                        "right_rim": right_rim_idx,
                        "handle_low": handle_low_idx,
                        "handle_high": handle_high_idx,
                        "breakout": breakout_candle_idx
                    },
                    "poly_coeffs": coeffs
                }
                self.patterns.append(pattern_info)
                print(f"Found valid pattern #{pattern_info['pattern_id']}")
                if len(self.patterns) >= 30:  # Stop after finding 30 patterns
                    print("\nFound 30 valid patterns. Stopping search.")
                    return self.patterns
                break  # Break the inner right_rim loop after finding one valid for this bottom

        print(f"Detection complete. Found {len(self.patterns)} valid patterns.")
        return self.patterns