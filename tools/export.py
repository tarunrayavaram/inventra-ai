"""Export utilities for data download and reporting."""

import json
import csv
from io import StringIO, BytesIO
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from database.db_manager import query
from config.logger import get_logger

logger = get_logger(__name__)


class ExportManager:
    """Manages data export to various formats."""

    def __init__(self):
        pass

    def export_to_json(self, data: Any, pretty: bool = True) -> str:
        """
        Export data to JSON string.

        Args:
            data: Data to export (dict, list, or DataFrame)
            pretty: Pretty print JSON

        Returns:
            JSON string
        """
        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient='records')

        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, default=str)

    def export_to_csv(self, data: Any) -> str:
        """
        Export data to CSV string.

        Args:
            data: Data to export (list of dicts or DataFrame)

        Returns:
            CSV string
        """
        if isinstance(data, pd.DataFrame):
            return data.to_csv(index=False)

        if not data:
            return ""

        # Convert list of dicts to CSV
        output = StringIO()
        if isinstance(data, list) and len(data) > 0:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        return output.getvalue()

    def export_inventory_report(self, format: str = 'json') -> str:
        """
        Export comprehensive inventory report.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        query = """
            SELECT
                i.*,
                v.name as vendor_name,
                v.quality_score,
                v.reliability_rating,
                v.lead_time_days,
                CASE
                    WHEN i.qty <= i.reorder_threshold THEN 'Low Stock'
                    ELSE 'In Stock'
                END as stock_status
            FROM inventory i
            LEFT JOIN vendors v ON i.vendor_id = v.vendor_id
            ORDER BY i.region, i.category, i.name
        """

        data = query(query)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_sales_report(
        self,
        start_date: str = None,
        end_date: str = None,
        format: str = 'json'
    ) -> str:
        """
        Export sales report with optional date filtering.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        query = """
            SELECT
                s.*,
                i.name as product_name,
                i.category
            FROM sales s
            LEFT JOIN inventory i ON s.sku = i.sku
        """

        params = []
        if start_date or end_date:
            query += " WHERE"
            if start_date:
                query += " s.date >= ?"
                params.append(start_date)
            if end_date:
                if start_date:
                    query += " AND"
                query += " s.date <= ?"
                params.append(end_date)

        query += " ORDER BY s.date DESC"

        data = query(query, tuple(params) if params else None)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_financial_report(
        self,
        start_date: str = None,
        end_date: str = None,
        format: str = 'json'
    ) -> str:
        """
        Export financial report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        query = "SELECT * FROM finance"

        params = []
        if start_date or end_date:
            query += " WHERE"
            if start_date:
                query += " date >= ?"
                params.append(start_date)
            if end_date:
                if start_date:
                    query += " AND"
                query += " date <= ?"
                params.append(end_date)

        query += " ORDER BY date DESC"

        data = query(query, tuple(params) if params else None)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_tickets_report(self, status: str = None, format: str = 'json') -> str:
        """
        Export tickets report.

        Args:
            status: Filter by status (optional)
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        query = """
            SELECT
                t.*,
                i.name as product_name,
                i.category,
                v.name as vendor_name
            FROM tickets t
            LEFT JOIN inventory i ON t.sku = i.sku
            LEFT JOIN vendors v ON t.vendor_id = v.vendor_id
        """

        if status:
            query += " WHERE t.status = ?"
            params = (status,)
        else:
            params = None

        query += " ORDER BY t.created_at DESC"

        data = query(query, params)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_vendor_performance(self, format: str = 'json') -> str:
        """
        Export vendor performance report.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        data = self.db.query("""
            SELECT * FROM vendors
            ORDER BY quality_score DESC, reliability_rating DESC
        """)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_weather_impact_analysis(self, format: str = 'json') -> str:
        """
        Export weather impact analysis report.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        data = self.db.query("""
            SELECT
                s.weather_condition,
                i.category,
                COUNT(*) as sale_count,
                SUM(s.qty) as total_qty_sold,
                AVG(s.revenue) as avg_revenue,
                AVG(s.temperature) as avg_temperature,
                AVG(s.rainfall) as avg_rainfall
            FROM sales s
            JOIN inventory i ON s.sku = i.sku
            GROUP BY s.weather_condition, i.category
            ORDER BY total_qty_sold DESC
        """)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_conversation_history(
        self,
        session_id: str = None,
        format: str = 'json'
    ) -> str:
        """
        Export conversation history.

        Args:
            session_id: Optional session ID filter
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        query = "SELECT * FROM conversations"

        if session_id:
            query += " WHERE session_id = ?"
            params = (session_id,)
        else:
            params = None

        query += " ORDER BY created_at DESC"

        data = query(query, params)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def export_forecast_accuracy(self, format: str = 'json') -> str:
        """
        Export forecast accuracy report.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Exported data string
        """
        data = self.db.query("""
            SELECT * FROM forecasts
            WHERE accuracy_score IS NOT NULL
            ORDER BY forecast_date DESC
        """)

        if format == 'csv':
            return self.export_to_csv(data)
        else:
            return self.export_to_json(data)

    def create_summary_report(self) -> Dict[str, Any]:
        """
        Create comprehensive summary report.

        Returns:
            Dict with all summary data
        """
        # Inventory summary
        inventory_summary = self.db.query("""
            SELECT
                COUNT(*) as total_items,
                SUM(CASE WHEN qty <= reorder_threshold THEN 1 ELSE 0 END) as low_stock_count,
                COUNT(DISTINCT region) as regions,
                COUNT(DISTINCT category) as categories
            FROM inventory
        """)[0]

        # Sales summary
        sales_summary = self.db.query("""
            SELECT
                COUNT(*) as total_sales,
                SUM(qty) as total_units_sold,
                SUM(revenue) as total_revenue,
                AVG(revenue) as avg_revenue
            FROM sales
        """)[0]

        # Financial summary
        financial_summary = self.db.query("""
            SELECT
                SUM(CASE WHEN type = 'sale' THEN amount ELSE 0 END) as total_sales,
                SUM(CASE WHEN type = 'purchase' THEN amount ELSE 0 END) as total_purchases,
                SUM(CASE WHEN type = 'sale' THEN amount ELSE -amount END) as net_profit
            FROM finance
        """)[0]

        # Ticket summary
        ticket_summary = self.db.query("""
            SELECT
                COUNT(*) as total_tickets,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tickets,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_tickets
            FROM tickets
        """)[0]

        return {
            'generated_at': datetime.now().isoformat(),
            'inventory': inventory_summary,
            'sales': sales_summary,
            'financial': financial_summary,
            'tickets': ticket_summary
        }


def get_export_manager() -> ExportManager:
    """Get ExportManager instance."""
    return ExportManager()
