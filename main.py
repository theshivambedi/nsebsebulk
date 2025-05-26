"""import subprocess
import sys

def run_pipeline():
    print("🚀 Starting automated BSE data pipeline")
    
    # Step 1: Fetch data
    print("⬇️ Fetching HTML data...")
    subprocess.run([sys.executable, "data.py"], check=True)
    
    # Step 2: Launch dashboard
    print("📊 Launching dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

if __name__ == "__main__":
    run_pipeline()"""


import subprocess
import sys
import os # For path joining

def run_pipeline():
    print("🚀 Starting automated BSE & NSE data pipeline")
    
    # Get the directory where main.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Step 1: Fetch data
    print("⬇️ Fetching HTML/JSON data for BSE & NSE...")
    data_script_path = os.path.join(current_dir, "data.py")
    subprocess.run([sys.executable, data_script_path], check=True)
    
    # Step 2: Launch dashboard
    print("📊 Launching dashboard...")
    streamlit_app_path = os.path.join(current_dir, "streamlit_app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", streamlit_app_path])

if __name__ == "__main__":
    run_pipeline()