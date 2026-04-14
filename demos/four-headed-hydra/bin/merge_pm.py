import csv

with open('20260402-investigation/postmortem-online-boutique/postmortem-base.md', 'r') as f:
    base_content = f.read()

timeline_md = "\n## Timeline\n\nTZ=UTC\n"
with open('20260402-investigation/postmortem-online-boutique/timeline.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Expected cols: Time,Description,Milestone
        desc = row.get('Description', '')
        time_full = row.get('Time', '').replace(' UTC', '')
        milestone = row.get('Milestone', '').strip()
        
        line = f"* `{time_full}`: {desc}"
        if milestone:
            line += f" <== <span style=\"color:red\">{milestone}</span>"
        timeline_md += line + "\n"

action_items_md = """
## Action Items

| Action Item | Owner | Priority | Type | Bug_id |
|-------------|-------|----------|------|--------|
| Fix OTel Config `opentelemetrycollector` to listen on `0.0.0.0` | sre-team@ | **P1** | Mitigate | |
| Standardize Canary to use CI/CD pipeline | platform@ | **P2** | Prevent | |
| Tighten frontend health probes | dev-team@ | **P2** | Prevent | |
| Fix `paymentservice` `visa_electron` legacy rejection | dev-team@ | **P3** | Process | |

"""

footer = "\n<!-- IMPORTANT: This PostMortem is AI-generated. Please review it carefully before submitting. -->\n"

with open('20260402-investigation/postmortem-online-boutique/postmortem-final.md', 'w') as f:
    f.write(base_content + action_items_md + timeline_md + footer)

print("Merged into postmortem-final.md")
