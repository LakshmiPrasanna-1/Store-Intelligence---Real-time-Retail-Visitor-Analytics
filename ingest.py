import json
import requests

with open('events.jsonl', 'r') as f:
    events = [json.loads(line) for line in f if line.strip()]

print(f'Total events: {len(events)}')

batch_size = 100
for i in range(0, len(events), batch_size):
    batch = events[i:i+batch_size]
    r = requests.post('http://localhost:8000/events/ingest', json=batch)
    print(f'Batch {i//batch_size + 1}: {r.status_code}')

print('Done! All events ingested.')