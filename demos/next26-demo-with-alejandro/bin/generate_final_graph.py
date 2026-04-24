#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "matplotlib"
# ]
# ///

import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os

def generate_graph():
    json_path = '20260424-ricc-investigation/evidence/errors.json'
    output_path = '20260424-ricc-investigation/evidence/checkout_outage_graph.png'
    
    with open(json_path) as f:
        data = json.load(f)

    records = []
    for ts in data.get('timeSeries', []):
        for p in ts.get('points', []):
            et = pd.to_datetime(p['interval']['endTime'])
            val = int(p['value'].get('int64Value', 0))
            records.append({'Time': et, 'Errors': val})

    if not records:
        print("NO DATA FOUND!")
        return

    df = pd.DataFrame(records)
    df['Time'] = df['Time'].dt.tz_convert('UTC')
    
    # 1. Add "GOOD" state points and reindex
    # Start at 13:30 and end at 19:00 to cover 14:00-18:30 range
    start_range = pd.to_datetime("2026-04-24 13:30:00Z")
    end_range = pd.to_datetime("2026-04-24 19:00:00Z")
    full_range = pd.date_range(start=start_range, end=end_range, freq='1min', tz='UTC')
    
    grouped = df.groupby(pd.Grouper(key='Time', freq='1min'))['Errors'].sum()
    grouped = grouped.reindex(full_range, fill_value=0)
    
    # Synthetic success rate for Availability visualization
    # We'll assume a baseline of 20 successful requests/min
    baseline_success = 20
    grouped_df = grouped.to_frame()
    grouped_df['Success'] = baseline_success
    grouped_df['Total'] = grouped_df['Success'] + grouped_df['Errors']
    grouped_df['Availability'] = (grouped_df['Success'] / grouped_df['Total']) * 100
    
    # 2. Smoothing
    volume = grouped_df['Errors'].rolling(5, min_periods=1).mean()
    avail = grouped_df['Availability'].rolling(5, min_periods=1).mean()

    # 3. Dual Axes Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # TOP: Availability (%)
    ax1.plot(avail.index, avail, color='#d93025', linewidth=3, label='Availability % (Estimated)')
    ax1.fill_between(avail.index, avail, color='#d93025', alpha=0.1)
    ax1.set_ylabel('Availability %', fontsize=12)
    ax1.set_ylim(-5, 105)
    ax1.set_title('Checkout Service Outage Lifecycle (2026-04-24)', fontsize=18, fontweight='bold')

    # BOTTOM: Error Volume (Req/min)
    ax2.plot(volume.index, volume, color='#1a73e8', linewidth=2, label='Error Log Count')
    ax2.fill_between(volume.index, volume, color='#1a73e8', alpha=0.1)
    ax2.set_ylabel('Errors / Min', fontsize=12)
    ax2.set_xlabel('Time (UTC)', fontsize=12)

    # Annotations
    milestones = [
        ("2026-04-24 14:06:24", "#d93025", ":", 2, "Start of Incident (NetworkPolicy)"),
        ("2026-04-24 14:46:59", "#f9ab00", "--", 2, "Frontend Canary Update"),
        ("2026-04-24 17:45:00", "#f9ab00", "--", 2, "Detection"),
        ("2026-04-24 17:57:45", "#1e8e3e", "-", 2, "Mitigation (Checkout)"),
        ("2026-04-24 18:15:20", "#1e8e3e", "-", 2, "Mitigation (500s)"),
        ("2026-04-24 18:16:00", "#1e8e3e", "-", 2, "Incident End")
    ]

    for time_str, color, style, lw, label in milestones:
        time = pd.to_datetime(time_str).tz_localize('UTC')
        for ax in [ax1, ax2]:
            ax.axvline(time, color=color, linestyle=style, linewidth=lw, label=label if ax == ax1 else "")

    ax1.grid(True, linestyle=':', alpha=0.6)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=10, frameon=True, shadow=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    generate_graph()
