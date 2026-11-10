# Django Sonar test suite

The suite covers middleware capture, parsers and filters, collectors, database routing, panels and views, template escaping, events/logging, management commands, and hardening regressions.

Run every test with either command:

```bash
python manage.py test django_sonar
python run_tests.py
```

Run a module or individual test with its dotted path:

```bash
python manage.py test django_sonar.tests.test_hardening
python manage.py test django_sonar.tests.test_hardening.MiddlewareHardeningTests.test_persistence_failure_does_not_change_application_response
```

`tests/__init__.py` intentionally does not import test cases. Django discovery is the source of truth, so new `test_*.py` modules are included automatically.

Middleware unit tests use explicit capture contexts where they exercise buffer helpers directly. Integration tests emit dumps, events, logs, and exceptions from inside the middleware call, matching production request scoping.
