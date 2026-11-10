"""
ML MCP Server - Uses ONLY Deployed Hugging Face Models

No fallbacks, no local logic - just API calls to deployed models.

Usage:
    export HUGGINGFACE_API_TOKEN="your_token"
    python integrations/ml_mcp_server.py
"""

import json
import asyncio
import httpx
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class MLMCPServer:
    """MCP Server - Pure Hugging Face API calls only"""

    def __init__(self):
        self.server = Server("ml-prediction")
        self.hf_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
        self._setup_tools()

    def _setup_tools(self):
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="analyze_sentiment",
                    description="Sentiment analysis using Hugging Face",
                    inputSchema={
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if name == "analyze_sentiment":
                return await self._analyze_sentiment(arguments["text"])
            raise ValueError(f"Unknown tool: {name}")

    async def _analyze_sentiment(self, text: str) -> list[TextContent]:
        """Call Hugging Face sentiment API"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}

            response = await client.post(
                "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english",
                headers=headers,
                json={"inputs": text},
                timeout=30.0
            )

            result = response.json()
            top = max(result[0], key=lambda x: x['score'])

            return [TextContent(
                type="text",
                text=json.dumps({
                    "sentiment": top['label'],
                    "confidence": round(top['score'], 3)
                }, indent=2)
            )]

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


async def main():
    print("ML MCP Server - Hugging Face API Only")
    print("Tool: analyze_sentiment\n")
    server = MLMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
