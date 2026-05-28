import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Load the raw logs
logs_file = "/Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/raw_frontend_logs.json"
print("Loading raw logs...")
with open(logs_file, 'r') as f:
    data = json.load(f)
print(f"Loaded {len(data)} log entries.")

# Extract relevant records
records = []
for entry in data:
    payload = entry.get('jsonPayload', {})
    if payload.get('message') == 'request complete':
        ts = payload.get('timestamp')
        status = payload.get('http.resp.status')
        path = payload.get('http.req.path', '')
        records.append({
            'timestamp': ts,
            'status': int(status) if status is not None else None,
            'path': path
        })

df = pd.DataFrame(records)
print(f"Extracted {len(df)} request complete records.")

# Convert timestamps to CEST
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['timestamp_cest'] = df['timestamp'].dt.tz_convert('Europe/Paris')
df['minute'] = df['timestamp_cest'].dt.floor('min')

# Create the full index from 16:00 to 16:50 CEST on 2026-05-28
start_time = pd.to_datetime('2026-05-28 16:00:00+02:00').tz_convert('Europe/Paris')
end_time = pd.to_datetime('2026-05-28 16:50:00+02:00').tz_convert('Europe/Paris')
full_time_range = pd.date_range(start=start_time, end=end_time, freq='1min')

# 1. Total Frontend Requests (Volume) per minute
frontend_volume = df.groupby('minute').size().reindex(full_time_range, fill_value=0)

# Calculate Overall Frontend Success Rate (%) (Success is any status that is NOT 500)
frontend_success_df = df[~df['status'].isin([500])]
frontend_successes = frontend_success_df.groupby('minute').size().reindex(full_time_range, fill_value=0)
frontend_success_rate = (frontend_successes / frontend_volume * 100).fillna(100.0)

# 2. Checkout Requests Volume and Success Rate per minute
checkout_df = df[df['path'] == '/cart/checkout']
checkout_volume = checkout_df.groupby('minute').size().reindex(full_time_range, fill_value=0)

# Success is status 200 or 422
checkout_success_df = checkout_df[checkout_df['status'].isin([200, 422])]
checkout_successes = checkout_success_df.groupby('minute').size().reindex(full_time_range, fill_value=0)

# Calculate Checkout Success Rate (%)
checkout_success_rate = (checkout_successes / checkout_volume * 100).fillna(100.0)

# Create a DataFrame for CSV export
metrics_df = pd.DataFrame({
    'Total_Frontend_Volume': frontend_volume,
    'Frontend_Success_Rate_Pct': frontend_success_rate,
    'Checkout_Volume': checkout_volume,
    'Checkout_Successes': checkout_successes,
    'Checkout_Success_Rate_Pct': checkout_success_rate
})
metrics_df.index.name = 'Timestamp_CEST'
csv_path = "/Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/checkout_metrics.csv"
metrics_df.to_csv(csv_path)
print(f"Exported metrics to CSV: {csv_path}")

# Function to plot the graph
def plot_graph(output_path, annotated=False):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Plot Success Rates (Top)
    ax1.plot(metrics_df.index, metrics_df['Checkout_Success_Rate_Pct'], color='#d62728', linewidth=2.5, label='Checkout Success Rate (%)')
    ax1.fill_between(metrics_df.index, metrics_df['Checkout_Success_Rate_Pct'], color='#d62728', alpha=0.08)
    
    ax1.plot(metrics_df.index, metrics_df['Frontend_Success_Rate_Pct'], color='#ff7f0e', linestyle='--', linewidth=2.0, label='Overall Frontend Success Rate (%)')
    
    ax1.set_ylabel('Success Rate (%)', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.set_ylim(-5, 105)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.set_title('Boutique Checkout Incident - 2026-05-28', fontsize=14, fontweight='bold')
    
    # Plot Volume (Bottom)
    ax2.plot(metrics_df.index, metrics_df['Total_Frontend_Volume'], color='#1f77b4', linewidth=2, label='Total Frontend Traffic')
    ax2.fill_between(metrics_df.index, metrics_df['Total_Frontend_Volume'], color='#1f77b4', alpha=0.15)
    
    # Add checkout volume for granularity
    ax2.plot(metrics_df.index, metrics_df['Checkout_Volume'], color='#2ca02c', linewidth=1.5, linestyle='--', label='Checkout Traffic')
    
    ax2.set_ylabel('Request Volume (Req/Min)', color='#1f77b4', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#1f77b4')
    ax2.set_xlabel('Time (CEST)', fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Format X axis timestamps nicely
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
    plt.xticks(rotation=45)
    
    if annotated:
        # Incident Milestones (CEST)
        milestones = [
            {'time': '2026-05-28 16:11:07', 'label': 'Trigger (Restrictive NetPol applied)', 'color': '#d62728', 'linestyle': '--'},
            {'time': '2026-05-28 16:34:28', 'label': 'Detected (Support Tickets escalated)', 'color': '#bcbd22', 'linestyle': '-.'},
            {'time': '2026-05-28 16:36:41', 'label': 'Mitigated (Faulty NetPol deleted)', 'color': '#2ca02c', 'linestyle': ':'},
            {'time': '2026-05-28 16:39:20', 'label': 'End (First Success + Pods recycled)', 'color': '#2ca02c', 'linestyle': '-'}
        ]
        
        for m in milestones:
            dt = pd.to_datetime(m['time']).tz_localize('Europe/Paris')
            # Add vertical lines to both axes
            ax1.axvline(dt, color=m['color'], linestyle=m['linestyle'], linewidth=1.5, alpha=0.8)
            ax2.axvline(dt, color=m['color'], linestyle=m['linestyle'], linewidth=1.5, alpha=0.8)
            
            # Position the text dynamically
            y_pos = 50 if 'Detected' in m['label'] else (75 if 'Trigger' in m['label'] else 25)
            ax1.text(dt + pd.Timedelta(seconds=30), y_pos, m['label'].split(' (')[0], rotation=90, verticalalignment='center',
                     fontsize=9, color='black', bbox=dict(facecolor='white', alpha=0.7, edgecolor=m['color'], boxstyle='round,pad=0.2'))
            
    # Add Legends at the end (strictly for Y-axes curves)
    ax1.legend(loc='lower left', framealpha=0.9, fontsize=8)
    ax2.legend(loc='upper right', framealpha=0.9, fontsize=8)
            
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved graph to {output_path}")

# Plot Draft Graph
draft_path = "/Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/incident_graph_draft.png"
plot_graph(draft_path, annotated=False)

# Plot Final Annotated Graph
final_path = "/Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/incident_graph_final.png"
plot_graph(final_path, annotated=True)

print("Done generating graphs!")
