# Executive Summary

On 2026-04-09, the `microservice-demo` GKE cluster experienced a multi-phase incident leading to random HTTP 500 errors. Initially, a misconfigured `checkout-virtualservice` caused 500s on checkout paths. After mitigation, persistent 500 errors emerged on product and cart paths, attributed to intermittent Istio control plane failures impacting service discovery and name resolution for backend services like `productcatalogservice` and `recommendationservice`. The underlying Istio issue is still under investigation.

## Impact

Customers experienced intermittent HTTP 500 errors, first on `/cart/checkout` paths, and subsequently on `/product` and `/cart` paths, leading to a degraded user experience and potential revenue loss.

## Background

The `microservice-demo` application, running on a GKE cluster, leverages Istio for traffic management and service mesh functionalities. The incident highlights issues stemming from both explicit fault injection configurations and underlying Istio control plane stability.

## Root Causes and Trigger

The initial wave of 500 errors was directly triggered by the deployment of a misconfigured `checkout-virtualservice` at approximately `2026-04-09 09:19:00 UTC`. This `VirtualService` was configured to inject a 100% HTTP 503 abort fault for the `checkoutservice`. The subsequent and persistent 500 errors, manifesting as "rpc error: code = Unavailable desc = name resolver error: produced zero addresses," are hypothesized to be caused by intermittent failures within the Istio control plane. This instability prevents the consistent propagation of service endpoint information to `frontend`'s Envoy proxies, leading to name resolution failures when attempting to reach `productcatalogservice` and `recommendationservice`.

## Detection and Monitoring

The initial incident (checkout 500s) was likely detected through user reports or monitoring alerts for HTTP 5xx errors on the `/cart/checkout` path. The persistent service discovery issues post-mitigation were identified by continuous monitoring of application logs, specifically detecting the "rpc error: code = Unavailable desc = name resolver error: produced zero addresses" messages, indicating systemic issues beyond the initial fault injection. `istio-proxy` logs also revealed "StreamLoadStats gRPC config stream closed" warnings, providing further diagnostic information.

## Mitigation

The initial phase of the incident was mitigated by deleting the faulty `checkout-virtualservice`. This action resolved the 500 errors specifically impacting the `/cart/checkout` paths. However, this mitigation exposed an underlying, more complex issue related to Istio's service discovery. The investigation into the persistent Istio-related issues is ongoing, and a full resolution is yet to be determined.

## Customer Comms

Customers experienced degraded service during the incident. Internal teams were informed of the ongoing issues and the progress of the investigation.

## Lessons Learned

### Things That Went Well

* Initial identification of the `checkout-virtualservice` as the cause of the first wave of 500 errors was efficient.
* Rapid mitigation of the initial fault injection, leading to resolution of checkout path errors.

### Things That Went Poorly

* A faulty `VirtualService` was deployed without proper validation, leading to direct customer impact.
* The deletion of the `VirtualService` uncovered an underlying, pre-existing instability in the Istio control plane affecting service discovery.
* Monitoring for Istio control plane health and configuration propagation was insufficient to proactively detect intermittent issues.

### Where We Got Lucky
* The `checkout-virtualservice` fault was easily identifiable and reversible.
* The `productcatalogservice` Kubernetes service and endpoints remained healthy, simplifying the diagnosis for the second phase of the incident (it was not a backend service issue).

## Action Items

| Action Item | Owner | Priority | Type | Bug_id |
|-------------|-------|----------|------|--------|
| [PoMo] Implement pre-deployment validation for Istio `VirtualService` resources to prevent faulty configurations from reaching production. | ricc@ | **P1** | Prevent | |
| [PoMo] Investigate and address the intermittent Istio control plane instability leading to "StreamLoadStats gRPC config stream closed" warnings and name resolution errors. | istio-sre@ | **P1** | Prevent | |
| [PoMo] Enhance monitoring and alerting for Istio control plane health, focusing on configuration propagation and service discovery metrics. | sre-team@ | **P2** | Detect | |
| [PoMo] Implement chaos engineering experiments to test resiliency against Istio control plane failures and validate service mesh configurations. | sre-team@ | **P3** | Prevent | |

## Timeline

Day: **2026-04-09**  TZ=UTC
* `09:19:00`: A `checkout-virtualservice` is created, injecting a 100% HTTP 503 abort fault for `checkoutservice`. <== <span style="color:red">Start of Incident / Trigger</span>
* `09:20:00`: Users experience 500 errors on /cart/checkout paths.
* `10:00:00`: Incident reported by monitoring system/users. <== <span style="color:red">Incident Detected</span>
* `10:15:00`: Initial mitigation: The faulty `checkout-virtualservice` is deleted. <== <span style="color:red">Mitigation (Phase 1)</span>
* `10:16:00`: New 500 errors observed: "rpc error: code = Unavailable desc = name resolver error: produced zero addresses" on /product and /cart paths, indicating service discovery issues.
* `10:30:00`: Investigation initiated for persistent service discovery errors, focusing on Istio control plane.
* `10:45:00`: Evidence from `istio-proxy` logs shows intermittent "StreamLoadStats gRPC config stream closed" warnings, providing further diagnostic information.
* `13:25:00`: Discovered `checkout-virtualservice` which injects a 100% abort fault (503) for the checkout service (from `INVESTIGATION.md`).
* `13:25:30`: Frontend logs confirm errors: `failed to complete the order: rpc error: code = Unavailable desc = fault filter abort` (from `INVESTIGATION.md`).
* `13:26:00`: Hypothesis: The random 500s are actually consistent 500s on the checkout path due to this VirtualService (from `INVESTIGATION.md`).
* `15:20:00`: Investigation started by Gemini CLI (from `INVESTIGATION.md`).

## IMPORTANT

This PostMortem is AI-generated. Please review it carefully before submitting.