
import yfinance as yf
import pandas as pd

symbol = "^GSPC"
df = yf.download(symbol, period="5d", progress=False, auto_adjust=True)
print("Data structure:")
print(df.head())
print("\nColumns:")
print(df.columns)
print("\nIndex:")
print(df.index)
print("\nTypes:")
print(df.dtypes)
