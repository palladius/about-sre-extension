# Investigation Log - 2026-05-19

- **Incident**: Users unable to purchase products.
- **Target Project**: `sre-next-prod`
- **GKE Cluster**: `online-boutique-prod`
- **Application URL**: http://34.55.56.97/

## Timeline

- **2026-05-19 10:00:00 UTC**: Incident reported by user. Starting investigation.
- **2026-05-19 12:49:18 UTC**: Frontend confirmed reachable (HTTP 200). Cluster `online-boutique-prod` found in `us-central1`.
- **2026-05-19 12:55:00 UTC**: **Root Cause Identified**. A NetworkPolicy `update-checkout-from-frontend` is blocking all traffic to `checkoutservice` except from a non-existent `frontend-checkout-test` app.
- **2026-05-19 12:57:00 UTC**: **Mitigation Action**. Deleting the poisonous NetworkPolicy.
- **2026-05-19 13:00:00 UTC**: **Verification**. Checkouts are now succeeding. Logs confirm requests reaching `checkoutservice`.
- **2026-05-19 13:05:00 UTC**: **Secondary Root Cause Identified**. `frontend-canary` has a typo in `PRODUCT_CATALOG_SERVICE_ADDR` (`productcatalogservices` instead of `productcatalogservice`).
- **2026-05-19 13:10:00 UTC**: **Final Mitigation**. Deleting broken `frontend-canary` deployment. Incident resolved.
