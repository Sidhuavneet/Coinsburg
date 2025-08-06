import pandas as pd
import os

# --- Configuration ---
REPORT_FILE = 'report.csv'
PATTERNS_DIR = 'patterns'
HTML_PLOTS_DIR = 'html_plots'
OUTPUT_FILE = 'summary.html'

def create_summary_dashboard():
    """
    Reads the report.csv and generates an interactive summary HTML dashboard.
    """
    print(f"Reading analysis results from {REPORT_FILE}...")
    try:
        df = pd.read_csv(REPORT_FILE)
    except FileNotFoundError:
        print(f"Error: {REPORT_FILE} not found. Please run main.py first.")
        return

    print(f"Generating interactive dashboard at {OUTPUT_FILE}...")

    # --- Start of HTML Content ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cup & Handle Pattern Analysis Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1400px; margin: 20px auto; padding: 0 20px; background-color: #f9f9f9; }}
            h1, h2 {{ color: #1a1a1a; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }}
            .controls {{ margin-bottom: 30px; text-align: center; }}
            .btn {{ background-color: #007bff; color: white; border: none; padding: 12px 24px; margin: 5px; border-radius: 5px; cursor: pointer; font-size: 16px; transition: background-color 0.3s; }}
            .btn:hover {{ background-color: #0056b3; }}
            .btn.active {{ background-color: #0056b3; }}
            .content-section {{ display: none; }} /* Hidden by default */
            .grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; }}
            /* New 2-column grid for plots */
            .grid-container-plots {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 20px; }}
            .grid-item {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }}
            .grid-item h4 {{ margin-top: 0; }}
            .grid-item img {{ max-width: 100%; border-radius: 4px; cursor: pointer; }} /* Added cursor pointer */
            /* THIS IS THE CHANGED LINE */
            .grid-item iframe {{ width: 100%; height: 400px; border: none; border-radius: 4px; pointer-events: none; }}
            .grid-item a {{ color: #007bff; text-decoration: none; font-size: 0.9em; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 0.9em; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}

            /* New Modal (Lightbox) Styles */
            .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.8); }}
            .modal-content {{ margin: auto; display: block; max-width: 90%; max-height: 90%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }}
            .close {{ position: absolute; top: 20px; right: 35px; color: #fff; font-size: 40px; font-weight: bold; transition: 0.3s; }}
            .close:hover, .close:focus {{ color: #bbb; text-decoration: none; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>Cup & Handle Pattern Analysis Dashboard</h1>
        <p>This dashboard summarizes the <strong>{len(df)}</strong> valid patterns detected by the analysis script. Use the buttons below to explore the results.</p>
        
        <div class="controls">
            <button class="btn" onclick="showSection('pngs')">View Static Images</button>
            <button class="btn" onclick="showSection('plots')">View Interactive Plots</button>
            <button class="btn" onclick="showSection('report')">View Full Report</button>
        </div>

        <div id="pngs" class="content-section">
            <h2>Static Pattern Images</h2>
            <p>Click on any image to see a larger preview.</p>
            <div class="grid-container">
    """
    for index, row in df.iterrows():
        pattern_id = row['pattern_id']
        png_path = os.path.join(PATTERNS_DIR, f"cup_handle_{pattern_id}.png")
        # Updated img tag to call the openModal function
        html_content += f"""
                <div class="grid-item">
                    <h4>Pattern #{pattern_id}</h4>
                    <img src="{png_path}" alt="Pattern #{pattern_id}" onclick="openModal(this.src)">
                </div>
        """
    html_content += "</div></div>"

    # --- Interactive Plots Section (with new 2-column grid) ---
    html_content += """
        <div id="plots" class="content-section">
            <h2>Interactive Plot Previews</h2>
            <p>Click the link below each preview to open the fully interactive chart in a new tab.</p>
            <div class="grid-container-plots">
    """
    for index, row in df.iterrows():
        pattern_id = row['pattern_id']
        html_plot_path = os.path.join(HTML_PLOTS_DIR, f"cup_handle_{pattern_id}.html")
        html_content += f"""
                <div class="grid-item">
                    <h4>Pattern #{pattern_id}</h4>
                    <iframe src="{html_plot_path}"></iframe>
                    <a href="{html_plot_path}" target="_blank">Open Full Interactive Chart</a>
                </div>
        """
    html_content += "</div></div>"

    # --- Full Report Section ---
    html_content += f"""
        <div id="report" class="content-section">
            <h2>Full Data Report</h2>
            {df.to_html(index=False)}
        </div>
    """

    # --- New Modal HTML Structure ---
    html_content += """
        <div id="myModal" class="modal">
            <span class="close" onclick="closeModal()">&times;</span>
            <img class="modal-content" id="modalImage">
        </div>
    """

    # --- JavaScript for controls and modal ---
    html_content += """
        <script>
            // Get modal elements
            var modal = document.getElementById("myModal");
            var modalImg = document.getElementById("modalImage");

            function openModal(src) {
                modal.style.display = "block";
                modalImg.src = src;
            }

            function closeModal() {
                modal.style.display = "none";
            }

            function showSection(sectionId) {
                document.querySelectorAll('.content-section').forEach(section => {
                    section.style.display = 'none';
                });
                document.querySelectorAll('.btn').forEach(button => {
                    button.classList.remove('active');
                });
                document.getElementById(sectionId).style.display = 'block';
                event.target.classList.add('active');
            }
            
            // Show the first section by default on page load
            document.addEventListener('DOMContentLoaded', (event) => {
                document.querySelector('.btn').click();
            });
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Interactive dashboard generated successfully!")

if __name__ == '__main__':
    create_summary_dashboard()