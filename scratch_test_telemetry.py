import requests
import time

payload = {
    "camera_id": "CAM 1", 
    "active_visitors": 2, 
    "active_tracks": 2, 
    "zone_occupancy": {"entrance": 2}, 
    "timestamp": "2026-05-31T12:00:00Z"
}

try:
    print("Testing with 'CAM 1'...")
    res = requests.post("http://localhost:8000/telemetry", json=payload)
    print(res.status_code, res.text)
    time.sleep(1)
    
    payload["camera_id"] = "CAM1"
    print("Testing with 'CAM1'...")
    res = requests.post("http://localhost:8000/telemetry", json=payload)
    print(res.status_code, res.text)
except Exception as e:
    print("Error:", e)
