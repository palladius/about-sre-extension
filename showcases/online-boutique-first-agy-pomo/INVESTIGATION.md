# Investigation: 2026-05-28

- **Investigator**: Benjamin 🏎️🎩
- **On-Call SRE**: ricc@
- **Senior SRE**: madhavikarra@
- **Harness**: Antigravity CLI (`agy`) — **FIRST PostMortem made with agy! 🚀🏆**
- **Start Time**: 2026-05-28T16:33:53+02:00

## Timeline

- **16:11:07**: trigger@ ricc@ executed Scenario 1 (`scenario1-PROD standard`), applying the restrictive NetworkPolicy `update-checkout-from-frontend` to GKE. <== <span style="color:red">Start of Incident</span>
- **16:11:11**: GKE event: `frontend` and `frontend-canary` pods rescheduled and restarted to apply network rules.
- **16:11:18**: trigger@ ricc@ executed Scenario 2 (`scenario2`), deploying the buggy `frontend-canary` rollout with the `productcatalogservices` DNS typo.
- **16:33:53**: Investigator Benjamin initiated investigation, listing available MCP tools.
- **16:34:28**: Support escalated multiple checkout failure tickets on http://34.55.56.97/ to on-call SRE ricc@. <== <span style="color:red">Incident Detected</span>
- **16:35:04**: Verified LoadBalancer IP `34.55.56.97` is active and healthy at the ingress layer.
- **16:35:11**: Checked all GKE pod statuses; noted stable frontend and canary pods were deployed/rolled out ~24 minutes prior (matching the `16:11` scenario execution exactly).
- **16:35:23**: Inspected `frontend` pod logs and found gRPC timeouts when calling `checkoutservice` on `34.118.235.113:5050` (`rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial tcp 34.118.235.113:5050: i/o timeout"`).
- **16:35:37**: Located NetworkPolicy `update-checkout-from-frontend` in the `default` namespace.
- **16:35:40**: Analyzed the policy spec and verified it restricted ingress to `app: frontend-checkout-test`, effectively blocking all traffic from the production `frontend` pods (`app: frontend`).
- **16:36:41**: Deleted the faulty NetworkPolicy `update-checkout-from-frontend`. <== <span style="color:red">Mitigation</span>
- **16:37:38**: GKE event: Deleted deadlocked `checkoutservice-55c958c6c-6r5l2` pod to clear stale network sockets.
- **16:38:06**: Inspected `frontend-canary` pod logs and found catalog resolution errors (`produced zero addresses`).
- **16:38:25**: Identified the `productcatalogservices:3550` host typo in `frontend-canary` spec.
- **16:38:36**: Patched the `frontend-canary` deployment to the correct hostname `productcatalogservice:3550` (GKE Event: `14:38:36Z`).
- **16:39:19**: Recycled stale production `frontend` pods to flush stale persistent connection pool caches.
- **16:39:20**: Verified first successful purchase logged in checkout service (`14:39:20.355Z payment went through`). <== <span style="color:red">Incident End</span>
- **16:43:58**: Cleanly deleted the verified `frontend-canary` deployment to return exclusively to a stable production baseline.
