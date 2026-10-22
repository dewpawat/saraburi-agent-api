# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2026-10-22

### Fixed
- **Database Connection Pool Resilience (`TCPTransport closed` Fix)**:
  - Added `pool_pre_ping=True` to `create_async_engine` in `app/core/database.py`. Automatically tests connections before issuing queries and gracefully reconnects if the socket was terminated, completely resolving `RuntimeError: unable to perform operation on <TCPTransport closed=True reading=False ...>; the handler is closed`.
  - Added `pool_recycle=1800` (30 minutes) to proactively retire and recycle idle database connections before hospital network firewalls or MySQL `wait_timeout` silently drop them.
  - Added conservative connection pool constraints (`pool_size=5`, `max_overflow=5`) to guarantee that the agent uses fewer than 10 total connections, strictly safeguarding the hospital's primary HIS/HOSxP database resources.

## [1.1.2] - 2026-10-22

### Changed
- **Host Network Mode (`network_mode: "host"`)**:
  - Switched default network from Docker Bridge to Host Network mode in `docker-compose.yml`.
  - Removed redundant `ports: - "18080:18080"` binding since host mode directly uses the host's network interfaces.
  - Resolves the 2-minute MySQL/MariaDB Reverse DNS Lookup timeout encountered on hospital HOSxP servers that lack `skip-name-resolve`.
  - Enables direct, low-latency database connectivity without Docker NAT / userland-proxy overhead.
- **Dual-Worker Concurrency (`--workers 2`)**:
  - Configured Uvicorn to run with 2 workers (`command: uvicorn app.main:app --host 0.0.0.0 --port 18080 --workers 2`) in `docker-compose.yml`.
  - Enables dual-lane request processing: ensures high-priority emergency alerts (Stroke Alert, RTI) are never blocked or delayed by heavy background reporting/sync queries.
- **Docker Compose Spec Modernization**:
  - Removed obsolete `version: "3.9"` attribute to align with current Compose specification and eliminate CLI warnings.

## [1.1.1] - 2026-10-01

### Fixed
- **SQLAlchemy Asyncio & Greenlet Dependency**:
  - Updated `requirements.txt` from `sqlalchemy` to `sqlalchemy[asyncio]`.
  - Resolves `ImportError: The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed` encountered during fresh `docker compose up -d --build` installs.
  - Ensures full forward-compatibility with SQLAlchemy 2.1+, which separated `greenlet` from core dependencies into the `[asyncio]` extra target.

## [1.1.0] - 2026-09-21

### Added
- **API Versioning**:
  - Added `APP_VERSION` configuration (`1.1.0`) centrally in `app/core/config.py`.
  - Added `"version"` field to `/api/v1/monitor/status`, `/api/v1/monitor/database`, and `/api/v1/monitor/full-check` endpoints for central monitoring and agent dashboard compatibility.
- **Safe Type Helpers & Formatters (`app/utils/formatters.py`)**:
  - `safe_str`: Safely converts values to string, converting `None`, empty, and literal `"None"`/`"null"` strings to `default` (null).
  - `safe_date_iso`: Safely parses and formats date/datetime/time and string dates to ISO 8601, gracefully handling `0000-00-00` and missing dates without throwing `AttributeError`.
  - `safe_float` & `safe_int`: Safely parses numeric/decimal values with fallback defaults.
  - `safe_get`: Safely accesses dictionary and SQLAlchemy `RowMapping` keys without raising `KeyError`.
- **Safe Subquery Runner (`safe_fetch_all`)**:
  - Wrapped optional subqueries in HIE Visit and Admit (`diag`, `drug`, `lab`, `allergy`, `er_oper`, `opd_oper`, `an`, `ipt_oper`) so that missing hospital tables or views (e.g. `s_drugitems` vs `drugitems`, `opd_allergy`, `er_regist_oper`) do not fail the main patient visit/admit request.
- **Daily Request Access Logging (`app/utils/logger.py` & Middleware)**:
  - Added HTTP access log middleware recording real client IP (via `X-Forwarded-For`), HTTP method, endpoint path, requested `X-Hospcode`, HTTP status code, and execution time in ms.
  - Generates 1 log file per day (`logs/access_YYYY-MM-DD.log` -> 365 files/year), keeping logs permanently without deletion.
  - Non-blocking and permission-safe: mounted `./logs:/app/logs` in `docker-compose.yml` with `RUN mkdir -p /app/logs && chmod -R 777 /app/logs` in `Dockerfile` and git-tracked via `.gitkeep`.

### Changed
- **Exception Handling & Response Standardization**:
  - Added `SQLAlchemyError` handler in `app/main.py`: Catches all database errors (missing tables, connection timeouts, syntax errors) and returns clean JSON format `{"MessageCode": "500", "Message": "Database Error: <message>"}` without leaking internal python tracebacks to clients.
  - Added `HTTPException` handler in `app/main.py`: Formats 401, 403, and 400 errors as `{"MessageCode": "<status_code>", "Message": "<detail>"}`.
  - Added `RequestValidationError` handler in `app/main.py`: Formats 422 errors into standard JSON with readable field validation summaries.
  - Added general `Exception` handler with server-side error logging via Python `logging` module.
- **Null & Type Safety Across Endpoints**:
  - Refactored `app/api/v1/hie.py`, `app/api/v1/stroke.py`, and `app/api/v1/rti.py` to use safe casting for all result rows.
  - Added hospital code fallback in `stroke.py`: if `ovst.hcode` is NULL, automatically falls back to `settings.HOSP_CODE`.
  - Refactored `rti.py` to bind `:hospcode` and `:hospcode9` directly in the query parameters instead of issuing separate `SET @hospcode` commands, ensuring thread and connection-pool safety.
- **Pydantic Model Updates**:
  - Made `HIEPatientItem.cid` and `HIEServiceItem.cid` optional so patients without CID do not trigger schema validation failures.
  - Added default empty lists to `StrokeIPDResponse`, `StrokeOPDResponse`, `RTIAccidentResponse`, and `RTIAccidentPlaceResponse`.
  - Made security headers in `get_header_security` optional so missing headers can be handled cleanly with 401 Unauthorized in standard format.

## [1.0.0] - 2026-01-06
- Initial release of Saraburi Agent API.
- Support for HIE (Patient, Service, Visit, Admit).
- Support for Stroke (IPD, OPD).
- Support for RTI (Accident, Place).
- System and Database monitoring endpoints.
