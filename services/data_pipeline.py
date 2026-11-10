"""Data ingestion and analysis pipeline - Functional implementation."""

from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta

from database.db_manager import query, to_dataframe

# Pure date calculation functions

def calculate_cutoff_date(days: int) -> str:
    """Calculate cutoff date for time-based queries.

    Pure function to compute date threshold.

    Args:
        days: Number of days to look back

    Returns:
        Date string in YYYY-MM-DD format
    """
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')


# Data retrieval functions

def fetch_sales_data(
    cutoff_date: Optional[str] = None,
    sku: Optional[str] = None
) -> pd.DataFrame:
    """Fetch sales data from database.

    Args:
        cutoff_date: Optional minimum date filter
        sku: Optional SKU filter

    Returns:
        DataFrame with sales data
    """
    sql = """
        SELECT s.*, i.name, i.category
        FROM sales s
        LEFT JOIN inventory i ON s.sku = i.sku
    """
    params = []

    conditions = []
    if cutoff_date:
        conditions.append("s.date >= ?")
        params.append(cutoff_date)
    if sku:
        conditions.append("s.sku = ?")
        params.append(sku)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    return to_dataframe(sql, tuple(params) if params else None)


def fetch_vendor_data() -> List[Dict[str, Any]]:
    """Fetch vendor performance data sorted by quality.

    Returns:
        List of vendor dictionaries
    """
    sql = """
        SELECT * FROM vendors
        ORDER BY quality_score DESC, reliability_rating DESC, lead_time_days ASC
    """
    vendors = query(sql)

    return [{
        'vendor_id': v.get('vendor_id'),
        'name': v.get('name'),
        'quality_score': v.get('quality_score'),
        'reliability': v.get('reliability_rating'),
        'lead_time_days': v.get('lead_time_days')
    } for v in vendors]


# Pure transformation functions

def aggregate_sales_metrics(df: pd.DataFrame, days: int) -> Dict[str, Any]:
    """Calculate sales metrics from DataFrame.

    Pure function to transform data into metrics.

    Args:
        df: Sales DataFrame
        days: Number of days in analysis period

    Returns:
        Dictionary of aggregated metrics
    """
    if df.empty:
        return {'error': 'No sales data found'}

    total_sales = int(df['qty'].sum())
    total_revenue = float(df['revenue'].sum())
    avg_daily_sales = float(total_sales / max(days, 1))

    # Top selling days
    top_days = df.nlargest(5, 'qty')[['date', 'sku', 'qty']].to_dict('records')

    # Weather impact
    weather_impact = df.groupby('weather_condition')['qty'].sum().to_dict()

    # Region performance
    region_performance = df.groupby('region')['revenue'].sum().to_dict()

    return {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'avg_daily_sales': avg_daily_sales,
        'top_selling_days': top_days,
        'weather_impact': weather_impact,
        'region_performance': region_performance,
        'period': f'last {days} days'
    }


def analyze_weather_impact_data(
    df: pd.DataFrame,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze weather's impact on sales.

    Pure function to transform sales data into weather insights.

    Args:
        df: Sales DataFrame with weather data
        category: Category being analyzed

    Returns:
        Weather impact analysis
    """
    if df.empty:
        return {'error': 'No data found'}

    # Group by weather condition
    weather_sales = df.groupby('weather_condition').agg({
        'qty': 'sum',
        'temperature': 'mean',
        'rainfall': 'mean'
    }).reset_index()

    # Best selling condition
    best_idx = weather_sales['qty'].idxmax()
    best_condition = weather_sales.loc[best_idx]

    # Weather analysis by condition
    weather_analysis = weather_sales.to_dict('records')

    return {
        'category': category or 'All',
        'best_selling_condition': {
            'condition': best_condition['weather_condition'],
            'total_qty': int(best_condition['qty'])
        },
        'avg_temp_range': {
            'min': float(df['temperature'].min()),
            'max': float(df['temperature'].max()),
            'avg': float(df['temperature'].mean())
        },
        'weather_analysis': weather_analysis
    }


# Main analysis functions

def get_sales_patterns(sku: Optional[str] = None, days: int = 365) -> Dict[str, Any]:
    """Analyze sales patterns over time.

    Args:
        sku: Optional SKU filter
        days: Number of days to analyze (default: 365)

    Returns:
        Sales pattern analysis dictionary
    """
    cutoff_date = calculate_cutoff_date(days)

    # Try to fetch recent data
    df = fetch_sales_data(cutoff_date, sku)

    # Fallback to all-time data if no recent data found
    if df.empty:
        df = fetch_sales_data(cutoff_date=None, sku=sku)

    return aggregate_sales_metrics(df, days)


def get_vendor_performance() -> List[Dict[str, Any]]:
    """Get vendor performance metrics.

    Returns:
        List of vendors sorted by performance
    """
    return fetch_vendor_data()


def analyze_weather_impact(category: Optional[str] = None) -> Dict[str, Any]:
    """Analyze how weather affects sales.

    Args:
        category: Optional category filter

    Returns:
        Weather impact analysis
    """
    sql = """
        SELECT s.*, i.category
        FROM sales s
        LEFT JOIN inventory i ON s.sku = i.sku
    """

    if category:
        sql += " WHERE i.category = ?"
        df = to_dataframe(sql, (category,))
    else:
        df = to_dataframe(sql)

    return analyze_weather_impact_data(df, category)


def get_context_for_decision(region: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive data context for decision making.
    
    Args:
        region: Optional region filter
    
    Returns:
        Comprehensive context dictionary
    """
    from agents.report_agent import get_inventory_status
    from tools.finance import get_financial_summary
    
    return {
        'inventory': get_inventory_status(region),
        'sales_patterns': get_sales_patterns(days=30),
        'financial_summary': get_financial_summary(region, days=30),
        'top_vendors': get_vendor_performance()[:5],
        'timestamp': datetime.now().isoformat()
    }


# Advanced analytics functions

def calculate_sales_velocity(sku: str, days: int = 30) -> float:
    """Calculate sales velocity for a product.

    Args:
        sku: Product SKU
        days: Analysis period

    Returns:
        Average daily sales rate
    """
    patterns = get_sales_patterns(sku=sku, days=days)
    return patterns.get('avg_daily_sales', 0.0)


def identify_trending_products(
    days: int = 30,
    min_sales: int = 10
) -> List[Dict[str, Any]]:
    """Identify products with increasing sales trends.

    Args:
        days: Analysis period
        min_sales: Minimum total sales to consider

    Returns:
        List of trending products
    """
    cutoff_date = calculate_cutoff_date(days)
    df = fetch_sales_data(cutoff_date)

    if df.empty:
        return []

    # Group by SKU and calculate trends
    product_sales = df.groupby('sku').agg({
        'qty': 'sum',
        'revenue': 'sum',
        'name': 'first',
        'category': 'first'
    }).reset_index()

    # Filter by minimum sales
    trending = product_sales[product_sales['qty'] >= min_sales]

    # Sort by quantity descending
    trending = trending.sort_values('qty', ascending=False)

    return trending.head(20).to_dict('records')


def analyze_regional_performance(days: int = 90) -> Dict[str, Any]:
    """Analyze sales performance by region.

    Args:
        days: Analysis period

    Returns:
        Regional performance breakdown
    """
    cutoff_date = calculate_cutoff_date(days)
    df = fetch_sales_data(cutoff_date)

    if df.empty:
        return {'error': 'No sales data found'}

    regional_metrics = df.groupby('region').agg({
        'qty': 'sum',
        'revenue': 'sum',
        'sku': 'count'
    }).reset_index()

    regional_metrics.columns = ['region', 'total_qty', 'total_revenue', 'transaction_count']

    # Calculate averages
    regional_metrics['avg_transaction_size'] = (
        regional_metrics['total_revenue'] / regional_metrics['transaction_count']
    )

    return {
        'period': f'last {days} days',
        'regions': regional_metrics.to_dict('records'),
        'best_region': regional_metrics.loc[regional_metrics['total_revenue'].idxmax()]['region'],
        'total_revenue': float(regional_metrics['total_revenue'].sum())
    }
