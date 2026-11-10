# Inventra - AI-Powered Inventory & Financial Management System

**An intelligent multi-agent system for inventory management, financial analysis, and business decision-making using LangGraph, Gemini AI, and weather forecasting.**

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Keys Setup](#api-keys-setup)
- [Troubleshooting](#troubleshooting)
- [Technology Stack](#technology-stack)

---

## Features

### Core Capabilities
- **Multi-Agent AI System**: Orchestrated using LangGraph for complex decision-making
- **Financial Analysis**: Automated financial summaries, profit/loss tracking, revenue analysis
- **Inventory Management**: Real-time stock tracking, low-stock alerts, reorder recommendations
- **Weather Integration**: Weather-based demand forecasting and inventory planning
- **Ticket Management**: Automated vendor ticketing for restocking and issues
- **Interactive Dashboard**: Streamlit-based web interface for visualization
- **Conversation Memory**: Maintains context across interactions
- **Export Capabilities**: Export reports to CSV, JSON, Excel

### AI Agents
1. **Coordinator Agent** (LangGraph): Orchestrates workflow between agents
2. **Decision Agent**: Makes inventory and financial recommendations
3. **Report Agent**: Generates data reports and summaries

---

## Architecture

### Simplified Multi-Agent Workflow (4-Node LangGraph)

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              (Streamlit Web App / CLI)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   1. CLASSIFY Intent    │
        │   (LLM Classification)  │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   2. GATHER Data        │
        │   (Report Agent)        │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   3. DECIDE (Optional)  │
        │   (Decision Agent + AI) │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   4. RESPOND Format     │
        │   (User-friendly text)  │
        └─────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Coordinator (LangGraph - 341 lines)            │
│   Classify → Gather → Decide → Respond                     │
└─────┬──────────────────────────────┬─────────────────┬──────┘
      │                              │                 │
┌─────▼─────────┐      ┌─────────────▼──────┐  ┌──────▼──────┐
│ Decision Agent│      │   Report Agent     │  │ Data Pipeline│
│ (Gemini AI)   │      │  (Data Analysis)   │  │ (Processing) │
│ - Reorder Rec │      │  - Inventory       │  │ - Aggregates│
│ - Vendor Sel  │      │  - Financial       │  │ - Caching   │
│ - Weather Fcs │      │  - Sales           │  │             │
│ + MCP Tools   │      │  - Tickets         │  │             │
└─────┬─────────┘      └─────────────┬──────┘  └──────┬──────┘
      │                              │                 │
┌─────▼──────────────────────────────▼─────────────────▼──────┐
│                   Services & Tools Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐               │
│  │ Finance  │  │ Weather  │  │   Tickets   │               │
│  │  Tool    │  │   Tool   │  │   Manager   │               │
│  └──────────┘  └──────────┘  └─────────────┘               │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    Database Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   SQLite     │  │   Memory     │  │     CSV      │      │
│  │  (inventra.db)│  │  (Conversations)│ │  (Seed Data) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **Simplified Flow**: 6 nodes reduced to 4 nodes (47% less complexity)
- **Clear Separation**: Coordinator orchestrates, agents execute
- **Side Effect Ownership**: Decision Agent owns tickets/forecasts via MCP tools
- **No Redundancy**: Removed duplicate forecast tracking and ticket creation logic

---

## Prerequisites

### Required Software
- **Python**: 3.10 or higher
- **pip**: Latest version
- **Git**: For cloning the repository

### Required API Keys
- **Google Gemini API Key**: For AI agents ([Get it here](https://makersuite.google.com/app/apikey))
- **OpenWeather API Key**: For weather forecasting ([Get it here](https://openweathermap.org/api))

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/programteam-cn/GenAI-Live-Course-Project-5-Intelligent-Financial-and-Inventory-Management.git
cd GenAI-Live-Course-Project-5-Intelligent-Financial-and-Inventory-Management
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

### Step 5: Initialize Database

```bash
# This will create and seed the database with sample data
python main.py setup
```

---

## Configuration

### Environment Variables

Edit the `.env` file with your API keys:

```bash
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY=your_openweather_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Database Configuration
DATABASE_PATH=./database/inventra.db

# Application Settings
LOG_LEVEL=INFO
WEATHER_CACHE_TTL=1800
MAX_CONVERSATION_HISTORY=10
```

### Database Configuration

The system uses SQLite database located at `database/inventra.db`. It includes:
- **Inventory**: Product stock levels and details
- **Sales**: Historical sales transactions
- **Finance**: Financial transactions (sales, purchases)
- **Vendors**: Vendor information
- **Tickets**: Reorder and issue tickets
- **Forecasts**: Weather-based demand forecasts

---

## Usage

### Option 1: Web Interface (Recommended)

```bash
# Start the Streamlit web application
python main.py web

# Or directly:
streamlit run ui/streamlit_app.py
```

The web interface will open at `http://localhost:8501`

**Features:**
- Chat interface for natural language queries
- Interactive data visualizations
- Real-time financial and inventory dashboards
- Quick action buttons for common tasks
- Ticket management interface

### Option 2: Command Line Interface (CLI)

```bash
# Start interactive CLI mode
python main.py cli
```

**Example Queries:**
```
> Show me the financial summary
> What items need reordering?
> Give me sales analysis for North region
> What are my pending tickets?
> Analyze inventory for monsoon season
```

### Option 3: View Statistics

```bash
# Display system statistics
python main.py stats
```

Shows:
- Total inventory items and low-stock count
- Sales summary (total units and revenue)
- Financial overview (sales, purchases, profit)
- Pending tickets count and value

---

## Project Structure

```
inventra/
├── agents/                    # AI Agents (LLM-powered)
│   ├── coordinator.py         # LangGraph orchestrator
│   ├── decision_agent.py      # Business decision making
│   └── report_agent.py        # Data aggregation & reports
│
├── services/                  # Business Logic & Workflows
│   ├── data_pipeline.py       # Data aggregation
│   ├── forecast_updater.py    # Weather-based forecasting
│   └── ticket_manager.py      # Ticket lifecycle management
│
├── tools/                     # Utility Functions
│   ├── finance.py             # Financial calculations
│   ├── weather.py             # Weather API integration
│   └── export.py              # Data export utilities
│
├── database/                  # Data Persistence Layer
│   ├── db_manager.py          # SQLite operations
│   ├── memory_manager.py      # Conversation history
│   ├── seed_db.py             # Database initialization
│   ├── inventra.db            # SQLite database
│   ├── schema.sql             # Database schema
│   └── data/                  # CSV seed files
│
├── integrations/              # External Integrations
│   └── mcp_tools.py           # MCP protocol tools
│
├── config/                    # Configuration
│   ├── settings.py            # Environment settings
│   └── logger.py              # Logging configuration
│
├── ui/                        # User Interface
│   └── streamlit_app.py       # Streamlit web app
│
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## API Keys Setup

### 1. Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key
5. Add to `.env`: `GEMINI_API_KEY=your_key_here`

### 2. OpenWeather API Key

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Go to API Keys section
4. Copy your default API key (or create a new one)
5. Add to `.env`: `OPENWEATHER_API_KEY=your_key_here`

**Note**: The free tier of OpenWeather API is sufficient for this application.

---

## Troubleshooting

### Issue: "Name cannot be empty" Error

**Cause**: Streamlit is caching old code or tools are not properly named.

**Solution**:
```bash
# Stop Streamlit (Ctrl+C)
# Clear cache
rm -rf ~/.streamlit/cache
# Restart
streamlit run ui/streamlit_app.py
```

### Issue: No data returned from queries

**Cause**: Database has historical data (2019-2024), queries default to recent dates.

**Solution**: The system automatically falls back to all-time data if no recent data is found. Default query range is 365 days.

### Issue: API Key errors

**Cause**: Missing or invalid API keys in `.env`

**Solution**:
1. Verify `.env` file exists in project root
2. Check API keys are correct (no extra spaces)
3. Ensure keys have proper permissions/are active
4. Restart the application after updating `.env`

### Issue: Database not found

**Cause**: Database not initialized

**Solution**:
```bash
python main.py setup
```

### Issue: Import errors

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

---

## Technology Stack

### AI & ML
- **LangGraph**: Multi-agent orchestration and workflow management
- **LangChain**: Agent creation and tool integration
- **Google Gemini AI**: Large language model for decision-making
- **OpenWeather API**: Weather data for demand forecasting

### Backend
- **Python 3.12**: Core programming language
- **SQLite**: Embedded database
- **Pandas**: Data manipulation and analysis
- **Pydantic**: Data validation and settings management

### Frontend
- **Streamlit**: Interactive web dashboard
- **Plotly**: Data visualization (if extended)

### Development
- **Git**: Version control
- **Python Virtual Environment**: Dependency isolation
- **Logging**: Python logging module

---

## Sample Queries

### Financial Analysis
```
- "Show me the financial summary"
- "What's our profit margin?"
- "Give me sales breakdown by region"
- "Show revenue trends"
```

### Inventory Management
```
- "What items are low in stock?"
- "Check inventory for North region"
- "Which products need reordering?"
- "Show me all electronics inventory"
```

### Business Decisions
```
- "Give me reorder recommendations"
- "What should I stock for monsoon season?"
- "Suggest vendors for restocking"
- "Analyze sales opportunities"
```

### Tickets
```
- "Show pending tickets"
- "What tickets need attention?"
- "List all vendor tickets"
```

---

## Contributing

This is an educational project. Feel free to:
- Report issues
- Suggest improvements
- Fork and extend functionality

---

## License

This project is created for educational purposes as part of the GenAI Live Course.

---

## Authors

- **GenAI Live Course Team**
- **Enhanced with Claude Code**

---

## Acknowledgments

- Google Gemini AI for providing the LLM capabilities
- LangChain and LangGraph for agent orchestration frameworks
- Streamlit for the amazing web framework
- OpenWeatherMap for weather data

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with detailed description

---

## Quick Start Summary

```bash
# 1. Clone and setup
git clone https://github.com/programteam-cn/GenAI-Live-Course-Project-5-Intelligent-Financial-and-Inventory-Management.git
cd GenAI-Live-Course-Project-5-Intelligent-Financial-and-Inventory-Management

# 2. Create environment and install
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Initialize database
python main.py setup

# 5. Run!
python main.py web
```

**That's it! Your AI-powered inventory management system is ready!**

---

**Last Updated**: 2025-10-29
**Version**: 2.1 (Simplified & Optimized)

## Recent Improvements

### v2.1 (2025-10-29) - Coordinator Simplification
- Reduced coordinator complexity by 47% (641 → 341 lines)
- Simplified LangGraph workflow (6 nodes → 4 nodes)
- Removed redundant forecast tracking and ticket creation logic
- Cleaner separation of concerns (coordinator orchestrates, agents execute)
- All tests passing (11/11, 100% success rate)

### v2.0 (2025-10-29) - Production Release
- Complete system testing (11/11 tests passed)
- Fixed weather tool naming for Gemini API compatibility
- Fixed database seeding path issue
- Added comprehensive test suite and detailed test report
- Export functionality verified (JSON, CSV, Summary reports)
