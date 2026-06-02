import cv2
import json
import time
from datetime import datetime, timezone
from collections import defaultdict
from ultralytics import YOLO

# --- CONFIG ---
# --- CONFIG ---
VIDEO_FILES = [
    "pipeline/CAM 1.mp4",
    "pipeline/CAM 2.mp4",
    "pipeline/CAM 3.mp4",
    "pipeline/CAM 4.mp4",
    "pipeline/CAM 5.mp4",
]
OUTPUT_FILE = "events.jsonl"
STORE_ID = "ST1008"
BILLING_STILL_THRESHOLD = 300
MOVEMENT_THRESHOLD = 20

# --- LOAD MODEL ---
model = YOLO("yolov8n.pt")  # downloads automatically on first run

# --- ZONE HELPER ---
def get_zone(y, frame_height):
    ratio = y / frame_height
    if ratio <= 0.30:
        return "ENTRY_EXIT"
    elif ratio <= 0.70:
        return "SKINCARE"
    else:
        return "BILLING"

# --- TRACKING STATE ---
visitor_zone_start = defaultdict(lambda: None)   # visitor_id -> timestamp when entered zone
visitor_last_pos = defaultdict(lambda: None)     # visitor_id -> last (x, y)
visitor_billing_start = defaultdict(lambda: None) # visitor_id -> when they entered billing
visitor_is_staff = defaultdict(lambda: False)    # visitor_id -> is_staff flag

def write_event(visitor_id, zone_id, is_staff):
    event = {
        "store_id": STORE_ID,
        "visitor_id": str(visitor_id),
        "event_type": "ZONE_DWELL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zone_id": zone_id,
        "is_staff": is_staff
    }
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"[EVENT] {event}")

# --- MAIN LOOP ---
# --- MAIN LOOP (all videos) ---
for VIDEO_PATH in VIDEO_FILES:
    print(f"\n Processing: {VIDEO_PATH}")
    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Error: Could not open {VIDEO_PATH}, skipping...")
        continue

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"FPS: {fps}, Frame Height: {frame_height}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Finished: {VIDEO_PATH}")
            break

        results = model.track(frame, persist=True, classes=[0], verbose=False)

        if results[0].boxes is None or results[0].boxes.id is None:
            continue

        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = box
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            zone = get_zone(cy, frame_height)
            now = time.time()

            if zone == "BILLING":
                if visitor_billing_start[track_id] is None:
                    visitor_billing_start[track_id] = now
                    visitor_last_pos[track_id] = (cx, cy)
                else:
                    last = visitor_last_pos[track_id]
                    movement = abs(cx - last[0]) + abs(cy - last[1])
                    if movement < MOVEMENT_THRESHOLD:
                        duration = now - visitor_billing_start[track_id]
                        if duration >= BILLING_STILL_THRESHOLD:
                            visitor_is_staff[track_id] = True
                    else:
                        visitor_billing_start[track_id] = now
                        visitor_last_pos[track_id] = (cx, cy)
            else:
                visitor_billing_start[track_id] = None

            write_event(track_id, zone, visitor_is_staff[track_id])

    cap.release()

print("\nAll videos processed! Events written to", OUTPUT_FILE)