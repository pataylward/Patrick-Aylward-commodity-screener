import yfinance as yf

# This is our list of assets: Gold Futures, Crude Oil, and Apple Stock
watchlist = ["GC=F", "CL=F", "AAPL"]

print("--- FETCHING LIVE COMMODITY DATA ---")

for ticker in watchlist:
    asset = yf.Ticker(ticker)
    data = asset.history(period="1d")
    latest_price = data['Close'].iloc[0]
    print(f"The current price of {ticker} is: ${latest_price:.2f}")

print("------------------------------------")
