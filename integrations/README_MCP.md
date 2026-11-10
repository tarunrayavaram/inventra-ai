# ML MCP Server - Setup & Usage Guide

## Overview

The ML MCP (Model Context Protocol) Server provides sentiment analysis capabilities using Hugging Face's deployed models. This server runs as a standalone process and can be accessed by the main Inventra application.

## Features

- **Sentiment Analysis**: Analyze text sentiment using DistilBERT model
- **Pure API Calls**: No local fallbacks - uses deployed Hugging Face models only
- **MCP Protocol**: Standard protocol for AI tool communication

## Prerequisites

### 1. Hugging Face API Token (Free)

Get your free API token from Hugging Face:

1. Visit [Hugging Face](https://huggingface.co/)
2. Sign up or log in to your account
3. Go to [Settings → Access Tokens](https://huggingface.co/settings/tokens)
4. Click "New token"
5. Give it a name (e.g., "inventra-mcp")
6. Select "Read" permission
7. Click "Generate token"
8. Copy the token

### 2. Add to Environment Variables

Edit your `.env` file and add:

```bash
HUGGINGFACE_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Running the MCP Server

### Option 1: Standalone Mode

Run the MCP server independently:

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate

# Set environment variable (if not in .env)
export HUGGINGFACE_API_TOKEN="your_token_here"

# Run the server
python integrations/mcp_server.py
```

The server will start and listen for MCP protocol messages via stdin/stdout.

### Option 2: Integrated with Inventra (Future Enhancement)

Currently, the MCP server runs standalone. Future integration with the main application would allow:
- Automatic server startup
- Sentiment analysis of customer feedback
- Product review analysis
- Vendor communication sentiment tracking

## Testing the MCP Server

### Test Sentiment Analysis

Create a test script `test_mcp.py`:

```python
import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def test_sentiment():
    # Start MCP server as subprocess
    server_params = {
        "command": "python",
        "args": ["integrations/mcp_server.py"]
    }

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Call sentiment analysis
            result = await session.call_tool(
                "analyze_sentiment",
                arguments={"text": "This product is absolutely amazing!"}
            )

            print("Sentiment Result:", result.content[0].text)

# Run test
asyncio.run(test_sentiment())
```

Run the test:

```bash
python test_mcp.py
```

Expected output:
```json
{
  "sentiment": "POSITIVE",
  "confidence": 0.999
}
```

## Available Tools

### analyze_sentiment

Analyzes the sentiment of text using DistilBERT model.

**Input:**
```json
{
  "text": "Your text to analyze"
}
```

**Output:**
```json
{
  "sentiment": "POSITIVE" | "NEGATIVE",
  "confidence": 0.0-1.0
}
```

**Example Use Cases:**
- Analyze customer feedback sentiment
- Evaluate vendor communication tone
- Process product review sentiment
- Monitor support ticket sentiment trends

## Architecture

```
┌─────────────────────────────────────────┐
│     Inventra Main Application          │
│  (agents, services, decision-making)   │
└────────────────┬────────────────────────┘
                 │
                 │ MCP Protocol
                 │ (stdio)
                 │
┌────────────────▼────────────────────────┐
│         ML MCP Server                   │
│    (integrations/mcp_server.py)        │
└────────────────┬────────────────────────┘
                 │
                 │ HTTPS API Calls
                 │
┌────────────────▼────────────────────────┐
│      Hugging Face Inference API        │
│   (distilbert sentiment analysis)      │
└─────────────────────────────────────────┘
```

## Troubleshooting

### Issue: "HUGGINGFACE_API_TOKEN not found"

**Solution:**
```bash
# Check if .env file exists
cat .env | grep HUGGINGFACE

# If not, add it
echo "HUGGINGFACE_API_TOKEN=your_token_here" >> .env
```

### Issue: "Rate limit exceeded"

**Cause:** Free tier has rate limits (1000 requests/month)

**Solution:**
- Wait for rate limit reset
- Upgrade to Hugging Face PRO ($9/month)
- Use caching to reduce API calls

### Issue: "Model loading timeout"

**Cause:** Cold start - model needs to load on first request

**Solution:**
- Wait 30-60 seconds for model to load
- Retry the request
- Models stay warm for ~15 minutes after last use

### Issue: Connection refused

**Cause:** MCP server not running

**Solution:**
```bash
# Start the server
python integrations/mcp_server.py
```

## Model Information

**Model:** `distilbert-base-uncased-finetuned-sst-2-english`

- **Type:** Sentiment Analysis
- **Base:** DistilBERT (smaller, faster BERT)
- **Training:** SST-2 sentiment dataset
- **Classes:** POSITIVE, NEGATIVE
- **Accuracy:** ~91% on SST-2 test set
- **Latency:** ~100-300ms (cold start: ~10s)

## API Rate Limits

### Free Tier (Default)
- **Requests:** 1,000 requests/month
- **Rate:** ~30 requests/hour
- **Timeout:** 30 seconds per request

### PRO Tier ($9/month)
- **Requests:** 1,000,000 requests/month
- **Rate:** No hourly limit
- **Priority:** Faster inference
- **Dedicated:** Optional dedicated endpoints

## Future Enhancements

1. **Additional Models:**
   - Product categorization
   - Named entity recognition
   - Text summarization

2. **Integration Features:**
   - Auto-analyze customer tickets
   - Sentiment trends dashboard
   - Vendor communication scoring

3. **Performance:**
   - Response caching
   - Batch processing
   - Model warm-up strategy

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file with real tokens
- Use `.env.example` for sharing templates
- Rotate tokens if accidentally exposed
- Use read-only tokens when possible

## Support

For issues with:
- **MCP Server:** Check this guide and logs
- **Hugging Face API:** Visit [HF Status](https://status.huggingface.co/)
- **Model Performance:** See [Model Card](https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english)

---

**Last Updated:** 2025-11-19
**Version:** 1.0
