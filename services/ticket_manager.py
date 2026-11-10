"""Ticket creation and management - Functional implementation."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from database.db_manager import query, execute
from config.logger import get_logger

logger = get_logger(__name__)


# Core ticket operations (functional)

def create_reorder_ticket(
    sku: str,
    reason: str,
    recommended_qty: int,
    vendor_id: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """Create a reorder ticket.

    Args:
        sku: Product SKU
        reason: Reason for reorder
        recommended_qty: Recommended quantity to order
        vendor_id: Vendor ID
        priority: Priority level (low/medium/high)

    Returns:
        Dictionary with creation result
    """
    sql = """
        INSERT INTO tickets (sku, reason, recommended_qty, vendor_id, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (sku, reason, recommended_qty, vendor_id, priority, "pending")

    try:
        execute(sql, params)

        # Get the created ticket
        ticket = query(
            "SELECT * FROM tickets WHERE sku = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
            (sku,)
        )[0]

        logger.info(f"Created reorder ticket for SKU {sku}: {recommended_qty} units from {vendor_id}")

        return {
            'success': True,
            'ticket_id': ticket['id'],
            'ticket': ticket,
            'message': f"Ticket #{ticket['id']} created for {sku}"
        }

    except Exception as e:
        logger.error(f"Failed to create ticket for SKU {sku}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_pending_tickets(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all pending tickets.

    Args:
        limit: Maximum number of tickets to return

    Returns:
        List of pending tickets
    """
    sql = """
        SELECT t.*, i.name as product_name, v.name as vendor_name
        FROM tickets t
        LEFT JOIN inventory i ON t.sku = i.sku
        LEFT JOIN vendors v ON t.vendor_id = v.vendor_id
        WHERE t.status = 'pending'
        ORDER BY t.priority DESC, t.created_at DESC
        LIMIT ?
    """
    return query(sql, (limit,))


def get_ticket_by_id(ticket_id: int) -> Optional[Dict[str, Any]]:
    """Get specific ticket by ID.

    Args:
        ticket_id: Ticket ID

    Returns:
        Ticket details or None
    """
    sql = """
        SELECT t.*, i.name as product_name, v.name as vendor_name
        FROM tickets t
        LEFT JOIN inventory i ON t.sku = i.sku
        LEFT JOIN vendors v ON t.vendor_id = v.vendor_id
        WHERE t.id = ?
    """
    tickets = query(sql, (ticket_id,))
    return tickets[0] if tickets else None


def update_ticket_status(
    ticket_id: int,
    status: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Update ticket status.

    Args:
        ticket_id: Ticket ID
        status: New status (pending/approved/rejected/completed)
        notes: Optional notes

    Returns:
        Dictionary with update result
    """
    sql = "UPDATE tickets SET status = ? WHERE id = ?"
    params = (status, ticket_id)

    try:
        rows = execute(sql, params)

        if rows > 0:
            logger.info(f"Updated ticket #{ticket_id} to status: {status}")
            return {
                'success': True,
                'ticket_id': ticket_id,
                'status': status,
                'message': f"Ticket #{ticket_id} updated to {status}"
            }
        else:
            return {
                'success': False,
                'error': f"Ticket #{ticket_id} not found"
            }

    except Exception as e:
        logger.error(f"Failed to update ticket #{ticket_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_ticket_stats() -> Dict[str, Any]:
    """Get ticket statistics.

    Returns:
        Dictionary with ticket counts by status and priority
    """
    # Count by status
    status_sql = """
        SELECT status, COUNT(*) as count
        FROM tickets
        GROUP BY status
    """
    status_counts = {row['status']: row['count'] for row in query(status_sql)}

    # Count by priority (pending only)
    priority_sql = """
        SELECT priority, COUNT(*) as count
        FROM tickets
        WHERE status = 'pending'
        GROUP BY priority
    """
    priority_counts = {row['priority']: row['count'] for row in query(priority_sql)}

    # Total value of pending tickets
    value_sql = """
        SELECT SUM(t.recommended_qty * v.unit_price) as total_value
        FROM tickets t
        JOIN vendors v ON t.vendor_id = v.vendor_id
        WHERE t.status = 'pending'
    """
    value_result = query(value_sql)
    total_value = value_result[0]['total_value'] if value_result and value_result[0]['total_value'] else 0

    return {
        'by_status': status_counts,
        'by_priority': priority_counts,
        'total_pending': status_counts.get('pending', 0),
        'total_value': float(total_value)
    }


# Pure calculation functions

def calculate_recommended_quantity(
    current_qty: int,
    threshold: int,
    multiplier: float = 2.0
) -> int:
    """Calculate recommended reorder quantity.

    Pure function for quantity calculation.

    Args:
        current_qty: Current quantity in stock
        threshold: Reorder threshold
        multiplier: Safety stock multiplier

    Returns:
        Recommended quantity to order
    """
    target_qty = int(threshold * multiplier)
    return max(0, target_qty - current_qty)


# Bulk ticket operations

def create_tickets_from_analysis(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Create tickets from Decision Agent recommendations.

    Args:
        analysis_result: Analysis result from decision agent

    Returns:
        Summary of tickets created
    """
    tickets_created = []
    errors = []

    # Extract context if available
    context = analysis_result.get('context', {})
    low_stock_items = context.get('inventory', {}).get('low_stock_items', [])

    # Create tickets for each low-stock item
    for item in low_stock_items:
        # Find best vendor from context
        top_vendors = context.get('top_vendors', [])
        vendor = top_vendors[0] if top_vendors else {'vendor_id': 'Unknown'}

        # Calculate recommended quantity
        recommended_qty = calculate_recommended_quantity(
            item['qty'],
            item['reorder_threshold']
        )

        result = create_reorder_ticket(
            sku=item['sku'],
            reason=f"Low stock: {item['qty']} units below threshold {item['reorder_threshold']}",
            recommended_qty=recommended_qty,
            vendor_id=vendor['vendor_id'],
            priority="high"
        )

        if result['success']:
            tickets_created.append(result['ticket'])
        else:
            errors.append({'sku': item['sku'], 'error': result['error']})

    return {
        'tickets_created': len(tickets_created),
        'tickets': tickets_created,
        'errors': errors,
        'summary': f"Created {len(tickets_created)} tickets, {len(errors)} errors"
    }


def create_bulk_tickets(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create multiple tickets at once.

    Args:
        items: List of ticket specifications

    Returns:
        Summary of bulk creation
    """
    tickets_created = []
    errors = []

    for item_spec in items:
        result = create_reorder_ticket(
            sku=item_spec['sku'],
            reason=item_spec.get('reason', 'Bulk reorder'),
            recommended_qty=item_spec['qty'],
            vendor_id=item_spec['vendor_id'],
            priority=item_spec.get('priority', 'medium')
        )

        if result['success']:
            tickets_created.append(result['ticket'])
        else:
            errors.append({'sku': item_spec['sku'], 'error': result['error']})

    return {
        'tickets_created': len(tickets_created),
        'tickets': tickets_created,
        'errors': errors
    }


# Query functions

def get_tickets_by_status(status: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get tickets filtered by status.

    Args:
        status: Status filter
        limit: Maximum results

    Returns:
        List of tickets
    """
    sql = """
        SELECT t.*, i.name as product_name, v.name as vendor_name
        FROM tickets t
        LEFT JOIN inventory i ON t.sku = i.sku
        LEFT JOIN vendors v ON t.vendor_id = v.vendor_id
        WHERE t.status = ?
        ORDER BY t.created_at DESC
        LIMIT ?
    """
    return query(sql, (status, limit))


def get_tickets_by_priority(priority: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get pending tickets filtered by priority.

    Args:
        priority: Priority filter (low/medium/high)
        limit: Maximum results

    Returns:
        List of tickets
    """
    sql = """
        SELECT t.*, i.name as product_name, v.name as vendor_name
        FROM tickets t
        LEFT JOIN inventory i ON t.sku = i.sku
        LEFT JOIN vendors v ON t.vendor_id = v.vendor_id
        WHERE t.status = 'pending' AND t.priority = ?
        ORDER BY t.created_at DESC
        LIMIT ?
    """
    return query(sql, (priority, limit))


# No OOP wrapper needed - use the functional API directly!
