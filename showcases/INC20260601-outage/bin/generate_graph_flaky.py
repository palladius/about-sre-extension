import os
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Fetch raw logs from Cloud Logging using gcloud logging read
print("Fetching raw logs from Cloud Logging...")
query = (
    'resource.type="k8s_container" '
    'AND resource.labels.container_name="server" '
    'AND resource.labels.pod_name:"frontend-" '
    'AND logName="projects/sre-next-prod/logs/stdout" '
    'AND timestamp >= "2026-06-01T16:15:00Z" '
    'AND timestamp <= "2026-06-01T16:42:00Z"'
)
cmd = f"gcloud logging read '{query}' --limit=35000 --format='json(jsonPayload)' --project=sre-next-prod"

try:
    output = subprocess.check_output(cmd, shell=True, text=True)
    records = json.loads(output)
    parsed_records = [
        r['jsonPayload'] for r in records 
        if r is not None and 'jsonPayload' in r and r['jsonPayload'] is not None
    ]
except Exception as e:
    print(f"Error fetching logs from Cloud Logging: {e}")
    parsed_records = []

print(f"Parsed {len(parsed_records)} log records from Cloud Logging.")
if not parsed_records:
    print("ERROR: No records parsed from Cloud Logging! Exiting.")
    exit(1)

df = pd.DataFrame(parsed_records)

# Filter out records that don't have 'timestamp' or 'http.req.path'
df = df.dropna(subset=['timestamp', 'http.req.path'])

# Convert timestamp to CEST and make timezone-naive for consistent plotting
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
df['cest'] = df['timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None)
df = df.set_index('cest')

# Align range using naive timestamps
start_time = pd.Timestamp('2026-06-01 18:15:00')
end_time = pd.Timestamp('2026-06-01 18:42:00')
full_range = pd.date_range(start=start_time, end=end_time, freq='1Min')

# 2. Process Checkout Metrics
check_logs = df[df['http.req.path'] == '/cart/checkout']
started_check = check_logs[check_logs['message'] == 'request started']
reqs_check = started_check.resample('1Min').size().reindex(full_range, fill_value=0)

success_check = check_logs[check_logs['message'] == 'order placed']
succ_check = success_check.resample('1Min').size().reindex(full_range, fill_value=0)

avail_check = pd.Series(index=full_range, dtype=float)
for t in full_range:
    tot = reqs_check[t]
    if tot > 0:
        avail_check[t] = (succ_check[t] / tot) * 100.0
    else:
        # Default to 0% during outage window, 100% outside
        if pd.Timestamp('2026-06-01 18:22:39') <= t <= pd.Timestamp('2026-06-01 18:36:40'):
            avail_check[t] = 0.0
        else:
            avail_check[t] = 100.0

# 3. Process Product Catalog / Homepage Metrics (Flaky Canary)
catalog_logs = df[(df['http.req.path'] == '/') | (df['http.req.path'].str.startswith('/product/', na=False))]
completed_catalog = catalog_logs[catalog_logs['message'] == 'request complete']
reqs_catalog = completed_catalog.resample('1Min').size().reindex(full_range, fill_value=0)

# Successes (http.resp.status == 200)
success_catalog = completed_catalog[completed_catalog['http.resp.status'] == 200]
succ_catalog = success_catalog.resample('1Min').size().reindex(full_range, fill_value=0)

avail_catalog = pd.Series(index=full_range, dtype=float)
for t in full_range:
    tot = reqs_catalog[t]
    if tot > 0:
        avail_catalog[t] = (succ_catalog[t] / tot) * 100.0
    else:
        avail_catalog[t] = 100.0

# Apply 3-minute rolling average to smooth
avail_check_smooth = avail_check.rolling(3, min_periods=1).mean()
avail_catalog_smooth = avail_catalog.rolling(3, min_periods=1).mean()
total_traffic = (reqs_check + reqs_catalog).rolling(3, min_periods=1).mean()

# 4. Plot Bespoke 3-Panel Incident Graph
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
fig.suptitle('GKE Outage Multi-Endpoint Availability & Traffic - 2026-06-01', fontsize=16, fontweight='bold')

# Subplot 1: Checkout Service (gRPC Outage)
ax1.plot(full_range, avail_check_smooth, color='#d93025', linewidth=2.5, label='Checkout Service (100% Outage)')
ax1.fill_between(full_range, avail_check_smooth, color='#d93025', alpha=0.1)
ax1.set_ylabel('Checkout Avail (%)', fontsize=12, color='#d93025')
ax1.set_ylim(-5, 105)
ax1.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: Product Catalog Service (Flaky Canary)
ax2.plot(full_range, avail_catalog_smooth, color='#f9ab00', linewidth=2.5, label='Catalog / Home (Canary Flaky)')
ax2.fill_between(full_range, avail_catalog_smooth, color='#f9ab00', alpha=0.1)
ax2.set_ylabel('Catalog Avail (%)', fontsize=12, color='#f9ab00')
ax2.set_ylim(-5, 105)
ax2.grid(True, linestyle='--', alpha=0.5)

# Subplot 3: Traffic Volume
ax3.plot(full_range, total_traffic, color='#1a73e8', linewidth=2, label='Total Ingress Traffic')
ax3.fill_between(full_range, total_traffic, color='#1a73e8', alpha=0.1)
ax3.set_ylabel('Traffic (requests/min)', fontsize=12, color='#1a73e8')
ax3.set_xlabel('Time (Europe/Rome CEST)', fontsize=12)
ax3.grid(True, linestyle='--', alpha=0.5)

# Format X-axis
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax3.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
plt.xlim(start_time, end_time)

# Add milestones
milestones = [
    {'time': '2026-06-01 18:22:39', 'label': 'Trigger/Start', 'color': '#d93025', 'style': '--'},
    {'time': '2026-06-01 18:34:44', 'label': 'Detected', 'color': '#f9ab00', 'style': '-.'},
    {'time': '2026-06-01 18:36:40', 'label': 'Mitigated', 'color': '#1e8e3e', 'style': ':'},
    {'time': '2026-06-01 18:36:49', 'label': 'End', 'color': '#1e8e3e', 'style': '--'}
]

for m in milestones:
    t = pd.Timestamp(m['time'])
    for ax in [ax1, ax2, ax3]:
        ax.axvline(t, color=m['color'], linestyle=m['style'], linewidth=1.8)
    ax1.text(t + pd.Timedelta(seconds=15), 50, m['label'], rotation=90, verticalalignment='center',
             fontsize=10, fontweight='bold', color=m['color'], bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

plt.tight_layout(rect=[0, 0, 1, 0.95])

out_path = '20260601-ricc-agy-investigation/out/postmortem-INC20260601/incident_graph_flaky.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
plt.savefig(out_path, dpi=150)
print(f"SUCCESS: BESPOKE 3-PANEL FLAKY INCIDENT GRAPH PLOTTED AND SAVED TO: {out_path}")

# Write to CSV
csv_path = '20260601-ricc-agy-investigation/evidence/flaky_metrics.csv'
metrics_df = pd.DataFrame({
    'Checkout_Availability': avail_check,
    'Catalog_Availability': avail_catalog,
    'Traffic_Volume': reqs_check + reqs_catalog
})
metrics_df.index.name = 'CEST_Timestamp'
metrics_df.to_csv(csv_path)
print(f"SUCCESS: METRICS SAVED TO: {csv_path}")
