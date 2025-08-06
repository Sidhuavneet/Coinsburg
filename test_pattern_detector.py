# test_pattern_detector.py

import os
import unittest
import pandas as pd
import numpy as np

from pattern_detector import PatternDetector

class TestPatternDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The CSV should be at project_root/data/test_data.csv
        base = os.path.dirname(__file__)
        csv_path = os.path.join(base, "data", "test_data.csv")
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(f"Expected test CSV at {csv_path}")
        cls.flat_df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    def run_detector(self, df):
        det = PatternDetector()
        return det.find_patterns(df.copy())

    def test_flat_data_no_patterns(self):
        """Flat sample CSV must yield zero patterns."""
        patterns = self.run_detector(self.flat_df)
        self.assertEqual(len(patterns), 0)

    def make_u_shape_df(self):
        """Construct a valid cup+handle+breakout so we can test a positive case."""
        idx = pd.date_range("2024-01-01 00:00", periods=56, freq="min")
        # Build a smooth U-bottom
        x = np.arange(40)
        y = 100 - ((x - 20) ** 2) / 20
        open_  = y + np.random.uniform(-0.3, 0.3, 40)
        high   = y + np.random.uniform(0.5, 1.0, 40)
        low    = y - np.random.uniform(0.5, 1.0, 40)
        close_ = y + np.random.uniform(-0.3, 0.3, 40)
        vol    = np.random.uniform(100, 200, 40)

        # Handle: 10 bars slight down
        h_open  = np.linspace(close_[-1], close_[-1] - 1.5, 10)
        h_high  = h_open + np.random.uniform(0.1, 0.4, 10)
        h_low   = h_open - np.random.uniform(0.1, 0.4, 10)
        h_close = h_open + np.random.uniform(-0.2, 0.2, 10)
        h_vol   = np.random.uniform(80, 150, 10)

        # Consolidation: 5 bars
        c_open  = np.full(5, h_close[-1])
        c_high  = c_open + np.random.uniform(0.1, 0.3, 5)
        c_low   = c_open - np.random.uniform(0.1, 0.3, 5)
        c_close = c_open + np.random.uniform(-0.1, 0.1, 5)
        c_vol   = np.random.uniform(80, 150, 5)

        # Breakout bar: above rim + 2*ATR
        rim_price = high.max()
        atr = (high - low).mean()
        b_open  = rim_price
        b_high  = rim_price + 2 * atr
        b_low   = rim_price - 0.1
        b_close = b_high - 0.2
        b_vol   = 500

        # Concatenate arrays
        o = np.concatenate([open_,  h_open,  c_open,  [b_open]])
        h = np.concatenate([high,   h_high,  c_high,  [b_high]])
        l = np.concatenate([low,    h_low,   c_low,   [b_low]])
        c = np.concatenate([close_, h_close, c_close, [b_close]])
        v = np.concatenate([vol,    h_vol,   c_vol,   [b_vol]])

        return pd.DataFrame({
            "timestamp": idx,
            "open":  o, "high": h, "low": l,
            "close": c, "volume": v
        })

    # def test_detects_valid_pattern(self):
    #     """Should detect at least one valid Cup & Handle in synthetic data."""
    #     df = self.make_u_shape_df()
    #     patterns = self.run_detector(df)
    #     self.assertGreaterEqual(len(patterns), 1, "Expected ≥1 valid pattern")
    #     p = patterns[0]
    #     # Basic structure checks
    #     for field in ("cup_depth", "cup_duration", "handle_duration", "r_squared_fit"):
    #         self.assertIn(field, p)

    def make_shallow_cup(self):
        df = self.make_u_shape_df()
        # Make cup too shallow: raise all lows by half the average candle size
        avg_rng = (df["high"] - df["low"]).mean()
        df.loc[:40, ["low", "open", "close"]] += avg_rng * 1.1
        return df

    def test_rejects_shallow_cup(self):
        df = self.make_shallow_cup()
        self.assertEqual(len(self.run_detector(df)), 0)

    def make_v_shape(self):
        df = self.make_u_shape_df()
        # Force a sharp V: collapse lows into two bars only
        df.loc[19:21, ["low","open","close"]] = df.loc[20, ["low","open","close"]].values
        return df

    def test_rejects_v_shape(self):
        df = self.make_v_shape()
        self.assertEqual(len(self.run_detector(df)), 0)

    def make_asymmetric_rims(self):
        df = self.make_u_shape_df()
        # Inflate right rim 20% above left
        df.at[39, "high"] *= 1.2
        return df

    def test_rejects_asymmetric_rims(self):
        df = self.make_asymmetric_rims()
        self.assertEqual(len(self.run_detector(df)), 0)

    def make_long_handle(self):
        df = self.make_u_shape_df()
        handle = df.iloc[40:50]
        # Duplicate to exceed 50 bars
        return pd.concat([df, pd.concat([handle]*2, ignore_index=True)], ignore_index=True)

    def test_rejects_long_handle(self):
        df = self.make_long_handle()
        self.assertEqual(len(self.run_detector(df)), 0)

    def make_no_breakout(self):
        df = self.make_u_shape_df()
        return df.iloc[:-1]  # drop that single breakout bar

    def test_rejects_no_breakout(self):
        df = self.make_no_breakout()
        self.assertEqual(len(self.run_detector(df)), 0)


if __name__ == "__main__":
    unittest.main()
