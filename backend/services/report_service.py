import sqlite3
from services.analytics_service import aggregate_analytics

def generate_report_data(db: sqlite3.Connection) -> dict:
    # In the future, this can prepare markdown payloads or AI contexts
    # For now, it simply fetches the aggregated analytics required for the modal
    return aggregate_analytics(db)
