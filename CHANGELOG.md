# Changelog

All notable changes to this project will be documented in this file.

## [0.6.0] - 2026-11-10

### Security
- Require patched Django releases (5.2.19+, 6.0.10+, or 6.1.3+) and sqlparse 0.6.1+ in package metadata
- Update pinned Django, Requests, urllib3, idna, and certifi dependencies and require setuptools 84.1.0+ for builds
- Audit pinned dependencies with pip-audit in CI
- Mask cookie headers and recursively filter sensitive keys in structured payloads, events, and log contexts
- Disable unstructured raw-body capture by default and add a configurable byte limit for explicit opt-in
- Isolate dump, event, log, and exception buffers per request with `ContextVar`

### Added
- Query capture across configured database aliases with `DEBUG=False` support and bounded details
- Configurable pagination for built-in panels and database indexes for common dashboard queries
- `clear_sonar_data --older-than DAYS` and `--database ALIAS`
- CI coverage for supported Python/Django combinations and package-content verification

### Changed
- Sonar collection is fail-open and no longer changes the application response when telemetry persistence fails
- Minimum supported versions are now Python 3.10 and Django 5.2
- The complete test runner now discovers every test using the active Python interpreter

### Fixed
- JSON and unstructured POST bodies are parsed according to content type
- Missing request/query details now return 404 instead of server errors
- Separate-database cleanup uses the alias selected by Django's database router
- Exception table column alignment and query database/duration display

## [0.5.2] - 2026-07-30

### Security
- **Stored XSS in SQL query detail** ([GHSA-9vgp-2j2c-w2mx](https://github.com/metalogico/django-sonar/security/advisories/GHSA-9vgp-2j2c-w2mx)) — remove `|safe` when rendering captured SQL and dumps so attacker-controlled query parameters are HTML-escaped in the dashboard
- **Clear all data** — `GET /sonar/clear/` no longer deletes records; clearing requires POST with CSRF

### Fixed
- Escape SQL and dump content in query detail, request detail queries, and dumps list templates

## [0.5.0] - 2026-02-11

### Added
- **Extensible panel system** - Custom panels can now be registered to extend Sonar's dashboard (contributed by @shanecp)
- **Events tracking** - New events panel with structured event data and level-aware status pills (contributed by @shanecp)
- **Logs tracking** - New logs panel with structured context capture and level-aware badges (contributed by @shanecp)
- **URL-driven navigation** - Sonar panels now support permalinks and URL-driven navigation (contributed by @shanecp)
- **Dark mode** - Full dark/light theme support with system preference detection and localStorage persistence

### Changed
- **Complete UI refresh** - Redesigned dashboard with refined typography, spacing, cards, tables, badges, and forms
- **Improved sidebar** - Cleaner navigation styling with active state indicators
- **Better empty states** - Contextual icons and messages for all empty panels
- **Upgraded Bootstrap** - Updated from 5.0.2 to 5.3.8
- **Upgraded Bootstrap Icons** - Updated to 1.13.1 with local font files
- **Upgraded HTMX** - Updated from 1.9.11 to 2.0.8
- **Upgraded sql-formatter** - Updated to latest version
- **Upgraded Django support** - Added Django 5.1 and 6.0 classifiers
- **Upgraded Python support** - Added Python 3.13 classifier
- **Build system** - Switched to setuptools build backend, removed setup.py

### Fixed
- **Login/denied pages** - Redesigned auth pages with centered layout and proper dark mode support

## [0.3.0] - 2025-10-08

### Added
- **Request filtering** - Filter requests by HTTP method, path, and status code (MET-25)
- **Pagination** - Requests table now paginated (25 per page) with htmx-powered navigation
- **Separate database support** - Database router to store Sonar data in a separate database for better performance
- **JSON serialization** - Automatic handling of Decimal, datetime, UUID, and other non-JSON-serializable types (MET-28)

### Fixed
- **Long URL support** - Changed `SonarRequest.path` from CharField(255) to TextField to support long URLs with query parameters (MET-27)
- **Filter persistence** - Fixed htmx polling to maintain active filters without parameter duplication

### Changed
- Request filtering UI with method dropdown, path search, and status input
- Improved pagination controls with First/Previous/Next/Last buttons
- Better handling of complex data types in payloads, headers, and session data

## [0.2.1] - 2024

### Added
- **Sensitive data filtering** - Automatic masking of passwords, tokens, API keys, and other sensitive fields (MET-29)
- **Query count display** - Show the number of database queries executed per request (MET-32)
- **PUT/PATCH payload support** - Capture request body data for PUT, PATCH, and other HTTP methods (MET-24)
- **Cleanup command** - Management command to prune old Sonar data (MET-22)
- **i18n URL support** - Better handling of internationalized URL patterns in path exclusions (MET-23)

### Fixed
- **Custom user model support** - Fixed compatibility with projects using custom user models (MET-12)
- **Template packaging** - Fixed missing template files in package distribution (MET-11)
- **Query tracking in production** - Improved database query logging when DEBUG=False (MET-26)
- **Superuser authentication** - Added proper permission checks for Sonar dashboard access (MET-10)

### Features
- Basic request monitoring
- Exception tracking
- Database query logging
- Dump utility (sonar() helper)
- Request details (headers, session, middlewares)
- Modern UI with htmx and Bootstrap 5
