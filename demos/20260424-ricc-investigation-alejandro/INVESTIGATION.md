# Investigation: Users unable to purchase products
**Date:** 2026-04-24
**User:** ricc
**Project ID:** sre-next-prod
**Cluster:** online-boutique-prod

## Timeline

- **10:45:00 (approx)** - User reports of "unable to purchase" start coming in.
- **10:47:23** - Investigation started by Gemini CLI.
- **10:52:15** - Discovered that `frontend` and `frontend-canary` are timing out when calling `checkoutservice`.
- **10:54:30** - Identified a suspicious `NetworkPolicy` named `update-checkout-from-frontend` created at `2026-04-24T14:06:24Z`.
- **10:55:00** - Root Cause Analysis: The `NetworkPolicy` restricts ingress to `checkoutservice` to pods with label `app: frontend-checkout-test`, but the production `frontend` pods have the label `app: frontend`. This is blocking all legitimate checkout traffic.
- **10:57:45** - Mitigation: Deleted the faulty `NetworkPolicy` `update-checkout-from-frontend`.
- **10:58:30** - Verification: Confirmed new orders are appearing in `checkoutservice` logs. Service restored.
- **11:05:00** - New report: Users experiencing intermittent 500 errors on the homepage.
- **11:08:15** - Analysis of logs shows 500 errors are exclusive to `frontend-canary` pods.
- **11:10:30** - Root Cause identified: `frontend-canary` deployment has a typo in the `PRODUCT_CATALOG_SERVICE_ADDR` environment variable.
- **11:15:20** - Mitigation: Scaled `frontend` to 2 replicas and `frontend-canary` to 0 replicas. Intermittent 500 errors resolved.
- **2026-04-24 10:48 UTC** - Generated final annotated incident graph: [images/checkout_outage_graph.png](images/checkout_outage_graph.png). This graph visualizes the full incident lifecycle, including "GOOD" state points, error volume, and synthetic availability impact.

## Deep Dive Root Cause Analysis (RCA)

- **14:06:24Z (Pre-Investigation)**: Audit logs show `ricc@gcp.altostrat.com` created the `update-checkout-from-frontend` NetworkPolicy. This immediately broke the checkout flow.
- **14:46:59Z (Pre-Investigation)**: Audit logs show `ricc@gcp.altostrat.com` updated the `frontend-canary` deployment, introducing the typo `productcatalogservices`. This introduced the intermittent 500 errors.
