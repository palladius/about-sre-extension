# Executive Summary

On 2026-04-09, the `microservice-demo` GKE cluster experienced a multi-phase incident leading to random HTTP 500 errors. Initially, a misconfigured `checkout-virtualservice` caused 500s on checkout paths. After mitigation, persistent 500 errors emerged on product and cart paths, attributed to intermittent Istio control plane failures impacting service discovery and name resolution for backend services like `productcatalogservice` and `recommendationservice`. The underlying Istio issue is still under investigation.

## Impact

Customers experienced intermittent HTTP 500 errors, first on `/cart/checkout` paths, and subsequently on `/product` and `/cart` paths. This directly impacted user ability to browse products and complete purchases, leading to a degraded user experience and potential revenue loss.

## Background

The `microservice-demo` application, running on a GKE cluster, leverages Istio for traffic management and service mesh functionalities. The incident highlights issues stemming from both explicit fault injection configurations and underlying Istio control plane stability.

## Root Causes and Trigger

The incident unfolded in two distinct phases. The initial wave of 500 errors was directly triggered by the deployment of a misconfigured `checkout-virtualservice` at approximately `2026-04-09 09:19:00 UTC`. This `VirtualService` was configured to inject a 100% HTTP 503 abort fault for the `checkoutservice`. The subsequent and persistent 500 errors, manifesting as "rpc error: code = Unavailable desc = name resolver error: produced zero addresses," are hypothesized to be caused by intermittent failures within the Istio control plane. This instability prevents the consistent propagation of service endpoint information to `frontend`'s Envoy proxies, leading to name resolution failures when attempting to reach `productcatalogservice` and `recommendationservice`.

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

Day: **YYYY-MM-DD**  TZ=US/Pacific
* `HH:MM:SS`: {Description} <== <span style="color:red">{Milestone if applicable}</span>
* `HH:MM:SS`: {Description}
* `HH:MM:SS`: {Description} <== <span style="color:red">{Milestone if applicable}</span>
* `HH:MM:SS`: {Description}

## IMPORTANT

This PostMortem is AI-generated. Please review it carefully before submitting.
