import sqlite3
import csv
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager

# --- CONFIG ---
DB_PATH = "app/store.db"
CSV_PATH = "app/Brigade_Bangalore_10_April_26 (1)bc6219c.csv"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT,
            visitor_id TEXT,
            event_type TEXT,
            timestamp TEXT,
            zone_id TEXT,
            is_staff INTEGER
        )
    """)
    conn.commit()
    conn.close()

# --- LIFESPAN (replaces @app.on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Store Intelligence API", lifespan=lifespan)

# --- REQUEST MODEL ---
class Event(BaseModel):
    store_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: str
    is_staff: bool

# --- ROUTE 1: Ingest Events ---
@app.post("/events/ingest")
def ingest_events(events: List[Event]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for event in events:
        cursor.execute("""
            INSERT INTO events (store_id, visitor_id, event_type, timestamp, zone_id, is_staff)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event.store_id,
            event.visitor_id,
            event.event_type,
            event.timestamp,
            event.zone_id,
            1 if event.is_staff else 0
        ))
    conn.commit()
    conn.close()
    return {"status": "success", "inserted": len(events)}

# --- ROUTE 2: Get Store Metrics ---
@app.get("/stores/{store_id}/metrics")
def get_metrics(store_id: str):
    # Step 1: Count unique non-staff visitors from SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT visitor_id)
        FROM events
        WHERE store_id = ? AND is_staff = 0
    """, (store_id,))
    row = cursor.fetchone()
    conn.close()

    total_visitors = row[0] if row else 0

    # Step 2: Count purchases from CSV
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail=f"CSV file not found at {CSV_PATH}")

    total_purchases = 0
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_purchases += 1  # each row = one purchase

    # Step 3: Calculate conversion rate
    conversion_rate = (
        round((total_purchases / total_visitors) * 100, 2)
        if total_visitors > 0 else 0.0
    )

    return {
        "store_id": store_id,
        "total_visitors": total_visitors,
        "total_purchases": total_purchases,
        "conversion_rate_percent": conversion_rate
    }