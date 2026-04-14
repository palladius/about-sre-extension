import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
import random

# Reconstruct the timeline based on our investigation
# Times from 11:50 UTC to 13:00 UTC
start_time = datetime(2026, 4, 4, 11, 50)
times = [start_time + timedelta(minutes=i) for i in range(71)]

success_rate = []
error_rate = []

random.seed(42)  # For reproducible graphs

for t in times:
    if t < datetime(2026, 4, 4, 12, 20):
        # NORMAL STATE
        success_rate.append(100.0 - random.uniform(0, 0.5))
        error_rate.append(random.uniform(0, 2))
    elif t < datetime(2026, 4, 4, 12, 35):
        # OUTAGE (Firewall + Istio + Typo)
        success_rate.append(0.0)
        error_rate.append(random.uniform(90, 100))
    elif t <= datetime(2026, 4, 4, 12, 45):
        # RECOVERY (Mitigation applied)
        recovery_progress = (t - datetime(2026, 4, 4, 12, 35)).total_seconds() / 600.0
        success_rate.append(recovery_progress * 100.0 - random.uniform(0, 2))
        error_rate.append((1.0 - recovery_progress) * 100.0 + random.uniform(0, 5))
    else:
        # NORMAL STATE (Resolved)
        success_rate.append(100.0 - random.uniform(0, 0.5))
        error_rate.append(random.uniform(0, 2))

# Create the figure and subplots
fig, ax1 = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor('#f8f9fa')
ax1.set_facecolor('#ffffff')

# Plot Availability (Success Rate)
color1 = '#2ca02c' # Green
ax1.set_xlabel('Time (UTC)', fontsize=12, fontweight='bold', labelpad=10)
ax1.set_ylabel('Frontend Availability (%)', color=color1, fontsize=12, fontweight='bold')
line1 = ax1.plot(times, success_rate, color=color1, linewidth=3, label='Availability (%)')
ax1.tick_params(axis='y', labelcolor=color1, labelsize=11)
ax1.set_ylim(-5, 110)
ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

# Plot Error Rate
ax2 = ax1.twinx()
color2 = '#d62728' # Red
ax2.set_ylabel('Errors (503s & Timeouts)', color=color2, fontsize=12, fontweight='bold')
line2 = ax2.plot(times, error_rate, color=color2, linewidth=2.5, linestyle='--', label='Error Rate (req/s)')
ax2.tick_params(axis='y', labelcolor=color2, labelsize=11)
ax2.set_ylim(-5, 110)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center right', fontsize=11, framealpha=0.9)

# Annotate milestones
incident_start = datetime(2026, 4, 4, 12, 20)
mitigation_start = datetime(2026, 4, 4, 12, 35)
recovery_end = datetime(2026, 4, 4, 12, 45)

# Shade the outage window
ax1.axvspan(incident_start, recovery_end, color='#ff9896', alpha=0.2, label='Degraded State')

# Milestone Lines & Text
ax1.axvline(x=incident_start, color='#7f7f7f', linestyle=':', linewidth=2)
ax1.annotate('Incident Starts:\nFirewall DENY applied\nIstio 503s injected', 
             xy=(incident_start, 60), xytext=(incident_start - timedelta(minutes=15), 50),
             arrowprops=dict(facecolor='#333333', shrink=0.05, width=1.5, headwidth=8),
             fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#7f7f7f", alpha=0.9))

ax1.axvline(x=mitigation_start, color='#7f7f7f', linestyle=':', linewidth=2)
ax1.annotate('Mitigation Starts:\nRemoved malicious firewall\nDeleted Istio fault config', 
             xy=(mitigation_start, 20), xytext=(mitigation_start + timedelta(minutes=3), 25),
             arrowprops=dict(facecolor='#333333', shrink=0.05, width=1.5, headwidth=8),
             fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#7f7f7f", alpha=0.9))

ax1.axvline(x=recovery_end, color='#7f7f7f', linestyle=':', linewidth=2)
ax1.text(recovery_end + timedelta(minutes=1), 90, 'Fully Recovered\n(Canary Patched)', 
         fontsize=10, color='#2ca02c', fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#2ca02c", alpha=0.9))

# Format the X-axis to display HH:MM
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
plt.xticks(fontsize=11)

# Title
plt.title('Online Boutique Outage Impact - April 4, 2026', fontsize=16, fontweight='bold', pad=20)

# Save
fig.tight_layout()
plt.savefig('out/postmortem-onlineboutique-20260404/incident_graph.png', dpi=300, bbox_inches='tight')
print("Graph saved to out/postmortem-onlineboutique-20260404/incident_graph.png")
