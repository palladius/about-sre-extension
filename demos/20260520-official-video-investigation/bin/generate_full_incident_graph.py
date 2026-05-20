import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import subprocess
import json
import sys
import os

out_path = '20260520-ricc-investigation/evidence/checkout_incident_graph_full.png'
csv_cache_path = '20260520-ricc-investigation/evidence/categorized_error_metrics.csv'

if os.path.exists(csv_cache_path):
    print(f"Loading data from local cache: {csv_cache_path}")
    pivot_df = pd.read_csv(csv_cache_path)
    pivot_df['timestamp'] = pd.to_datetime(pivot_df['timestamp'])
    pivot_df.set_index('timestamp', inplace=True)
else:
    # Fetch logs from just before the bad deployment to just after the fix
    cmd = [
        "gcloud", "logging", "read",
        'resource.type="k8s_container" resource.labels.namespace_name="default" severity>=ERROR timestamp>="2026-05-19T12:00:00Z" timestamp<="2026-05-20T14:00:00Z"',
        "--project=sre-next-prod",
        "--format=json(timestamp,jsonPayload.error)",
    ]

    print("Fetching 24 hours of error logs with payloads to plot the full timeline... this might take a moment.")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print("Error fetching logs:", res.stderr)
        sys.exit(1)

    try:
        logs = json.loads(res.stdout)
    except json.JSONDecodeError:
        print("Failed to parse logs JSON.")
        sys.exit(1)

    print(f"Fetched {len(logs)} error logs.")

    if len(logs) == 0:
        print("No logs found, cannot plot.")
        sys.exit(0)

    # Parse data and categorize errors
    data = []
    for log in logs:
        ts = log.get('timestamp')
        err_msg = log.get('jsonPayload', {}).get('error', '')
        
        category = 'Other'
        if 'name resolver error' in err_msg or 'productcatalog' in err_msg:
            category = 'Canary DNS Errors'
        elif 'connection timed out' in err_msg or 'dial tcp' in err_msg:
            category = 'Checkout Timeouts (Stable)'
            
        data.append({'timestamp': ts, 'category': category})

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Bucket into 5-minute intervals
    df['timestamp'] = df['timestamp'].dt.floor('5min')

    # Pivot table to get counts per category per timestamp
    pivot_df = df.pivot_table(index='timestamp', columns='category', aggfunc='size', fill_value=0)

    # Save to CSV for future runs
    pivot_df.to_csv(csv_cache_path)
    print(f"Saved categorized data to {csv_cache_path}")

# Reindex to ensure continuous timeline from 19:00 to 14:00
full_range = pd.date_range(start="2026-05-19 12:00:00", end="2026-05-20 14:00:00", freq='5min', tz='UTC')
pivot_df = pivot_df.reindex(full_range, fill_value=0)

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 7))

# Plot lines
colors = {
    'Canary DNS Errors': '#4285F4', # Google Blue
    'Checkout Timeouts (Stable)': '#34A853', # Google Green
    'Other': '#ffffff' # White for anything else
}

for col in pivot_df.columns:
    if col in colors:
        ax.plot(pivot_df.index, pivot_df[col], color=colors[col], linewidth=2, label=col)
        ax.fill_between(pivot_df.index, pivot_df[col], color=colors[col], alpha=0.3)

# Annotations (UTC)
milestones = [
    ('2026-05-19 19:59:49', 'Faulty Deployments (Trigger)', '#d93025'),
    ('2026-05-20 13:35:00', 'Investigation Started', '#f9ab00'),
    ('2026-05-20 13:37:31', 'Mitigation & Recovery', '#1e8e3e')
]

for time_str, label, color in milestones:
    dt = pd.to_datetime(time_str).tz_localize('UTC')
    ax.axvline(x=dt, color=color, linestyle='--', linewidth=2, zorder=3)
    ax.text(dt, ax.get_ylim()[1]*0.95, f" {label}", rotation=90, 
            verticalalignment='top', color=color, fontweight='bold',
            bbox=dict(facecolor='black', alpha=0.8, edgecolor='none'))

# Formatting
ax.set_title('Online Boutique Outage - Differentiated Error Types', fontsize=18, pad=20, color='white')
ax.set_ylabel('Error Count (5 min buckets)', fontsize=12)
ax.set_xlabel('Time (UTC)', fontsize=12)

date_form = DateFormatter("%b %d\n%H:%M")
ax.xaxis.set_major_formatter(date_form)
plt.xticks(rotation=0)

ax.grid(True, alpha=0.2, linestyle='--')
ax.legend(loc='upper left', frameon=True, facecolor='black', edgecolor='white')

plt.tight_layout()
plt.savefig(out_path, dpi=150, facecolor='black')
print(f"Graph saved to {out_path}")
