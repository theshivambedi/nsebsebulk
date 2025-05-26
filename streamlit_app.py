"""import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Streamlit config
st.set_page_config(layout="wide")
st.title("🔥 BSE Bulk Deals - Net Positions")
st.caption("Dominant side pricing | Auto-refreshing")

def calculate_net_positions():
    # Load HTML file
    html_file = Path("bseindia.html")
    if not html_file.exists():
        st.error("Data not found. Run data.py first!")
        return None
    
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Process all deals
    table = soup.find("table", {"id": "ContentPlaceHolder1_gvbulk_deals"})
    deals = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        deals.append({
            "Security": f"{cols[2].get_text(strip=True)} ({cols[1].get_text(strip=True)})",
            "Client": cols[3].get_text(strip=True),
            "Type": cols[4].get_text(strip=True),
            "Qty": int(cols[5].get_text(strip=True).replace(",", "")),
            "Price": float(cols[6].get_text(strip=True))
        })

    # Calculate NET positions with dominant pricing
    net_data = defaultdict(lambda: {
        'buy_qty': 0, 'buy_value': 0, 'sell_qty': 0, 'sell_value': 0,
        'buy_prices': [], 'sell_prices': []
    })

    for deal in deals:
        key = (deal["Client"], deal["Security"])
        if deal["Type"] == "B":
            net_data[key]["buy_qty"] += deal["Qty"]
            net_data[key]["buy_value"] += deal["Qty"] * deal["Price"]
            net_data[key]["buy_prices"].append((deal["Qty"], deal["Price"]))
        else:
            net_data[key]["sell_qty"] += deal["Qty"]
            net_data[key]["sell_value"] += deal["Qty"] * deal["Price"]
            net_data[key]["sell_prices"].append((deal["Qty"], deal["Price"]))

    # Prepare final dataframe
    results = []
    for (client, security), data in net_data.items():
        net_qty = data["buy_qty"] - data["sell_qty"]
        if net_qty == 0:
            continue  # Skip balanced positions

        if net_qty > 0:  # Net buyer
            dominant_prices = data["buy_prices"]
            action = "NET BUY"
            total_value = data["buy_value"] - data["sell_value"]
        else:  # Net seller
            dominant_prices = data["sell_prices"]
            action = "NET SELL"
            total_value = data["sell_value"] - data["buy_value"]
            net_qty = -net_qty  # Convert to positive

        # Calculate weighted average from dominant side only
        total_weight = sum(qty for qty, _ in dominant_prices)
        dominant_avg = sum(qty * price for qty, price in dominant_prices) / total_weight

        results.append({
            "Client": client,
            "Security": security,
            "Action": action,
            "Net Qty": net_qty,
            "Avg Price (₹)": dominant_avg,
            "Total Value (₹)": total_value
        })

    return pd.DataFrame(results)

# Main display logic
df = calculate_net_positions()
if df is not None:
    # Format numbers
    df_display = df.copy()
    df_display["Net Qty"] = df["Net Qty"].apply(lambda x: f"{x:,}")
    df_display["Avg Price (₹)"] = df["Avg Price (₹)"].apply(lambda x: f"₹{x:,.2f}")
    df_display["Total Value (₹)"] = df["Total Value (₹)"].apply(lambda x: f"₹{x:,.2f}")

    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Clients", df["Client"].nunique())
    col2.metric("Total Securities", df["Security"].nunique())
    col3.metric("Total Net Positions", len(df))

    # Display table
    st.dataframe(
        df_display,
        column_config={
            "Client": st.column_config.TextColumn(width="large"),
            "Security": st.column_config.TextColumn(width="large"),
            "Action": st.column_config.TextColumn(width="small"),
            "Net Qty": st.column_config.TextColumn("Shares", width="medium"),
            "Avg Price (₹)": st.column_config.TextColumn(width="medium"),
            "Total Value (₹)": st.column_config.TextColumn(width="medium")
        },
        hide_index=True,
        use_container_width=True
    )"""

import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from collections import defaultdict
import json

# Streamlit config
st.set_page_config(layout="wide")

def calculate_bse_net_positions():
    html_file = Path("bse_bulk_deals.html")
    if not html_file.exists():
        st.error(f"BSE data file ({html_file}) not found. Run data.py first!")
        return None
    
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
        if "BSE data fetch failed" in content or not content.strip():
            st.error("BSE data fetch seems to have failed. Please check data.py logs.")
            return None
        soup = BeautifulSoup(content, "html.parser")

    table = soup.find("table", {"id": "ContentPlaceHolder1_gvbulk_deals"})
    if not table:
        all_tables = soup.find_all("table")
        if all_tables:
            for t in all_tables:
                header_texts = [th.get_text(strip=True).lower() for th in t.find_all("th")]
                if "deal date" in header_texts and "security code" in header_texts and "client name" in header_texts:
                    table = t
                    st.warning("Primary BSE deals table not found, using a fallback. Results might vary.")
                    break
        if not table:
            st.error("Could not find the deals table in BSE HTML. Structure might have changed or data missing.")
            return None
        
    deals = []
    table_rows = table.find_all("tr")
    if len(table_rows) <= 1:
        st.info("No bulk deals data found in the BSE HTML for the current period.")
        return pd.DataFrame()

    for row_idx, row in enumerate(table_rows[1:], 1): 
        cols = row.find_all("td")
        if len(cols) < 7:
            continue
        try:
            security_name = cols[2].get_text(strip=True)
            security_code = cols[1].get_text(strip=True)
            client_name = cols[3].get_text(strip=True)
            deal_type_text = cols[4].get_text(strip=True).upper() 
            quantity = int(cols[5].get_text(strip=True).replace(",", ""))
            price = float(cols[6].get_text(strip=True).replace(",", ""))

            if not all([security_name, security_code, client_name, deal_type_text]) or quantity == 0 or price == 0.0:
                 continue

            deal_type = "B" if "BUY" in deal_type_text or "B" == deal_type_text else "S"
            deals.append({
                "Security": f"{security_name} ({security_code})",
                "Client": client_name,
                "Type": deal_type,
                "Qty": quantity,
                "Price": price
            })
        except (ValueError, IndexError):
            continue
            
    if not deals:
        st.info("No valid BSE deals could be parsed from the HTML.")
        return pd.DataFrame()

    return _calculate_generic_net_positions(deals, "BSE")

def calculate_nse_net_positions():
    json_file = Path("nse_bulk_deals.json")
    if not json_file.exists():
        st.error(f"NSE data file ({json_file}) not found. Run data.py first!")
        return None

    with open(json_file, "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError:
            st.error("Failed to decode NSE JSON. File might be corrupted.")
            return None

    nse_deals_raw = []
    if isinstance(raw_data, dict) and "data" in raw_data:
        nse_deals_raw = raw_data["data"]
    elif isinstance(raw_data, list):
        nse_deals_raw = raw_data
    else:
        st.error("NSE JSON data not in expected format.")
        return None
    
    if not nse_deals_raw:
        st.info("No bulk deals data found in the NSE JSON for the current period.")
        return pd.DataFrame()

    deals = []
    for idx, deal_info in enumerate(nse_deals_raw, 1):
        try:
            symbol = deal_info.get('BD_SYMBOL', 'N/A')
            scrip_name = deal_info.get('BD_SCRIP_NAME', symbol) 
            client_name = deal_info.get('BD_CLIENT_NAME', 'N/A')
            buy_sell_text = deal_info.get('BD_BUY_SELL', '').upper()
            quantity = int(deal_info.get('BD_QTY_TRD', 0))
            price = float(deal_info.get('BD_TP_WATP', 0.0))

            if not all([symbol, scrip_name, client_name, buy_sell_text]) or quantity == 0 or price == 0.0:
                continue

            deal_type = "B" if "BUY" in buy_sell_text else "S"
            deals.append({
                "Security": f"{scrip_name} ({symbol})",
                "Client": client_name,
                "Type": deal_type,
                "Qty": quantity,
                "Price": price
            })
        except (ValueError, TypeError, KeyError): # Catch more specific errors if possible
            continue
            
    if not deals:
        st.info("No valid NSE deals could be parsed from the JSON.")
        return pd.DataFrame()

    return _calculate_generic_net_positions(deals, "NSE")

def _calculate_generic_net_positions(deals, exchange_name):
    net_data = defaultdict(lambda: {
        'buy_qty': 0, 'buy_value': 0, 'sell_qty': 0, 'sell_value': 0,
        'buy_prices': [], 'sell_prices': []
    })

    for deal in deals:
        if not deal["Client"] or not deal["Client"].strip() or \
           not deal["Security"] or not deal["Security"].strip():
            continue

        key = (deal["Client"], deal["Security"])
        if deal["Type"] == "B":
            net_data[key]["buy_qty"] += deal["Qty"]
            net_data[key]["buy_value"] += deal["Qty"] * deal["Price"]
            net_data[key]["buy_prices"].append((deal["Qty"], deal["Price"]))
        elif deal["Type"] == "S":
            net_data[key]["sell_qty"] += deal["Qty"]
            net_data[key]["sell_value"] += deal["Qty"] * deal["Price"]
            net_data[key]["sell_prices"].append((deal["Qty"], deal["Price"]))

    results = []
    for (client, security), data in net_data.items():
        net_qty_val = data["buy_qty"] - data["sell_qty"]
        if net_qty_val == 0:
            continue

        if net_qty_val > 0:
            dominant_prices = data["buy_prices"]
            action = "NET BUY"
            total_value = data["buy_value"] - data["sell_value"]
            net_qty_display = net_qty_val
        else: # net_qty_val < 0
            dominant_prices = data["sell_prices"]
            action = "NET SELL"
            total_value = data["sell_value"] - data["buy_value"]
            net_qty_display = -net_qty_val

        if not dominant_prices:
            avg_price = 0.0
        else:
            total_dominant_qty = sum(qty for qty, _ in dominant_prices)
            avg_price = sum(qty * price for qty, price in dominant_prices) / total_dominant_qty if total_dominant_qty else 0.0
        
        results.append({
            "Client": client,
            "Security": security,
            "Action": action,
            "Net Qty": net_qty_display,
            "Avg Price (₹)": avg_price,
            "Total Value (₹)": total_value
        })
    
    return pd.DataFrame(results)

# ---- Streamlit Main UI ----

# Exchange selection at the top of the main page
selected_exchange = st.radio(
    label="Select Exchange:",  # Label for the radio buttons
    options=("BSE", "NSE"),
    key="exchange_selector_main_page", # Unique key
    horizontal=True,
    # label_visibility="collapsed" # Uncomment if you want to hide the "Select Exchange:" label
)

st.title(f"🔥 {selected_exchange} Bulk Deals - Net Positions")
st.caption("Dominant side pricing | Refresh page to update data (after re-running data.py).")

df = None
if selected_exchange == "BSE":
    df = calculate_bse_net_positions()
elif selected_exchange == "NSE":
    df = calculate_nse_net_positions()

if df is not None and not df.empty:
    df = df.sort_values(by=["Client", "Security"], ascending=[True, True]).reset_index(drop=True)
    
    df_display = df.copy()
    df_display["Net Qty"] = df["Net Qty"].apply(lambda x: f"{x:,.0f}")
    df_display["Avg Price (₹)"] = df["Avg Price (₹)"].apply(lambda x: f"₹{x:,.2f}")
    df_display["Total Value (₹)"] = df["Total Value (₹)"].apply(lambda x: f"₹{x:,.2f}")

    # Metrics display
    num_clients = df["Client"].nunique()
    num_securities = df["Security"].nunique()
    num_positions = len(df)

    # Using st.columns for a cleaner layout of metrics
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.metric("Clients (Net Position)", f"{num_clients:,}")
    with mcol2:
        st.metric("Securities (Net Position)", f"{num_securities:,}")

    st.dataframe(
        df_display,
        column_config={
            "Client": st.column_config.TextColumn(label="Client Name", width="large"),
            "Security": st.column_config.TextColumn(label="Security Name (Symbol)", width="large"),
            "Action": st.column_config.TextColumn(width="small"),
            "Net Qty": st.column_config.TextColumn("Net Shares", width="medium"),
            "Avg Price (₹)": st.column_config.TextColumn("Avg. Price (Dom.)",width="medium"),
            "Total Value (₹)": st.column_config.TextColumn("Net Traded Value",width="medium")
        },
        hide_index=True,
        use_container_width=True,
        height=700  # Fixed height for a more "static" viewport
    )
elif df is not None and df.empty:
    st.info(f"No net bulk deal positions to display for {selected_exchange} based on the current data and filters.")
# else: df is None, error messages are handled within the calculation functions

# You can add a small footer or information section here if needed, instead of the sidebar.
st.markdown("---")