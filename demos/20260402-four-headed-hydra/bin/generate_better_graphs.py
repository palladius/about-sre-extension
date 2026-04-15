import os
from datetime import datetime, timezone, timedelta
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from google.cloud import monitoring_v3

# Set timezone to UTC for labeling
target_tz = timezone.utc

def fetch_metric(project_id, filter_str, start_time, end_time, label_name=None):
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(end_time.timestamp())},
        "start_time": {"seconds": int(start_time.timestamp())},
    })
    
    aggregation_dict = {
        "alignment_period": {"seconds": 600}, # 10 min
        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
        "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_SUM,
    }
    if label_name:
        aggregation_dict["group_by_fields"] = [label_name]
        
    aggregation = monitoring_v3.Aggregation(aggregation_dict)
    
    results = client.list_time_series(request={
        "name": project_name,
        "filter": filter_str,
        "interval": interval,
        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        "aggregation": aggregation,
    })
    data = []
    for series in results:
        label_val = "total"
        if label_name:
            label_val = series.metric.labels.get(label_name.split('.')[-1], "unknown")
        for point in series.points:
            data.append({"time": point.interval.end_time.timestamp(), "label": label_val, "value": point.value.double_value})
    return pd.DataFrame(data)

project_id = "sre-next"
now = datetime.now(timezone.utc)
end_t = now
start_t = end_t - timedelta(hours=24) 

plt.figure(figsize=(15, 10))

# Subplot 1: Frontend Traffic
print("Fetching Frontend Traffic...")
df_fe = fetch_metric(project_id, 
                  'metric.type="istio.io/service/server/request_count" AND resource.labels.namespace_name="default" AND metric.labels.destination_workload_name="frontend"',
                  start_t, end_t, "metric.labels.response_code")

ax1 = plt.subplot(2, 1, 1)
if not df_fe.empty:
    df_fe['time'] = pd.to_datetime(df_fe['time'], unit='s', utc=True).dt.tz_convert(target_tz)
    pivot_fe = df_fe.groupby(['time', 'label']).sum().reset_index().pivot(index='time', columns='label', values='value').fillna(0)
    
    if '200' in pivot_fe.columns:
        plt.plot(pivot_fe.index, pivot_fe['200'], label='Success (200 OK)', color='green')
    
    err_5xx = [c for c in pivot_fe.columns if c.startswith('5')]
    if err_5xx:
        plt.plot(pivot_fe.index, pivot_fe[err_5xx].sum(axis=1), label='Errors (5xx)', color='red')

plt.title("Frontend Ingress Traffic (Requests/sec)")
plt.ylabel("QPS")
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %Z'))
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 2: Internal gRPC Errors
print("Fetching Checkout Errors...")
df_checkout = fetch_metric(project_id, 
                  'metric.type="istio.io/service/server/request_count" AND resource.labels.namespace_name="default" AND metric.labels.destination_service_name="checkoutservice"',
                  start_t, end_t, "metric.labels.response_code")

ax2 = plt.subplot(2, 1, 2)
if not df_checkout.empty:
    df_checkout['time'] = pd.to_datetime(df_checkout['time'], unit='s', utc=True).dt.tz_convert(target_tz)
    pivot_chk = df_checkout.groupby(['time', 'label']).sum().reset_index().pivot(index='time', columns='label', values='value').fillna(0)
    
    if '503' in pivot_chk.columns:
        plt.plot(pivot_chk.index, pivot_chk['503'], label='Checkout 503 (Blackhole)', color='purple', linewidth=2)
    
    df_otel = fetch_metric(project_id, 
                  'metric.type="istio.io/service/server/request_count" AND metric.labels.destination_service_name="opentelemetrycollector"',
                  start_t, end_t, "metric.labels.response_code")
    if not df_otel.empty:
         df_otel['time'] = pd.to_datetime(df_otel['time'], unit='s', utc=True).dt.tz_convert(target_tz)
         pivot_otel = df_otel.groupby(['time', 'label']).sum().reset_index().pivot(index='time', columns='label', values='value').fillna(0)
         plt.plot(pivot_otel.index, pivot_otel.sum(axis=1), label='OTel Collector Traffic', color='orange', linestyle='--')

plt.title("Root Cause Correlation: Checkout Blackhole & OTel Traffic")
plt.ylabel("QPS")
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %Z'))
plt.legend()
plt.grid(True, alpha=0.3)

# Add Remediation Markers
fix_time = (now - timedelta(minutes=10)).replace(tzinfo=timezone.utc).astimezone(target_tz)
plt.axvline(x=fix_time, color='blue', linestyle='-.', label='Remediation Applied')

plt.tight_layout()
save_path = "20260402-investigation/postmortem-online-boutique/improved_incident_graphs.png"
plt.savefig(save_path)
print(f"Improved graphs saved to {save_path}")
