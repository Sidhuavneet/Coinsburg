# Coinsburg
# Quantitative Cup & Handle Pattern Detector for BTC/USDT Futures

This project is a complete, end-to-end quantitative system designed to automatically detect, validate, and visualize **"Cup and Handle"** chart patterns from high-frequency cryptocurrency financial data. The system fetches 1-minute BTC/USDT futures data from Binance, applies a rigorous set of validation rules to identify high-probability patterns, and generates a comprehensive set of visual and data-driven reports.

---

## ✨ Features

* **Automated Data Pipeline**: Includes a script (`download_data.py`) to automatically fetch and prepare a full year of 1-minute data from Binance.
* **Robust Detection Engine**: Uses `scipy.signal.find_peaks` to identify patterns and applies over 7 financial rules (duration, depth, parabolic fit, retracement levels, etc.).
* **Comprehensive Visualization Suite**:

  * Static `.png` images for visual inspection.
  * Fully interactive `.html` plots via Plotly.
* **Interactive Dashboard**: `generate_summary.py` produces a `summary.html` dashboard with previews and links.
* **Quantitative Reporting**: Outputs `report.csv` with key stats for every validated pattern.
* **Unit Tested Logic**: `test_pattern_detector.py` ensures invalid patterns are rejected.

---

## 📂 Project Structure

```
/
├── data/
│   └── test_data.csv         # Real sample for unit testing
│
├── html_plots/               # Output directory for interactive plots
├── patterns/                 # Output directory for static images
│
├── download_data.py          # Fetches market data from Binance
├── generate_summary.py       # Creates the interactive summary dashboard
├── main.py                   # Main analysis script
├── pattern_detector.py       # Core logic for detection and validation
├── plot_utils.py             # Plot generation utilities
├── README.md                 # Project documentation
├── requirements.txt          # Dependencies
└── test_pattern_detector.py  # Unit tests
```

---

## 🛠️ Setup and Installation

### Prerequisites

* Python 3.8 or newer
* pip (Python package installer)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

### 2. Install Dependencies

```bash

# Install required packages
pip install -r requirements.txt
```

**Note on TA-Lib**: You may need to install the TA-Lib C library manually if errors occur.

---

## 🚀 Usage Workflow

### Download the Data

```bash
python download_data.py
```

Generates: `data/your_binance_futures_data_2024.csv`

### Run the Main Analysis

```bash
python main.py
```

Generates:

* `.png` and `.html` files for valid patterns
* `report.csv`
* `summary.html`

### Review the Results

* **Dashboard**: Open `summary.html`
* **Static Images**: `/patterns/*.png`
* **Interactive Plots**: `/html_plots/*.html`
* **Raw Data**: `report.csv`

---

## ✅ Running Unit Tests

```bash
python -m unittest test_pattern_detector.py
```

Expect output: `OK` if all tests pass.

---

## ⚙️ Configuration

The detection criteria can be adjusted in the `PatternDetector` class in `pattern_detector.py`:

```python
self.validation_params = {
    "min_cup_duration": 30,
    "max_cup_duration": 200,
    "min_handle_depth": 0.01,
    ...
}
```

Modify values to experiment with stricter or looser conditions.

---

##  Screenshots

<img width="1703" height="252" alt="{6C3A3736-151D-4317-B148-C0183775CA7C}" src="https://github.com/user-attachments/assets/a829f73d-6d40-4d9c-9215-bf6227ac054e" />

<img width="1700" height="449" alt="{4FD0CF93-8A43-4AA4-B6EB-F2485EABCAF1}" src="https://github.com/user-attachments/assets/a06abfc7-a9cd-4e2c-882c-dcb92b20441d" />

<img width="1920" height="1030" alt="{A777991C-3785-403E-9876-2E89F9995363}" src="https://github.com/user-attachments/assets/508e71b3-8e66-4e93-91a7-d5f81fc4b3e2" />

<img width="1920" height="1036" alt="{9936E001-10E6-424D-953A-0E84EDD41536}" src="https://github.com/user-attachments/assets/6ba58e64-ad4e-460c-b9ea-b03192d978b7" />

<img width="1920" height="1029" alt="{DBC4C7D8-592E-4609-A84C-3F46B6DD9AF5}" src="https://github.com/user-attachments/assets/50807d75-b347-4148-950c-c111bb74abaf" />

<img width="1919" height="1033" alt="{6B1BE04C-9CBC-4281-B280-86E29EC001A0}" src="https://github.com/user-attachments/assets/113d41b0-2dd3-4884-a726-0c142bb101fb" />

