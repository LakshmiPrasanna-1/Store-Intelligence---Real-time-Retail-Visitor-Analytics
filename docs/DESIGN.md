# System Design

## Staff Detection
We handle "Staff Movement" by monitoring each tracked person's position in the BILLING zone. If a person remains in the billing zone for more than 5 minutes with less than 20 pixels of movement, they are flagged as `is_staff: true` and excluded from conversion rate calculations.

## Zone Layout
The video frame is split vertically into three zones: top 30% is ENTRY/EXIT, middle 40% is SKINCARE, and bottom 30% is BILLING. Zone events are written in real-time to a JSONL file and ingested into SQLite via the API.