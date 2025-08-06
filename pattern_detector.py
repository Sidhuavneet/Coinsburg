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
        df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        avg_candle_size = (df['high'] - df['low']).mean()
        print(f"Average candle size: {avg_candle_size:.2f}")
        
        swing_highs, _ = find_peaks(df['high'], prominence=avg_candle_size*0.5, distance=5)
        swing_lows, _ = find_peaks(-df['low'], prominence=avg_candle_size*0.5, distance=5)
        
        print(f"Found {len(swing_highs)} swing highs and {len(swing_lows)} swing lows.")

        for low_idx in swing_lows:
            possible_left_rims = swing_highs[swing_highs < low_idx]
            if len(possible_left_rims) == 0:
                continue
            
            left_rim_idx = possible_left_rims[-1]
            left_rim_price = df['high'].iloc[left_rim_idx]

            possible_right_rims = swing_highs[swing_highs > low_idx]
            if len(possible_right_rims) == 0:
                continue

            for right_rim_idx in possible_right_rims:
                cup_duration = right_rim_idx - left_rim_idx
                if not (self.config["cup_duration"][0] <= cup_duration <= self.config["cup_duration"][1]):
                    continue
                
                right_rim_price = df['high'].iloc[right_rim_idx]
                
                rim_level_diff = abs(left_rim_price - right_rim_price) / max(left_rim_price, right_rim_price)
                if rim_level_diff > self.config["rim_level_diff_max"]:
                    continue
                
                rim_line_price = min(left_rim_price, right_rim_price)
                cup_bottom_price = df['low'].iloc[low_idx]
                cup_depth = rim_line_price - cup_bottom_price
                if cup_depth < self.config["cup_depth_min_factor"] * avg_candle_size:
                    continue

                cup_data = df.iloc[left_rim_idx : right_rim_idx + 1]
                x_cup = np.arange(len(cup_data))
                y_cup = cup_data['low'].values
                
                coeffs = np.polyfit(x_cup, y_cup, 2)
                if coeffs[0] <= 0:
                    continue
                    
                p = np.poly1d(coeffs)
                y_pred = p(x_cup)
                r_squared = self._calculate_r_squared(y_cup, y_pred)
                
                if r_squared < self.config["r_squared_min"]:
                    continue

                handle_search_area = df.iloc[right_rim_idx:]
                if len(handle_search_area) < self.config["handle_duration"][0]:
                    continue

                # --- THIS IS THE CORRECTED SECTION ---
                handle_slice = handle_search_area.iloc[1:self.config["handle_duration"][1] + 1]
                if handle_slice.empty:
                    continue
                
                # Get the prices and Timestamp labels first
                handle_high = handle_slice['high'].max()
                handle_high_timestamp = handle_slice['high'].idxmax()
                handle_low = handle_slice['low'].min()
                handle_low_timestamp = handle_slice['low'].idxmin()

                # Convert Timestamp labels to integer row positions
                handle_high_idx = df.index.get_loc(handle_high_timestamp)
                handle_low_idx = df.index.get_loc(handle_low_timestamp)
                
                # Now all calculations are between integers
                handle_duration = handle_low_idx - right_rim_idx
                # --- END OF CORRECTED SECTION ---

                if not (self.config["handle_duration"][0] <= handle_duration <= self.config["handle_duration"][1]):
                    continue
                    
                if handle_high > max(left_rim_price, right_rim_price):
                    continue

                handle_retrace = (rim_line_price - handle_low) / cup_depth
                if handle_retrace > self.config["handle_retrace_max"]:
                    continue
                
                if handle_low < cup_bottom_price:
                    continue

                resistance_level = rim_line_price
                breakout_search_start_idx = handle_high_idx
                breakout_search_area = df.iloc[breakout_search_start_idx : breakout_search_start_idx + 60]
                
                breakout_candle = None
                breakout_candle_idx_int = -1 # Use integer index
                
                for i in range(len(breakout_search_area)):
                    candle = breakout_search_area.iloc[i]
                    atr_val = candle['ATR']
                    if atr_val is None or np.isnan(atr_val): continue

                    if candle['high'] > (resistance_level + self.config["breakout_atr_factor"] * atr_val):
                        breakout_candle = candle
                        breakout_candle_idx_int = df.index.get_loc(candle.name) # Convert timestamp to integer
                        break
                
                if breakout_candle is None:
                    continue

                avg_volume_cup_handle = df.iloc[left_rim_idx:breakout_candle_idx_int]['volume'].mean()
                volume_spike = breakout_candle['volume'] > (avg_volume_cup_handle * self.config["volume_spike_factor"])

                pattern_info = {
                    "pattern_id": len(self.patterns) + 1,
                    "status": "valid",
                    "reason": "All rules passed",
                    "start_time": df.iloc[left_rim_idx]['timestamp'],
                    "end_time": breakout_candle['timestamp'],
                    "cup_depth": cup_depth,
                    "cup_duration": cup_duration,
                    "handle_depth": rim_line_price - handle_low,
                    "handle_duration": handle_duration,
                    "r_squared_fit": r_squared,
                    "breakout_candle_timestamp": breakout_candle['timestamp'],
                    "volume_spike": volume_spike,
                    "indices": {
                        "left_rim": left_rim_idx,
                        "cup_bottom": low_idx,
                        "right_rim": right_rim_idx,
                        "handle_low": handle_low_idx,
                        "handle_high": handle_high_idx,
                        "breakout": breakout_candle_idx_int
                    },
                    "poly_coeffs": coeffs
                }
                self.patterns.append(pattern_info)
                if len(self.patterns) >= 30: # Stop after finding 30 patterns
                    print("\nFound 30 valid patterns. Stopping search.")
                    return self.patterns
                break 

        print(f"Detection complete. Found {len(self.patterns)} valid patterns.")
        return self.patterns
