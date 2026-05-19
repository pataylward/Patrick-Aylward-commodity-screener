from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import sqlite3
from contextlib import contextmanager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DATABASE MANAGEMENT SYSTEM ---
# This safely opens and closes the database connection
@contextmanager
def get_db():
    conn = sqlite3.connect("commodities.db")
    try:
        yield conn
    finally:
        conn.close()

# This function builds the SQL database from scratch if it doesn't exist
def initialize_database():
    with get_db() as conn:
        cursor = conn.cursor()
        # Create the table schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                analysts TEXT,
                drivers TEXT,
                risks TEXT
            )
        """)
        
        # The Master Data Payload
        initial_data = [
            ("URA", "Uranium (Global X ETF)", 
             "Wall Street investment banks have established a structurally bullish consensus on the uranium sector, with consensus 12-month price targets implying a 15% to 25% near-term upside. Institutional research desks emphasize that structural supply deficits are no longer transient but are baked into global utility frameworks.", 
             "1. Clean Energy Infrastructure Pivots: Structural global transition toward net-zero.\n2. Structural Production Deficits: Mine supply continues to lag aggregate global demand.\n3. Geopolitical Supply Chain Risks: Aggressive long-term contracting volumes to secure non-aligned fuel rods.", 
             "1. Policy Volatility: Highly sensitive to shifting political regimes.\n2. Operational Delays: Capital expenditure execution risks.\n3. Enrichment Bottlenecks: Bottlenecks in Western conversion capacity."),
            
            ("SI=F", "Silver Futures", 
             "Wall Street commodity desks maintain a highly constructive structural outlook on silver, with 12-month price targets implying a 12% to 18% upside from current ranges. Institutional accumulation is quietly accelerating as industrial demand outpaces mine output.", 
             "1. Photovoltaic (Solar) Deficits: Explosive global expansion of solar panel manufacturing.\n2. Dual-Vector Asset Class: Acts as both a monetary safe-haven and an industrial necessity.\n3. Structural Mine Deficits: Over 70% of silver is mined as a secondary byproduct, constraining new supply.", 
             "1. Industrial Slowdown: Highly vulnerable to sudden macroeconomic contractions.\n2. Technological Substitutions: Solar manufacturers researching 'thrifting' methods.\n3. High Retail Volatility: Susceptible to violent short-term liquidations."),
            
            ("LIT", "Lithium & Battery Tech (ETF)",
             "The analyst community is sharply divided. Equity research analysts remain near-term cautious due to inventory destocking, while long-term technological analysts maintain an aggressive buy bias, arguing current depressions offer a generational entry point.",
             "1. Irreversible EV Secular Trend: Backed by binding regulatory manufacturing mandates.\n2. Grid-Scale Battery Deployment: BESS systems scaling exponentially.\n3. Localization Subsidies: Western infrastructure bills guaranteeing high-margin domestic off-take.",
             "1. Short-Term Supply Overhangs: Sustained low-cost production flooding spot markets.\n2. Evolving Battery Chemistry: Solid-state architectures could decrease lithium intensity.\n3. Automotive Sales Micro-Cycles: Near-term consumer adoption plateaus."),
            
            ("GC=F", "Gold Futures",
             "Major investment bank consensus targets remain heavily weighted to the upside. Goldman Sachs targets a structural continuation toward $5,400/oz by year-end. The underlying multi-year accumulation floor remains highly resilient.",
             "1. Structural Central Bank Accumulation: Shifting away from Western fiat reserves.\n2. Macro and Geopolitical Tail Risks: Persistent systemic debasement hedge.\n3. Real Interest Rate Tracking: Easing curves reduce the opportunity cost of holding.",
             "1. Hawkish Central Bank Reversals: Unexpected interest rate hike cycles.\n2. Severe Market Liquidity Events: Dumped by institutions to meet immediate cash margin demands.\n3. Relentless US Dollar Strength: DXY rallies build immediate deflationary pricing drag."),
            
            ("CL=F", "Crude Oil Futures",
             "Energy analyst desks have experienced substantial near-term volatility revisions, with near-term spikes heavily tied to transit bottlenecks. Long-term consensus curves flatten as structural supply balances tip back to equilibrium.",
             "1. Geopolitical Transit Chokepoints: Elevated transit restrictions across critical marine choke points.\n2. Cartel Supply Discipline: Extended OPEC+ production quota restrictions.\n3. Emerging Market Demand: Resilient strategic commercial inventory builds.",
             "1. Rapid Electrification Penetration: Accelerating consumer EV adoption curves.\n2. Geopolitical Resolution Crushes: Diplomatic breakthroughs instantly wiping out risk premiums.\n3. Systemic Global Recessions: Broad manufacturing downturns cutting shipping utilization."),
            
            ("RIO", "Iron Ore (Rio Tinto)",
             "Industrial metal analysts remain broadly conservative, holding a neutral structural bias. Consensus projections target a narrow price bandwidth, heavily dependent on state-level infrastructure fixed-asset allocations.",
             "1. Emerging Market Infrastructure Buildouts: Aggressive developments across India and Southeast Asia.\n2. Low-Cost Production Moats: Tier-1 miners operating with incredibly low cash-cost baselines.\n3. High-Grade Green Steel Transition: Increasing structural demand for high-grade pellets.",
             "1. Real Estate Contractions: Multi-year consolidation within commercial real estate.\n2. Supply-Side Flooding: Expansion completions in South America and Africa.\n3. Scrap Metal Recycling Substitution: Accelerating domestic steel recycling capabilities.")
        ]
        
        # Insert data using OR REPLACE so it updates cleanly if you ever change the text
        cursor.executemany("""
            INSERT OR REPLACE INTO research (ticker, name, analysts, drivers, risks) 
            VALUES (?, ?, ?, ?, ?)
        """, initial_data)
        
        conn.commit()

# Run the database setup immediately when the server starts
initialize_database()

# --- 2. THE API ROUTER ---
@app.get("/screener/{ticker}")
def get_commodity_data(ticker: str):
    ticker = ticker.upper()
    
    # Query the SQL Database instead of reading a Python dictionary
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, analysts, drivers, risks FROM research WHERE ticker = ?", (ticker,))
        row = cursor.fetchone()
        
    if row:
        name, analysts, drivers, risks = row
        
        # Still fetch live pricing from Yahoo Finance
        asset = yf.Ticker(ticker)
        df = asset.history(period="30d")
        
        if not df.empty:
            prices = df['Close'].tolist()
            dates = [date.strftime('%b %d') for date in df.index]
            latest_price = prices[-1]
            
            return {
                "ticker": ticker,
                "name": name,
                "live_price": round(latest_price, 2),
                "analyst_view": analysts,
                "macro_drivers": drivers,
                "key_risks": risks,
                "chart_prices": prices,
                "chart_labels": dates
            }
    
    return {"error": "Ticker data missing in Database"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
