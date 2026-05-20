from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import json
import math
import os
import threading
from contextlib import contextmanager

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Cloud Database detection
DB_URL = os.environ.get("DATABASE_URL")
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

@contextmanager
def get_db():
    if DB_URL:
        import psycopg2
        conn = psycopg2.connect(DB_URL)
    else:
        import sqlite3
        conn = sqlite3.connect("commodities.db")
    try: yield conn
    finally: conn.close()

class ResearchUpdate(BaseModel):
    ticker: str
    analysts: str
    drivers: str
    risks: str

def initialize_database():
    with get_db() as conn:
        cursor = conn.cursor()
        if DB_URL:
            cursor.execute("CREATE TABLE IF NOT EXISTS research (ticker VARCHAR PRIMARY KEY, name VARCHAR, analysts TEXT, drivers TEXT, risks TEXT, chart_data TEXT)")
            # Migration: add chart_data column if upgrading from old schema
            try:
                cursor.execute("ALTER TABLE research ADD COLUMN chart_data TEXT DEFAULT '{}'")
                conn.commit()
            except:
                pass  # Column already exists, safe to ignore
        else:
            cursor.execute("CREATE TABLE IF NOT EXISTS research (ticker TEXT PRIMARY KEY, name TEXT, analysts TEXT, drivers TEXT, risks TEXT, chart_data TEXT)")
            # Migration: add chart_data column if upgrading from old schema
            try:
                cursor.execute("ALTER TABLE research ADD COLUMN chart_data TEXT DEFAULT '{}'")
                conn.commit()
            except:
                pass  # Column already exists, safe to ignore

        initial_data = [
            ("URA", "Uranium (Global X ETF)", 
             "<span class='badge buy'>OVERWEIGHT</span> <br><br><ul><li><strong>Consensus Target:</strong> Base case 12-month price targets imply a 25% upside from current consolidation levels.</li><li><strong>Institutional Positioning:</strong> Institutional desks note that structural supply deficits are now mathematically irreversible through 2030.</li><li><strong>Structural Outlook:</strong> Aggressive Western utility contracting cycles are driving unprecedented strength in the term market.</li></ul>", 
             "<ul><li><strong>Tech Giant Demand:</strong> Hyperscalers (Amazon, Microsoft) are signing massive nuclear power purchase agreements to fuel AI data centers.</li><li><strong>Supply Bifurcation:</strong> Western utilities are aggressively, and permanently, shifting their supply chains away from Russian enrichment.</li><li><strong>SMR Adoption:</strong> Small Modular Reactors are rapidly moving past conceptual design and securing massive regulatory approval and funding.</li></ul>", 
             "<ul><li><strong>Policy Volatility:</strong> The sector remains heavily reliant on favorable government subsidies, grid policy, and shifts in public perception.</li><li><strong>Kazatomprom Surprises:</strong> Unexpected production quota increases from the world's largest producer could temporarily crush spot prices.</li><li><strong>Project Delays:</strong> Next-generation reactors and tier-2 mine restarts are facing severe capital constraints and timeline blowouts.</li></ul>", 
             "{}"),

            ("SI=F", "Silver Futures", 
             "<span class='badge buy'>OVERWEIGHT</span> <br><br><ul><li><strong>Consensus Target:</strong> Base case projections imply a 15% upside over the next 12 months.</li><li><strong>Institutional Positioning:</strong> Hedge funds and CTAs are actively increasing net-long exposure.</li><li><strong>Structural Outlook:</strong> Highly constructive outlook due to the most severe physical deficit in modern history.</li></ul>", 
             "<ul><li><strong>Photovoltaic Boom:</strong> Explosive global expansion of solar panel manufacturing requires massive volumes of high-grade silver paste.</li><li><strong>Secondary Byproduct Constraint:</strong> Over 70% of silver is mined as a byproduct of copper/zinc, making supply highly inelastic to silver price spikes.</li><li><strong>Electrification Drive:</strong> Surging global EV production is steadily increasing the required silver loadings per vehicle.</li></ul>", 
             "<ul><li><strong>Industrial Contraction:</strong> Highly vulnerable to global manufacturing PMIs dipping below the 50 baseline.</li><li><strong>Thrifting:</strong> Solar manufacturers are actively researching and implementing ways to use less silver per panel.</li><li><strong>Yield Spikes:</strong> Higher real interest rates increase the opportunity cost of holding non-yielding industrial precious metals.</li></ul>", 
             "{}"),

            ("LIT", "Lithium & Battery Tech", 
             "<span class='badge hold'>NEUTRAL</span> <br><br><ul><li><strong>Consensus Target:</strong> Near-term caution due to inventory destocking, though long-term targets remain heavily skewed to the upside.</li><li><strong>Institutional Positioning:</strong> Growth and tech-focused funds are actively accumulating at these support levels.</li><li><strong>Structural Outlook:</strong> The market remains highly fragmented, awaiting a clear catalyst in consumer EV sales recovery to break out of the current range.</li></ul>", 
             "<ul><li><strong>Irreversible EV Trend:</strong> Long-term demand is firmly backed by binding, state-level regulatory manufacturing mandates globally.</li><li><strong>Grid-Scale Storage:</strong> Battery Energy Storage Systems (BESS) are scaling exponentially to stabilize renewable-heavy Western power grids.</li><li><strong>Strategic Onshoring:</strong> Massive government subsidies (like the US IRA) are aggressively driving local supply chain build-outs.</li></ul>", 
             "<ul><li><strong>Supply Overhangs:</strong> Sustained low-cost production from emerging markets continues to flood the spot market and cap rallies.</li><li><strong>Battery Chemistry Shifts:</strong> The pivot towards solid-state architectures or sodium-ion alternatives could permanently decrease lithium intensity.</li><li><strong>EV Demand Slowdown:</strong> Continued consumer pushback driven by charging infrastructure bottlenecks and elevated financing rates.</li></ul>", 
             "{}"),

            ("GC=F", "Gold Futures", 
             "<span class='badge hold'>NEUTRAL</span> <br><br><ul><li><strong>Consensus Target:</strong> Price targets remain elevated, but near-term entry points appear technically stretched.</li><li><strong>Institutional Positioning:</strong> Central banks continue aggressive buying, while retail ETF inflows remain surprisingly muted.</li><li><strong>Structural Outlook:</strong> The underlying multi-year accumulation floor remains highly resilient despite short-term headwinds.</li></ul>", 
             "<ul><li><strong>Central Bank Accumulation:</strong> BRICS+ nations are aggressively shifting sovereign reserves away from Western fiat currencies.</li><li><strong>Debasement Hedge:</strong> Serves as a persistent, systemic protection against spiraling global sovereign debt levels.</li><li><strong>Safe Haven Premium:</strong> Ongoing geopolitical fragmentation continues to drive structural premium pricing.</li></ul>", 
             "<ul><li><strong>Hawkish Surprises:</strong> Unexpectedly strong economic data could force central banks to hold rates higher for much longer.</li><li><strong>USD Strength:</strong> A relentless, sustained rally in the DXY acts as an immediate deflationary drag on dollar-denominated gold.</li><li><strong>Profit Taking:</strong> Highly vulnerable to sharp, algorithmic sell-offs and liquidations at current all-time highs.</li></ul>", 
             "{}"),

            ("CL=F", "Crude Oil Futures", 
             "<span class='badge hold'>NEUTRAL</span> <br><br><ul><li><strong>Consensus Target:</strong> Forward curves suggest range-bound, sideways trading for the next two quarters.</li><li><strong>Institutional Positioning:</strong> Algorithmic trend-followers are heavily dictating near-term momentum swings.</li><li><strong>Structural Outlook:</strong> Supply balances are tipping back to equilibrium, making the market heavily dependent on OPEC+ policy.</li></ul>", 
             "<ul><li><strong>Geopolitical Chokepoints:</strong> Elevated transit restrictions and risks across critical global marine shipping routes.</li><li><strong>OPEC+ Discipline:</strong> Extended cartel production quota restrictions continue to artificially tighten the physical market.</li><li><strong>SPR Replenishment:</strong> Strategic reserve purchases by sovereign governments are creating a soft floor underneath spot prices.</li></ul>", 
             "<ul><li><strong>Demand Destruction:</strong> Systemic global economic slowing threatens to severely cut commercial shipping and manufacturing utilization.</li><li><strong>Electrification:</strong> Accelerating consumer EV adoption curves are permanently denting long-term gasoline demand forecasts.</li><li><strong>Non-OPEC Supply:</strong> Record-breaking production output from the US, Brazil, and Guyana threatens to flood the market.</li></ul>", 
             "{}"),

            ("RIO", "Iron Ore (Rio Tinto)", 
             "<span class='badge sell'>UNDERWEIGHT</span> <br><br><ul><li><strong>Consensus Target:</strong> Industrial metal analysts remain broadly conservative, targeting a narrow, range-bound price bandwidth.</li><li><strong>Institutional Positioning:</strong> Macro funds remain heavily underweight, awaiting clear signals of state-level infrastructure stimulus.</li><li><strong>Structural Outlook:</strong> The traditional growth engine (Chinese real estate) is structurally impaired, forcing the market to rely on emerging market demand.</li></ul>", 
             "<ul><li><strong>Emerging Market Buildouts:</strong> Aggressive industrial developments across India and Southeast Asia are beginning to offset legacy market weakness.</li><li><strong>Green Steel Premium:</strong> There is rapidly increasing structural demand for the high-grade pellets required for low-carbon direct reduced iron (DRI) processes.</li><li><strong>Supply Discipline:</strong> Top-tier global miners are maintaining remarkably strict production discipline to artificially defend their operating margins.</li></ul>", 
             "<ul><li><strong>Real Estate Contractions:</strong> The multi-year consolidation and deleveraging within massive commercial real estate markets acts as a permanent drag.</li><li><strong>Supply Flooding:</strong> Massive, delayed expansion completions in Africa and South America are finally coming online.</li><li><strong>Scrap Utilization:</strong> The increased use of recycled scrap steel in electric arc furnaces is permanently reducing the baseline demand for raw iron ore.</li></ul>", 
             "{}")
        ]

        for row in initial_data:
            try:
                # FIX 1: Use correct INSERT syntax for each DB engine
                if DB_URL:
                    cursor.execute(
                        "INSERT INTO research VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        row
                    )
                else:
                    cursor.execute(
                        "INSERT OR IGNORE INTO research VALUES (?, ?, ?, ?, ?, ?)",
                        row
                    )
            except Exception as e:
                print(f"[DB Init] Insert failed for {row[0]}: {e}")
        conn.commit()

def refresh_market_data():
    print("Initiating Background Data Refresh with Macro Vectors...")
    tickers = ["URA", "SI=F", "LIT", "GC=F", "CL=F", "RIO"]
    with get_db() as conn:
        cursor = conn.cursor()
        placeholder = "%s" if DB_URL else "?"
        try:
            dxy_asset = yf.Ticker("DX-Y.NYB")
            dxy_df = dxy_asset.history(period="5y", interval="1mo").tail(24)
            dxy_prices = [round(x, 2) for x in dxy_df['Close'].tolist()]
        except Exception as e:
            print(f"[DXY] Failed: {e}")
            dxy_prices = []

        for ticker in tickers:
            try:
                asset = yf.Ticker(ticker)
                df = asset.history(period="5y", interval="1mo")
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                df['SMA_12'] = df['Close'].rolling(window=12).mean()
                df_display = df.tail(24)
                data_payload = {
                    "prices": [round(x, 2) for x in df_display['Close'].tolist()],
                    "sma": [round(x, 2) if not math.isnan(x) else None for x in df_display['SMA_12'].tolist()],
                    "volume": [int(x) for x in df_display['Volume'].tolist()],
                    "dxy": dxy_prices,
                    "labels": [date.strftime('%b %Y') for date in df_display.index]
                }
                cursor.execute(
                    f"UPDATE research SET chart_data = {placeholder} WHERE ticker = {placeholder}",
                    (json.dumps(data_payload), ticker)
                )
                conn.commit()
                print(f"[{ticker}] Updated successfully.")
            except Exception as e:
                print(f"[{ticker}] Failed: {e}")

# --- ADMIN API ENDPOINTS ---
@app.get("/admin/data/{ticker}")
def get_admin_data(ticker: str):
    ticker = ticker.upper()
    with get_db() as conn:
        cursor = conn.cursor()
        placeholder = "%s" if DB_URL else "?"
        cursor.execute(f"SELECT analysts, drivers, risks FROM research WHERE ticker = {placeholder}", (ticker,))
        row = cursor.fetchone()
    if row:
        return {"analysts": row[0], "drivers": row[1], "risks": row[2]}
    raise HTTPException(status_code=404, detail="Ticker not found")

@app.post("/admin/update")
def update_research(data: ResearchUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        placeholder = "%s" if DB_URL else "?"
        cursor.execute(
            f"UPDATE research SET analysts = {placeholder}, drivers = {placeholder}, risks = {placeholder} WHERE ticker = {placeholder}",
            (data.analysts, data.drivers, data.risks, data.ticker)
        )
        conn.commit()
    return {"status": "success"}

# --- PUBLIC API ENDPOINT ---
@app.get("/screener/{ticker}")
def get_commodity_data(ticker: str):
    ticker = ticker.upper()
    with get_db() as conn:
        cursor = conn.cursor()
        placeholder = "%s" if DB_URL else "?"
        cursor.execute(
            f"SELECT name, analysts, drivers, risks, chart_data FROM research WHERE ticker = {placeholder}",
            (ticker,)
        )
        row = cursor.fetchone()
    if row:
        name, analysts, drivers, risks, chart_data_str = row
        try:
            chart_data = json.loads(chart_data_str)
        except:
            chart_data = {"prices": [], "sma": [], "volume": [], "dxy": [], "labels": []}
        return {
            "name": name,
            "analysts": analysts,
            "drivers": drivers,
            "risks": risks,
            "chart_prices": chart_data.get("prices", []),
            "chart_sma": chart_data.get("sma", []),
            "chart_volume": chart_data.get("volume", []),
            "chart_dxy": chart_data.get("dxy", []),
            "chart_labels": chart_data.get("labels", [])
        }
    return {"error": "Ticker not found"}

@app.on_event("startup")
def start_scheduler():
    initialize_database()
    # FIX 2: Run initial data refresh in background so server boots instantly
    # (avoids Render health check timeout caused by slow yfinance calls)
    threading.Thread(target=refresh_market_data, daemon=True).start()
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_market_data, 'interval', hours=12)
    scheduler.start()

# FIX 3: Bind to 0.0.0.0 so Render can reach the server
# Start command on Render should be: uvicorn server:app --host 0.0.0.0 --port $PORT
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
