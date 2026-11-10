"""Financial calculations helper."""

from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta

from database.db_manager import to_dataframe


def get_financial_summary(region: str = None, days: int = 365) -> Dict[str, Any]:
    """Get financial summary. Defaults to 365 days to handle historical data."""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    query = "SELECT * FROM finance WHERE date >= ?"
    params = [cutoff_date]

    if region:
        query += " AND region = ?"
        params.append(region.capitalize())

    df = to_dataframe(query, tuple(params))

    # Fallback to all-time data if no recent data found
    if df.empty:
        query = "SELECT * FROM finance"
        params = []
        if region:
            query += " WHERE region = ?"
            params.append(region.capitalize())
        df = to_dataframe(query, tuple(params) if params else ())

    if df.empty:
        return {'error': 'No finance data found'}

    total_sales = df[df['type'] == 'sale']['amount'].sum()
    total_purchases = df[df['type'] == 'purchase']['amount'].sum()
    net_profit = total_sales - total_purchases

    return {
        'total_sales': float(total_sales),
        'total_purchases': float(total_purchases),
        'net_profit': float(net_profit),
        'transaction_count': len(df),
        'avg_transaction_value': float(df['amount'].mean()) if len(df) > 0 else 0,
        'period': f'last {days} days'
    }


def calculate_profit_margin(sales: float, purchases: float) -> float:
    """Calculate profit margin percentage."""
    if sales == 0:
        return 0.0
    return ((sales - purchases) / sales) * 100


def get_transactions_by_sku(sku: str, days: int = 30) -> List[Dict[str, Any]]:
    """Get transactions for a specific SKU."""
    db = get_db()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    query = """
        SELECT * FROM finance
        WHERE sku = ? AND date >= ?
        ORDER BY date DESC
    """
    return db.query(query, (sku, cutoff_date))


def get_revenue_by_region(days: int = 30) -> Dict[str, float]:
    """Get revenue breakdown by region."""
    db = get_db()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    query = """
        SELECT region, SUM(amount) as total_revenue
        FROM finance
        WHERE type = 'sale' AND date >= ?
        GROUP BY region
        ORDER BY total_revenue DESC
    """
    results = db.query(query, (cutoff_date,))
    return {r['region']: float(r['total_revenue']) for r in results}


def get_top_revenue_products(limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get top revenue-generating products.

    Args:
        limit: Number of products to return
        days: Number of days to analyze

    Returns:
        List of products with revenue
    """
    db = get_db()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    query = """
        SELECT
            f.sku,
            i.name,
            i.category,
            SUM(f.amount) as total_revenue,
            COUNT(*) as transaction_count
        FROM finance f
        LEFT JOIN inventory i ON f.sku = i.sku
        WHERE f.type = 'sale' AND f.date >= ?
        GROUP BY f.sku, i.name, i.category
        ORDER BY total_revenue DESC
        LIMIT ?
    """
    return db.query(query, (cutoff_date, limit))
