import json
import pandas as pd
from datetime import datetime

# Load raw logs
with open('20260520-ricc-investigation/evidence/raw_errors.json', 'r') as f:
    logs = json.load(f)

# Extract timestamps and bucket by minute
timestamps = []
for entry in logs:
    # Only count if there's an actual application error
    if entry.get('jsonPayload') and entry['jsonPayload'].get('error'):
        ts_str = entry.get('timestamp')
        if ts_str:
            dt = pd.to_datetime(ts_str).floor('min').replace(tzinfo=None)
            timestamps.append(dt)

# Create a DataFrame
df = pd.DataFrame(timestamps, columns=['timestamp'])
df['count'] = 1
grouped = df.groupby('timestamp').sum()

# Define the full range
start_time = datetime(2026, 5, 20, 13, 20)
end_time = datetime(2026, 5, 20, 13, 50)
full_range = pd.date_range(start=start_time, end=end_time, freq='1min')

# Reindex and fill with 0
grouped = grouped.reindex(full_range, fill_value=0)
grouped.index.name = 'timestamp'
grouped = grouped.reset_index()

# Save to CSV
grouped.to_csv('20260520-ricc-investigation/evidence/error_metrics.csv', index=False)
print(f"Saved {len(grouped)} rows to error_metrics.csv")
print(grouped)
