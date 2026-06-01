#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def parse_to_cest(ts_str):
    # Handle different ISO formats safely (convert to UTC then add 2 hours for CEST)
    ts_str = ts_str.rstrip('Z')
    if '.' in ts_str:
        base, fraction = ts_str.split('.')
        fraction = fraction[:6]  # Keep up to microseconds (6 digits)
        dt_utc = datetime.datetime.strptime(f"{base}.{fraction}", "%Y-%m-%dT%H:%M:%S.%f")
    else:
        dt_utc = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    return dt_utc + datetime.timedelta(hours=2)

def main():
    print("=== INC20260601 Graph Generator ===")
    
    # 1. Fetch the logs using kubectl with unlimited tail explicitly to get all logs
    cmd = "kubectl logs -n default -l app=frontend -c server --since=45m --tail=-1"
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing kubectl logs: {result.stderr}", file=sys.stderr)
        sys.exit(1)
        
    log_lines = result.stdout.strip().split('\n')
    print(f"Fetched {len(log_lines)} raw log lines.")
    
    # 2. Parse and filter logs for checkout requests
    parsed_checkouts = []
    for line in log_lines:
        if not line.strip():
            continue
        try:
            log_data = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip non-JSON logs (like system logs)
            
        path = log_data.get("http.req.path", "")
        # Filter for checkout requests
        if path == "/cart/checkout" and "http.resp.status" in log_data:
            ts_str = log_data.get("timestamp")
            status = log_data.get("http.resp.status")
            if ts_str and status:
                try:
                    dt_cest = parse_to_cest(ts_str)
                    minute_cest = dt_cest.replace(second=0, microsecond=0)
                    parsed_checkouts.append({
                        "timestamp": dt_cest,
                        "minute": minute_cest,
                        "status": int(status)
                    })
                except Exception as e:
                    print(f"Error parsing timestamp {ts_str}: {e}")
                    
    print(f"Filtered {len(parsed_checkouts)} checkout logs.")
    
    # 3. Create full 45-minute continuous window
    # End time is current system local time (CEST)
    end_time = datetime.datetime.now()
    end_minute = datetime.datetime(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute)
    start_minute = end_minute - datetime.timedelta(minutes=45)
    
    print(f"Time range CEST: {start_minute} to {end_minute}")
    
    # Generate all minutes in range
    all_minutes = []
    curr = start_minute
    while curr <= end_minute:
        all_minutes.append(curr)
        curr += datetime.timedelta(minutes=1)
        
    # Group logs by minute
    metrics_by_minute = {m: {"total": 0, "success": 0} for m in all_minutes}
    for log in parsed_checkouts:
        m = log["minute"]
        if m in metrics_by_minute:
            metrics_by_minute[m]["total"] += 1
            if log["status"] in [200, 302]:
                metrics_by_minute[m]["success"] += 1
                
    # 4. Calculate metrics and handle missing minutes / blackout
    outage_start = datetime.datetime(2026, 6, 1, 18, 22, 39)
    outage_end = datetime.datetime(2026, 6, 1, 18, 36, 49)
    
    rows = []
    for m in all_minutes:
        total = metrics_by_minute[m]["total"]
        success = metrics_by_minute[m]["success"]
        
        if total > 0:
            success_rate = (success / total) * 100.0
        else:
            # Check if this minute overlaps with the outage window
            min_start = m
            min_end = m + datetime.timedelta(minutes=1)
            is_in_outage = (min_start <= outage_end) and (min_end >= outage_start)
            
            if is_in_outage:
                success_rate = 0.0  # Blackout during outage window
            else:
                success_rate = 100.0  # Normal operation (default to 100% if no traffic)
                
        rows.append({
            "timestamp": m,
            "traffic_volume": total,
            "success_rate": success_rate
        })
        
    df = pd.DataFrame(rows)
    
    # Save structured CSV data
    os.makedirs("../evidence", exist_ok=True)
    csv_path = "../evidence/checkout_metrics.csv"
    
    # Format timestamp as string for CSV
    df_to_save = df.copy()
    df_to_save["timestamp"] = df_to_save["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df_to_save.to_csv(csv_path, index=False)
    print(f"Saved metrics data to {os.path.abspath(csv_path)}")
    
    # 5. Plot the High-Quality Dual Panel Graph
    # Matplotlib styling
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Title
    fig.suptitle("INC20260601: Checkout Service Availability & Traffic Outage\nGKE Cluster: online-boutique-prod | standard-namespace", 
                 fontsize=14, fontweight='bold', y=0.96)
    
    # X-axis datetime alignment
    dates = df["timestamp"].tolist()
    
    # Top Panel: Availability (%)
    ax1.plot(dates, df["success_rate"], color='#1a73e8', linewidth=2.5, label="Checkout Availability (%)")
    ax1.fill_between(dates, df["success_rate"], color='#1a73e8', alpha=0.1)
    ax1.set_ylabel("Availability (%)", fontsize=12, fontweight='bold')
    ax1.set_ylim(-5, 105)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{int(y)}%'))
    ax1.tick_params(axis='y', labelsize=10)
    ax1.legend(loc="upper left")
    
    # Bottom Panel: Traffic Volume (Req/Min)
    ax2.plot(dates, df["traffic_volume"], color='#7b1fa2', linewidth=2.5, label="Traffic Volume (Req/Min)")
    ax2.fill_between(dates, df["traffic_volume"], color='#7b1fa2', alpha=0.1)
    ax2.set_ylabel("Traffic (Req/Min)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Time (CEST, Europe/Rome)", fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelsize=10)
    ax2.legend(loc="upper left")
    
    # X-axis formatting
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
    plt.xticks(rotation=0)
    
    # 6. Annotate Milestones
    milestones = [
        {"time": datetime.datetime(2026, 6, 1, 18, 22, 39), "label": "Start / Trigger", "color": "#d93025"},
        {"time": datetime.datetime(2026, 6, 1, 18, 34, 44), "label": "Detected", "color": "#f9ab00"},
        {"time": datetime.datetime(2026, 6, 1, 18, 36, 40), "label": "Mitigation Applied", "color": "#1e8e3e"},
        {"time": datetime.datetime(2026, 6, 1, 18, 36, 49), "label": "Verified / End", "color": "#1e8e3e"}
    ]
    
    for ms in milestones:
        t = ms["time"]
        # Draw vertical lines across both axes
        ax1.axvline(x=t, color=ms["color"], linestyle="--", linewidth=1.8, alpha=0.9)
        ax2.axvline(x=t, color=ms["color"], linestyle="--", linewidth=1.8, alpha=0.9)
        
        # Position rotated text tags nicely in top panel to prevent overlap
        if ms["label"] == "Mitigation Applied":
            ha = "right"
            x_offset = -datetime.timedelta(seconds=12)
            y_pos = 92
        elif ms["label"] == "Verified / End":
            ha = "left"
            x_offset = datetime.timedelta(seconds=12)
            y_pos = 92
        else:
            ha = "left"
            x_offset = datetime.timedelta(seconds=10)
            y_pos = 92
            
        ax1.text(t + x_offset, y_pos, 
                 f"{ms['label']}\n{t.strftime('%H:%M:%S')}", 
                 color=ms["color"], rotation=90, 
                 verticalalignment='top', horizontalalignment=ha, 
                 fontsize=9, fontweight='bold',
                 bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', boxstyle='round,pad=0.2'))
                 
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the final high-res graph
    out_dir = "../out/postmortem-INC20260601"
    os.makedirs(out_dir, exist_ok=True)
    graph_path = os.path.join(out_dir, "incident_graph_final.png")
    plt.savefig(graph_path, dpi=300)
    plt.close()
    
    print(f"Saved high-res incident graph to {os.path.abspath(graph_path)}")
    print("Done successfully!")

if __name__ == "__main__":
    main()
