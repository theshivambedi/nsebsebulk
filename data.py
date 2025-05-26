"""import requests

def fetch_data():
    url = "https://www.bseindia.com/markets/equity/EQReports/bulk_deals.aspx?expandable=3"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"})
    with open("bseindia.html", "w", encoding="utf-8") as f:
        f.write(response.text)

if __name__ == "__main__":
    fetch_data()"""


import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

# Common headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def fetch_bse_data():
    """Fetch BSE bulk deals data"""
    try:
        url = "https://www.bseindia.com/markets/equity/EQReports/bulk_deals.aspx"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise HTTP errors
        
        with open("bse_bulk_deals.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ BSE data saved to bse_bulk_deals.html")
    except Exception as e:
        print(f"❌ BSE fetch failed: {str(e)}")

def fetch_nse_data():
    """Fetch NSE bulk deals data"""
    try:
        # Dynamic date range (last 7 days)
        today = datetime.now().strftime("%d-%m-%Y")
        past_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        
        url = f"https://www.nseindia.com/api/historicalOR/bulk-block-short-deals?optionType=bulk_deals&from={past_date}&to={today}"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)
            # Required to set cookies
            s.get("https://www.nseindia.com/report-detail/display-bulk-and-block-deals", timeout=10)
            time.sleep(2)  # Avoid rate limiting
            
            response = s.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            with open("nse_bulk_deals.json", "w") as f:
                json.dump(data, f)
            print("✅ NSE data saved to nse_bulk_deals.json")
    except Exception as e:
        print(f"❌ NSE fetch failed: {str(e)}")

def main():
    print("🔄 Fetching market data...")
    fetch_bse_data()
    fetch_nse_data()
    print("✨ Data fetch completed!")

if __name__ == "__main__":
    main()    