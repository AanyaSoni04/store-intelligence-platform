# Technology Choices

> Rationale for every technology decision in the Store Intelligence System.

## Language: Python 3.11

**Why:** Industry standard for ML/CV pipelines. Strong ecosystem for YOLOv8 (ultralytics), OpenCV, and data processing. Type hints and `match` statement available in 3.11+.

**Trade-off:** Slower than Go/Rust for pure API serving, but the detection pipeline is the bottleneck, not the API.

## Web Framework: FastAPI

**Why:** Native async support, automatic OpenAPI docs, Pydantic v2 integration, WebSocket support built-in. The fastest Python framework for this use case.

**Alternatives considered:** Flask (lacks async, no built-in validation), Django (too heavy for an API-first project).

## Data Validation: Pydantic v2

**Why:** Tight FastAPI integration, excellent performance (Rust-based core), discriminated unions for event metadata, clean serialization.

## Database: SQLite (via SQLAlchemy)

**Why:** Zero-infrastructure setup, file-based, sufficient for single-store demo. WAL mode enables concurrent reads during writes.

**Trade-off:** Not suitable for multi-node deployment. Production would use PostgreSQL.

**Why SQLAlchemy ORM:** Migration-ready, database-agnostic (easy swap to PostgreSQL), relationship management.

## Detection: YOLOv8-nano

<!-- TODO: Document model choice rationale -->
<!-- TODO: Benchmark inference speed -->

## Tracking: ByteTrack (via supervision)

<!-- TODO: Document why ByteTrack over DeepSORT -->
<!-- TODO: Document supervision library benefits -->

## Geometry: Shapely

<!-- TODO: Document why Shapely for polygon operations -->

## Testing: Pytest

**Why:** De facto Python testing standard. Fixtures, parametrize, and async support. In-memory SQLite for fast, isolated integration tests.

## Containerization: Docker Compose

**Why:** Single-command startup (`docker compose up`), reproducible environment, volume mounts for data persistence.

## Logging: Structured JSON (python-json-logger)

**Why:** Machine-parseable logs for production log aggregation. Human-readable during development.

---

## What We'd Change in Production

<!-- TODO: Document production-grade upgrades:
    - PostgreSQL or TimescaleDB for time-series queries
    - Redis Streams for event bus
    - Kubernetes for orchestration
    - Prometheus + Grafana for monitoring
    - Appearance embedding model for re-entry
    - POS integration API
    - CI/CD pipeline
-->
