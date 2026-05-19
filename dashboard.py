import yfinance as yf
import matplotlib.pyplot as plt

# 1. This is your master database containing your 6 commodities and your personal research notes
COMMODITY_DATABASE = {
    "URA": {
        "Name": "Uranium (Global X ETF)",
        "Analysts": "Strong Bullish consensus due to structural deficit. Average price targets imply 15-20% upside.",
        "Drivers": "Global rotation to nuclear energy for net-zero goals, long-term supply shortages, and structural underinvestment in mines.",
        "Risks": "Highly dependent on government policy shifts, potential safety/accident stigmas, and project development delays."
    },
    "GC=F": {
        "Name": "Gold Futures",
        "Analysts": "Wall Street targets range between $4,700 - $5,000. Implied upside of roughly 5-10%.",
        "Drivers": "Heavy buying from global central banks, inflation hedging, and global macroeconomic uncertainties.",
        "Risks": "A sharp rise in real interest rates makes non-yielding gold less attractive; a massive rally in the US Dollar."
    },
    "SI=F": {
        "Name": "Silver Futures",
        "Analysts": "Volatile targets but generally bullish tracking gold. High industrial demand targets suggest 12% upside.",
        "Drivers": "Massive structural demand in green energy (solar panels) and electronics, acting as both a precious and industrial metal.",
        "Risks": "Highly sensitive to global industrial slowdowns and economic recessions."
    },
    "CL=F": {
        "Name": "Crude Oil Futures",
        "Analysts": "Neutral-to-Bearish targets over the long-term. 12-month targets hover around current prices.",
        "Drivers": "OPEC+ supply cuts keeping prices steady, paired with steady short-term global transportation demand.",
        "Risks": "Rapid acceleration of Electric Vehicle (EV) adoption and global economic recessions slowing down factory production."
    },
    "LIT": {
        "Name": "Lithium & Battery Tech (ETF)",
        "Analysts": "Highly split. Long-term upside potential remains massive, but short-term targets are depressed due to oversupply.",
        "Drivers": "Irreversible structural shift toward global EV adoption and grid-scale battery storage infrastructure.",
        "Risks": "Current market oversupply slowing down mining revenue; risk of alternative battery chemistries replacing lithium."
    },
    "RIO": {
        "Name": "Iron Ore (Rio Tinto)",
        "Analysts": "Neutral consensus. Tied tightly to heavy infrastructure spending cycles.",
        "Drivers": "Global steel manufacturing demand and ongoing real estate development projects across developing markets.",
        "Risks": "A major slowdown in construction activity or real estate development directly crushes iron ore demand."
    }
}

print("=== MY COMMODITY SCREENER DASHBOARD ===")
print("Tickers available: URA, GC=F, SI=F, CL=F, LIT, RIO")
print("=======================================")

# Ask the user which commodity they want to analyze
target = input("Enter a Ticker to view chart & research: ").strip().upper()

if target in COMMODITY_DATABASE:
    info = COMMODITY_DATABASE[target]
    print(f"\nFetching live market data for {info['Name']}...")
    
    # Fetch price data from Yahoo Finance
    asset = yf.Ticker(target)
    df = asset.history(period="1mo")
    
    if not df.empty:
        latest_price = df['Close'].iloc[-1]
        
        # --- PRINT RESEARCH REPORT TO THE SCREEN ---
        print("\n" + "="*50)
        print(f" INVESTMENT REPORT: {info['Name']} ({target})")
        print(f" Current Live Price: ${latest_price:.2f}")
        print("="*50)
        
        print(f"\n[A) ANALYST TARGETS & SENTIMENT]")
        print(info["Analysts"])
        
        print(f"\n[B) MACRO DRIVERS (Why is it priced like this?)]")
        print(info["Drivers"])
        
        print(f"\n[C) POTENTIAL RISKS & THREATS]")
        print(info["Risks"])
        print("="*50)
        
        # --- GENERATE THE INTERACTIVE MOUNTAIN CHART ---
        print("\nOpening the interactive chart window...")
        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df['Close'], color='midnightblue', linewidth=2)
        plt.fill_between(df.index, df['Close'], color='midnightblue', alpha=0.1) # Soft fill shading
        
        plt.title(f"{info['Name']} ({target}) - 30-Day Trend", fontsize=12, fontweight='bold')
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.ylabel("Price ($)")
        
        plt.show()
        
    else:
        print("Error: Pulling market data failed.")
else:
    print("Invalid Ticker. Please restart and use one from the list!")
