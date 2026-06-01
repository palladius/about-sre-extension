#!/usr/bin/env python3
import json
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def generate_graph(json_file, output_file):
    print(f"Reading logs from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)

    records = []
    for entry in data:
        payload = entry.get('jsonPayload', {})
        # Extract timestamp from jsonPayload or resource/entry
        ts_str = payload.get('timestamp') or entry.get('timestamp')
        if not ts_str:
            continue
        
        status = payload.get('http.req.id') # wait, let's look at status field: jsonPayload.http.resp.status
        # In frontend request complete:
        status_code = payload.get('http.resp.status')
        if status_code is None:
            # Maybe it's a fallback, let's check
            continue
        
        # Parse timestamp
        dt = pd.to_datetime(ts_str)
        records.append({
            'Time': dt,
            'Status': int(status_code)
        })

    if not records:
        print("Error: No valid records found in the JSON file!")
        sys.exit(1)

    df = pd.DataFrame(records)
    # Convert to UTC and make tz-naive for matplotlib compatibility
    df['Time'] = df['Time'].dt.tz_convert('UTC').dt.tz_localize(None)
    
    # Success is defined as HTTP status code 200
    df['Success'] = df['Status'] == 200
    df['Failure'] = df['Status'] != 200

    # Define the precise range we want to plot (15:35:00 UTC to 17:55:00 UTC)
    start_range = pd.to_datetime('2026-05-28 15:35:00')
    end_range = pd.to_datetime('2026-05-28 17:55:00')
    
    # Floor timestamps to the minute
    df['Minute'] = df['Time'].dt.floor('min')
    
    # Group by minute and count success / failure
    grouped = df.groupby('Minute').agg(
        Successes=('Success', 'sum'),
        Failures=('Failure', 'sum')
    )
    
    # Reindex to ensure continuous 1-minute bins and fill missing intervals with 0
    full_range = pd.date_range(start=start_range, end=end_range, freq='1min')
    grouped = grouped.reindex(full_range, fill_value=0)
    
    # Calculate Total and Success Rate
    grouped['Total'] = grouped['Successes'] + grouped['Failures']
    grouped['SuccessRate'] = 100.0
    valid_total_mask = grouped['Total'] > 0
    grouped.loc[valid_total_mask, 'SuccessRate'] = (grouped.loc[valid_total_mask, 'Successes'] / grouped.loc[valid_total_mask, 'Total']) * 100.0
    
    # Create the dual plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    # ------------------ TOP PANEL: Success Rate ------------------
    ax1.plot(grouped.index, grouped['SuccessRate'], color='#1e8e3e', linewidth=2.5, label='Success Rate %')
    ax1.fill_between(grouped.index, grouped['SuccessRate'], color='#1e8e3e', alpha=0.1)
    
    # Style TOP panel
    ax1.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_ylim(-5, 105)
    ax1.set_title('Checkout Success & Failure Metrics - Incident Recovery Analysis', fontsize=16, fontweight='bold', pad=15)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # ------------------ BOTTOM PANEL: Volume ------------------
    ax2.plot(grouped.index, grouped['Successes'], color='#1a73e8', linewidth=2, label='Successes (HTTP 200)')
    ax2.plot(grouped.index, grouped['Failures'], color='#d93025', linewidth=2, label='Failures (HTTP 500)')
    ax2.fill_between(grouped.index, grouped['Successes'], color='#1a73e8', alpha=0.05)
    ax2.fill_between(grouped.index, grouped['Failures'], color='#d93025', alpha=0.05)
    
    # Style BOTTOM panel
    ax2.set_ylabel('Volume (Requests / Min)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (UTC) - 2026-05-28', fontsize=12, fontweight='bold', labelpad=10)
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    # Format x-axis timestamps explicitly showing day info
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
    fig.autofmt_xdate()

    # Incident Milestone Annotations (UTC)
    milestones = [
        {'time': '2026-05-28 15:42:10', 'label': 'Incident Start (15:42:10)', 'color': '#d93025', 'style': '--', 'lw': 2},
        {'time': '2026-05-28 17:39:55', 'label': 'Detected (17:39:55)', 'color': '#f9ab00', 'style': '-.', 'lw': 2},
        {'time': '2026-05-28 17:42:00', 'label': 'Mitigation 1 (17:42:00)', 'color': '#1e8e3e', 'style': ':', 'lw': 2},
        {'time': '2026-05-28 17:43:15', 'label': 'Checkout Restored (17:43:15)', 'color': '#1e8e3e', 'style': '-', 'lw': 1.5},
        {'time': '2026-05-28 17:49:00', 'label': 'Canary Outage Identified (17:49:00)', 'color': '#f9ab00', 'style': '-.', 'lw': 1.5},
        {'time': '2026-05-28 17:49:23', 'label': 'Mitigation 2 (17:49:23)', 'color': '#1e8e3e', 'style': ':', 'lw': 2},
        {'time': '2026-05-28 17:49:40', 'label': 'Full Recovery (17:49:40)', 'color': '#1e8e3e', 'style': '-', 'lw': 2.5}
    ]

    for ms in milestones:
        ms_time = pd.to_datetime(ms['time'])
        for ax in [ax1, ax2]:
            ax.axvline(ms_time, color=ms['color'], linestyle=ms['style'], linewidth=ms['lw'])
            
        # Draw annotation text on the top graph
        # Position label slightly offset from the vertical line
        ax1.text(ms_time + pd.Timedelta(seconds=45), 5, ms['label'], 
                 rotation=90, color=ms['color'], weight='bold', fontsize=9,
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))

    # Add legends
    ax1.legend(loc='lower left', framealpha=0.9)
    ax2.legend(loc='upper right', framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"Successfully generated and saved incident recovery graph to: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python plot_incident.py <input_logs.json> <output_graph.png>")
        sys.exit(1)
    generate_graph(sys.argv[1], sys.argv[2])
