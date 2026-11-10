# Running Inventra with UV

This guide shows you how to run Inventra using `uv`, a fast Python package manager.

## Prerequisites

Install `uv` if you haven't already:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with Homebrew (macOS)
brew install uv
```

## Quick Start with UV

### 1. Sync Dependencies

This will create a virtual environment and install all dependencies:

```bash
uv sync
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
```

Add your API keys:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

### 3. Run the Application

#### Option 1: Web Interface (Recommended)

```bash
uv run python main.py web
```

Or using the entry point:

```bash
uv run inventra web
```

#### Option 2: CLI Mode

```bash
uv run python main.py cli
```

Or:

```bash
uv run inventra cli
```

#### Option 3: View Statistics

```bash
uv run python main.py stats
```

Or:

```bash
uv run inventra stats
```

## Advanced UV Commands

### Add a New Dependency

```bash
uv add package-name
```

### Add a Development Dependency

```bash
uv add --dev pytest
```

### Remove a Dependency

```bash
uv remove package-name
```

### Update All Dependencies

```bash
uv sync --upgrade
```

### Run Streamlit Directly

```bash
uv run streamlit run ui/streamlit_app.py
```

### Run MCP Server

```bash
uv run python integrations/mcp_server.py
```

## Why UV?

- **Fast**: 10-100x faster than pip
- **Reliable**: Deterministic dependency resolution
- **Simple**: No need to manually manage virtual environments
- **Compatible**: Works with standard Python packaging (pyproject.toml)

## Troubleshooting

### Issue: UV not found

**Solution:**
```bash
# Ensure uv is in your PATH
which uv

# If not found, reinstall or add to PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

### Issue: Python version mismatch

**Solution:**
```bash
# UV can manage Python versions too
uv python install 3.11
uv sync --python 3.11
```

### Issue: Dependencies not syncing

**Solution:**
```bash
# Force reinstall
uv sync --reinstall
```

## Comparison: pip vs UV

| Task | pip/venv | UV |
|------|----------|-----|
| Create env + install | `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` | `uv sync` |
| Run script | `python main.py web` | `uv run python main.py web` |
| Add dependency | `pip install package && pip freeze > requirements.txt` | `uv add package` |
| Speed | Slower | **10-100x faster** |

## Getting API Keys

### Google Gemini API Key (Required)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API Key
3. Add to `.env`: `GEMINI_API_KEY=your_key`

### OpenWeather API Key (Required)
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Copy API key
4. Add to `.env`: `OPENWEATHER_API_KEY=your_key`

## Complete Setup Example

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone/navigate to project
cd inventra

# 3. Sync dependencies (creates venv + installs packages)
uv sync

# 4. Configure API keys
cp .env.example .env
nano .env  # Add your API keys

# 5. Run the application
uv run inventra web

# That's it! 🎉
```

## What UV Does Automatically

1. ✅ Creates a virtual environment (`.venv/`)
2. ✅ Installs all dependencies from `pyproject.toml`
3. ✅ Manages Python versions
4. ✅ Ensures reproducible builds
5. ✅ Handles dependency conflicts

## Need Help?

- **UV Documentation**: https://docs.astral.sh/uv/
- **Inventra README**: See [README.md](README.md)
- **Setup Guide**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

**Version**: 2.1.0  
**Last Updated**: 2024-10-24
