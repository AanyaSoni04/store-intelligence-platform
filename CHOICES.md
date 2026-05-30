# Technology Choices

> Rationale for every technology decision in the Store Intelligence System.

## Language: Python 3.11

**Why:** Python is the industry standard for ML and CV pipelines. It boasts a strong ecosystem for YOLOv8 (Ultralytics), OpenCV, and matrix-based data processing. Furthermore, Python 3.11 introduces significant performance enhancements and structural pattern matching (`match` statements), providing strict runtime control over asynchronous event streams.

**Trade-off:** Python handles pure HTTP API serving slower than compiled languages like Go or Rust. However, the bottleneck in this architecture is the bounding-box inference and detection pipeline, making Python's rich ML ecosystem vastly more valuable than raw API throughput.

## Web Framework: FastAPI

**Why:** FastAPI provides native asynchronous ASGI support, enabling non-blocking execution essential for maintaining high-throughput event processing. It includes built-in WebSocket support for real-time dashboard broadcasting and natively integrates with Pydantic for validation, creating self-documenting APIs via OpenAPI.

**Alternatives Considered:** Flask lacks native async support and built-in type validation. Django's monolithic architecture and heavy ORM are too cumbersome for an API-first microservice.

## Data Validation: Pydantic v2

**Why:** Pydantic v2's Rust-based core provides unmatched validation speeds. By utilizing discriminated unions, the system safely processes heterogeneous tracking events (e.g., zone entries vs. queue drop-offs) while guaranteeing type safety before hitting the database.

## Detection: YOLOv8-nano

**Why:** YOLOv8-nano was selected to strictly balance edge-compute infrastructure constraints against the required bounding-box accuracy. Retail CCTV feeds typically output at 1080p and 15fps. Processing this resolution in real-time requires a lightweight architecture to prevent thermal throttling and compute bottlenecks on edge appliances. The nano variant provides a high enough mean Average Precision (mAP) to detect individuals confidently without incurring the massive multi-gigabyte VRAM overhead required by larger models like YOLOv8x.

## Tracking: ByteTrack (via `supervision`)

**Why:** Retail environments are characterized by high-density crowds and frequent partial occlusions (e.g., shopping carts, product displays, overlapping shoppers). Traditional tracking algorithms like DeepSORT struggle in these environments by discarding low-confidence bounding boxes, leading to fragmented visitor IDs. ByteTrack mitigates this by utilizing low-scoring detection boxes to bridge tracking gaps, ensuring robust identity retention during heavy occlusions. Integrating this via the `supervision` library ensures clean, scalable API interactions rather than relying on brittle, custom tracker implementations.

## Geometry: Shapely

**Why:** Shapely serves as the geometric engine for retail zone tracking. When visitors navigate a store, their bounding-box centroids are mapped into a 2D coordinate space. Shapely efficiently calculates polygon intersections between these dynamic centroids and predefined static store zones (e.g., 'Produce', 'Checkout'). This allows for sub-millisecond mathematical confirmation of a visitor's location without relying on resource-heavy visual AI confirmation.

## Database: SQLite vs. PostgreSQL/Redis

**Why SQLite:** We utilize SQLite initialized in WAL (Write-Ahead Logging) mode. This configuration allows concurrent reads during writes, which is critical for real-time event ingestion while the dashboard simultaneously queries KPI metrics. It requires zero infrastructure and serves perfectly for single-store edge deployments.

**The Enterprise Trade-off:** As the system scales to a multi-store enterprise deployment, SQLite creates an I/O bottleneck and prevents cross-store aggregation. In a production environment, this will be migrated to:
- **PostgreSQL** (paired with TimescaleDB) as the permanent event sink to handle heavy time-series metric aggregations and cross-store indexing.
- **Redis Streams** as an ephemeral event bus to manage high-velocity telemetry spikes and buffer the relational database during peak shopping hours.

## Containerization: Docker Compose

**Why:** Docker Compose provides a reproducible environment via a single command (`docker compose up`), encapsulating the API, model weights, and volume mounts for persistent SQLite data.

## Logging: Structured JSON (`python-json-logger`)

**Why:** JSON logs are highly machine-parseable, natively integrating with ELK or Grafana Loki stacks for production log aggregation, while remaining human-readable for rapid development debugging.
