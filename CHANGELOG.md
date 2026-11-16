# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2026-11-16

### Security
- **Fake `X-Forwarded-For` accepted when every hop is a LAN address** (introduced in 1.2.0): if all addresses in the header were trusted / private (e.g. external traffic NAT-ed to the LAN gateway before Apache), the agent used the **left-most** address, which the caller can type. It now uses the **right-most** one, added by the nearest proxy. Found on the สสจ. agent (192.168.6.89): a request through `saraburiapi.moph.go.th/agent/` with `X-Forwarded-For: 192.168.6.86` was logged as 192.168.6.86. Callers that reach the agent directly, and callers behind a proxy with a public IP, were not affected.

### Notes
- Do not put the LAN gateway / NAT address (e.g. `192.168.6.1`) in `API_ALLOWED_IPS` / `API_ALLOWED_IP2`: every request that comes through that gateway, including from the internet via a reverse proxy, then passes the IP check and only the API key protects the agent.

## [1.3.0] - 2026-11-16

Hospitals can upgrade straight from 1.1.x to 1.3.0 (includes everything in 1.2.0). Existing MySQL `.env` files work unchanged.

### Added
- **PostgreSQL support** for hospitals running HOSxP on PostgreSQL (e.g. 10695): set `DB_TYPE=postgresql` in `.env`. Without `DB_TYPE` (every `.env` before 1.3.0) the agent uses MySQL / MariaDB exactly as before. Accepted values: `mysql`, `mariadb`, `postgresql`, `postgres`, `pgsql`; any other value stops startup with a clear message.
  - Driver `asyncpg`. Every PostgreSQL session is read-only (`default_transaction_read_only=on`) and has a 10 s connect timeout, like the MySQL driver.
  - All HIE / Stroke / RTI queries have PostgreSQL versions in `app/sql/postgresql.py`. They return the same fields and the same text formats as MySQL (time as `8:05:09`, upper-case RTI keys, MySQL's NULL ordering, NULL-safe address concatenation, HIV / interpretation lab masking case-insensitive).
  - On PostgreSQL, optional HIE sub-queries run inside a savepoint, so a missing table (e.g. `s_drugitems`) only skips that part, as on MySQL. Without it PostgreSQL would abort every following query of the request.
- `DB_PORT` is optional: defaults to 3306 (mysql) or 5432 (postgresql).
- `/monitor/system-info` and `/monitor/full-check` now include `database_type` (`mysql` / `postgresql`) and `database_version` (read with a 3 s limit; `null` if the DB does not answer). Fields are added only, nothing removed.

### Changed
- MySQL queries are untouched: endpoints now call `sql_for("<key>", """<same MySQL SQL>""")`, which returns the original MySQL text unless `DB_TYPE=postgresql`. Checked that all 24 MySQL SQL strings are byte-for-byte identical to 1.2.0.
- `/monitor/database` and `/monitor/full-check`: when an error has no message (e.g. a connect timeout) the error type is returned instead of an empty string.

### Tested
- Mock HOSxP schema with identical data on MariaDB 10.6, PostgreSQL 16 and PostgreSQL 9.6; all 15 endpoint cases compared as JSON:
  - 1.2.0 on MySQL vs 1.3.0 on MySQL: identical (only difference is the order of lab items with the same `order_date`, which the original query does not sort and MySQL returns in any order).
  - 1.3.0 on MySQL vs 1.3.0 on PostgreSQL 16 / 9.6: identical (drug list order inside `drug_name` ignored for the same reason).
  - PostgreSQL without `s_drugitems`, DB restart (automatic reconnect), DB down, monitor auth rules.

## [1.2.0] - 2026-11-16

### Fixed
- **HIE Visit / Admit `procedure_opd` always empty**: `HIEProcedureOpdItem` was declared twice in `hie_model.py`; the second declaration (IPD fields) replaced the first, so every OPD procedure came back as `{ref_date: null, oper_name: null, ...}`. The IPD model is now `HIEProcedureIptItem` (used by `procedure_an`), and `procedure_opd` returns `opd_oper_code`, `opd_oper_name`, `price` again. Also removed a duplicated `dchtime` field in `HIEAnItem` (output unchanged).
- **`TCPTransport closed ... the handler is closed` DB errors**: v1.1.3's `pool_pre_ping` only reconnects on errors the driver reports as a disconnect. When a pooled connection's socket has already been closed, uvloop raises a plain `RuntimeError` that `pool_pre_ping` lets through, so one request per dead connection failed (seen at hospcode 10812 on v1.1.3, ~25% of checks). `app/core/database.py` now pings every connection on checkout and treats *any* ping failure as a disconnect, so SQLAlchemy discards it and reconnects before the query runs. Reproduced and verified in Docker: v1.1.3 fails the first request, v1.2.0 succeeds.
- **Time zone**: container now runs in `Asia/Bangkok` (`TZ` + `tzdata` in `Dockerfile`). Before, daily access-log files rolled over at 07:00 Thai time and `/monitor` times were UTC.

### Security
- **Monitor endpoints**: `GET /monitor/status` and `GET /monitor/database` stay public. `/monitor/system-info`, `/monitor/performance`, `/monitor/full-check` are now **POST** and require `x-api-key` + `x-hospcode` from an allowed IP (no body needed). Calling them with GET returns 405.
- **`/monitor/database` error detail**: callers that pass the API-key check (same headers as above) still get the full DB error. Anyone else gets only the error type and code, e.g. `OperationalError (2003)`, so DB host/IP is not exposed.
- **IP allowlist could be bypassed with a fake `X-Forwarded-For`**: the header is now trusted only when the request comes from a proxy listed in `TRUSTED_PROXIES` (default: `127.0.0.1`, `::1` and private LAN ranges), and the right-most untrusted hop is used. Requests that reach the agent directly ignore the header.
- Caller IP is checked before the API key, and the key is compared in constant time.
- `/openapi.json` is now disabled together with `/docs` and `/redoc` when `APP_ENV=production` (case-insensitive).

### Added
- `API_ALLOWED_IPS`: comma-separated list of allowed IPs or CIDR ranges. `API_ALLOWED_IP1` / `API_ALLOWED_IP2` still work and are merged, so existing `.env` files need no change. Invalid entries and inline `#` comments are ignored with a log warning instead of breaking startup.
- `TRUSTED_PROXIES`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE` (optional; defaults keep v1.1.3 behaviour: pool 5 + overflow 5 **per worker**, recycle 1800 s).
- A warning line in `docker compose logs` each time a DB connection is dropped and reopened (`saraburi_agent.database: DB connection dropped ...`), to measure how often a hospital's network or DB cuts connections.

### Changed
- `requirements.txt` pins every package to the set tested for this release (FastAPI 0.163.1, SQLAlchemy 2.1.8, aiomysql 0.3.2, uvicorn 0.54.0, ...), so every hospital builds the same versions.
- `Dockerfile`: removed `build-essential`, `default-libmysqlclient-dev`, `gcc` (not needed: the driver is pure Python) and the unused `.env.example` copy; default `CMD` now matches `docker-compose.yml` (`--workers 2`).
- Unknown keys in `.env` are ignored instead of failing startup; settings use the pydantic v2 `model_config`.
- Note on 1.1.3's pool wording: limits are per worker, so 2 workers can open up to 20 connections in total.

### Removed
- `app/utils/test_calc.py` (leftover test file) and the obsolete `version:` key in `.devcontainer/docker-compose.yml`.

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
