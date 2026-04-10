import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone

PROJECT_ID = 'sre-next'
FILTER = (
    'resource.type="k8s_container" '
    'resource.labels.namespace_name="default" '
    '(resource.labels.pod_name:"frontend" OR resource.labels.pod_name:"frontend-canary") '
    'severity=ERROR '
    '(jsonPayload.http.resp.status=500 OR httpRequest.status=500) '
    'timestamp >= "2026-04-09T12:00:00Z" '
    'AND timestamp <= "2026-04-09T14:30:00Z"'
)

def fetch_logs():
    cmd = [
        'gcloud', 'logging', 'read', FILTER,
        '--project', PROJECT_ID,
        '--format', 'json(timestamp)'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching logs: {result.stderr}")
        sys.exit(1)
    return json.loads(result.stdout)

def process_logs(logs):
    counts = {}
    for entry in logs:
        ts_str = entry['timestamp']
        # Handle formats like 2026-04-09T12:13:50.194021Z
        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        minute_ts = ts.replace(second=0, microsecond=0)
        counts[minute_ts] = counts.get(minute_ts, 0) + 1
    
    start_time = datetime.fromisoformat("2026-04-09T12:00:00+00:00")
    end_time = datetime.fromisoformat("2026-04-09T14:30:00+00:00")
    
    current_time = start_time
    output = []
    output.append("time,5xx_count")
    
    while current_time <= end_time:
        count = counts.get(current_time, 0)
        output.append(f"{current_time.strftime('%Y-%m-%d %H:%M:00+00:00')},{count}")
        current_time += timedelta(minutes=1)
    
    return "\n".join(output)

if __name__ == "__main__":
    logs = fetch_logs()
    csv_content = process_logs(logs)
    with open('20260409-ricc-investigation/evidence/frontend_500_errors.csv', 'w') as f:
        f.write(csv_content)
    print("CSV created successfully.")
