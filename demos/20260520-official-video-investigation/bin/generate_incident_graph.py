import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import os

csv_path = '20260520-ricc-investigation/evidence/error_metrics.csv'
out_path = '20260520-ricc-investigation/evidence/checkout_incident_graph.png'

# Read CSV and parse dates
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# Ensure continuity (reindex just in case)
full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='1min')
df = df.reindex(full_range, fill_value=0)

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(12, 6))

# Plot the area
ax.fill_between(df.index, df['count'], color='#d93025', alpha=0.3)
ax.plot(df.index, df['count'], color='#d93025', linewidth=2, label='Frontend Errors/min')

# Annotations (UTC)
milestones = [
    ('13:32:30', 'Impact Started', '#d93025'),
    ('13:35:00', 'Investigation Started', '#f9ab00'),
    ('13:36:45', 'Mitigation Applied', '#1e8e3e'),
    ('13:37:31', 'Verified & Resolved', '#1e8e3e')
]

for time_str, label, color in milestones:
    dt = pd.to_datetime(f"2026-05-20 {time_str}")
    ax.axvline(x=dt, color=color, linestyle='--', linewidth=2, zorder=3)
    ax.text(dt, ax.get_ylim()[1]*0.95, f" {label}", rotation=90, 
            verticalalignment='top', color=color, fontweight='bold',
            bbox=dict(facecolor='black', alpha=0.7, edgecolor='none'))

# Formatting
ax.set_title('Online Boutique Checkout Incident - 2026-05-20', fontsize=16, pad=20, color='white')
ax.set_ylabel('Error Count (per minute)', fontsize=12)
ax.set_xlabel('Time (UTC)', fontsize=12)

# X-axis time formatting
date_form = DateFormatter("%H:%M")
ax.xaxis.set_major_formatter(date_form)
plt.xticks(rotation=45)

ax.grid(True, alpha=0.2)
ax.legend(loc='upper right')

plt.tight_layout()
plt.savefig(out_path, dpi=150, facecolor='black')
print(f"Graph saved to {out_path}")
