# Incident Investigation: 2026-05-28 Outage

- **SRE Investigator**: Benjamin 🤠🏎️
- **Cluster**: `online-boutique-prod`
- **Project ID**: `sre-next-prod`
- **IP Address**: http://34.55.56.97/
- **Harness**: Antigravity CLI (`agy`)

## Timeline of Events

| Timestamp (UTC) | Event / Discovery | Description |
| :--- | :--- | :--- |
| 2026-05-28T17:39:55Z | Incident Triggered | User reported inability to purchase products on the online boutique. |
| 2026-05-28T17:40:13Z | Env Verified | Verified environment credentials: project `sre-next-prod`, cluster `online-boutique-prod`. |
| 2026-05-28T17:40:20Z | Pods Checked | Noticed recent rollout of `checkoutservice` (~3h ago) and `frontend` (~70m ago). |
| 2026-05-28T17:40:25Z | Frontend Logs Analyzed | Discovered frontend is timing out when dialing `checkoutservice` (ClusterIP `34.118.235.113:5050`). |
| 2026-05-28T17:40:33Z | NetworkPolicies Queried | Found a recent NetworkPolicy `update-checkout-from-frontend` deployed 118 minutes ago. |
| 2026-05-28T17:40:35Z | NetPol Misconfiguration Identified | The NetworkPolicy restricts ingress to `checkoutservice` to only pods with label `app=frontend-checkout-test`. However, our actual frontend pods are labeled `app=frontend`. This blocks all legitimate traffic. |
| 2026-05-28T17:40:45Z | Root Cause Confirmed | Correlated the NetworkPolicy creation timestamp with the scenario1 breakage log entry. |
| 2026-05-28T17:42:00Z | Mitigation Executed | Successfully deleted the misconfigured `update-checkout-from-frontend` NetworkPolicy. |
| 2026-05-28T17:42:43Z | Connection pools flushed | Rolled out a restart on `frontend` and `frontend-canary` deployments to clear pooled connections. |
| 2026-05-28T17:43:15Z | Incident Resolved | Verified checkoutservice is successfully processing orders again (200 OKs and PlaceOrder gRPC logging). |
| 2026-05-28T17:49:00Z | Canary Outage Identified | Detected name resolver errors (`produced zero addresses`) on `frontend-canary` due to a typo in `PRODUCT_CATALOG_SERVICE_ADDR` env var (`productcatalogservices` instead of `productcatalogservice`). |
| 2026-05-28T17:49:23Z | Canary Hotfix Executed | Applied correct environment variable configuration to the `frontend-canary` deployment. |
| 2026-05-28T17:49:40Z | Canary Recovered | Rollout completed successfully and confirmed DNS lookup issues are resolved (HTTP 200 OKs flowing). |

## Investigation Findings
- **Root Cause Hypothesis**: A breakage script (`scenario1-PROD standard`) applied a K8s `NetworkPolicy` named `update-checkout-from-frontend` which mistakenly restricts ingress traffic to `checkoutservice` to only pods labeled `app=frontend-checkout-test`. Because the real frontend pods are labeled `app=frontend`, all purchase flows (which invoke `checkoutservice` from `frontend`) fail with a TCP connection timeout.
- **Confidence Level**: High (100% correlation between policy creation time, policy selector labels, and frontend timeout logs).
- **Evidence**:
  - **Exhibit A (NetworkPolicy Spec)**: [exhibit_A_network_policy.yaml](file:///Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/exhibit_A_network_policy.yaml)
  - **Exhibit B (Frontend Dialing Timeout Logs)**: [exhibit_B_frontend_logs.txt](file:///Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/exhibit_B_frontend_logs.txt)
  - **Exhibit C (Breakages Log Correlation)**: [exhibit_C_breakages_log.txt](file:///Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/exhibit_C_breakages_log.txt)
  - **Exhibit D (Incident Recovery Graph)**: [incident_recovery_graph_rev1.png](file:///Users/ricc/git/sre-extension/gh/investigation/20260528-ricc-agy-investigation/evidence/incident_recovery_graph_rev1.png)

## Mitigation Strategy & Actuation
- **Mitigation Taxonomy Category**: Rollback / Deletion
- **Mitigation Actuation**: Deleted the misconfigured `NetworkPolicy`.
- **Verification**: Confirmed `PlaceOrder` requests are completing successfully (logs show payments going through and order emails being sent).

---
*Investigation Completed successfully.*
