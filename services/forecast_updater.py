"""Forecast updater - Updates forecasts with actual data for accuracy tracking."""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from database.db_manager import query
from database.memory_manager import get_forecast_tracker
from config.logger import get_logger

logger = get_logger(__name__)


class ForecastUpdater:
    """Updates forecasts with actual sales and weather data."""

    def __init__(self):
        self.tracker = get_forecast_tracker()

    def update_past_forecasts(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Update forecasts with actual data for past predictions.

        Args:
            days_back: How many days back to look for forecasts

        Returns:
            Dict with update statistics
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # Get forecasts that need updating
        pending_forecasts = query("""
            SELECT * FROM forecasts
            WHERE forecast_date >= ?
            AND forecast_date <= date('now')
            AND accuracy_score IS NULL
            ORDER BY forecast_date ASC
        """, (cutoff_date,))

        updated_count = 0
        errors = []

        for forecast in pending_forecasts:
            try:
                # Get actual sales data for the forecast date
                actual_sales = self._get_actual_sales(
                    sku=forecast['sku'],
                    forecast_date=forecast['forecast_date']
                )

                # Get actual weather data for the forecast date
                actual_weather = self._get_actual_weather(
                    forecast_date=forecast['forecast_date']
                )

                if actual_sales is not None:
                    # Update forecast with actual data
                    self.tracker.update_actual_data(
                        forecast_id=forecast['id'],
                        actual_demand=actual_sales,
                        actual_weather=actual_weather or 'Unknown'
                    )
                    updated_count += 1
                    logger.info(f"Updated forecast #{forecast['id']} for SKU {forecast['sku']}")

            except Exception as e:
                error_msg = f"Failed to update forecast #{forecast['id']}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return {
            'total_pending': len(pending_forecasts),
            'updated': updated_count,
            'errors': len(errors),
            'error_messages': errors
        }

    def _get_actual_sales(self, sku: str, forecast_date: str) -> int:
        """
        Get actual sales quantity for a SKU on a specific date.

        Args:
            sku: Product SKU
            forecast_date: Date to check (YYYY-MM-DD)

        Returns:
            Total quantity sold or None if no data
        """
        # Query sales data for the forecast date (±3 days window)
        date_obj = datetime.strptime(forecast_date, '%Y-%m-%d')
        start_date = (date_obj - timedelta(days=3)).strftime('%Y-%m-%d')
        end_date = (date_obj + timedelta(days=3)).strftime('%Y-%m-%d')

        result = query("""
            SELECT SUM(qty) as total_qty
            FROM sales
            WHERE sku = ?
            AND date BETWEEN ? AND ?
        """, (sku, start_date, end_date))

        if result and result[0]['total_qty'] is not None:
            return int(result[0]['total_qty'])

        return None

    def _get_actual_weather(self, forecast_date: str) -> str:
        """
        Get actual weather condition for a specific date.

        Args:
            forecast_date: Date to check (YYYY-MM-DD)

        Returns:
            Weather condition or None
        """
        # Query sales data to get weather (since sales include weather)
        date_obj = datetime.strptime(forecast_date, '%Y-%m-%d')
        start_date = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')

        result = query("""
            SELECT weather_condition, COUNT(*) as cnt
            FROM sales
            WHERE date BETWEEN ? AND ?
            GROUP BY weather_condition
            ORDER BY cnt DESC
            LIMIT 1
        """, (start_date, end_date))

        if result and result[0]['weather_condition']:
            return result[0]['weather_condition']

        return 'Unknown'

    def get_forecast_accuracy_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive forecast accuracy report.

        Returns:
            Dict with accuracy metrics and insights
        """
        stats = self.tracker.get_accuracy_stats()

        # Get recent forecasts with accuracy
        recent = self.tracker.get_recent_forecasts(limit=10, include_pending=False)

        # Get forecasts that still need updating
        pending = self.tracker.get_recent_forecasts(limit=20, include_pending=True)
        pending_count = sum(1 for f in pending if f['accuracy_score'] is None)

        # Calculate accuracy trends
        accuracy_by_date = query("""
            SELECT
                DATE(forecast_date) as date,
                AVG(accuracy_score) as avg_accuracy,
                COUNT(*) as forecast_count
            FROM forecasts
            WHERE accuracy_score IS NOT NULL
            GROUP BY DATE(forecast_date)
            ORDER BY date DESC
            LIMIT 30
        """)

        return {
            'overall_stats': stats,
            'recent_forecasts': recent,
            'pending_updates': pending_count,
            'accuracy_trend': accuracy_by_date,
            'total_forecasts': stats.get('total_forecasts', 0),
            'avg_accuracy': stats.get('avg_accuracy', 0)
        }


def get_forecast_updater() -> ForecastUpdater:
    """Get ForecastUpdater instance."""
    return ForecastUpdater()


if __name__ == "__main__":
    """Run forecast updater as standalone script."""
    print("=" * 70)
    print("  FORECAST UPDATER - Updating Past Forecasts with Actual Data")
    print("=" * 70)

    updater = get_forecast_updater()

    print("\nUpdating forecasts from the past 30 days...")
    result = updater.update_past_forecasts(days_back=30)

    print(f"\nResults:")
    print(f"  Total pending forecasts: {result['total_pending']}")
    print(f"  Successfully updated: {result['updated']}")
    print(f"  Errors: {result['errors']}")

    if result['errors'] > 0:
        print(f"\nError messages:")
        for error in result['error_messages']:
            print(f"  - {error}")

    print("\n" + "=" * 70)
    print("  FORECAST ACCURACY REPORT")
    print("=" * 70)

    report = updater.get_forecast_accuracy_report()

    overall = report['overall_stats'].get('overall', {})
    print(f"\nOverall Statistics:")
    print(f"  Total forecasts evaluated: {overall.get('total_forecasts', 0)}")
    print(f"  Average accuracy: {overall.get('avg_accuracy', 0):.1f}%")
    print(f"  Min accuracy: {overall.get('min_accuracy', 0):.1f}%")
    print(f"  Max accuracy: {overall.get('max_accuracy', 0):.1f}%")
    print(f"  Pending updates: {report['pending_updates']}")

    if report['overall_stats'].get('by_sku'):
        print(f"\nTop SKUs by Forecast Count:")
        for item in report['overall_stats']['by_sku'][:5]:
            print(f"  - {item['sku']}: {item['forecast_count']} forecasts, "
                  f"{item['avg_accuracy']:.1f}% accuracy")

    print("\n" + "=" * 70)
