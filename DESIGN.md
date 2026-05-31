# Design Document

> Architecture decisions, data flows, and AI-driven trade-offs for the Store Intelligence System.

## Architecture

The Store Intelligence System operates as a decoupled, event-driven edge-to-cloud telemetry pipeline. Its primary objective is to convert raw, unstructured video feeds into actionable, real-time structured retail analytics. The architecture is broadly divided into three main tiers: the Edge Detection Tier (handling video ingestion and tracking), the Aggregation & Persistence Tier (handling event routing, state machines, and data storage), and the Presentation Tier (handling real-time visualization and analytics reporting). By decoupling these layers, the system guarantees high throughput and fault tolerance; if the Presentation Tier experiences high load, the Edge Detection Tier remains unaffected and continues to process frames.

## Detection Pipeline

The detection pipeline is the foundation of our physical-to-digital translation. It is designed to operate locally on edge appliances to minimize latency and bandwidth overhead. 
1. **Frame Extraction:** The pipeline captures raw RTSP or physical video feeds, utilizing OpenCV to extract individual frames at a down-sampled rate (e.g., 5-15 FPS). This down-sampling is a deliberate design choice to conserve memory and edge compute cycles while preserving enough temporal resolution to track human movement.
2. **Object Detection:** Frames are passed through the YOLOv8-nano model, which outputs high-confidence bounding boxes for all humans in the frame.
3. **Tracking & Re-ID:** The bounding boxes are fed into the ByteTrack engine, which assigns and maintains unique identifiers (IDs) for each individual. ByteTrack dynamically recovers lost tracks during brief occlusions using low-confidence detections, reducing fragmented tracking sessions.
4. **Geometric State Resolution:** The tracked centroids of each bounding box are processed mathematically by Shapely against a configuration of predefined virtual store polygons (e.g., Entry, Aisle 1, Checkout). This confirms when a shopper crosses a physical boundary.

## Event Flow

At the core of the analytics engine is a robust Finite State Machine (FSM). Every tracked individual holds an independent FSM progressing through a strict sequence based on geometric intersections.
1. **State Transitions:** As a centroid enters or exits a polygon, the FSM transitions the visitor's state (e.g., `OUTSIDE` → `ENTERED` → `IN_ZONE` → `IN_QUEUE` → `EXITED`).
2. **Event Dispatch:** Each transition generates discrete, timestamped events (e.g., `ZONE_ENTER`, `ZONE_EXIT`, `PURCHASE_PROXY`). 
3. **Robust Handling:** This strict transitional logic explicitly mitigates several common CCTV footage challenges:
   - *Group Entry:* Because YOLOv8 and ByteTrack are capable of isolating distinct bounding boxes even in tight clusters, the FSM instantiates separate parallel states for each group member, preventing undercounting during holiday rushes.
   - *Re-entry Tracking:* If a visitor exits the camera view and returns quickly (e.g., walking behind a pillar), the FSM implements a temporal cooldown buffer. Before marking a visitor as definitively `EXITED`, the state is held in suspense. If ByteTrack recovers the ID within the buffer window, the FSM resumes the session without incorrectly inflating the visitor count.
   - *Queue Occlusion:* When multiple shoppers cluster closely at a register, bounding boxes frequently overlap, drop, or merge. As long as the centroid remains within the Shapely checkout polygon, the FSM maintains their queued status until a definitive exit trajectory is established.

## Database

The system utilizes SQLite initialized in WAL (Write-Ahead Logging) mode. 
1. **Schema Design:** The database schema is optimized for time-series event ingestion. An `events` table serves as an immutable append-only ledger, capturing raw telemetry (camera ID, store ID, event type, timestamp, visitor ID). 
2. **Performance Constraints:** By enabling WAL mode, the system allows concurrent read operations while writes are occurring. This is critical for real-time event ingestion where the detection pipeline is constantly appending rows, while the backend API simultaneously runs complex `GROUP BY` aggregations to serve dashboard metrics.
3. **Edge Suitability:** For a single-store edge deployment, SQLite requires zero external infrastructure, drastically reducing operational complexity, setup time, and maintenance overhead while providing ACID compliance.

## API Layer

The API layer acts as the central nervous system connecting the edge pipeline with the frontend dashboard.
1. **Framework:** Built on FastAPI, the API utilizes native asynchronous ASGI support. This enables non-blocking execution, ensuring that heavy metric queries do not bottleneck the ingestion of incoming event streams.
2. **Ingestion & Validation:** Events are ingested in batches via a `POST /events/ingest` endpoint. Pydantic v2 schemas rigorously validate heterogeneous event payloads (e.g., ensuring a queue event contains the correct metadata compared to a zone entry event) before persistence, preventing database corruption.
3. **Aggregation Engines:** The API exposes specialized endpoints (`/stores/{id}/metrics`, `/stores/{id}/funnel`) that dynamically aggregate the raw SQLite ledger into high-level KPIs like conversion rates, average dwell times, and queue abandonment metrics.

## Dashboard

The Presentation Tier is a real-time, browser-based monitoring console tailored for store managers and operations teams.
1. **Telemetry & Real-Time Sync:** Utilizing WebSocket connections to the FastAPI layer, the dashboard receives instant telemetry broadcasts. This allows the Live Operations widgets to instantly reflect active tracks, zone occupancy, and system health without requiring manual page refreshes or heavy long-polling.
2. **Design Philosophy:** The interface follows a vanilla HTML/CSS/JS architecture (eliminating heavy dependencies like React or Webpack) to keep the frontend payload incredibly light and performant on lower-end retail back-office computers.
3. **Data Visualization:** The dashboard dynamically renders complex metrics, such as a multi-step conversion funnel and heatmaps, parsing the JSON responses from the API layer to provide immediate business intelligence context alongside the live video feed.

## AI-Assisted Decisions

To meet strict project deadlines and optimize architectural complexity, the codebase was heavily shaped by LLM interactions in three distinct pivots:
1. **Geometric FSM Over VLM Compute:** Initially, the pipeline considered passing keyframes to a Vision-Language Model (VLM) to semantically classify visitor behavior (e.g., "Is the person standing in the checkout line?"). AI consultation advised against this due to severe latency and edge-compute overhead. Instead, we pivoted to a rule-based geometric FSM using Shapely, achieving sub-millisecond, 100x faster processing with a fraction of the compute footprint while maintaining accuracy.
2. **Cross-Camera Deduplication Strategy:** Handling overlapping fields of view between Entry and Floor cameras often results in duplicated visitor counts. Through an architectural consultation with an LLM, we designed a temporal-spatial deduplication matrix. When a tracking ID exits the Entry camera's polygon and a new ID appears in the overlapping Floor camera's polygon within a strict temporal window, the IDs are algorithmically merged, preserving the continuity of the shopping session.
3. **Staff Identification via Color-Histogram:** To prevent store staff from skewing customer metrics, we needed an efficient filtering mechanism. Rather than training a heavy, custom YOLO class specifically for staff detection, we utilized an LLM to generate an optimized OpenCV color-histogram extraction snippet. This snippet isolates the dominant color from the bounding box; if the color matches predefined staff uniform parameters, the `is_staff` boolean flag is set, and the FSM silently filters these events out of the customer KPIs.
