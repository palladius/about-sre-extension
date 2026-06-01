# Outage Investigation: 2026-06-01 Online Boutique Outage

* **Date**: 2026-06-01
* **User**: ricc
* **Harness**: agy
* **Outage Target**: `online-boutique-prod` GKE Cluster (http://34.55.56.97/)
* **Project ID**: `sre-next-prod`

## Timeline of Events
- **01:20:19.000 US/Pacific (10:20:19 CEST)**: `ricc@` executes chaos `scenario1-PROD standard` script in production to simulate blackholing cart checkout.
- **01:20:22.000 US/Pacific**: NetworkPolicy `update-checkout-from-frontend` successfully applied by the script.
- **01:20:23.484 US/Pacific**: Last successful order processed by `checkoutservice` before ingress traffic was blackholed.
- **01:20:31.000 US/Pacific (10:20:31 CEST)**: `ricc@` executes `scenario2` script introducing a configuration typo in the newly deployed `frontend-canary` environment variables.
- **08:48:19.000 US/Pacific**: USER escalates issue reporting that users are unable to purchase products from the boutique application. Jennifer 🐉 armed with a Mace/Club ⚔️ takes the case!
- **08:48:26.000 US/Pacific**: Jennifer 🐉 initializes the dated outage investigation folder.
- **08:48:33.000 US/Pacific**: Jennifer 🐉 runs log check on frontend and detects gRPC timeout errors dialing checkoutservice IP `34.118.235.113:5050`.
- **08:49:12.000 US/Pacific**: Jennifer 🐉 discovers `update-checkout-from-frontend` NetworkPolicy and escalates root cause details to senior SRE `madhavikarra@`.
- **08:49:31.000 US/Pacific**: Jennifer 🐉 deletes the problematic `update-checkout-from-frontend` NetworkPolicy using kubectl.
- **08:49:34.000 US/Pacific**: Jennifer 🐉 patches the `PRODUCT_CATALOG_SERVICE_ADDR` environment variable typo in frontend-canary deployment.
- **08:49:51.000 US/Pacific**: Jennifer 🐉 triggers rolling restart of frontend deployment to flush Calico connection tracking tables.
- **08:51:19.000 US/Pacific**: Rolling restart of frontend deployment successfully completes in background task.
- **08:51:21.000 US/Pacific**: Verification script successfully executes and validates 100% checkout success rate. Checkoutservice log processing resumed.

## Evidence Collected (in `./evidence/`)
- **Exhibit A**: `evidence/network_policy.yaml` - The misconfigured ingress network policy that blocks traffic from the frontend to the checkout service.
- **Exhibit B**: `evidence/frontend_logs_timeout.json` - Log snippet illustrating the `i/o timeout` when the frontend tries to complete a checkout.
- **Exhibit C**: `evidence/frontend_canary_bad_env.yaml` - Frontend canary config showing the `productcatalogservices` DNS name resolution typo.
- **Exhibit D**: `evidence/frontend_homepage_logs.csv` - 3.3MB CSV containing all homepage and product catalog transactions for outage timeframe analysis.
- **Exhibit E**: `out/postmortem-20260601-outage/incident_graph_rev2.png` - Beautiful bespoke dual-outage telemetry graph showing checkout blackout (100% -> 0% -> 100%) side-by-side with product catalog flakiness (100% -> ~60% -> 100%).

## Sparkline Telemetry
- **Checkout Availability**: `█▄                             ▅██` (Complete outage)
- **Product Catalog Availability**: `█▆▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▅▆▇██` (Canary flakiness ~60% success rate)

