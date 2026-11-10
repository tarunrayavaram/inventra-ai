"""Report agent - Functional implementation with pure data retrieval functions."""

from typing import Dict, Any, List, Optional
import pandas as pd
from database.db_manager import query, to_dataframe
from tools.finance import get_financial_summary as tool_get_finance
from services.data_pipeline import get_sales_patterns as pipeline_get_sales, get_vendor_performance as pipeline_get_vendors


# Pure data retrieval functions

def get_inventory_status(region: Optional[str] = None) -> Dict[str, Any]:
    """Get current inventory status with low-stock alerts.

    Args:
        region: Optional region filter (north, south, east, west, central)

    Returns:
        Dictionary containing inventory statistics and low-stock items
    """
    sql = "SELECT * FROM inventory"
    params = None

    if region:
        sql += " WHERE region = ?"
        params = (region.capitalize(),)

    df = to_dataframe(sql, params)

    # Identify low-stock items (pure transformation)
    low_stock = df[df['qty'] <= df['reorder_threshold']]

    # Aggregate by category and region
    inventory_summary = df.groupby('category')['qty'].sum().to_dict()
    region_summary = df.groupby('region')['qty'].sum().to_dict()

    return {
        'total_items': len(df),
        'low_stock_count': len(low_stock),
        'low_stock_items': low_stock.to_dict('records'),
        'inventory_summary': inventory_summary,
        'region_summary': region_summary
    }


def get_product_details(sku: str) -> Optional[Dict[str, Any]]:
    """Get detailed product information including vendor data.

    Args:
        sku: Product SKU identifier

    Returns:
        Product details dictionary or None if not found
    """
    sql = """
        SELECT i.*, v.name as vendor_name, v.quality_score, v.reliability_rating, v.lead_time_days
        FROM inventory i
        LEFT JOIN vendors v ON i.vendor_id = v.vendor_id
        WHERE i.sku = ?
    """
    result = query(sql, (sku,))
    return result[0] if result else None


def get_inventory_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all inventory items in a category.

    Args:
        category: Product category name

    Returns:
        List of inventory items
    """
    sql = "SELECT * FROM inventory WHERE category = ? ORDER BY name"
    return query(sql, (category,))


def get_inventory_by_vendor(vendor_id: str) -> List[Dict[str, Any]]:
    """Get all inventory items from a specific vendor.

    Args:
        vendor_id: Vendor identifier

    Returns:
        List of inventory items
    """
    sql = "SELECT * FROM inventory WHERE vendor_id = ? ORDER BY name"
    return query(sql, (vendor_id,))


def get_inventory_by_region(region: str) -> List[Dict[str, Any]]:
    """Get all inventory items in a region.

    Args:
        region: Region name

    Returns:
        List of inventory items
    """
    sql = "SELECT * FROM inventory WHERE region = ? ORDER BY category, name"
    return query(sql, (region.capitalize(),))


# Pure calculation functions

def calculate_reorder_quantity(
    current_qty: int,
    threshold: int,
    multiplier: float = 2.0
) -> int:
    """Calculate recommended reorder quantity.

    Pure function for reorder calculation based on current stock level.

    Args:
        current_qty: Current quantity in stock
        threshold: Reorder threshold level
        multiplier: Safety stock multiplier (default: 2.0)

    Returns:
        Recommended reorder quantity
    """
    target_qty = int(threshold * multiplier)
    reorder_qty = max(0, target_qty - current_qty)
    return reorder_qty


def calculate_stock_coverage_days(
    current_qty: int,
    avg_daily_sales: float
) -> float:
    """Calculate days of stock coverage remaining.

    Args:
        current_qty: Current quantity in stock
        avg_daily_sales: Average daily sales rate

    Returns:
        Number of days until stockout
    """
    if avg_daily_sales <= 0:
        return float('inf')
    return current_qty / avg_daily_sales


def identify_critical_items(
    inventory_items: List[Dict[str, Any]],
    coverage_threshold_days: int = 7
) -> List[Dict[str, Any]]:
    """Identify items at risk of stockout.

    Pure function to filter critical inventory items.

    Args:
        inventory_items: List of inventory items with qty and avg_daily_sales
        coverage_threshold_days: Minimum acceptable coverage days

    Returns:
        List of critical items needing immediate attention
    """
    critical = []
    for item in inventory_items:
        avg_sales = item.get('avg_daily_sales', 0)
        if avg_sales > 0:
            coverage = calculate_stock_coverage_days(item['qty'], avg_sales)
            if coverage < coverage_threshold_days:
                item_copy = item.copy()
                item_copy['coverage_days'] = coverage
                critical.append(item_copy)
    return critical


# Delegation functions (calls to other modules)

def get_sales_patterns(sku: Optional[str] = None, days: int = 365) -> Dict[str, Any]:
    """Get sales patterns analysis.

    Delegates to data_pipeline module.

    Args:
        sku: Optional SKU filter
        days: Number of days to analyze

    Returns:
        Sales pattern analysis dictionary
    """
    return pipeline_get_sales(sku, days)


def get_financial_summary(region: Optional[str] = None, days: int = 365) -> Dict[str, Any]:
    """Get financial summary.

    Delegates to finance tool.

    Args:
        region: Optional region filter
        days: Number of days to analyze

    Returns:
        Financial summary dictionary
    """
    return tool_get_finance(region, days)


def get_vendor_performance() -> List[Dict[str, Any]]:
    """Get vendor performance metrics.

    Delegates to data_pipeline module.

    Returns:
        List of vendors with performance metrics
    """
    return pipeline_get_vendors()


# Aggregate report functions

def get_comprehensive_inventory_report(region: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive inventory report with all metrics.

    Args:
        region: Optional region filter

    Returns:
        Complete inventory analysis
    """
    status = get_inventory_status(region)
    sales = get_sales_patterns(days=30)

    return {
        **status,
        'sales_velocity': sales.get('avg_daily_sales', 0),
        'revenue_last_30d': sales.get('total_revenue', 0),
        'critical_items': identify_critical_items(status['low_stock_items'])
    }


def get_product_full_analysis(sku: str) -> Dict[str, Any]:
    """Get complete analysis for a specific product.

    Args:
        sku: Product SKU

    Returns:
        Complete product analysis including sales and vendor data
    """
    product = get_product_details(sku)
    if not product:
        return {'error': f'Product {sku} not found'}

    sales = get_sales_patterns(sku=sku, days=90)

    return {
        'product': product,
        'sales_analysis': sales,
        'reorder_recommendation': calculate_reorder_quantity(
            current_qty=product['qty'],
            threshold=product['reorder_threshold']
        )
    }

