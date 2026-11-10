import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date, time
from uuid import UUID


@dataclass
class _CaptureContext:
    dumps: list = field(default_factory=list)
    exceptions: list = field(default_factory=list)
    events: list = field(default_factory=list)
    logs: list = field(default_factory=list)


_capture_context = ContextVar('django_sonar_capture_context', default=None)


def start_capture_context():
    """Start an isolated capture context and return its reset token."""
    return _capture_context.set(_CaptureContext())


def end_capture_context(token):
    """Restore the context that preceded ``start_capture_context``."""
    _capture_context.reset(token)


def is_capture_active():
    return _capture_context.get() is not None


def _get_buffer(name):
    context = _capture_context.get()
    return getattr(context, name) if context is not None else None


def _reset_buffer(name):
    buffer = _get_buffer(name)
    if buffer is not None:
        buffer.clear()


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
    return _get_buffer('dumps') or []


def reset_sonar_dump():
    _reset_buffer('dumps')


def get_sonar_exceptions():
    return _get_buffer('exceptions') or []


def add_sonar_exception(exception):
    sonar_exceptions = _get_buffer('exceptions')
    if sonar_exceptions is not None:
        sonar_exceptions.append(exception)


def reset_sonar_exceptions():
    _reset_buffer('exceptions')


def get_sonar_events():
    return _get_buffer('events') or []


def add_sonar_event(event):
    sonar_events = _get_buffer('events')
    if sonar_events is not None:
        sonar_events.append(event)


def reset_sonar_events():
    _reset_buffer('events')


def get_sonar_logs():
    return _get_buffer('logs') or []


def add_sonar_log(log_entry):
    sonar_logs = _get_buffer('logs')
    if sonar_logs is not None:
        sonar_logs.append(log_entry)


def reset_sonar_logs():
    _reset_buffer('logs')


def sonar(*args):
    sonar_dump = _get_buffer('dumps')
    if sonar_dump is None:
        return

    for arg in args:
        try:
            # Convert to JSON-serializable format
            serializable_arg = make_json_serializable(arg)
            # Verify it's actually serializable
            json.dumps(serializable_arg)
            sonar_dump.append(serializable_arg)
        except (TypeError, ValueError) as e:
            # If still not serializable, store error info
            print(f"SONAR: Argument of type {type(arg).__name__} could not be serialized: {e}")
