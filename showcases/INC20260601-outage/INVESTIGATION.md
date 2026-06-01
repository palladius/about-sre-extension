# Outage Investigation: unable to purchase a product from online boutique

## Metadata
* **Incident Start Time**: 2026-06-01T18:22:39+02:00
* **Target Project ID**: `sre-next-prod`
* **GKE Cluster Name**: `online-boutique-prod`
* **GKE Region**: `us-central1`
* **Investigator**: Jennifer 🐉
* **Harness**: Antigravity CLI (`agy`)

## Timeline & Discoveries

* **2026-06-01T18:22:39+02:00**: Trigger event: `ricc@` applied scenario1-PROD standard (applied NetworkPolicy `update-checkout-from-frontend` blocking checkout traffic).
* **2026-06-01T18:22:51+02:00**: Trigger event: `ricc@` applied scenario2 (buggy `frontend-canary` rollout).
* **2026-06-01T18:22:53+02:00**: GKE scheduler scaled up `frontend-canary` replica set `frontend-canary-7655454899` from 0 to 1.
* **2026-06-01T18:34:44+02:00**: Incident escalated to SRE Jennifer. Support ticket opened for checkout and home page issues.
* **2026-06-01T18:35:08+02:00**: Verified GCP credentials and active identities:
  * `gcloud` Active Account: `ricc@gcp.altostrat.com`
  * Project ID: `sre-next-prod`
  * Active Cluster Name: `online-boutique-prod`
* **2026-06-01T18:35:17+02:00**: Checked pod health; observed `frontend-canary` and main `frontend` pods running.
* **2026-06-01T18:35:22+02:00**: Discovered boutique IP address `34.55.56.97` returns `500 Internal Server Error` on frontend load balancer.
* **2026-06-01T18:35:25+02:00**: Fetched frontend pod logs and identified two distinct failures:
  1. `could not retrieve products: rpc error: code = Unavailable desc = name resolver error: produced zero addresses` (on frontend-canary pod or some traffic).
  2. `failed to complete the order: rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial tcp 34.118.235.113:5050: i/o timeout"` during checkout.
* **2026-06-01T18:35:33+02:00**: Inspected deployments; identified that `frontend-canary` deployment env variable `PRODUCT_CATALOG_SERVICE_ADDR` has a typo: `productcatalogservices:3550` instead of `productcatalogservice:3550`.
* **2026-06-01T18:35:47+02:00**: Listed NetworkPolicies and discovered `update-checkout-from-frontend` NetworkPolicy.
* **2026-06-01T18:35:50+02:00**: Analyzed NetworkPolicy; found ingress rules restrict `checkoutservice` to `app=frontend-checkout-test` instead of standard `app=frontend` label.
* **2026-06-01T18:36:37+02:00**: Deleted the faulty `update-checkout-from-frontend` NetworkPolicy.
* **2026-06-01T18:36:40+02:00**: Scaled down the broken `frontend-canary` deployment to 0 replicas.
* **2026-06-01T18:36:49+02:00**: Completed verification loop. 100% of requests are returning `HTTP/1.1 200 OK`. Outage mitigated.

---

## Hypotheses & Evidence

### Hypothesis A: Broken Checkout due to Network Policy
* **Description**: The `update-checkout-from-frontend` NetworkPolicy blocks standard frontend pods (`app=frontend`) from communicating with `checkoutservice`.
* **Confidence**: High (100% match with the connection timeout error: `dial tcp 34.118.235.113:5050: i/o timeout`).
* **Evidence**:
  * NetworkPolicy definition restricts ingress to pods with label `app: frontend-checkout-test`.
  * Frontend pods have label `app: frontend`.
  * Status: **Mitigated** (faulty NetworkPolicy deleted at 18:36:37).

### Hypothesis B: Intermittent 500 Errors on Home Page due to Canary Config Typo
* **Description**: `frontend-canary` pod has a typo in `PRODUCT_CATALOG_SERVICE_ADDR` env variable, attempting to resolve `productcatalogservices:3550` instead of `productcatalogservice:3550`.
* **Confidence**: High.
* **Evidence**:
  * Deployment YAML for `frontend-canary` contains `value: productcatalogservices:3550`.
  * Logs from frontend container show name resolution failure.
  * Status: **Mitigated** (canary scaled down to 0 replicas at 18:36:40).
