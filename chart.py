import yfinance as yf
import matplotlib.pyplot as plt

# Our clean list of your 6 custom commodities
COMMODITIES = {
    "GC=F": "Gold",
    "SI=F": "Silver",
    "CL=F": "Crude Oil",
    "URA": "Uranium (ETF)",
    "LIT": "Lithium (ETF)",
    "RIO": "Iron Ore (Rio Tinto)"
}

print("--- COMMODITY CHART GENERATOR ---")
print("Available commodities to plot:")
for ticker, name in COMMODITIES.items():
    print(f"- {name} (Ticker: {ticker})")
print("---------------------------------")

# Ask you which one you want to see when you run the script
target = input("Type the Ticker you want to graph (e.g., URA or GC=F): ").strip()

if target in COMMODITIES:
    print(f"Fetching 1 month of history for {COMMODITIES[target]}...")
    
    # 1. Fetch 1 month of daily closing prices
    asset = yf.Ticker(target)
    df = asset.history(period="1mo")
    
    if not df.empty:
        # 2. Setup the visual chart style
        plt.figure(figsize=(10, 5))
        
        # 3. Plot the 'Close' prices as a solid line (just like your screenshot!)
        plt.plot(df.index, df['Close'], color='firebrick', linewidth=2)
        
        # 4. Fill the area underneath the line with a soft gradient red tint
        plt.fill_between(df.index, df['Close'], color='firebrick', alpha=0.1)
        
        # 5. Add titles and clean styling
        plt.title(f"{COMMODITIES[target]} ({target}) - Past 30 Days", fontsize=14, fontweight='bold')
        plt.xlabel("Date", fontsize=10)
        plt.ylabel("Price ($)", fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.5) # Adds a soft background grid
        
        # 6. Pop open the interactive window with your graph!
        print("Opening graph window...")
        plt.show()
    else:
        print("Error: Could not find any price data for that ticker.")
else:
    print("That ticker is not in your commodity list. Make sure to type it exactly.")
    

    
