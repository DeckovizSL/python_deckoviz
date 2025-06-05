import json
import datetime
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles datetime objects by converting them to ISO format strings.
    """
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            return obj.isoformat()
        # Let the base class default method handle other types
        return super().default(obj)


def json_dumps(obj: Any) -> str:
    """
    Serialize obj to a JSON formatted string with datetime handling.
    
    Args:
        obj: Python object to be serialized
        
    Returns:
        JSON formatted string
    """
    return json.dumps(obj, cls=DateTimeEncoder)
