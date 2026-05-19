# Institutional Commodity Intelligence Terminal

## Overview
A full-stack financial data platform designed to monitor and analyze structural macro theses across core commodities (Uranium, Silver, Lithium, Gold, Crude Oil, Iron Ore). 

This platform bridges asynchronous market data pipelines with embedded database persistence, delivering a reactive, institutional-grade dark-mode interface.

## Architecture & Tech Stack
* **Backend Engine:** Python (`FastAPI`) for high-performance asynchronous REST routing.
* **Data Pipeline:** `yfinance` integration for real-time market time-series extraction.
* **Persistence Layer:** Embedded SQLite database (`sqlite3`) strictly separating qualitative research from application logic.
* **Frontend UI:** Vanilla JavaScript, HTML5, and CSS3.
* **Visualizations:** `Chart.js` for dynamic charting and algorithmic layout adjustments.

## Core Features
* **Real-Time Data Injection:** Fetches and structures live 30-day closing arrays dynamically upon asset selection.
* **Fundamental Math Engine:** Client-side JavaScript computes 30-day rolling highs, lows, and percentage returns.
* **Algorithmic UI:** Charting and metric cards automatically shift to Institutional Green or Crimson Red based on monthly performance.
* **Database Driven:** Research theses are persisted in an SQL table rather than hardcoded, allowing for scalable administration.

## Local Setup
1. Clone the repository.
2. Install Python dependencies: `pip install fastapi uvicorn yfinance`
3. Launch the API server: `python server.py` (The SQLite database will auto-generate on first run).
4. Open `dashboard.html` in any modern web browser.
