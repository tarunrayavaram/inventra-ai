# Complete Setup Guide - Inventra AI System

## Quick Start (5 Minutes)

This project comes with a **pre-seeded database**, so you can start immediately after setting up API keys!

### Step 1: Extract/Clone Project

```bash
# If from ZIP
unzip inventra-complete.zip
cd inventra

# If from GitHub
git clone <repo-url>
cd inventra
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate          # macOS/Linux
# OR
venv\Scripts\activate              # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

Required API keys in `.env`:

```bash
# 1. Google Gemini API (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# 2. OpenWeather API (Required)
OPENWEATHER_API_KEY=your_openweather_api_key_here

# 3. Hugging Face API (Optional - for MCP sentiment analysis)
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```

### Step 5: Run the Application!

```bash
# Option 1: Web Interface (Recommended)
python main.py web

# Option 2: Command Line Interface
python main.py cli

# Option 3: View Statistics
python main.py stats
```

**That's it!** The database is already included with sample data. 🎉

---

## Getting API Keys (All Free!)

### 1. Google Gemini API Key ⭐ REQUIRED

**What it's for:** AI-powered business decisions, inventory analysis, and natural language processing.

**How to get it:**

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AI...`)
5. Add to `.env`: `GEMINI_API_KEY=AIza...`

**Free Tier:**
- 60 requests per minute
- 1 million tokens per day
- Perfect for this application!

### 2. OpenWeather API Key ⭐ REQUIRED

**What it's for:** Weather-based demand forecasting for inventory planning.

**How to get it:**

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Go to [My API Keys](https://home.openweathermap.org/api_keys)
4. Copy your default API key
5. Add to `.env`: `OPENWEATHER_API_KEY=abc123...`

**Free Tier:**
- 60 calls per minute
- 1,000,000 calls per month
- Current weather data
- More than enough!

### 3. Hugging Face API Token ⭕ OPTIONAL

**What it's for:** ML MCP Server for sentiment analysis (currently standalone feature).

**How to get it:**

1. Visit [Hugging Face](https://huggingface.co/)
2. Sign up or log in
3. Go to [Settings → Access Tokens](https://huggingface.co/settings/tokens)
4. Click "New token"
5. Name it (e.g., "inventra-mcp")
6. Select "Read" permission
7. Click "Generate token"
8. Copy the token (starts with `hf_...`)
9. Add to `.env`: `HUGGINGFACE_API_TOKEN=hf_...`

**Free Tier:**
- 1,000 requests per month
- Sentiment analysis model
- Used by MCP server (optional)

---

## What's Included

### ✅ Pre-Configured Database

The `database/inventra.db` file (936 KB) comes pre-loaded with:

- **100 inventory items** across 5 regions
- **9,157 sales transactions** (2019-2024)
- **5,000 financial records**
- **20 vendor profiles**
- **0 pending tickets** (clean slate)
- **0 forecasts** (clean slate)

**You don't need to run any database setup!**

### ✅ Sample Data Overview

```
Regions: North, South, East, West, Central
Categories: Electronics, Kitchen Appliances, Home Appliances, Lighting, Home Care
Vendors: 20 suppliers with quality scores and reliability ratings
Date Range: January 2019 - October 2024
```

### ✅ Application Features

1. **Multi-Agent AI System** (LangGraph orchestration)
2. **Natural Language Queries** (ask questions in plain English)
3. **Financial Analysis** (profit/loss, revenue trends)
4. **Inventory Management** (stock tracking, reorder alerts)
5. **Weather Forecasting** (demand prediction)
6. **Ticket Management** (automated vendor tickets)
7. **Interactive Dashboard** (Streamlit web interface)
8. **Conversation Memory** (context across queries)

---

## Usage Examples

### Web Interface

```bash
python main.py web
```

Opens at `http://localhost:8501`

**Try these queries:**
- "Show me the financial summary"
- "What items are low in stock?"
- "Give me sales analysis for North region"
- "What should I reorder for monsoon season?"
- "Show pending tickets"

### CLI Mode

```bash
python main.py cli
```

Interactive command-line interface with the same capabilities.

### Statistics

```bash
python main.py stats
```

Quick overview of:
- Inventory levels and low-stock count
- Sales summary (last 30 days)
- Financial metrics (last 90 days)
- Pending tickets

---

## Optional: ML MCP Server

The ML MCP Server provides sentiment analysis using Hugging Face models.

### Setup

1. Get Hugging Face token (see above)
2. Add to `.env`: `HUGGINGFACE_API_TOKEN=hf_...`
3. Run the server:

```bash
python integrations/mcp_server.py
```

### Features

- Sentiment analysis of text
- Uses DistilBERT model
- MCP protocol compatible

See [integrations/README_MCP.md](integrations/README_MCP.md) for detailed documentation.

---

## Troubleshooting

### Issue: Module not found errors

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: API key errors

**Solution:**
1. Check `.env` file exists in project root
2. Verify API keys have no extra spaces or quotes
3. Test API keys:
   - Gemini: https://makersuite.google.com/app/apikey
   - OpenWeather: https://home.openweathermap.org/api_keys
4. Restart the application after updating `.env`

### Issue: Database file not found

**Solution:**

The database is already included! Check that `database/inventra.db` exists:

```bash
ls -lh database/inventra.db
```

If missing, you may have extracted incorrectly. Re-extract the ZIP or re-clone the repo.

### Issue: Streamlit won't start

**Solution:**
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache

# Try direct command
streamlit run ui/streamlit_app.py
```

### Issue: No data returned from queries

**Cause:** Database has historical data (2019-2024), default queries look at recent dates.

**Solution:** The system automatically falls back to all-time data if no recent data found. Default range is 365 days.

---

## Project Structure

```
inventra/
├── agents/                   # AI Agents
│   ├── coordinator.py        # LangGraph orchestrator
│   ├── decision_agent.py     # Business decisions
│   └── report_agent.py       # Data reports
│
├── services/                 # Business logic
│   ├── data_pipeline.py      # Data aggregation
│   ├── forecast_updater.py   # Weather forecasting
│   └── ticket_manager.py     # Ticket management
│
├── tools/                    # Utilities
│   ├── finance.py            # Financial calculations
│   ├── weather.py            # Weather API
│   └── export.py             # Data export
│
├── database/                 # Database layer
│   ├── inventra.db          # ⭐ Pre-seeded SQLite DB
│   ├── db_manager.py         # Database operations
│   ├── memory_manager.py     # Conversation history
│   ├── schema.sql            # Schema definition
│   └── data/*.csv            # Seed data (reference)
│
├── integrations/             # External integrations
│   ├── mcp_server.py         # ML MCP Server
│   └── README_MCP.md         # MCP documentation
│
├── config/                   # Configuration
│   ├── settings.py           # Settings management
│   └── logger.py             # Logging
│
├── ui/                       # User interface
│   └── streamlit_app.py      # Streamlit web app
│
├── main.py                   # Entry point
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── README.md                 # Main documentation
└── SETUP_GUIDE.md           # This file
```

---

## System Requirements

### Minimum Requirements

- **Python:** 3.10 or higher
- **RAM:** 2 GB
- **Storage:** 100 MB (excluding venv)
- **OS:** macOS, Linux, or Windows

### Recommended

- **Python:** 3.11 or 3.12
- **RAM:** 4 GB
- **Storage:** 500 MB
- **Internet:** For API calls

---

## Technology Stack

- **AI/ML:** LangGraph, LangChain, Google Gemini, Hugging Face
- **Backend:** Python 3.12, SQLite, Pandas
- **Frontend:** Streamlit
- **APIs:** OpenWeather, Hugging Face Inference
- **Protocol:** MCP (Model Context Protocol)

---

## Support & Resources

- **Main README:** [README.md](README.md)
- **MCP Server Guide:** [integrations/README_MCP.md](integrations/README_MCP.md)
- **GitHub Issues:** Report bugs and request features
- **API Documentation:**
  - [Google Gemini](https://ai.google.dev/tutorials/python_quickstart)
  - [OpenWeather](https://openweathermap.org/api)
  - [Hugging Face](https://huggingface.co/docs/api-inference/index)

---

## What's Next?

After setup, try:

1. **Explore the Web Interface:**
   ```bash
   python main.py web
   ```
   Ask natural language questions!

2. **Check Statistics:**
   ```bash
   python main.py stats
   ```

3. **Try CLI Mode:**
   ```bash
   python main.py cli
   ```

4. **Optional: Run MCP Server:**
   ```bash
   python integrations/mcp_server.py
   ```

Enjoy using Inventra! 🎉

---

**Version:** 2.1
**Last Updated:** 2025-11-19
**Database:** Pre-seeded and ready to use
