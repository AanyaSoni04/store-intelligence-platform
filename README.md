# 🛍️ Store Intelligence Platform

> **An Edge-to-Cloud Computer Vision pipeline converting CCTV footage into real-time retail analytics.**

Store Intelligence processes CCTV video to detect, track, and analyze customer behavior in retail stores. The system generates structured events from raw footage at the "Edge" and streams them to our Cloud API, powering a beautiful real-time analytics dashboard.

**The Pipeline:** Raw CCTV → YOLOv8 Detection → ByteTrack Identity Tracking → Zone Logic → Telemetry Stream → FastAPI Analytics Engine → Vercel Live Dashboard

---

## 🌐 Live Project Links (Hackathon Reviewers)

Experience the project instantly without running any code:

*   📊 **Live Dashboard:** [https://store-intelligence-dashboard.vercel.app](https://store-intelligence-dashboard.vercel.app)
*   📚 **Live API Docs (Swagger):** [https://store-intelligence-api-76n7.onrender.com/docs](https://store-intelligence-api-76n7.onrender.com/docs)

> 🚨 **Hackathon Note:** Our backend API is hosted on Render's free tier, which goes to sleep and resets its temporary database after 15 minutes of inactivity. **If the dashboard appears empty, please see the "Seeding the Database" section below!**

---

## 💻 How to Run Locally

To see the true magic of the Edge-to-Cloud architecture, you can run the YOLOv8 tracking pipeline on your own machine. As it processes a video, it will stream live telemetry directly to the hosted dashboard!

### 1. Prerequisites
- Python 3.9+
- A sample `.mp4` CCTV or retail video file

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/AanyaSoni04/store-intelligence-platform.git
cd store-intelligence-platform

# Install all required dependencies
pip install -r requirements.txt
```

### 3. Run the Computer Vision Pipeline
Place your sample video in the `data/` folder and run the pipeline. This script runs the YOLOv8 AI locally on your GPU/CPU, and streams the extracted analytics directly to our live Render API!

```bash
python scripts/run_pipeline.py --video data/your_sample_video.mp4 --camera CAM1
```
*Once it starts processing frames, open the [Live Dashboard](https://store-intelligence-dashboard.vercel.app) to watch the charts update in real-time!*

---

## 🌱 Seeding the Database (If Empty)

Because our cloud API runs on a free tier, it routinely wipes its local SQLite database to save space. If you open the dashboard and the metrics are at `0`, you can instantly populate it with thousands of realistic simulated events!

Run this in your terminal:
```bash
python scripts/seed_remote.py
```
*Wait ~10 seconds, refresh the Vercel dashboard, and enjoy the data visualization!*

---

## 🏗️ Architecture Stack

*   **Computer Vision (Edge):** `Python`, `YOLOv8` (Ultralytics), `ByteTrack`, `OpenCV`
*   **Backend API (Cloud):** `FastAPI`, `SQLite`, `SQLAlchemy`, Hosted on `Render`
*   **Frontend Dashboard:** `Vanilla JS`, `HTML/CSS`, `Chart.js`, Hosted on `Vercel`

## 📡 Core API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/events/ingest` | POST | Edge devices push batch telemetry events here |
| `/stores/{id}/metrics` | GET | Core KPI snapshot (visitors, conversion, queue depth) |
| `/stores/{id}/funnel` | GET | Customer journey funnel with drop-off rates |
| `/stores/{id}/heatmap` | GET | Zone visit frequency for store layout optimization |
| `/stores/{id}/anomalies` | GET | Automated alerts (e.g. high queue abandonment) |

---

## 🛠️ Project Structure

```text
├── src/store_intel/       # Main backend application package
│   ├── api/               # FastAPI route handlers & endpoints
│   ├── analytics/         # KPI computation engines
│   ├── db/                # SQLAlchemy models + CRUD operations
│   ├── detection/         # YOLOv8 + ByteTrack processing pipeline
│   └── events/            # Pydantic schemas + Event state machine
├── dashboard/             # Browser-based live dashboard (Vercel)
├── scripts/               # CLI utilities (Run pipeline, Seed database)
├── DESIGN.md              # Design decisions and architectural trade-offs
└── CHOICES.md             # Technology rationale
```

### 🏆 *Built for the AI Hackathon*
*Transforming physical retail, one frame at a time.*
