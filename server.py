from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import json
import math
import os
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
            placeholder = "%s"
        else:
            cursor.execute("CREATE TABLE IF NOT EXISTS research (ticker TEXT PRIMARY KEY, name TEXT, analysts TEXT, drivers TEXT, risks TEXT, chart_data TEXT)")
            placeholder = "?"

        initial_data = [
            ("URA", "Uranium (Global X ETF)", "<span class='badge buy'>OVERWEIGHT</span> <br><br>Consensus 12-mo PT implies 25% upside. Institutional desks note that structural supply deficits are now irreversible through 2030, driven by Western utility contracting cycles.", "<ul><li><strong>Supply Bifurcation:</strong> Western utilities aggressively shifting away from Rosatom enrichment.</li><li><strong>SMR Adoption:</strong> Small Modular Reactors moving from conceptual to regulatory approval.</li><li><strong>Mine Restarts:</strong> Prolonged lag time in bringing Tier 2 mines back online restricts spot supply.</li></ul>", "<ul><li><strong>Policy Volatility:</strong> Heavy reliance on favorable government subsidies and grid policy.</li><li><strong>Kazatomprom Misses:</strong> Unexpected production increases from the world's largest producer could crush spot prices.</li></ul>", "{}"),
            ("SI=F", "Silver Futures", "<span class='badge buy'>OVERWEIGHT</span> <br><br>Highly constructive structural outlook. Industrial demand is quietly outpacing mine output, creating the most severe physical deficit in modern history.", "<ul><li><strong>Photovoltaic Boom:</strong> Explosive global expansion of solar panel manufacturing requires high-grade silver paste.</li><li><strong>Secondary Byproduct Constraint:</strong> Over 70% of silver is mined as a byproduct of copper/zinc, making supply highly inelastic to silver price spikes.</li></ul>", "<ul><li><strong>Industrial Contraction:</strong> Highly vulnerable to global manufacturing PMIs dipping below 50.</li><li><strong>Thrifting:</strong> Solar manufacturers actively researching ways to use less silver per panel.</li></ul>", "{}"),
            ("LIT", "Lithium & Battery Tech", "<span class='badge hold'>NEUTRAL</span> <br><br>The analyst community is cautious due to inventory destocking, but long-term tech analysts maintain an aggressive buy bias.", "<ul><li><strong>Irreversible EV Trend:</strong> Backed by binding regulatory manufacturing mandates.</li><li><strong>Grid-Scale Storage:</strong> BESS systems scaling exponentially across Western grids.</li></ul>", "<ul><li><strong>Supply Overhangs:</strong> Sustained low-cost production flooding spot markets.</li><li><strong>Battery Chemistry:</strong> Shift towards solid-state architectures could decrease lithium intensity.</li></ul>", "{}"),
            ("GC=F", "Gold Futures", "<span class='badge hold'>NEUTRAL</span> <br><br>Consensus targets remain elevated, but near-term entry points are stretched. The underlying multi-year accumulation floor remains highly resilient.", "<ul><li><strong>Central Bank Accumulation:</strong> BRICS+ nations aggressively shifting reserves away from Western fiat.</li><li><strong>Debasement Hedge:</strong> Persistent systemic hedge against spiraling sovereign debt.</li></ul>", "<ul><li><strong>Hawkish Surprises:</strong> Unexpectedly strong economic data forcing central banks to hold rates higher for longer.</li><li><strong>USD Strength:</strong> A relentless rally in the DXY acts as immediate deflationary drag.</li></ul>", "{}"),
            ("CL=F", "Crude Oil Futures", "<span class='badge hold'>NEUTRAL</span> <br><br>High near-term volatility tied to transit bottlenecks. Long-term consensus curves flatten as structural supply balances tip back to equilibrium.", "<ul><li><strong>Geopolitical Chokepoints:</strong> Elevated transit restrictions across critical marine routes.</li><li><strong>OPEC+ Discipline:</strong> Extended cartel production quota restrictions.</li></ul>", "<ul><li><strong>Demand Destruction:</strong> Systemic global recessions cutting shipping and manufacturing utilization.</li><li><strong>Electrification:</strong> Accelerating consumer EV adoption curves denting gasoline demand.</li></ul>", "{}"),
            ("RIO", "Iron Ore (Rio Tinto)", "<span class='badge sell'>UNDERWEIGHT</span> <br><br>Industrial metal analysts remain broadly conservative. Consensus projections target a narrow price bandwidth, heavily dependent on state-level infrastructure allocations.", "<ul><li><strong>Emerging Market Buildouts:</strong> Aggressive developments across India and Southeast Asia.</li><li><strong>Green Steel:</strong> Increasing structural demand for high-grade pellets.</li></ul>", "<ul><li><strong>Real Estate Contractions:</strong> Multi-year consolidation within commercial real estate markets.</li><li><strong>Supply Flooding:</strong> Expansion completions in South America and Africa coming online.</li></ul>", "{}")
        ]
        
        for row in initial_data:
            try:
                cursor.execute(f"INSERT INTO research VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}) ON CONFLICT DO NOTHING", row)
            except:
                pass 
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
        except: dxy_prices = []

        for ticker in tickers:
            try:
                asset = yf.Ticker(ticker)
                df = asset.history(period="5y", interval="1mo") 
                if df.index.tz is not None: df.index = df.index.tz_localize(None)
                df['SMA_12'] = df['Close'].rolling(window=12).mean()
                df_display = df.tail(24) 
                data_payload = {"prices": [round(x, 2) for x in df_display['Close'].tolist()], "sma": [round(x, 2) if not math.isnan(x) else None for x in df_display['SMA_12'].tolist()], "volume": [int(x) for x in df_display['Volume'].tolist()], "dxy": dxy_prices, "labels": [date.strftime('%b %Y') for date in df_display.index]}
                cursor.execute(f"UPDATE research SET chart_data = {placeholder} WHERE ticker = {placeholder}", (json.dumps(data_payload), ticker))
                conn.commit()
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
    if row: return {"analysts": row[0], "drivers": row[1], "risks": row[2]}
    raise HTTPException(status_code=404, detail="Ticker not found")

@app.post("/admin/update")
def update_research(data: ResearchUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        placeholder = "%s" if DB_URL else "?"
        cursor.execute(f"UPDATE research SET analysts = {placeholder}, drivers = {placeholder}, risks = {placeholder} WHERE ticker = {placeholder}", 
                       (data.analysts, data.drivers, data.risks, data.ticker))
        conn.commit()
    return {"status": "success"}

# --- PUBLIC API ENDPOINT ---
@app.get("/screener/{ticker}")
def get_commodity_data(ticker: str):
    ticker = ticker.upper()
    with get_db() as conn:
        cursor = conn.cursor()
        placeholder = "%s" if DB_URL else "?"
        cursor.execute(f"SELECT name, analysts, drivers, risks, chart_data FROM research WHERE ticker = {placeholder}", (ticker,))
        row = cursor.fetchone()
    if row:
        name, analysts, drivers, risks, chart_data_str = row
        try: chart_data = json.loads(chart_data_str)
        except: chart_data = {"prices": [], "sma": [], "volume": [], "dxy": [], "labels": []}
        return {"name": name, "analysts": analysts, "drivers": drivers, "risks": risks, "chart_prices": chart_data.get("prices", []), "chart_sma": chart_data.get("sma", []), "chart_volume": chart_data.get("volume", []), "chart_dxy": chart_data.get("dxy", []), "chart_labels": chart_data.get("labels", [])}
    return {"error": "Ticker not found"}

@app.on_event("startup")
def start_scheduler():
    initialize_database()
    refresh_market_data()
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_market_data, 'interval', hours=12)
    scheduler.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
