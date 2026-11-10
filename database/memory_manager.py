"""Conversation history and forecast tracking - Functional implementation."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from database.db_manager import query, execute
from config.logger import get_logger

logger = get_logger(__name__)


# Pure helper functions

def generate_session_id() -> str:
    """Generate a unique session ID.

    Pure function using UUID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def parse_metadata(metadata_str: Optional[str]) -> Dict[str, Any]:
    """Parse JSON metadata string.

    Pure function to safely parse JSON.

    Args:
        metadata_str: JSON string or None

    Returns:
        Parsed dictionary or empty dict
    """
    if not metadata_str:
        return {}

    try:
        return json.loads(metadata_str)
    except:
        return {}


def serialize_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[str]:
    """Serialize metadata to JSON string.

    Pure function to convert dict to JSON.

    Args:
        metadata: Dictionary to serialize

    Returns:
        JSON string or None
    """
    if not metadata:
        return None

    try:
        return json.dumps(metadata)
    except:
        return None


# Conversation management functions

def add_conversation(
    session_id: Optional[str],
    user_message: str,
    assistant_message: str,
    intent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Save conversation to memory.

    Args:
        session_id: Session identifier (generates new if None)
        user_message: User's message
        assistant_message: Assistant's response
        intent: Classified intent
        metadata: Additional metadata

    Returns:
        Conversation ID
    """
    sid = session_id or generate_session_id()
    metadata_json = serialize_metadata(metadata)

    sql = """
        INSERT INTO conversations (session_id, user_message, assistant_message, intent, metadata)
        VALUES (?, ?, ?, ?, ?)
    """

    execute(sql, (sid, user_message, assistant_message, intent, metadata_json))

    # Get the inserted ID
    result = query(
        "SELECT id FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (sid,)
    )

    conversation_id = result[0]['id'] if result else 0
    logger.info(f"Saved conversation {conversation_id} for session {sid}")

    return conversation_id


def get_session_history(
    session_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get conversation history for a session.

    Args:
        session_id: Session identifier
        limit: Maximum conversations to return

    Returns:
        List of conversations in chronological order
    """
    sql = """
        SELECT * FROM conversations
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """

    conversations = query(sql, (session_id, limit))

    # Parse metadata JSON
    for conv in conversations:
        conv['metadata'] = parse_metadata(conv.get('metadata'))

    return list(reversed(conversations))  # Return in chronological order


def get_recent_conversations(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversations across all sessions.

    Args:
        limit: Maximum number of conversations

    Returns:
        List of recent conversations
    """
    sql = """
        SELECT * FROM conversations
        ORDER BY created_at DESC
        LIMIT ?
    """

    conversations = query(sql, (limit,))

    for conv in conversations:
        conv['metadata'] = parse_metadata(conv.get('metadata'))

    return conversations


def search_conversations(
    keyword: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search conversations by keyword.

    Args:
        keyword: Search keyword
        limit: Maximum results

    Returns:
        List of matching conversations
    """
    sql = """
        SELECT * FROM conversations
        WHERE user_message LIKE ? OR assistant_message LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
    """

    pattern = f"%{keyword}%"
    conversations = query(sql, (pattern, pattern, limit))

    for conv in conversations:
        conv['metadata'] = parse_metadata(conv.get('metadata'))

    return conversations


def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get summary statistics for a session.

    Args:
        session_id: Session identifier

    Returns:
        Dictionary with session statistics
    """
    # Total messages
    total = query(
        "SELECT COUNT(*) as count FROM conversations WHERE session_id = ?",
        (session_id,)
    )

    # Intent distribution
    intents = query("""
        SELECT intent, COUNT(*) as count
        FROM conversations
        WHERE session_id = ? AND intent IS NOT NULL
        GROUP BY intent
    """, (session_id,))

    # First and last message
    timerange = query("""
        SELECT MIN(created_at) as first, MAX(created_at) as last
        FROM conversations
        WHERE session_id = ?
    """, (session_id,))

    return {
        'session_id': session_id,
        'total_messages': total[0]['count'] if total else 0,
        'intent_distribution': {i['intent']: i['count'] for i in intents},
        'first_message': timerange[0]['first'] if timerange else None,
        'last_message': timerange[0]['last'] if timerange else None
    }


def clear_session(session_id: str) -> int:
    """Clear conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Number of conversations deleted
    """
    rows = execute(
        "DELETE FROM conversations WHERE session_id = ?",
        (session_id,)
    )

    logger.info(f"Cleared {rows} conversations for session {session_id}")
    return rows


# Forecast tracking functions

def record_forecast(
    forecast_date: str,
    sku: str,
    predicted_demand: int,
    predicted_weather: str,
    recommendation: str
) -> int:
    """Record a forecast for future accuracy tracking.

    Args:
        forecast_date: Date of forecast (YYYY-MM-DD)
        sku: Product SKU
        predicted_demand: Predicted demand quantity
        predicted_weather: Predicted weather condition
        recommendation: Recommendation made

    Returns:
        Forecast ID
    """
    sql = """
        INSERT INTO forecasts (forecast_date, sku, predicted_demand, predicted_weather, recommendation)
        VALUES (?, ?, ?, ?, ?)
    """

    execute(sql, (forecast_date, sku, predicted_demand, predicted_weather, recommendation))

    result = query("SELECT id FROM forecasts ORDER BY id DESC LIMIT 1")

    return result[0]['id'] if result else 0


def calculate_forecast_accuracy(predicted: int, actual: int) -> float:
    """Calculate forecast accuracy score.

    Pure function to compute accuracy percentage.

    Args:
        predicted: Predicted demand
        actual: Actual demand

    Returns:
        Accuracy score (0-100%)
    """
    if predicted == 0:
        return 0.0

    error = abs(predicted - actual)
    accuracy = max(0, 100 - (error / predicted * 100))

    return accuracy


def update_actual_data(
    forecast_id: int,
    actual_demand: int,
    actual_weather: str
) -> None:
    """Update forecast with actual data and calculate accuracy.

    Args:
        forecast_id: Forecast ID
        actual_demand: Actual demand that occurred
        actual_weather: Actual weather condition
    """
    # Get forecast
    forecast = query(
        "SELECT * FROM forecasts WHERE id = ?",
        (forecast_id,)
    )

    if not forecast:
        logger.warning(f"Forecast {forecast_id} not found")
        return

    predicted_demand = forecast[0]['predicted_demand']

    # Calculate accuracy score
    accuracy_score = calculate_forecast_accuracy(predicted_demand, actual_demand)

    # Update forecast
    sql = """
        UPDATE forecasts
        SET actual_demand = ?, actual_weather = ?, accuracy_score = ?
        WHERE id = ?
    """

    execute(sql, (actual_demand, actual_weather, accuracy_score, forecast_id))

    logger.info(f"Updated forecast {forecast_id} with accuracy score {accuracy_score:.1f}%")


def get_accuracy_stats() -> Dict[str, Any]:
    """Get overall forecast accuracy statistics.

    Returns:
        Dictionary with accuracy metrics
    """
    # Overall accuracy
    overall = query("""
        SELECT
            COUNT(*) as total_forecasts,
            AVG(accuracy_score) as avg_accuracy,
            MIN(accuracy_score) as min_accuracy,
            MAX(accuracy_score) as max_accuracy
        FROM forecasts
        WHERE accuracy_score IS NOT NULL
    """)

    # Accuracy by SKU
    by_sku = query("""
        SELECT
            sku,
            COUNT(*) as forecast_count,
            AVG(accuracy_score) as avg_accuracy
        FROM forecasts
        WHERE accuracy_score IS NOT NULL
        GROUP BY sku
        ORDER BY forecast_count DESC
        LIMIT 10
    """)

    return {
        'overall': overall[0] if overall else {},
        'by_sku': by_sku,
        'total_forecasts': overall[0]['total_forecasts'] if overall else 0,
        'avg_accuracy': overall[0]['avg_accuracy'] if overall else 0
    }


def get_recent_forecasts(
    limit: int = 20,
    include_pending: bool = True
) -> List[Dict[str, Any]]:
    """Get recent forecasts.

    Args:
        limit: Maximum number of forecasts
        include_pending: Include forecasts without actual data

    Returns:
        List of forecasts
    """
    if include_pending:
        sql = "SELECT * FROM forecasts ORDER BY created_at DESC LIMIT ?"
        params = (limit,)
    else:
        sql = """
            SELECT * FROM forecasts
            WHERE accuracy_score IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        """
        params = (limit,)

    return query(sql, params)


# Legacy OOP wrappers for backwards compatibility

class MemoryManager:
    """Legacy MemoryManager class for backwards compatibility.

    NOTE: This is a thin wrapper around functional implementations.
    Consider using the functional API directly for new code.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or generate_session_id()

    def add_conversation(
        self,
        user_message: str,
        assistant_message: str,
        intent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        return add_conversation(self.session_id, user_message, assistant_message, intent, metadata)

    def get_session_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        sid = session_id or self.session_id
        return get_session_history(sid, limit)

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        return get_recent_conversations(limit)

    def search_conversations(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        return search_conversations(keyword, limit)

    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.session_id
        return get_session_summary(sid)

    def clear_session(self, session_id: Optional[str] = None):
        sid = session_id or self.session_id
        return clear_session(sid)


class ForecastTracker:
    """Legacy ForecastTracker class for backwards compatibility.

    NOTE: This is a thin wrapper around functional implementations.
    Consider using the functional API directly for new code.
    """

    def __init__(self):
        # No state needed
        pass

    def record_forecast(
        self,
        forecast_date: str,
        sku: str,
        predicted_demand: int,
        predicted_weather: str,
        recommendation: str
    ) -> int:
        return record_forecast(forecast_date, sku, predicted_demand, predicted_weather, recommendation)

    def update_actual_data(
        self,
        forecast_id: int,
        actual_demand: int,
        actual_weather: str
    ):
        return update_actual_data(forecast_id, actual_demand, actual_weather)

    def get_accuracy_stats(self) -> Dict[str, Any]:
        return get_accuracy_stats()

    def get_recent_forecasts(
        self,
        limit: int = 20,
        include_pending: bool = True
    ) -> List[Dict[str, Any]]:
        return get_recent_forecasts(limit, include_pending)


def get_memory_manager(session_id: Optional[str] = None) -> MemoryManager:
    """Get MemoryManager instance (legacy compatibility)."""
    return MemoryManager(session_id)


def get_forecast_tracker() -> ForecastTracker:
    """Get ForecastTracker instance (legacy compatibility)."""
    return ForecastTracker()
