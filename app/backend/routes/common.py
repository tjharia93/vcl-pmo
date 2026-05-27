from __future__ import annotations

from datetime import date, datetime


def row_dict(row) -> dict:
    data = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        data[col.name] = value
    return data
