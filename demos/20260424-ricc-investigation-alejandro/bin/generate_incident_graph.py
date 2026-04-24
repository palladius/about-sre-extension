
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import subprocess

# Incident Context
START_INCIDENT = "2026-04-24 14:06:24"
CANARY_UPDATE = "2026-04-24 14:46:59"
DETECTION = "2026-04-24 17:45:00"
MITIGATION_1 = "2026-04-24 17:57:45"
MITIGATION_2 = "2026-04-24 18:15:20"
END_INCIDENT = "2026-04-24 18:16:00"

def fetch_data(filter_str, name="data"):
    cmd = [
        "gcloud", "monitoring", "timeseries", "list",
        f"--filter={filter_str}",
        "--interval-start=2026-04-24T13:00:00Z",
        "--interval-end=2026-04-24T19:00:00Z",
        "--format=json",
        "--project=sre-next-prod"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching {name}: {result.stderr}")
        return []
    return json.loads(result.stdout)

def process_ts(ts_data):
    all_points = []
    for ts in ts_data:
        for point in ts.get('points', []):
            all_points.append({
                'timestamp': point['interval']['endTime'],
                'value': int(point['value']['int64Value'])
            })
    if not all_points:
        return pd.DataFrame(columns=['timestamp', 'value'])
    df = pd.DataFrame(all_points)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').resample('1min').sum().fillna(0)
    return df

print("Fetching ERROR logs...")
error_json = fetch_data('metric.type = "logging.googleapis.com/log_entry_count" AND metric.label.severity = "ERROR"', "errors")
print("Fetching INFO logs...")
info_json = fetch_data('metric.type = "logging.googleapis.com/log_entry_count" AND metric.label.severity = "INFO"', "info")

df_error = process_ts(error_json)
df_info = process_ts(info_json)

# Combine and align
df = df_info.rename(columns={'value': 'baseline'}).join(df_error.rename(columns={'value': 'errors'}), how='outer').fillna(0)

# Calculate availability proxy (1 - errors/total)
# For boutique, let's just plot errors vs baseline volume
df['total'] = df['baseline'] + df['errors']
df['availability'] = 100 * (1 - df['errors'] / df['total'].replace(0, 1))
# Smooth availability
df['availability_smooth'] = df['availability'].rolling(window=5, min_periods=1).mean()

# Save CSV for reference
df.to_csv('20260424-ricc-investigation/evidence/incident_metrics.csv')

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# Top: Availability / Error Rate
ax1.plot(df.index, df['availability_smooth'], color='#d93025', linewidth=2, label='Availability % (Success Rate)')
ax1.fill_between(df.index, df['availability_smooth'], 100, color='#d93025', alpha=0.1)
ax1.set_ylim(0, 105)
ax1.set_ylabel('Availability (%)', fontsize=12, fontweight='bold')
ax1.grid(True, which='both', linestyle='--', alpha=0.5)
ax1.set_title('Online Boutique - Checkout Outage & Frontend Errors (2026-04-24)', fontsize=16, fontweight='bold', pad=20)

# Bottom: Volume
ax2.bar(df.index, df['errors'], color='#d93025', alpha=0.6, label='Error Count', width=0.0005)
ax2.plot(df.index, df['baseline'], color='#1a73e8', linewidth=1, label='Baseline Volume (INFO)', alpha=0.4)
ax2.set_ylabel('Log Count / min', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.3)

# Annotations
milestones = [
    (START_INCIDENT, 'NetworkPolicy Block', '#d93025', '--'),
    (CANARY_UPDATE, 'Frontend Canary (Typo)', '#f9ab00', ':'),
    (DETECTION, 'Detection (Human)', '#f9ab00', '-.'),
    (MITIGATION_1, 'Deleted NetworkPolicy', '#1e8e3e', '--'),
    (MITIGATION_2, 'Scaling Frontend', '#1e8e3e', '--'),
    (END_INCIDENT, 'Incident End', '#1e8e3e', '-')
]

for ts_str, label, color, style in milestones:
    ts = pd.to_datetime(ts_str)
    ax1.axvline(x=ts, color=color, linestyle=style, linewidth=2, alpha=0.8)
    ax2.axvline(x=ts, color=color, linestyle=style, linewidth=2, alpha=0.8)
    # Add text label
    ax1.text(ts, 107, label, rotation=45, color=color, fontsize=10, fontweight='bold', ha='center')

# Formatting X-axis
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%Y-%m-%d', tz='UTC'))
ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))
ax2.set_xlabel('Time (UTC)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('20260424-ricc-investigation/evidence/checkout_outage_graph.png', dpi=300)
print("Graph saved to 20260424-ricc-investigation/evidence/checkout_outage_graph.png")
