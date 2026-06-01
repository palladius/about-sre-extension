import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Load raw frontend checkout logs
json_path = '20260601-ricc-agy-investigation/evidence/frontend_checkout_logs.json'
df = pd.read_json(json_path)

# Normalize jsonPayload
payloads = pd.json_normalize(df['jsonPayload'])
payloads['timestamp'] = pd.to_datetime(payloads['timestamp'], utc=True)
payloads['pdt'] = payloads['timestamp'].dt.tz_convert('US/Pacific')

# Set index to pdt
payloads = payloads.set_index('pdt')

# 2. Resample by minute to count requests and successes
# Total requests started
started = payloads[payloads['message'] == 'request started']
reqs_per_min = started.resample('1Min').size()

# Successes (order placed)
successes = payloads[payloads['message'] == 'order placed']
succ_per_min = successes.resample('1Min').size()

# Align indices using a complete minute range
start_time = pd.Timestamp('2026-06-01 00:00:00', tz='US/Pacific')
end_time = pd.Timestamp('2026-06-01 10:00:00', tz='US/Pacific')
full_range = pd.date_range(start=start_time, end=end_time, freq='1Min', tz='US/Pacific')

reqs_per_min = reqs_per_min.reindex(full_range, fill_value=0)
succ_per_min = succ_per_min.reindex(full_range, fill_value=0)

# 3. Calculate Availability % (Success Rate) per minute
availability = pd.Series(index=full_range, dtype=float)
for t in full_range:
    total = reqs_per_min[t]
    if total > 0:
        availability[t] = (succ_per_min[t] / total) * 100.0
    else:
        # Default to 100% when there is no traffic (unless during blackout period)
        if pd.Timestamp('2026-06-01 01:20:23', tz='US/Pacific') <= t <= pd.Timestamp('2026-06-01 08:51:21', tz='US/Pacific'):
            availability[t] = 0.0
        else:
            availability[t] = 100.0

# 5-minute rolling average for smooth curve
avail_smooth = availability.rolling(5, min_periods=1).mean()
reqs_smooth = reqs_per_min.rolling(5, min_periods=1).mean()

# 4. Create bespoke GKE incident graph
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
fig.suptitle('GKE Outage Metrics - 2026-06-01 Cart Checkout Failure', fontsize=16, fontweight='bold')

# Subplot 1: Success Rate (Availability %)
ax1.plot(full_range, avail_smooth, color='#d93025', linewidth=2.5, label='Checkout Success Rate (%)')
ax1.fill_between(full_range, avail_smooth, color='#d93025', alpha=0.1)
ax1.set_ylabel('Availability (%)', fontsize=12, color='#d93025')
ax1.set_ylim(-5, 105)
ax1.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: Traffic Volume (Requests/Min)
ax2.plot(full_range, reqs_smooth, color='#1a73e8', linewidth=2, label='Checkout Traffic Volume')
ax2.fill_between(full_range, reqs_smooth, color='#1a73e8', alpha=0.1)
ax2.set_ylabel('Traffic (requests/min)', fontsize=12, color='#1a73e8')
ax2.set_xlabel('Time (US/Pacific PDT)', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.5)

# 5. Format X-axis
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))
plt.xlim(start_time, end_time)

# 6. Add Milestones & Annotations
milestones = [
    {'time': '2026-06-01 01:20:19', 'label': 'Trigger/Start', 'color': '#d93025', 'style': '--'},
    {'time': '2026-06-01 08:48:19', 'label': 'Detected', 'color': '#f9ab00', 'style': '-.'},
    {'time': '2026-06-01 08:49:31', 'label': 'Mitigated', 'color': '#1e8e3e', 'style': ':'},
    {'time': '2026-06-01 08:51:21', 'label': 'End', 'color': '#1e8e3e', 'style': '--'}
]

for m in milestones:
    t = pd.Timestamp(m['time'], tz='US/Pacific')
    # Draw vertical lines on both subplots
    ax1.axvline(t, color=m['color'], linestyle=m['style'], linewidth=1.8)
    ax2.axvline(t, color=m['color'], linestyle=m['style'], linewidth=1.8)
    
    # Annotate labels
    ax1.text(t + pd.Timedelta(minutes=5), 50, m['label'], rotation=90, verticalalignment='center',
             fontsize=10, fontweight='bold', color=m['color'], bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save final graph
os.makedirs('20260601-ricc-agy-investigation/out/postmortem-20260601-outage', exist_ok=True)
out_path = '20260601-ricc-agy-investigation/out/postmortem-20260601-outage/incident_graph_rev1.png'
plt.savefig(out_path, dpi=150)
print(f"SUCCESS: BESPOKE INCIDENT GRAPH PLOTTED AND SAVED TO: {out_path}")
