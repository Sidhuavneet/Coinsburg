import os
import requests
import zipfile
import pandas as pd
from tqdm import tqdm
import shutil

# --- Configuration ---
SYMBOL = "BTCUSDT"
YEAR = "2024"
MONTHS = range(1, 13)
OUTPUT_DIR = "data"
FINAL_CSV_NAME = "your_binance_futures_data_2024.csv"
BASE_URL = f"https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/"
TEMP_DIR = "temp_downloads"

def download_and_process_data():
    """
    Automates the downloading, unzipping, and combining of Binance data.
    """
    print("--- Starting Automated Data Download ---")

    # --- 1. Setup Directories ---
    if os.path.exists(TEMP_DIR):
        print(f"Cleaning up old files from '{TEMP_DIR}' directory...")
        shutil.rmtree(TEMP_DIR)
    
    os.makedirs(TEMP_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # --- 2. Download and Unzip Monthly Files ---
    for month in tqdm(MONTHS, desc="Downloading Monthly Files"):
        month_str = f"{month:02d}"
        file_name = f"{SYMBOL}-1m-{YEAR}-{month_str}"
        zip_file_path = os.path.join(TEMP_DIR, f"{file_name}.zip")
        
        url = f"{BASE_URL}{file_name}.zip"
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(TEMP_DIR)
            
            os.remove(zip_file_path)

        except requests.exceptions.HTTPError as e:
            print(f"Warning: Could not download {url}. Status code: {e.response.status_code}. Skipping month {month_str}.")
        except Exception as e:
            print(f"An error occurred for month {month_str}: {e}")

    # --- 3. Combine CSV files ---
    print("\n--- Combining all monthly CSV files ---")
    all_csv_files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR) if f.endswith('.csv')]
    all_csv_files.sort()

    if not all_csv_files:
        print("No CSV files found to combine. Exiting.")
        return

    col_names = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
                 'taker_buy_quote_asset_volume', 'ignore']

    df_list = [pd.read_csv(f, header=None, names=col_names, low_memory=False) for f in tqdm(all_csv_files, desc="Reading CSVs")]
    
    master_df = pd.concat(df_list, ignore_index=True)

    # --- 4. Format the DataFrame (NEW ROBUST METHOD) ---
    print("--- Formatting data ---")
    
    # Force the 'open_time' column to be numeric. Any text will become an empty value (NaN).
    master_df['open_time'] = pd.to_numeric(master_df['open_time'], errors='coerce')
    
    # Drop any rows where 'open_time' is now empty. This removes the bad header row.
    master_df.dropna(subset=['open_time'], inplace=True)
    
    # Now that it's clean, safely convert the column to integers.
    master_df['open_time'] = master_df['open_time'].astype('int64')

    # Proceed with the original conversion, which will now succeed.
    master_df['timestamp'] = pd.to_datetime(master_df['open_time'], unit='ms')
    final_df = master_df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # --- 5. Save the Final CSV and Clean Up ---
    final_output_path = os.path.join(OUTPUT_DIR, FINAL_CSV_NAME)
    final_df.to_csv(final_output_path, index=False)
    
    print(f"\nSuccessfully created final data file at: {final_output_path}")
    
    shutil.rmtree(TEMP_DIR)
    print(f"Cleaned up temporary directory: '{TEMP_DIR}'")
    
    print("--- Automation Complete ---")

if __name__ == "__main__":
    download_and_process_data()