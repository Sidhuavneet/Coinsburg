import pandas as pd
import os
import subprocess  # Import the subprocess module
from pattern_detector import PatternDetector
from plot_utils import plot_and_save

# --- CONFIGURATION ---
DATA_FILE = os.path.join('data', 'your_binance_futures_data_2024.csv')
PATTERNS_DIR = 'patterns'
HTML_PLOTS_DIR = 'html_plots'
REPORT_FILE = 'report.csv'
MAX_PATTERNS_TO_PLOT = 30

def main():
    """
    Main execution function.
    """
    # --- 1. SETUP DIRECTORIES ---
    if not os.path.exists(PATTERNS_DIR):
        os.makedirs(PATTERNS_DIR)
    if not os.path.exists(HTML_PLOTS_DIR):
        os.makedirs(HTML_PLOTS_DIR)
    if not os.path.exists('data'):
        os.makedirs('data')
        print("FATAL: 'data' directory not found. Please create it and add your data file.")
        print(f"The script expects a file at: {DATA_FILE}")
        return

    # --- 2. LOAD DATA ---
    print(f"Loading data from {DATA_FILE}...")
    try:
        df = pd.read_csv(DATA_FILE)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp', drop=False)
        df = df.sort_index()
        print("Data loaded successfully.")
    except FileNotFoundError:
        print(f"FATAL: Data file not found at '{DATA_FILE}'.")
        print("Please run 'python download_data.py' first to fetch the required data.")
        return
    except Exception as e:
        print(f"An error occurred while loading data: {e}")
        return

    # --- 3. RUN DETECTION ---
    detector = PatternDetector()
    valid_patterns = detector.find_patterns(df)

    if not valid_patterns:
        print("No valid Cup and Handle patterns were found with the current criteria.")
        return

    print(f"\nFound {len(valid_patterns)} valid patterns. Preparing to plot and generate report.")
    
    # --- 4. PLOT PATTERNS AND GENERATE REPORT ---
    plotted_count = 0
    patterns_for_report = []

    for pattern in valid_patterns:
        if plotted_count < MAX_PATTERNS_TO_PLOT:
            print(f"\nProcessing pattern #{pattern['pattern_id']}...")
            plot_and_save(df, pattern, PATTERNS_DIR, HTML_PLOTS_DIR)
            plotted_count += 1
        
        report_entry = pattern.copy()
        del report_entry['indices']
        del report_entry['poly_coeffs']
        patterns_for_report.append(report_entry)

    if plotted_count > 0:
        print(f"\nSuccessfully plotted and saved {plotted_count} patterns to the '{PATTERNS_DIR}' and '{HTML_PLOTS_DIR}' folders.")

    # --- 5. SAVE REPORT ---
    report_df = pd.DataFrame(patterns_for_report)
    report_df.to_csv(REPORT_FILE, index=False)
    print(f"\nValidation summary report saved to '{REPORT_FILE}'.")
    
    # --- 6. GENERATE FINAL HTML DASHBOARD (NEW STEP) ---
    try:
        print("\n--- Running Summary Generation ---")
        # This command runs the new script as a separate process
        subprocess.run(["python", "generate_summary.py"], check=True)
    except FileNotFoundError:
        print("Error: Could not find 'generate_summary.py'. Make sure it's in the same directory.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while generating the summary dashboard: {e}")

    
    if plotted_count < MAX_PATTERNS_TO_PLOT:
        print(f"\nWARNING: The system found only {plotted_count} patterns, which is less than the target of {MAX_PATTERNS_TO_PLOT}.")

if __name__ == "__main__":
    main()