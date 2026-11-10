"""LangGraph orchestration - Functional implementation."""

import operator
from typing import Dict, Any, TypedDict, Annotated, Sequence, Callable, Optional
from functools import partial

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from agents.decision_agent import analyze_inventory_needs, analyze_sales_opportunity, optimize_vendor_selection
from agents.report_agent import get_inventory_status, get_sales_patterns, get_financial_summary
from services.ticket_manager import get_pending_tickets, get_ticket_stats
from config.settings import get_settings
from config.logger import get_logger
from database.memory_manager import add_conversation

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State object for LangGraph workflow."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    intent: str
    region: str
    category: str
    sku: str
    data_result: Dict[str, Any]
    decision_result: Dict[str, Any]
    final_response: str


# Pure helper functions for parsing

def parse_classification_response(content: str) -> Dict[str, Optional[str]]:
    """Parse LLM classification response into structured data.

    Args:
        content: Raw LLM response text

    Returns:
        Dictionary with intent, region, category, and sku
    """
    result = {
        'intent': 'general',
        'region': None,
        'category': None,
        'sku': None
    }

    for line in content.strip().split("\n"):
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        val = val.strip()
        key = key.strip()

        if key == "intent":
            result['intent'] = val
        elif key == "region" and val.lower() != "none":
            result['region'] = val
        elif key == "category" and val.lower() != "none":
            result['category'] = val
        elif key == "sku" and val.lower() != "none":
            result['sku'] = val

    return result


def build_classification_prompt(query: str) -> str:
    """Build prompt for intent classification.

    Args:
        query: User query string

    Returns:
        Formatted prompt string
    """
    return f"""Analyze this query and classify the intent:

Query: "{query}"

Intents:
- inventory_status: Check inventory levels
- sales_analysis: Sales patterns/trends
- financial_report: Financial metrics
- reorder_recommendation: Reorder suggestions
- sales_opportunity: Find sales opportunities
- vendor_selection: Vendor recommendations
- ticket_status: View tickets
- general: General question/greeting

Extract: region (north/south/east/west/central), category, sku (if mentioned, else "none")

Format:
intent: <name>
region: <value_or_none>
category: <value_or_none>
sku: <value_or_none>"""


# Node functions (pure except for LLM/database calls)

def classify_intent(state: AgentState, llm: ChatGoogleGenerativeAI) -> AgentState:
    """Classify user intent and extract parameters.

    Args:
        state: Current workflow state
        llm: Language model instance

    Returns:
        Updated state with classification results
    """
    query = state.get("query", "")
    prompt = build_classification_prompt(query)
    response = llm.invoke([HumanMessage(content=prompt)])

    parsed = parse_classification_response(response.content)

    state["intent"] = parsed['intent']
    state["region"] = parsed['region']
    state["category"] = parsed['category']
    state["sku"] = parsed['sku']

    logger.info(f"Classified intent: {parsed['intent']} (region={parsed['region']}, category={parsed['category']}, sku={parsed['sku']})")
    return state


def gather_data(state: AgentState) -> AgentState:
    """Gather data based on intent using functional report agent.

    Args:
        state: Current workflow state

    Returns:
        Updated state with gathered data
    """
    intent = state["intent"]
    region = state.get("region")
    sku = state.get("sku")

    data_gatherers = {
        "inventory_status": lambda: get_inventory_status(region=region),
        "sales_analysis": lambda: get_sales_patterns(sku=sku, days=365),
        "financial_report": lambda: get_financial_summary(region=region, days=365),
        "ticket_status": lambda: {
            'tickets': get_pending_tickets(),
            'stats': get_ticket_stats()
        }
    }

    data_result = data_gatherers.get(intent, lambda: {})()
    state["data_result"] = data_result
    logger.info(f"Gathered data for intent: {intent}")
    return state


def make_decision(state: AgentState) -> AgentState:
    """Make AI-powered decision using functional decision agent.

    Args:
        state: Current workflow state

    Returns:
        Updated state with decision results
    """
    intent = state["intent"]
    region = state.get("region")
    category = state.get("category")
    sku = state.get("sku")

    decision_makers = {
        "reorder_recommendation": lambda: analyze_inventory_needs(region=region),
        "sales_opportunity": lambda: analyze_sales_opportunity(category=category),
        "vendor_selection": lambda: optimize_vendor_selection(sku=sku)
    }

    decision_result = decision_makers.get(intent, lambda: {})()
    state["decision_result"] = decision_result
    logger.info(f"Made decision for intent: {intent}")
    return state


# Pure formatting functions

def format_inventory(data: Dict, region: Optional[str] = None) -> str:
    """Format inventory response."""
    region_str = f" in {region.capitalize()} region" if region else ""
    lines = [f"INVENTORY STATUS{region_str}\n"]
    lines.append(f"Total items: {data.get('total_items', 0)}")
    lines.append(f"Low stock alerts: {data.get('low_stock_count', 0)}\n")

    if data.get('inventory_summary'):
        lines.append("INVENTORY BY CATEGORY:")
        for cat, qty in sorted(data['inventory_summary'].items()):
            lines.append(f"- {cat}: {qty} units")
        lines.append("")

    if not region and data.get('region_summary'):
        lines.append("INVENTORY BY REGION:")
        for reg, qty in sorted(data['region_summary'].items()):
            lines.append(f"- {reg.capitalize()}: {qty} units")
        lines.append("")

    if data.get('low_stock_items'):
        lines.append("LOW STOCK ITEMS:")
        for item in data['low_stock_items'][:10]:
            lines.append(f"- {item['name']} ({item['sku']}): {item['qty']} units (threshold: {item['reorder_threshold']})")
    else:
        lines.append("All items adequately stocked!")

    return "\n".join(lines)


def format_sales(data: Dict) -> str:
    """Format sales response."""
    if 'error' in data:
        return f"Sales Analysis: {data['error']}"

    period = data.get('period', 'last 365 days')
    return (
        f"SALES ANALYSIS ({period})\n\n"
        f"Total sales: {data.get('total_sales', 0)} units\n"
        f"Total revenue: Rs {data.get('total_revenue', 0):,.2f}\n"
        f"Avg daily sales: {data.get('avg_daily_sales', 0):.1f} units"
    )


def format_financial(data: Dict, region: Optional[str] = None) -> str:
    """Format financial response."""
    if 'error' in data:
        return f"Financial Report: {data['error']}"

    region_str = f" for {region.capitalize()} region" if region else ""
    period = data.get('period', 'last 365 days')
    lines = [f"FINANCIAL SUMMARY ({period}){region_str}\n"]

    lines.append(f"Total sales: Rs {data.get('total_sales', 0):,.2f}")
    lines.append(f"Total purchases: Rs {data.get('total_purchases', 0):,.2f}")
    lines.append(f"Net profit: Rs {data.get('net_profit', 0):,.2f}")

    if data.get('total_sales', 0) > 0:
        margin = (data.get('net_profit', 0) / data.get('total_sales', 1)) * 100
        lines.append(f"Profit margin: {margin:.1f}%")

    return "\n".join(lines)


def format_tickets(data: Dict) -> str:
    """Format ticket response."""
    stats = data.get('stats', {})
    tickets = data.get('tickets', [])

    lines = [
        "TICKET STATUS\n",
        f"Total pending: {stats.get('total_pending', 0)}",
        f"Total value: Rs {stats.get('total_value', 0):,.2f}\n"
    ]

    if tickets:
        lines.append("RECENT TICKETS:")
        for t in tickets[:10]:
            product_name = t.get('product_name') or 'N/A'
            lines.append(
                f"#{t['id']:3d} | {t['sku']:8s} | {product_name[:25]:25s} | "
                f"Qty: {t['recommended_qty']:3d} | {t['priority']:6s}"
            )

    return "\n".join(lines)


def format_response(state: AgentState) -> AgentState:
    """Format final response for user.

    Args:
        state: Current workflow state

    Returns:
        Updated state with formatted response
    """
    intent = state["intent"]
    data = state.get("data_result", {})
    decision = state.get("decision_result", {})

    formatters = {
        "inventory_status": lambda: format_inventory(data, state.get("region")),
        "sales_analysis": lambda: format_sales(data),
        "financial_report": lambda: format_financial(data, state.get("region")),
        "ticket_status": lambda: format_tickets(data),
        "reorder_recommendation": lambda: decision.get('analysis', 'No recommendations available.'),
        "sales_opportunity": lambda: decision.get('analysis', 'No opportunities identified.'),
        "vendor_selection": lambda: decision.get('analysis', 'No vendor recommendations available.'),
    }

    response = formatters.get(intent, lambda: "I'm Inventra, your AI assistant. How can I help?")()
    state["final_response"] = response
    return state


# Pure routing functions

def route_after_classify(state: AgentState) -> str:
    """Determine next node after classification.

    Args:
        state: Current workflow state

    Returns:
        Next node name ('gather' or 'respond')
    """
    intent = state["intent"]
    data_or_decision_intents = {
        "inventory_status", "sales_analysis", "financial_report", "ticket_status",
        "reorder_recommendation", "sales_opportunity", "vendor_selection"
    }

    return "gather" if intent in data_or_decision_intents else "respond"


def route_after_gather(state: AgentState) -> str:
    """Determine next node after data gathering.

    Args:
        state: Current workflow state

    Returns:
        Next node name ('decide' or 'respond')
    """
    intent = state["intent"]
    decision_intents = {"reorder_recommendation", "sales_opportunity", "vendor_selection"}

    return "decide" if intent in decision_intents else "respond"


# Graph building function

def build_workflow(llm: ChatGoogleGenerativeAI) -> StateGraph:
    """Build LangGraph workflow with functional nodes.

    Args:
        llm: Language model instance to use for classification

    Returns:
        Compiled StateGraph workflow
    """
    workflow = StateGraph(AgentState)

    # Partial application to bind LLM to classify function
    classify_with_llm = partial(classify_intent, llm=llm)

    # Add 4 nodes: classify -> gather -> decide -> respond
    workflow.add_node("classify", classify_with_llm)
    workflow.add_node("gather", gather_data)
    workflow.add_node("decide", make_decision)
    workflow.add_node("respond", format_response)

    # Define routing
    workflow.set_entry_point("classify")

    workflow.add_conditional_edges(
        "classify",
        route_after_classify,
        {"gather": "gather", "respond": "respond"}
    )

    workflow.add_conditional_edges(
        "gather",
        route_after_gather,
        {"decide": "decide", "respond": "respond"}
    )

    workflow.add_edge("decide", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()


def create_initial_state(query: str) -> AgentState:
    """Create initial workflow state from query.

    Args:
        query: User query string

    Returns:
        Initial state dictionary
    """
    return {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "intent": "",
        "region": None,
        "category": None,
        "sku": None,
        "data_result": {},
        "decision_result": {},
        "final_response": ""
    }


def save_conversation_to_memory(
    session_id: Optional[str],
    query: str,
    response: str,
    state: AgentState
) -> None:
    """Save conversation to memory storage.

    Args:
        session_id: Optional session identifier
        query: User query
        response: Assistant response
        state: Final workflow state
    """
    try:
        add_conversation(
            session_id=session_id,
            user_message=query,
            assistant_message=response,
            intent=state.get('intent'),
            metadata={
                'region': state.get('region'),
                'category': state.get('category'),
                'sku': state.get('sku')
            }
        )
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")


# Main processing function

def process_query(query: str, session_id: Optional[str] = None) -> str:
    """Process user query through multi-agent workflow.

    Args:
        query: User query string
        session_id: Optional session identifier for memory

    Returns:
        Final response string
    """
    settings = get_settings()

    # Create LLM instance
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.2
    )

    # Build workflow and initial state
    workflow = build_workflow(llm)
    initial_state = create_initial_state(query)

    # Execute workflow
    final_state = workflow.invoke(initial_state)
    response = final_state["final_response"]

    # Save to memory
    save_conversation_to_memory(session_id, query, response, final_state)

    return response
