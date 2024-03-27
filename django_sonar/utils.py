import json
import threading

_thread_locals = threading.local()
_thread_locals.sonar_dump = []


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
            # Attempt to serialize the argument
            json.dumps(arg)
            sonar_dump += [arg]
            _thread_locals.sonar_dump = sonar_dump
        except TypeError:
            # If a TypeError is raised, the argument is not serializable
            print(f"SONAR: Argument {arg} is not serializable.")
