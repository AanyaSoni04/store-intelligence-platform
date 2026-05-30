# Design Document

> Architecture decisions and trade-offs for the Store Intelligence System.

## System Architecture

<!-- TODO: Add detailed architecture diagram (Mermaid) -->
<!-- TODO: Describe data flow from CCTV to dashboard -->

## Database Design

### Schema: 3 Tables

The system uses a minimal 3-table schema:

1. **`stores`** — registered retail stores
2. **`visitors`** — deduplicated visitor identities
3. **`events`** — append-only event log (single source of truth)

**Why 3 tables instead of more?**

All analytics (metrics, funnel, heatmap, anomalies) are computed on demand from the `events` table. This avoids:
- Schema migrations when adding new event types
- Stale materialized data
- Complex synchronization between tables

<!-- TODO: Document trade-offs of JSON metadata vs normalized columns -->

## Event System

### Finite State Machine

Each tracked person is modeled as an FSM with states:
`OUTSIDE → ENTERED → IN_ZONE → IN_QUEUE → EXITED`

<!-- TODO: Add FSM diagram -->
<!-- TODO: Document state transition rules -->
<!-- TODO: Document dwell time tracking logic -->

## Detection Pipeline

<!-- TODO: Document YOLOv8 configuration and performance -->
<!-- TODO: Document ByteTrack parameters and track management -->
<!-- TODO: Document frame skipping strategy -->

## Edge Case Handling

<!-- TODO: Document handling of:
    - Group entry
    - Staff movement
    - Re-entry
    - Partial occlusion
    - Empty store periods
    - Queue buildup
-->

## Anomaly Detection

<!-- TODO: Document threshold-based rules and their rationale -->
<!-- TODO: Document cooldown logic -->

## Future Improvements

<!-- TODO: Document production upgrade path:
    - Appearance embeddings for re-entry
    - Camera overlap handling
    - POS integration
    - Redis event bus
    - Statistical anomaly detection
-->
