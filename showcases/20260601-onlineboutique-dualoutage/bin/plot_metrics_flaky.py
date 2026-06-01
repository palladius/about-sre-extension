import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Load checkout logs
print("Loading checkout logs...")
checkout_path = '20260601-ricc-agy-investigation/evidence/frontend_checkout_logs.json'
df_check = pd.read_json(checkout_path)
pay_check = pd.json_normalize(df_check['jsonPayload'])
pay_check['timestamp'] = pd.to_datetime(pay_check['timestamp'], utc=True)
pay_check['pdt'] = pay_check['timestamp'].dt.tz_convert('US/Pacific')
pay_check = pay_check.set_index('pdt')

# 2. Resample checkout metrics
started_check = pay_check[pay_check['message'] == 'request started']
reqs_check = started_check.resample('1Min').size()
success_check = pay_check[pay_check['message'] == 'order placed']
succ_check = success_check.resample('1Min').size()

# Align range
start_time = pd.Timestamp('2026-06-01 01:00:00', tz='US/Pacific')
end_time = pd.Timestamp('2026-06-01 09:15:00', tz='US/Pacific')
full_range = pd.date_range(start=start_time, end=end_time, freq='1Min', tz='US/Pacific')

reqs_check = reqs_check.reindex(full_range, fill_value=0)
succ_check = succ_check.reindex(full_range, fill_value=0)

# Calculate checkout availability
avail_check = pd.Series(index=full_range, dtype=float)
for t in full_range:
    tot = reqs_check[t]
    if tot > 0:
        avail_check[t] = (succ_check[t] / tot) * 100.0
    else:
        if pd.Timestamp('2026-06-01 01:20:23', tz='US/Pacific') <= t <= pd.Timestamp('2026-06-01 08:51:21', tz='US/Pacific'):
            avail_check[t] = 0.0
        else:
            avail_check[t] = 100.0

# 3. Load homepage & product catalog logs
print("Loading homepage/product logs...")
home_path = '20260601-ricc-agy-investigation/evidence/frontend_homepage_logs.csv'

df_home = pd.read_csv(home_path)
df_home['timestamp'] = pd.to_datetime(df_home['timestamp'], utc=True)
df_home['pdt'] = df_home['timestamp'].dt.tz_convert('US/Pacific')
df_home = df_home.set_index('pdt')

# Since we only downloaded 'request complete' logs, total requests is all of them
reqs_home = df_home.resample('1Min').size()

# Successes (http.resp.status == 200)
success_home = df_home[df_home['http.resp.status'] == 200]
succ_home = success_home.resample('1Min').size()

reqs_home = reqs_home.reindex(full_range, fill_value=0)
succ_home = succ_home.reindex(full_range, fill_value=0)

# Calculate homepage availability
avail_home = pd.Series(index=full_range, dtype=float)
for t in full_range:
    tot = reqs_home[t]
    if tot > 0:
        avail_home[t] = (succ_home[t] / tot) * 100.0
    else:
        avail_home[t] = 100.0

# Apply rolling average to smooth
avail_check_smooth = avail_check.rolling(5, min_periods=1).mean()
avail_home_smooth = avail_home.rolling(5, min_periods=1).mean()
reqs_total_smooth = (reqs_check + reqs_home).rolling(5, min_periods=1).mean()

# 4. Plot both availability curves side-by-side
print("Plotting dual availability graphs...")
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
fig.suptitle('GKE Outage Multi-Endpoint Availability - 2026-06-01', fontsize=16, fontweight='bold')

# Subplot 1: Checkout Service (100 -> 0 -> 100)
ax1.plot(full_range, avail_check_smooth, color='#d93025', linewidth=2.5, label='Checkout Service (gRPC blocked)')
ax1.fill_between(full_range, avail_check_smooth, color='#d93025', alpha=0.1)
ax1.set_ylabel('Checkout Avail (%)', fontsize=12, color='#d93025')
ax1.set_ylim(-5, 105)
ax1.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: Product Catalog Endpoint (100 -> ~66.7 -> 100)
ax2.plot(full_range, avail_home_smooth, color='#f9ab00', linewidth=2.5, label='Product Catalog Service (Flaky Canary)')
ax2.fill_between(full_range, avail_home_smooth, color='#f9ab00', alpha=0.1)
ax2.set_ylabel('Catalog Avail (%)', fontsize=12, color='#f9ab00')
ax2.set_ylim(-5, 105)
ax2.grid(True, linestyle='--', alpha=0.5)

# Subplot 3: Traffic Volume
ax3.plot(full_range, reqs_total_smooth, color='#1a73e8', linewidth=2, label='Total Ingress Traffic')
ax3.fill_between(full_range, reqs_total_smooth, color='#1a73e8', alpha=0.1)
ax3.set_ylabel('Total requests/min', fontsize=12, color='#1a73e8')
ax3.set_xlabel('Time (US/Pacific PDT)', fontsize=12)
ax3.grid(True, linestyle='--', alpha=0.5)

# Format axes
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax3.xaxis.set_major_locator(mdates.HourLocator(interval=1))
plt.xlim(start_time, end_time)

# Add milestones
milestones = [
    {'time': '2026-06-01 01:20:19', 'label': 'Trigger/Start', 'color': '#d93025', 'style': '--'},
    {'time': '2026-06-01 08:48:19', 'label': 'Detected', 'color': '#f9ab00', 'style': '-.'},
    {'time': '2026-06-01 08:49:31', 'label': 'Mitigated', 'color': '#1e8e3e', 'style': ':'},
    {'time': '2026-06-01 08:51:21', 'label': 'End', 'color': '#1e8e3e', 'style': '--'}
]

for m in milestones:
    t = pd.Timestamp(m['time'], tz='US/Pacific')
    for ax in [ax1, ax2, ax3]:
        ax.axvline(t, color=m['color'], linestyle=m['style'], linewidth=1.8)
    ax1.text(t + pd.Timedelta(minutes=5), 50, m['label'], rotation=90, verticalalignment='center',
             fontsize=10, fontweight='bold', color=m['color'], bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

plt.tight_layout(rect=[0, 0, 1, 0.95])

out_path = '20260601-ricc-agy-investigation/out/postmortem-20260601-outage/incident_graph_rev2.png'
plt.savefig(out_path, dpi=150)
print(f"SUCCESS: DUAL OUTAGE GRAPH PLOTTED AND SAVED TO: {out_path}")
