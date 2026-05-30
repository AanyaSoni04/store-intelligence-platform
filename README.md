# Store Intelligence System

> End-to-end pipeline converting CCTV footage into real-time retail analytics.

## Overview

Store Intelligence processes CCTV video to detect, track, and analyze customer behavior in retail stores. The system generates structured events from raw footage and serves real-time analytics via a REST API and live dashboard.

**Pipeline:** Raw CCTV → Detection (YOLOv8 + ByteTrack) → Event Stream → Intelligence API → Live Dashboard

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose

### Run with Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Dashboard:** http://localhost:8000/dashboard

### Run Locally (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH=src  # Linux/Mac
set PYTHONPATH=src     # Windows

# Run the API server
uvicorn store_intel.main:app --reload --port 8000

# Run tests
pytest
```

## Architecture

```
CCTV Video → Frame Decoder → YOLOv8 Detector → ByteTrack Tracker
    → Zone Manager → Event FSM → SQLite (events table)
    → FastAPI Analytics API → WebSocket → Live Dashboard
```

<!-- TODO: Add architecture diagram image -->

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System health check |
| `/events/ingest` | POST | Batch event ingestion |
| `/stores/{id}/metrics` | GET | KPI snapshot (visitors, conversion, dwell, queue, abandonment) |
| `/stores/{id}/funnel` | GET | Visitor funnel with drop-off rates |
| `/stores/{id}/heatmap` | GET | Zone visit frequency |
| `/stores/{id}/anomalies` | GET | Detected anomalies |

## Project Structure

```
├── src/store_intel/       # Main application package
│   ├── api/               # FastAPI route handlers
│   ├── analytics/         # KPI computation engines
│   ├── db/                # SQLAlchemy models + CRUD
│   ├── detection/         # CCTV processing pipeline
│   ├── events/            # Pydantic schemas + event FSM
│   └── tracking/          # Visitor identity + staff exclusion
├── dashboard/             # Browser-based live dashboard
├── tests/                 # Pytest unit + integration tests
├── configs/               # Zone polygon configuration
├── scripts/               # CLI utilities
├── DESIGN.md              # Design decisions and trade-offs
└── CHOICES.md             # Technology rationale
```

<!-- TODO: Add sections for:
    - Configuration guide
    - Zone setup guide
    - Detection pipeline usage
    - Sample API requests/responses
    - Contributing guidelines
-->

## Testing

```bash
pytest -v                    # Run all tests
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
```

## License

<!-- TODO: Add license -->
