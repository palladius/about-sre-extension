import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os

# Ensure evidence dir exists
os.makedirs("20260519-ricc-investigation/evidence", exist_ok=True)

# REAL DATA from Cloud Monitoring (aggregated hourly)
data = {
    'timestamp': [
        "2026-05-18 22:00:00", "2026-05-18 23:00:00", "2026-05-19 00:00:00", 
        "2026-05-19 01:00:00", "2026-05-19 02:00:00", "2026-05-19 03:00:00", 
        "2026-05-19 04:00:00", "2026-05-19 05:00:00", "2026-05-19 06:00:00", 
        "2026-05-19 07:00:00", "2026-05-19 08:00:00", "2026-05-19 09:00:00", 
        "2026-05-19 10:00:00", "2026-05-19 11:00:00", "2026-05-19 12:00:00", 
        "2026-05-19 13:00:00", "2026-05-19 14:00:00"
    ],
    'errors': [120, 23, 1120, 5350, 5406, 5417, 5373, 5708, 5484, 5562, 5371, 5423, 5572, 5505, 4843, 7, 2],
    'info': [98619, 98340, 89238, 64289, 63772, 63928, 63138, 70340, 64063, 64266, 63783, 63598, 64434, 64534, 68906, 26906, 10000]
}

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')

# Calculate Availability Proxy
df['total'] = df['info'] + df['errors']
df['availability'] = 100 * (1 - df['errors'] / df['total'])

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# Top: Availability
ax1.plot(df.index, df['availability'], color='#d93025', linewidth=3, label='Availability % (Success Rate)')
ax1.fill_between(df.index, df['availability'], 100, color='#d93025', alpha=0.1)
ax1.set_ylim(80, 101) # Zoom in to show the drop clearly
ax1.set_ylabel('Availability (%)', fontsize=12, fontweight='bold')
ax1.grid(True, which='both', linestyle='--', alpha=0.5)
ax1.set_title('Online Boutique - Global Checkout Outage (2026-05-19)', fontsize=18, fontweight='bold', pad=25)
ax1.legend(loc='lower left')

# Bottom: Volume
ax2.bar(df.index, df['errors'], color='#d93025', alpha=0.8, label='Error Log Volume', width=0.03)
ax2.plot(df.index, df['info'], color='#1a73e8', linewidth=2, label='Normal Traffic (INFO)', alpha=0.5)
ax2.set_ylabel('Logs / Hour', fontsize=12, fontweight='bold')
ax2.set_xlabel('Time (UTC)', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.3)

# Formatting X-axis
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))

# Incident Milestones
START_INCIDENT = datetime(2026, 5, 19, 0, 46, 22)
DETECTION = datetime(2026, 5, 19, 10, 0, 0)
MITIGATION = datetime(2026, 5, 19, 12, 57, 0)
END_INCIDENT = datetime(2026, 5, 19, 13, 10, 0)

milestones = [
    (START_INCIDENT, 'Rollout Trigger', '#d93025', '-'),
    (DETECTION, 'Detection', '#f9ab00', '--'),
    (MITIGATION, 'Policy Deleted', '#1e8e3e', '--'),
    (END_INCIDENT, 'Resolved', '#1e8e3e', '-')
]

for ts, label, color, style in milestones:
    ax1.axvline(x=ts, color=color, linestyle=style, linewidth=2.5)
    ax2.axvline(x=ts, color=color, linestyle=style, linewidth=2.5)
    ax1.text(ts + timedelta(minutes=15), 85, label, color=color, rotation=90, 
             verticalalignment='bottom', fontweight='bold', fontsize=10,
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

plt.tight_layout()
plt.savefig('20260519-ricc-investigation/evidence/checkout_incident_graph.png', dpi=150)
print("Graph saved to 20260519-ricc-investigation/evidence/checkout_incident_graph.png")
