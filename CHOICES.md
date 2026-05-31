# Technology Choices

> Detailed rationale for every critical technology and framework decision in the Store Intelligence System.

## Why YOLOv8

For the core object detection pipeline, we selected **YOLOv8-nano**. 
Retail CCTV feeds typically output at 1080p and 15-30 FPS. Processing this resolution in real-time requires an incredibly lightweight architecture to prevent thermal throttling, dropped frames, and hardware bottlenecks on constrained edge appliances (such as a standard retail back-office PC or a small form-factor NVR). The YOLOv8 "nano" variant was chosen because it strictly balances edge-compute infrastructure constraints against the required bounding-box accuracy. It provides a highly competitive mean Average Precision (mAP) that accurately detects individuals in various lighting conditions and postures without incurring the massive multi-gigabyte VRAM overhead required by larger, more bloated models like YOLOv8x or Transformer-based detectors. Furthermore, YOLOv8 natively integrates into the Ultralytics Python ecosystem, streamlining the pipeline construction.

## Why ByteTrack

Retail environments are notoriously difficult for computer vision tracking algorithms due to high-density crowds and frequent partial occlusions (e.g., shopping carts, high shelving, product displays, and overlapping shoppers). We selected **ByteTrack** (via the `supervision` library) as our multi-object tracking solution.
Traditional tracking algorithms (like SORT or DeepSORT) struggle in retail environments because they rigidly discard low-confidence bounding boxes, treating them as background noise. When a shopper is partially hidden behind an aisle, their bounding box confidence drops, causing DeepSORT to abruptly terminate their track and assign a new ID when they reappear, heavily fragmenting visitor IDs and artificially inflating the total visitor count. 
ByteTrack specifically mitigates this by uniquely retaining and utilizing low-scoring detection boxes to bridge tracking gaps. It associates these low-confidence boxes with existing high-confidence tracklets, ensuring exceptionally robust identity retention during heavy occlusions and dramatically improving the accuracy of our downstream conversion metrics.

## Why SQLite

For data persistence, we selected **SQLite** configured in WAL (Write-Ahead Logging) mode.
The Store Intelligence system is fundamentally designed as an edge-native microservice meant to run in isolation within a single retail location. SQLite perfectly aligns with this architecture because it requires zero external infrastructure, no dedicated server processes, and no complex networking configurations. It drastically reduces operational complexity and setup time for a quick hackathon prototype and edge deployment.
By enabling WAL mode, SQLite allows concurrent read operations while writes are occurring. This feature is absolutely critical: the real-time event ingestion pipeline is constantly appending raw telemetry rows, while the backend FastAPI layer simultaneously runs complex, heavy `GROUP BY` aggregations to serve metrics to the frontend dashboard. WAL mode prevents the database from locking up during these simultaneous high-velocity operations, maintaining the real-time feel of the dashboard.

## Why FastAPI

We selected **FastAPI** as the backbone for our API and presentation layer.
High-throughput event processing requires a framework capable of non-blocking I/O execution. FastAPI provides native, top-tier asynchronous ASGI support out of the box. As the detection pipeline blasts hundreds of event payloads per minute, FastAPI's async handlers effortlessly queue and process these requests without locking the main thread.
Additionally, FastAPI natively integrates with Pydantic for validation, creating self-documenting APIs via OpenAPI, which accelerated development. Crucially, FastAPI includes robust built-in WebSocket support. This allowed us to easily create a bi-directional telemetry broadcast channel, pushing real-time active tracks and zone occupancy data directly to the frontend dashboard with minimal latency and code overhead.

## Alternatives Rejected

Several alternative technologies were evaluated but ultimately rejected to maintain system performance, simplicity, and project scope:

1. **Rejected: DeepSORT (Tracking)**
   - *Reason:* As mentioned above, DeepSORT discards low-confidence bounding boxes during partial occlusions, which are extremely common in retail environments (e.g., people behind shelves). This led to severe identity fragmentation compared to ByteTrack. Furthermore, DeepSORT requires an additional feature extraction model (Re-ID), which consumes additional GPU/CPU compute cycles that edge appliances cannot afford.

2. **Rejected: PostgreSQL / Redis (Database/Caching)**
   - *Reason:* While PostgreSQL paired with Redis Streams is the enterprise standard for high-velocity telemetry spikes and time-series aggregation, introducing them into a hackathon prototype or a single-store edge deployment creates massive infrastructure bloat. Managing Docker compose dependencies, volume mounts, and networking for three separate databases contradicts the goal of a lightweight, plug-and-play edge appliance. SQLite WAL provides sufficient concurrency for a single-store load.

3. **Rejected: Flask / Django (Web Framework)**
   - *Reason:* Flask lacks native, built-in async support and robust WebSocket handling out of the box, relying instead on cumbersome extensions. Django’s monolithic architecture and heavy ORM are far too cumbersome and opinionated for a lightweight, API-first microservice focused purely on data ingestion and aggregation.

4. **Rejected: React / Next.js (Frontend)**
   - *Reason:* Implementing a massive React or Next.js single-page application requires Node.js, Webpack/Vite build steps, and hundreds of megabytes of `node_modules`. For an edge dashboard meant to run locally on lower-end retail hardware, a vanilla HTML/CSS/JS architecture ensures the payload is incredibly lightweight, instantly loads, and removes complex build-chain dependencies, perfectly aligning with the "keep it simple" philosophy of the project.

5. **Rejected: Vision-Language Models (VLM) for Logic**
   - *Reason:* Using VLMs (like GPT-4V or LLaVA) to semantically analyze keyframes to determine shopper state ("Is the user in line?") introduces severe latency (seconds per frame), massive API costs, and privacy concerns (sending CCTV footage to the cloud). By rejecting VLMs in favor of a rule-based geometric FSM using Shapely, we process states in sub-milliseconds entirely locally.
