"""LLM-powered business decision making - Functional implementation."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.report_agent import get_inventory_status, calculate_reorder_quantity
from database.memory_manager import record_forecast
from services.data_pipeline import get_sales_patterns, get_vendor_performance
from tools.finance import get_financial_summary
from tools.weather import get_weather_forecast_tool
from config.settings import get_settings
from config.logger import get_logger

logger = get_logger(__name__)


# Pure formatting functions

def format_low_stock_items(items: List[Dict]) -> str:
    """Format low stock items for LLM prompt.

    Pure function to transform data into readable text.

    Args:
        items: List of low-stock inventory items

    Returns:
        Formatted string for LLM consumption
    """
    if not items:
        return "None"

    lines = []
    for item in items[:10]:  # Limit to top 10
        lines.append(
            f"- {item['sku']}: {item['name']} ({item['category']}) - "
            f"{item['qty']} units (threshold: {item['reorder_threshold']})"
        )
    return "\n".join(lines)


def format_vendors(vendors: List[Dict]) -> str:
    """Format vendor list for LLM prompt.

    Pure function to transform vendor data into readable text.

    Args:
        vendors: List of vendor performance data

    Returns:
        Formatted string for LLM consumption
    """
    lines = []
    for i, v in enumerate(vendors, 1):
        lines.append(
            f"{i}. {v['name']}\n"
            f"   - Vendor ID: {v['vendor_id']}\n"
            f"   - Quality Score: {v['quality_score']}/5.0\n"
            f"   - Reliability: {v['reliability']}\n"
            f"   - Lead Time: {v['lead_time_days']} days"
        )
    return "\n".join(lines)


# Prompt building functions (pure)

def build_system_prompt(mcp_instructions: str) -> str:
    """Build system prompt for decision agent.

    Args:
        mcp_instructions: MCP tool usage instructions

    Returns:
        Complete system prompt string
    """
    return f"""You are an intelligent inventory and financial decision agent for Inventra.

Your role is to analyze data and provide actionable recommendations considering:
- Current inventory levels and low-stock situations
- Historical sales patterns and trends
- Weather forecasts and seasonal impacts
- Vendor performance and reliability
- Financial metrics and profitability

When making decisions:
1. Always consider weather impact on product categories
2. Prioritize high-quality, reliable vendors
3. Balance inventory costs with stockout risks
4. Focus on profitable regions and products
5. Provide specific, actionable recommendations with quantities and vendors

{mcp_instructions}

Be concise, data-driven, and business-focused in your analysis."""


def build_inventory_analysis_prompt(
    inventory_info: Dict[str, Any],
    vendors: List[Dict[str, Any]],
    region: Optional[str] = None
) -> str:
    """Build prompt for inventory needs analysis.

    Args:
        inventory_info: Inventory status data
        vendors: Top vendor performance data
        region: Optional region filter

    Returns:
        Formatted prompt string
    """
    region_str = f" for {region.capitalize()} region" if region else ""

    return f"""Analyze inventory situation{region_str}:

Inventory Summary:
- Total items: {inventory_info['total_items']}
- Low stock items: {inventory_info['low_stock_count']}

Low Stock Items:
{format_low_stock_items(inventory_info['low_stock_items'])}

Top Available Vendors:
{format_vendors(vendors)}

Task: Use the weather forecast tool to check upcoming weather for {region or 'all regions'}, then recommend:
1. Which items to reorder immediately and why
2. Recommended quantities based on weather and sales patterns
3. Best vendors to use for each item
4. Priority order for each recommendation

Keep recommendations actionable and specific."""


def build_sales_opportunity_prompt(
    sales_data: Dict[str, Any],
    category: Optional[str] = None,
    days: int = 7
) -> str:
    """Build prompt for sales opportunity analysis.

    Args:
        sales_data: Recent sales performance data
        category: Optional category filter
        days: Forecast days

    Returns:
        Formatted prompt string
    """
    category_str = f" for {category}" if category else ""

    return f"""Analyze sales opportunities{category_str} for the next {days} days:

Recent Sales Performance (30 days):
- Total sales: {sales_data.get('total_sales', 0)} units
- Total revenue: Rs {sales_data.get('total_revenue', 0):,.2f}
- Top regions: {list(sales_data.get('region_performance', {}).keys())[:3]}

Task: Check weather forecast for all regions and identify:
1. Which product categories will likely see increased demand
2. Which regions present the best opportunities
3. Recommended inventory adjustments to capture demand
4. Expected revenue impact

Focus on weather-sensitive products."""


def build_vendor_selection_prompt(
    vendors: List[Dict[str, Any]],
    sku: Optional[str] = None
) -> str:
    """Build prompt for vendor selection optimization.

    Args:
        vendors: Vendor performance data
        sku: Optional SKU filter

    Returns:
        Formatted prompt string
    """
    sku_str = f" for SKU {sku}" if sku else ""

    return f"""Recommend optimal vendor selection{sku_str}:

Top 10 Vendors by Performance:
{format_vendors(vendors)}

Task: Analyze and recommend:
1. Best overall vendor
2. Backup vendor options
3. Trade-offs between quality, lead time, and reliability
4. Risk mitigation strategies

Consider quality score, reliability rating, and lead time in your analysis."""


def build_financial_health_prompt(
    finance: Dict[str, Any],
    region: Optional[str] = None
) -> str:
    """Build prompt for financial health analysis.

    Args:
        finance: Financial metrics data
        region: Optional region filter

    Returns:
        Formatted prompt string
    """
    region_str = f" for {region.capitalize()} region" if region else ""

    profit_margin = (finance['net_profit'] / finance['total_sales'] * 100) if finance['total_sales'] > 0 else 0

    return f"""Analyze financial health{region_str} (last 90 days):

Financial Summary:
- Total sales: Rs {finance['total_sales']:,.2f}
- Total purchases: Rs {finance['total_purchases']:,.2f}
- Net profit: Rs {finance['net_profit']:,.2f}
- Profit margin: {profit_margin:.1f}%
- Transaction count: {finance['transaction_count']}

Task: Provide:
1. Financial health assessment
2. Key insights on profitability trends
3. Recommendations to improve margins
4. Cost optimization opportunities
5. Revenue growth strategies

Be specific and actionable."""


# Agent creation function

def create_decision_agent_executor() -> Tuple[AgentExecutor, ChatGoogleGenerativeAI]:
    """Create LangChain agent executor for decision making.

    Returns:
        Tuple of (AgentExecutor, LLM instance)
    """
    settings = get_settings()

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3,
    )

    tools = [get_weather_forecast_tool]

    logger.info(f"Decision Agent initialized with {len(tools)} tool(s)")

    system_prompt = build_system_prompt("")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=5,
        handle_parsing_errors=True
    )

    return agent_executor, llm


# Main decision functions

def analyze_inventory_needs(region: Optional[str] = None) -> Dict[str, Any]:
    """Analyze inventory and recommend reorders.

    Functional implementation using agent executor.

    Args:
        region: Optional region filter

    Returns:
        Dictionary with analysis results and recommendations
    """
    # Get data
    inventory_info = get_inventory_status(region)
    vendors = get_vendor_performance()[:5]

    # Build prompt
    prompt = build_inventory_analysis_prompt(inventory_info, vendors, region)

    # Execute analysis
    agent_executor, _ = create_decision_agent_executor()
    result = agent_executor.invoke({"input": prompt})

    # Record forecasts for tracking
    today = datetime.now().strftime('%Y-%m-%d')
    for item in inventory_info['low_stock_items']:
        predicted_qty = calculate_reorder_quantity(item['qty'], item['reorder_threshold'])
        if predicted_qty > 0:
            record_forecast(
                forecast_date=today,
                sku=item['sku'],
                predicted_demand=predicted_qty,
                predicted_weather="Unknown",
                recommendation=f"Reorder {predicted_qty} units due to low stock"
            )

    return {
        'region': region,
        'low_stock_count': inventory_info['low_stock_count'],
        'analysis': result['output'],
        'context': {
            'inventory': inventory_info,
            'top_vendors': vendors
        }
    }


def analyze_sales_opportunity(category: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
    """Identify sales opportunities based on weather and trends.

    Args:
        category: Optional category filter
        days: Number of days to forecast

    Returns:
        Dictionary with opportunity analysis
    """
    # Get recent sales data
    sales_data = get_sales_patterns(days=30)

    # Build prompt
    prompt = build_sales_opportunity_prompt(sales_data, category, days)

    # Execute analysis
    agent_executor, _ = create_decision_agent_executor()
    result = agent_executor.invoke({"input": prompt})

    return {
        'category': category,
        'forecast_days': days,
        'analysis': result['output'],
        'sales_data': sales_data
    }


def optimize_vendor_selection(sku: Optional[str] = None) -> Dict[str, Any]:
    """Recommend best vendors for procurement.

    Args:
        sku: Optional SKU filter

    Returns:
        Dictionary with vendor recommendations
    """
    # Get vendor performance data
    vendors = get_vendor_performance()

    # Build prompt
    prompt = build_vendor_selection_prompt(vendors, sku)

    # Execute analysis
    agent_executor, _ = create_decision_agent_executor()
    result = agent_executor.invoke({"input": prompt})

    return {
        'sku': sku,
        'analysis': result['output'],
        'top_vendors': vendors[:5]
    }


def analyze_financial_health(region: Optional[str] = None) -> Dict[str, Any]:
    """Analyze financial health and provide recommendations.

    Args:
        region: Optional region filter

    Returns:
        Dictionary with financial analysis
    """
    # Get financial data
    finance = get_financial_summary(region=region, days=90)

    if 'error' in finance:
        return {'error': finance['error'], 'region': region}

    # Build prompt
    prompt = build_financial_health_prompt(finance, region)

    # Execute analysis
    agent_executor, _ = create_decision_agent_executor()
    result = agent_executor.invoke({"input": prompt})

    return {
        'region': region,
        'analysis': result['output'],
        'metrics': finance
    }


# Batch analysis function

def analyze_all_regions(analysis_type: str = 'inventory') -> Dict[str, Any]:
    """Run analysis across all regions.

    Args:
        analysis_type: Type of analysis ('inventory', 'financial', 'sales')

    Returns:
        Dictionary with results for each region
    """
    regions = ['north', 'south', 'east', 'west', 'central']

    analysis_functions = {
        'inventory': analyze_inventory_needs,
        'financial': analyze_financial_health,
        'sales': lambda r: analyze_sales_opportunity(category=None, days=7)
    }

    analysis_func = analysis_functions.get(analysis_type, analyze_inventory_needs)

    results = {}
    for region in regions:
        try:
            results[region] = analysis_func(region)
        except Exception as e:
            logger.error(f"Failed to analyze {region}: {e}")
            results[region] = {'error': str(e)}

    return {
        'analysis_type': analysis_type,
        'results': results
    }
