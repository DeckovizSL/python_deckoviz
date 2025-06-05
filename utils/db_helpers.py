from typing import List, Dict, Any
from sqlalchemy.engine.row import Row

def row_to_dict(row: Row) -> Dict[str, Any]:
    """
    Convert SQLAlchemy Row object to dictionary.
    
    Args:
        row: SQLAlchemy Row object
        
    Returns:
        Dictionary with column names as keys and row values as values
    """
    if not row:
        return {}
    
    # Convert to dict using column names from Row object's _fields attribute if available
    if hasattr(row, "_fields"):
        return {key: value for key, value in zip(row._fields, row)}
    
    # Handle legacy SQLAlchemy versions or named tuples
    try:
        return dict(row._mapping)
    except (AttributeError, TypeError):
        pass
    
    # Fallback to position-based dictionary
    try:
        return {key: row[idx] for idx, key in enumerate(row.keys())}
    except (AttributeError, TypeError):
        pass
    
    # Last resort - return as positional dictionary
    return {f"col_{i}": val for i, val in enumerate(row)}

def rows_to_dict_list(rows: List[Row]) -> List[Dict[str, Any]]:
    """
    Convert a list of SQLAlchemy Row objects to a list of dictionaries.
    
    Args:
        rows: List of SQLAlchemy Row objects
        
    Returns:
        List of dictionaries with column names as keys and row values as values
    """
    return [row_to_dict(row) for row in rows]