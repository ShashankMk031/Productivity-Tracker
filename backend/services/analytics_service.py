import sqlite3
from analytics.metrics import get_global_metrics, get_behavioral_insights, get_task_metrics
from analytics.charts import get_chart_data

def aggregate_analytics(db: sqlite3.Connection) -> dict:
    global_metrics = get_global_metrics(db)
    insights = get_behavioral_insights(db)
    chart_data = get_chart_data(db)
    
    return {
        "metrics": global_metrics,
        "insights": insights,
        "charts": chart_data
    }
