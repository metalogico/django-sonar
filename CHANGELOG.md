# Changelog

All notable changes to this project will be documented in this file.

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
