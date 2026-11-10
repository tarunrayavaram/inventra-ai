"""Streamlit UI for Inventra - AI-powered Inventory & Financial Management."""

import sys
import traceback
from pathlib import Path

# Add parent directory to path so we can import agents and utils
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from agents.coordinator import process_query as coordinator_process_query
from agents.report_agent import get_inventory_status, get_sales_patterns
from services.ticket_manager import get_pending_tickets, get_ticket_stats
from config.settings import get_settings
from config.logger import get_logger
from services.forecast_updater import get_forecast_updater

logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Inventra - AI Inventory Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# No need for agent loading - use functional API directly


def load_forecast_updater():
    """Load forecast updater."""
    if 'forecast_updater' not in st.session_state:
        st.session_state.forecast_updater = get_forecast_updater()
    return st.session_state.forecast_updater


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm Inventra, your AI assistant for inventory and financial management. How can I help you today?"}
        ]
    if "conversation_count" not in st.session_state:
        st.session_state.conversation_count = 0


def render_sidebar():
    """Render sidebar with system info and quick actions."""
    with st.sidebar:
        st.markdown("### 📦 Inventra")
        st.markdown("AI-Powered Inventory Management")
        st.markdown("---")

        # Quick stats
        st.markdown("### Quick Stats")

        # Inventory summary
        inv = get_inventory_status()
        st.metric("Total Items", inv['total_items'])
        st.metric("Low Stock Alerts", inv['low_stock_count'],
                 delta=f"-{inv['low_stock_count']}" if inv['low_stock_count'] > 0 else "0",
                 delta_color="inverse")

        # Ticket stats
        ticket_stats = get_ticket_stats()
        st.metric("Pending Tickets", ticket_stats['total_pending'])
        st.metric("Ticket Value", f"Rs {ticket_stats['total_value']:,.0f}")

        st.markdown("---")

        # Quick actions
        st.markdown("### Quick Actions")

        if st.button("🔄 Check All Regions"):
            st.session_state.pending_query = "Give me inventory status for all regions"
            st.rerun()

        if st.button("💰 Financial Summary"):
            st.session_state.pending_query = "Show me the financial summary"
            st.rerun()

        if st.button("📝 View Tickets"):
            st.session_state.pending_query = "What are my pending tickets?"
            st.rerun()

        if st.button("🎯 Get Recommendations"):
            st.session_state.pending_query = "Give me reorder recommendations"
            st.rerun()

        st.markdown("---")
        st.markdown(f"**Model:** {get_settings().gemini_model}")
        st.markdown(f"**Session:** {st.session_state.conversation_count} messages")


def render_chat_interface():
    """Render main chat interface."""
    st.markdown("<div class='main-header'>Inventra AI Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Ask me anything about inventory, sales, finances, or get recommendations</div>", unsafe_allow_html=True)

    # Check if there's a pending query from Quick Actions
    pending_query = None
    if 'pending_query' in st.session_state:
        pending_query = st.session_state.pending_query
        del st.session_state.pending_query

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    prompt = st.chat_input("Ask about inventory, sales, finances, or get recommendations...")
    
    # Handle the query (either from pending or from chat input)
    query_to_process = pending_query or prompt
    if query_to_process:
        handle_user_query(query_to_process)


def handle_user_query(prompt: str):
    """Process a user query through the coordinator."""
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.conversation_count += 1

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response and display it
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                # Call the coordinator's process_query function (note: renamed import)
                response = coordinator_process_query(prompt)

                # Display response
                st.markdown(response)

                # Add to messages
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.error(f"Traceback:\n```\n{traceback.format_exc()}\n```")
                logger.error(f"Error processing query: {e}")
                logger.error(traceback.format_exc())
                st.session_state.messages.append({"role": "assistant", "content": error_msg})


def render_data_explorer():
    """Render data explorer tab."""
    st.markdown("### 📊 Data Explorer")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Inventory by Region")
        inv = get_inventory_status()
        if inv.get('region_summary'):
            df = pd.DataFrame([
                {"Region": k, "Quantity": v}
                for k, v in inv['region_summary'].items()
            ])
            st.dataframe(df, width='stretch')
            st.bar_chart(df.set_index("Region"))

    with col2:
        st.markdown("#### Inventory by Category")
        if inv.get('inventory_summary'):
            df = pd.DataFrame([
                {"Category": k, "Quantity": v}
                for k, v in inv['inventory_summary'].items()
            ])
            st.dataframe(df, width='stretch')
            st.bar_chart(df.set_index("Category"))

    # Low stock items
    if inv.get('low_stock_items'):
        st.markdown("#### ⚠️ Low Stock Items")
        low_stock_df = pd.DataFrame(inv['low_stock_items'])
        st.dataframe(
            low_stock_df[['sku', 'name', 'category', 'region', 'qty', 'reorder_threshold']],
            width='stretch'
        )

    # Sales patterns
    st.markdown("#### 📈 Sales Trends (Last 30 days)")
    sales = get_sales_patterns(days=30)
    if 'error' not in sales:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", f"{sales['total_sales']} units")
        col2.metric("Revenue", f"Rs {sales['total_revenue']:,.0f}")
        col3.metric("Avg Daily Sales", f"{sales['avg_daily_sales']:.1f} units")

        if sales.get('region_performance'):
            st.markdown("**Sales by Region:**")
            reg_df = pd.DataFrame([
                {"Region": k, "Revenue": v}
                for k, v in sales['region_performance'].items()
            ])
            st.bar_chart(reg_df.set_index("Region"))


def render_ticket_manager():
    """Render ticket manager tab."""
    st.markdown("### 📝 Ticket Manager")

    # Ticket stats
    stats = get_ticket_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pending", stats['total_pending'])
    col2.metric("Total Value", f"Rs {stats['total_value']:,.0f}")

    if stats.get('by_priority'):
        high = stats['by_priority'].get('high', 0)
        med = stats['by_priority'].get('medium', 0)
        low = stats['by_priority'].get('low', 0)
        col3.metric("High Priority", high)

    # Pending tickets table
    st.markdown("#### Pending Tickets")
    tickets = get_pending_tickets()

    if tickets:
        tickets_df = pd.DataFrame(tickets)
        display_cols = ['id', 'sku', 'product_name', 'recommended_qty', 'vendor_name', 'priority', 'created_at']
        available_cols = [col for col in display_cols if col in tickets_df.columns]

        st.dataframe(
            tickets_df[available_cols],
            width='stretch',
            hide_index=True
        )

        # Ticket actions
        st.markdown("#### Update Ticket Status")
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            ticket_id = st.selectbox("Select Ticket", [t['id'] for t in tickets])

        with col2:
            new_status = st.selectbox("New Status", ["pending", "approved", "rejected", "completed"])

        with col3:
            if st.button("Update"):
                from services.ticket_manager import update_ticket_status
                result = update_ticket_status(ticket_id, new_status)
                if result['success']:
                    st.success(result['message'])
                    st.rerun()
                else:
                    st.error(result.get('error', 'Failed to update'))
    else:
        st.info("No pending tickets")


def render_forecast_accuracy():
    """Render forecast accuracy tab."""
    st.markdown("### 🎯 Forecast Accuracy Tracking")

    updater = load_forecast_updater()

    # Action buttons
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("🔄 Update Forecasts"):
            with st.spinner("Updating forecasts with actual data..."):
                result = updater.update_past_forecasts(days_back=30)
                st.success(f"Updated {result['updated']} forecasts!")
                if result['errors'] > 0:
                    st.warning(f"{result['errors']} errors occurred")
                st.rerun()

    # Get forecast accuracy report
    report = updater.get_forecast_accuracy_report()
    overall = report['overall_stats'].get('overall', {})

    # Overall metrics
    st.markdown("#### 📊 Overall Accuracy Metrics")
    col1, col2, col3, col4 = st.columns(4)

    total_forecasts = overall.get('total_forecasts', 0) or 0
    avg_accuracy = overall.get('avg_accuracy') or 0
    max_accuracy = overall.get('max_accuracy') or 0
    pending_updates = report.get('pending_updates', 0) or 0

    col1.metric("Total Forecasts", total_forecasts)
    col2.metric("Avg Accuracy", f"{avg_accuracy:.1f}%")
    col3.metric("Best Accuracy", f"{max_accuracy:.1f}%")
    col4.metric("Pending Updates", pending_updates)

    # Accuracy trend chart
    if report['accuracy_trend']:
        st.markdown("#### 📈 Accuracy Trend Over Time")
        trend_df = pd.DataFrame(report['accuracy_trend'])
        if not trend_df.empty:
            st.line_chart(trend_df.set_index('date')['avg_accuracy'])

    # Accuracy by SKU
    if report['overall_stats'].get('by_sku'):
        st.markdown("#### 🏆 Top Products by Forecast Accuracy")

        sku_df = pd.DataFrame(report['overall_stats']['by_sku'])
        if not sku_df.empty:
            # Format the dataframe
            sku_df['avg_accuracy'] = sku_df['avg_accuracy'].apply(lambda x: f"{x:.1f}%")
            sku_df.columns = ['SKU', 'Forecast Count', 'Avg Accuracy']

            st.dataframe(sku_df, width='stretch', hide_index=True)

            # Bar chart
            sku_chart_df = pd.DataFrame(report['overall_stats']['by_sku'])
            sku_chart_df['avg_accuracy'] = sku_chart_df['avg_accuracy'].astype(float)
            st.bar_chart(sku_chart_df.set_index('sku')['avg_accuracy'])

    # Recent forecasts
    if report['recent_forecasts']:
        st.markdown("#### 📋 Recent Forecast Results")

        recent_df = pd.DataFrame(report['recent_forecasts'])
        if not recent_df.empty:
            display_cols = ['sku', 'forecast_date', 'predicted_demand', 'actual_demand',
                          'predicted_weather', 'actual_weather', 'accuracy_score']
            available_cols = [col for col in display_cols if col in recent_df.columns]

            # Format accuracy score
            if 'accuracy_score' in recent_df.columns:
                recent_df['accuracy_score'] = recent_df['accuracy_score'].apply(
                    lambda x: f"{x:.1f}%" if pd.notna(x) else "Pending"
                )

            st.dataframe(
                recent_df[available_cols],
                width='stretch',
                hide_index=True
            )
    else:
        st.info("No forecast data available yet. Make some recommendations to start tracking accuracy!")

    # Insights
    if total_forecasts > 0 and avg_accuracy is not None:
        st.markdown("#### 💡 Insights")

        if avg_accuracy >= 80:
            st.success(f"🎉 Excellent forecast accuracy at {avg_accuracy:.1f}%! The system is performing well.")
        elif avg_accuracy >= 60:
            st.info(f"📊 Good forecast accuracy at {avg_accuracy:.1f}%. Room for improvement by refining weather-demand correlations.")
        else:
            st.warning(f"⚠️ Forecast accuracy is {avg_accuracy:.1f}%. Consider reviewing the prediction models and weather impact factors.")


def main():
    """Main application."""
    init_session_state()

    render_sidebar()

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat Assistant", "📊 Data Explorer", "📝 Tickets", "🎯 Forecast Accuracy"])

    with tab1:
        render_chat_interface()

    with tab2:
        render_data_explorer()

    with tab3:
        render_ticket_manager()

    with tab4:
        render_forecast_accuracy()


if __name__ == "__main__":
    main()
