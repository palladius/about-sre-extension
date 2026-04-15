import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

# Time generation (17:30 to 18:15 CEST)
start_time = datetime(2026, 4, 2, 17, 30)
end_time = datetime(2026, 4, 2, 18, 15)
times = [start_time + timedelta(minutes=i) for i in range(int((end_time - start_time).total_seconds() / 60))]

# Synthetic data generation
frontend_errors = []
checkout_errors = []

for t in times:
    # Frontend errors (start at 17:49, end at 18:04)
    if datetime(2026, 4, 2, 17, 49) <= t < datetime(2026, 4, 2, 18, 4):
        frontend_errors.append(50 + np.random.normal(0, 2))
    else:
        frontend_errors.append(np.random.normal(0.5, 0.2))
        
    # Checkout errors (start at 17:43, end at 18:04)
    if datetime(2026, 4, 2, 17, 43) <= t < datetime(2026, 4, 2, 18, 4):
        checkout_errors.append(100)
    else:
        checkout_errors.append(np.random.normal(0.2, 0.1))

# Clamp to 0-100
frontend_errors = np.clip(frontend_errors, 0, 100)
checkout_errors = np.clip(checkout_errors, 0, 100)

# Plotting
plt.figure(figsize=(14, 7))

# Check if seaborn is available, otherwise fallback
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    plt.style.use('ggplot')

# Shaded regions for states (to please Ben Treynor: GOOD -> BREAKING -> GOOD)
plt.axvspan(start_time, datetime(2026, 4, 2, 17, 43), color='#2ecc71', alpha=0.15, label='GOOD State')
plt.axvspan(datetime(2026, 4, 2, 17, 43), datetime(2026, 4, 2, 18, 4), color='#e74c3c', alpha=0.15, label='BREAKING (Outage)')
plt.axvspan(datetime(2026, 4, 2, 18, 4), end_time, color='#2ecc71', alpha=0.15, label='RECOVERING / GOOD')

# Lines
plt.plot(times, frontend_errors, label='Frontend 500 Error Rate (%)', color='#c0392b', linewidth=3)
plt.plot(times, checkout_errors, label='Checkout 503 Error Rate (%)', color='#8e44ad', linewidth=3, linestyle='--')

# Annotations (Key Milestones)
annotations = [
    (datetime(2026, 4, 2, 17, 43), 'Checkout Blackhole Configured', '#d35400'),
    (datetime(2026, 4, 2, 17, 46), 'Customer Reports 500s (Detection)', '#f39c12'),
    (datetime(2026, 4, 2, 17, 49), 'Misconfigured Canary Deployed', '#c0392b'),
    (datetime(2026, 4, 2, 18, 4), 'Mitigation (Rollback)', '#27ae60')
]

for time, text, color in annotations:
    plt.axvline(x=time, color=color, linestyle='-', linewidth=2.5, alpha=0.8)
    plt.text(time - timedelta(minutes=0.5), 103, text, rotation=45, verticalalignment='bottom', 
             horizontalalignment='right', color=color, fontweight='bold', fontsize=11, 
             bbox=dict(facecolor='white', edgecolor=color, boxstyle='round,pad=0.3', alpha=0.9))

plt.title('System Availability: microservice-demo Error Rates (April 2, 2026)', fontsize=18, fontweight='bold', pad=30)
plt.xlabel('Time (CEST)', fontsize=14, fontweight='bold')
plt.ylabel('Error Rate (%)', fontsize=14, fontweight='bold')
plt.ylim(-5, 115)
plt.legend(loc='center left', fontsize=12, framealpha=0.9)
plt.grid(True, alpha=0.3)

# Formatting x-axis
ax = plt.gca()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

plt.tight_layout()
plt.savefig('out/postmortem-demo03-500s/incident_graph.png', dpi=300, bbox_inches='tight')
print("Graph successfully generated at out/postmortem-demo03-500s/incident_graph.png")
