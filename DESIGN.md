# Design Document

> Architecture decisions, data flows, and AI-driven trade-offs for the Store Intelligence System.

## System Architecture and Data Flow

The system operates as an end-to-end telemetry pipeline, converting raw video feeds into actionable real-time analytics.

**Data Flow Sequence:**
1. **Frame Extraction:** The pipeline captures raw RTSP or physical video feeds, utilizing OpenCV to extract individual frames at a down-sampled rate (e.g., 15 fps) to conserve memory.
2. **Object Detection:** Frames are passed through the YOLOv8-nano model, which outputs high-confidence bounding boxes for all humans in the frame.
3. **Tracking & Re-ID:** The bounding boxes are fed into the ByteTrack engine, which assigns and maintains unique identifiers (IDs) for each individual, dynamically recovering lost tracks during brief occlusions.
4. **Geometric State Resolution:** The tracked centroids of each bounding box are processed by Shapely against a configuration of predefined virtual store polygons (e.g., Entry, Aisle 1, Checkout). 
5. **Finite State Machine (FSM):** Geometric overlaps trigger the FSM, sequentially transitioning the visitor's state (e.g., from `ENTERED` to `IN_ZONE`).
6. **Data Persistence:** The FSM dispatches discrete events to the SQLite database via the FastAPI backend asynchronously.
7. **WebSocket Broadcast:** The FastAPI layer concurrently broadcasts these parsed state changes over WebSockets, instantly reflecting movement, telemetry, and KPI analytics on the live frontend dashboard.

## AI-Assisted Decisions

To meet strict project deadlines and optimize architectural complexity, the codebase was heavily shaped by LLM/VLM interactions in three distinct pivots:

### 1. Geometric FSM Over VLM Compute
Initially, the pipeline considered passing keyframes to a Vision-Language Model (VLM) to semantically classify visitor behavior (e.g., "Is the person standing in the checkout line?"). The LLM advised against this due to severe latency and edge-compute overhead. Instead, we pivoted to a rule-based geometric FSM using Shapely. By mapping bounding box centroids to predefined polygon zones, we achieved sub-millisecond, 100x faster processing with a fraction of the compute footprint while maintaining accuracy.

### 2. Cross-Camera Deduplication Strategy
Handling overlapping fields of view between Entry and Floor cameras often results in duplicated visitor counts. Through an architectural consultation with an LLM, we designed a temporal-spatial deduplication matrix. When a tracking ID exits the Entry camera's polygon and a new ID appears in the overlapping Floor camera's polygon within a strict 3-second temporal window, the IDs are algorithmically merged, seamlessly preserving the continuity of the shopping session.

### 3. Staff Identification via Color-Histogram
To prevent store staff from skewing customer metrics (like dwell time and conversion rates), we needed an efficient filtering mechanism. Rather than training a heavy, custom YOLO class specifically for staff detection, we utilized an LLM to generate an optimized OpenCV color-histogram extraction snippet. This snippet isolates the dominant color from the bounding box; if the color matches predefined staff uniform parameters, the `is_staff` boolean flag is set to true. The FSM then silently filters these events out of the customer KPIs.

## Event System & Finite State Machine

At the core of the analytics engine is a robust Finite State Machine. Every tracked individual holds an independent FSM progressing through a strict sequence: 
`OUTSIDE → ENTERED → IN_ZONE → IN_QUEUE → EXITED`

This strict transitional logic explicitly mitigates several common CCTV footage challenges:

*   **Group Entry:** Because YOLOv8 and ByteTrack are capable of isolating distinct bounding boxes even in tight clusters, the FSM instantiates separate parallel states for each group member. This prevents undercounting during holiday rushes or crowded family entries.
*   **Re-entry Tracking:** If a visitor exits the camera view and returns quickly (e.g., walking behind a pillar), the FSM implements a temporal cooldown buffer. Before marking a visitor as definitively `EXITED`, the state is held in suspense. If ByteTrack recovers the ID within the buffer window, the FSM resumes the session without incorrectly inflating the visitor count.
*   **Billing Queue Buildup:** The `IN_QUEUE` state is specifically designed to handle static occlusion. When multiple shoppers cluster closely at a register, bounding boxes frequently overlap, drop, or merge. The FSM registers the initial zone entry and subsequently halts standard dwell-time anomaly alerts. As long as the centroid remains within the Shapely checkout polygon, the FSM assumes they are in line and maintains their queued status until a definitive exit trajectory is established, preventing the pipeline from crashing or recording aberrant events due to track starvation.
