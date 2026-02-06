from datetime import datetime, timedelta

def calculate_date_diff(start_date: datetime, end_date: datetime) -> int:
    return (end_date - start_date).days

def add_days(start_date: datetime, days: int) -> datetime:
    return start_date + timedelta(days=days)
