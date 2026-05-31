# Store Intelligence: Engineering Handoff Document

This document serves as the final submission summary for the Store Intelligence hiring challenge. It provides a comprehensive overview of the architecture, data flows, methodologies, and instructions for running the project.

---

## 1. Architecture Summary

Store Intelligence is built using a clean, hexagonal architecture designed to separate computer vision extraction from backend data aggregation and frontend visualization. 

* **Detection Layer:** A Python-based computer vision pipeline that interfaces directly with local video feeds using OpenCV. It wraps Ultralytics YOLOv8 for object detection and the `supervision` library's ByteTrack for multi-object tracking.
* **Tracking & State Layer:** A robust `VisitorManager` maintains active memory of bounding boxes mapped to persistent `track_id`s, evaluating centroid intersections against configurable polygonal zones to emit discrete temporal events.
* **Backend Layer:** A FastAPI web server encapsulating a SQLite database via SQLAlchemy. It exposes RESTful endpoints for querying calculated metrics and a WebSocket channel for real-time dashboard syncing.
* **Frontend Layer:** A lightweight, vanilla JavaScript dashboard featuring glassmorphism design and Chart.js integrations that pull data on-load and react instantly to WebSocket broadcasts.

## 2. End-to-end Data Flow

The pipeline is a genuine end-to-end process moving from raw pixels to business intelligence:

1. **Video Ingestion:** `cv2.VideoCapture` streams frames from an `.mp4` file.
2. **Inference & Tracking:** YOLOv8 detects persons (class `0`); ByteTrack associates bounding boxes frame-over-frame to assign persistent integer IDs.
3. **Spatial Mapping:** `ZoneManager` uses ray-casting to determine if a person's centroid intersects defined polygon zones (e.g., `browsed_zone`, `billing_queue`).
4. **Event Materialization:** `VisitorManager` monitors state transitions. Entering a new zone generates a `ZONE_ENTER`. Leaving a zone calculates dwell time and generates a `ZONE_EXIT`. Heuristics flag prolonged zone traversals as `STAFF_DETECTED`.
5. **API Ingestion:** Mapped events are batched and POSTed to `/events/ingest`.
6. **Data Storage:** FastAPI validates payloads via Pydantic and commits them to SQLite.
7. **Broadcast:** The `/ws` endpoint emits an `EVENTS_INGESTED` signal.
8. **Dashboard Pull:** The browser receives the WS signal, fetches aggregated data via the `GET /stores/{id}/*` analytics endpoints, and re-renders Chart.js natively.

## 3. Key Technologies Used

* **Computer Vision:** `opencv-python` (Frame extraction), `ultralytics` (YOLOv8 Object Detection), `supervision` (ByteTrack MOT & PolyZone logic).
* **Backend:** `FastAPI` (REST/WS API), `Uvicorn` (ASGI Server), `Pydantic` (Data Validation).
* **Database:** `SQLAlchemy` (ORM), `SQLite` (Relational Storage).
* **Frontend:** HTML5/CSS3 (Vanilla), JavaScript, `Chart.js` (Visualizations).
* **Deployment:** `Docker` & `Docker Compose`.

## 4. Analytics Methodology

The analytics layer performs raw SQL aggregations over specific trailing time windows (e.g., `1h`, `1d`, `7d`).

* **Metrics:** Unique visitors are counted via `COUNT(DISTINCT visitor_id)`. Conversion rate is calculated as `purchases / total visitors`. Avg Dwell Time averages the `metadata.dwell_seconds` field of `ZONE_EXIT` events. Abandonment looks for queues joined without a corresponding purchase.
* **Funnel:** Drop-off rates calculate the sequential degradation of unique visitors reaching specific milestones (Entry → Browse → Queue → Purchase). 
* **Heatmap:** Groups all `ZONE_ENTER` events by `zone_id`, aggregating total visit counts and averaging the dwell time per zone.
* **Anomalies:** Checks events against predefined threshold parameters (e.g., dwell time > 15 mins triggers a severity badge alert).

## 5. Assumptions and Limitations

* **Database Engine:** SQLite is currently used for simplicity and ease of setup. It will experience locking under high concurrent write/read loads (e.g., thousands of events per second combined with heavy dashboard polling).
* **Tracking Fidelity:** The system relies on a single camera's perspective. It does not implement ReID (Re-identification) across multiple overlapping camera feeds.
* **Staff Heuristics:** Staff are currently detected using deterministic zone-traversal and dwell-time heuristics rather than visual uniform classification.

## 6. How to Run Locally

To run the full stack natively for development:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Export PYTHONPATH
export PYTHONPATH="src"    # Linux/Mac
# set PYTHONPATH="src"     # Windows

# 3. Run the FastAPI Server (Hosts DB, API, and Dashboard)
python -m uvicorn store_intel.main:app --reload

# 4. In a separate terminal, run the CCTV Pipeline
python scripts/run_pipeline.py --video path/to/video.mp4 --camera CAM3
```

Navigate to `http://localhost:8000/dashboard` to view the live interface.

## 7. Docker Usage

The project includes a multi-stage Dockerfile that installs necessary underlying C-libraries (X11, libgl) required for OpenCV.

```bash
# Build and spin up the environment
docker-compose up --build
```
*Note: The `docker-compose.yml` is configured to boot the API server. The detection pipeline can be executed as a standalone worker container against mounted volumes.*

## 8. API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/events/ingest` | Securely ingests a batch of standardized `StoreEvent` models. |
| `GET`  | `/stores/{id}/metrics` | Returns snapshot KPIs (`unique_visitors`, `conversion_rate`, etc). |
| `GET`  | `/stores/{id}/funnel` | Returns stage counts and sequential `drop_off_rates`. |
| `GET`  | `/stores/{id}/heatmap` | Returns aggregated `visit_count` and `avg_dwell_seconds` per zone. |
| `GET`  | `/stores/{id}/anomalies` | Returns a list of behavioral outliers detected in the trailing window. |
| `WS`   | `/ws` | WebSocket channel emitting realtime database update signals. |

## 9. Dashboard Capabilities

The responsive web dashboard (`dashboard/app.js`) is served statically via FastAPI and provides:
* **Reactive Polling:** Listens to the `/ws` channel to trigger seamless `.fetch()` updates without hard page reloads.
* **KPI Cards:** Displays real-time calculations of footfall, conversion, and abandonment with descriptive tooltips.
* **Custom Visuals:** Utilizes Chart.js with custom inline plugins to dynamically draw labels on funnel bars and rank heatmap zones descending by volume.
* **Anomaly Feed:** A real-time, scrollable alert log with color-coded severity badges and localized timestamps.

## 10. Future Improvements

* **Infrastructure:** Migrate from SQLite to PostgreSQL (`asyncpg`) to support concurrent ingest loads, and add Redis caching to prevent re-aggregating historical 7-day SQL queries on every WebSocket ping.
* **Computer Vision:** Incorporate a lightweight ReID model (e.g., OSNet) alongside ByteTrack to maintain visitor identities across blind spots and multiple cameras.
* **Security:** Implement JWT or OAuth2 middleware to secure the ingestion and analytics endpoints.
* **Testing:** Expand unit tests to thoroughly cover the raw SQL injection points within the `analytics/` package to ensure robust data integrity.
