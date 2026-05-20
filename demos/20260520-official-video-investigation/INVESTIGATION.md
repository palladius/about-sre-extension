# Official Video Investigation: Online Boutique Checkout Issue - 2026-05-20

> **Video Link**: [Coming Soon / Link to be provided]

## Summary
Users reporting inability to purchase products.

## Timeline
- **2026-05-19 19:59:49 UTC**: Faulty `NetworkPolicy` (`update-checkout-from-frontend`) was created, blocking ingress to `checkoutservice`.
- **2026-05-19 20:00:11 UTC**: `frontend-canary` deployment was created. It contained a typo in `PRODUCT_CATALOG_SERVICE_ADDR` (`productcatalogservices:3550`).
- **2026-05-20 13:32:30 UTC**: `frontend-canary` logs show: `could not retrieve products: rpc error: code = Unavailable desc = name resolver error: produced zero addresses`.
- **2026-05-20 13:33:07 UTC**: `frontend` (stable) logs show: `failed to complete the order: rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial tcp 34.118.235.113:5050: connect: connection timed out"`.
- **2026-05-20 13:35:00 UTC**: Investigation started by Gemini CLI. Folder structure created.
- **2026-05-20 13:36:00 UTC**: RCA completed. NetworkPolicy and Canary Typo identified as root causes.
- **2026-05-20 13:36:45 UTC**: **Mitigation Executed**:
    - `networkpolicy/update-checkout-from-frontend` deleted.
    - `deployment/frontend-canary` patched with correct `PRODUCT_CATALOG_SERVICE_ADDR`.
- **2026-05-20 13:37:31 UTC**: **Verification**:
    - Rollout status of `frontend-canary` checked: Success.
    - Log check: Error rate dropped to zero. Investigation paused.
