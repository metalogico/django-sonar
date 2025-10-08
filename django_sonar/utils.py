import json
import threading
from decimal import Decimal
from datetime import datetime, date, time
from uuid import UUID

_thread_locals = threading.local()
_thread_locals.sonar_dump = []


def make_json_serializable(obj):
    """
    Convert non-JSON-serializable objects to serializable format.
    
    Handles:
    - Decimal -> float or string
    - datetime, date, time -> ISO format string
    - UUID -> string
    - bytes -> string (decoded)
    - Sets -> lists
    - Complex nested structures (dicts, lists)
    
    :param obj: Object to convert
    :return: JSON-serializable version of the object
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    if isinstance(obj, Decimal):
        # Convert Decimal to float, or to string if precision matters
        return float(obj)
    
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    
    if isinstance(obj, UUID):
        return str(obj)
    
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            return obj.decode('utf-8', errors='replace')
    
    if isinstance(obj, set):
        return [make_json_serializable(item) for item in obj]
    
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    
    # For other objects, try to convert to string
    try:
        return str(obj)
    except Exception:
        return f"<non-serializable: {type(obj).__name__}>"


def get_sonar_dump():
    return getattr(_thread_locals, 'sonar_dump', [])


def reset_sonar_dump():
    _thread_locals.sonar_dump = []


def get_sonar_exceptions():
    return getattr(_thread_locals, 'sonar_exceptions', [])


def add_sonar_exception(exception):
    sonar_exceptions = get_sonar_exceptions()
    sonar_exceptions += [exception]
    _thread_locals.sonar_exceptions = sonar_exceptions


def reset_sonar_exceptions():
    _thread_locals.sonar_exceptions = []


def sonar(*args):
    sonar_dump = get_sonar_dump()
    for arg in args:
        try:
            # Convert to JSON-serializable format
            serializable_arg = make_json_serializable(arg)
            # Verify it's actually serializable
            json.dumps(serializable_arg)
            sonar_dump += [serializable_arg]
            _thread_locals.sonar_dump = sonar_dump
        except (TypeError, ValueError) as e:
            # If still not serializable, store error info
            print(f"SONAR: Argument of type {type(arg).__name__} could not be serialized: {e}")
