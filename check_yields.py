import yfinance as yf
import datetime
import pandas as pd

def check_yields():
    try:
        # Fetch data for the last 5 days to ensure we get the latest trading day
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=10)
        
        tickers = ["^IRX", "^TNX", "^TYX"]
        print(f"Fetching data for {tickers}...")
        
        data = yf.download(tickers, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if data.empty:
            print("No data fetched.")
            return

        # Handle MultiIndex columns if present (yfinance update)
        if isinstance(data.columns, pd.MultiIndex):
             # Depending on yfinance version, structure varies. 
             # Often it's (PriceType, Ticker). We want 'Close'.
             # Let's just print the tail of 'Close' if possible.
             try:
                 df_close = data['Close']
             except KeyError:
                 # Fallback if structure is different
                 print("Columns:", data.columns)
                 return
        else:
             df_close = data['Close']

        print("\nLatest Data (Close):")
        print(df_close.tail())
        
        latest = df_close.iloc[-1]
        irx = latest['^IRX']
        tnx = latest['^TNX']
        
        print(f"\nLatest Values:")
        print(f"3-Month Bill (^IRX): {irx:.4f}%")
        print(f"10-Year Note (^TNX): {tnx:.4f}%")
        
        spread = tnx - irx
        print(f"Spread (10Y - 3M): {spread:.4f}%")
        
        if spread < 0:
            print("Status: INVERTED (倒掛)")
        else:
            print("Status: NORMAL (正常)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_yields()
