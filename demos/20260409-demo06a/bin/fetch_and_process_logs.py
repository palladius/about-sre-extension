import json
import subprocess
from datetime import datetime, timedelta, timezone
import csv

PROJECT_ID = 'sre-next'
START_TIME = '2026-04-09T09:00:00Z'
END_TIME = '2026-04-09T14:30:00Z'
POD_PREFIX = 'frontend'
OUTPUT_FILE = '20260409-ricc-investigation/evidence/frontend_500_errors.csv'

def fetch_logs():
    filter_str = (
        f'resource.type="k8s_container" AND '
        f'resource.labels.pod_name:"{POD_PREFIX}" AND '
        f'(severity=ERROR OR httpRequest.status=500 OR jsonPayload.http.resp.status=500) AND '
        f'timestamp >= "{START_TIME}" AND timestamp <= "{END_TIME}"'
    )
    
    cmd = [
        'gcloud', 'logging', 'read', filter_str,
        '--project', PROJECT_ID,
        '--format', 'json',
        '--limit', '10000' # Adjust if needed
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching logs: {result.stderr}")
        return []
    
    return json.loads(result.stdout)

def process_logs(entries):
    counts = {}
    
    # Initialize all minutes with 0
    start_dt = datetime.fromisoformat(START_TIME.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(END_TIME.replace('Z', '+00:00'))
    
    current_dt = start_dt
    while current_dt <= end_dt:
        counts[current_dt.strftime('%Y-%m-%d %H:%M:00+00:00')] = 0
        current_dt += timedelta(minutes=1)
        
    for entry in entries:
        ts_str = entry.get('timestamp')
        if not ts_str:
            continue
        
        # Parse timestamp and round to minute
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        minute_str = dt.strftime('%Y-%m-%d %H:%M:00+00:00')
        
        if minute_str in counts:
            counts[minute_str] += 1
            
    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', '5xx_count'])
        for time_str in sorted(counts.keys()):
            writer.writerow([time_str, counts[time_str]])
    
    print(f"Successfully wrote {len(counts)} rows to {OUTPUT_FILE}")

if __name__ == '__main__':
    entries = fetch_logs()
    process_logs(entries)
