# About SRE Extension

Self: https://github.com/palladius/about-sre-extension/

## Motivation

The SRE Extension for Gemini CLI streamlines incident response by integrating deep cloud expertise and observability directly into the terminal. It automates data aggregation from Cloud Logging, Monitoring, and Kubernetes to provide a unified timeline, uses AI to generate hypotheses and suggest low-risk mitigations, and facilitates the automatic creation of blameless postmortems—all while maintaining human-in-the-loop control for safe operations.

## Results

We have validated the SRE Extension across several simulated incident scenarios:

### Incident 1: Random 500s (Istio Service Discovery Failure)
- **Postmortem:** [Istio Service Discovery Failure](demos/20260409-demo06a/post-mortem/postmortem-final.md)
- **Summary:** Independently investigated HTTP 500 errors and identified a faulty Istio `VirtualService` with a 100% abort fault, uncovering a latent instability in the Istio control plane.

### Incident 2: Online Boutique Cluster Outage (Firewall & Canary)
- **Postmortem:** [Online Boutique Cluster Outage](demos/20260414-outage/postmortem-final.md)
- **Summary:** Autonomously diagnosed a "poisonous" canary deployment with an environment variable typo and isolated a VPC firewall rule blocking external traffic.

### Incident 3: The "Triple-Threat" Simultaneous Outage (2026-04-04)
- **Postmortem:** [Triple-Threat Investigation](demos/online-boutique-triple-threat/postmortem-final.md)
- **Summary:** Handled three overlapping failures: a rogue firewall rule, an Istio fault injection, and a deployment typo, using event correlation to distinguish network vs. app layers.
- **Why it's cool:** Features complex, annotation-heavy graphs proving deep technical correlation across the entire stack.

### Incident 4: The "Four-Headed Hydra" Complex Failure (2026-04-02)
- **Postmortem:** [Four-Headed Hydra Postmortem](demos/four-headed-hydra/postmortem-final2.md)
- **Summary:** Investigated a "Hydra" of failures including OTel collector misconfiguration, an Istio "blackhole," and GKE node churn.
- **Why it's cool:** Uses high-resolution incident visualizations and an engaging, emoji-rich narrative that showcases the AI's "personality."

## Execution Safety

Safety is strictly enforced:
- **Operator Control:** All mitigations are monitored by an SRE operator.
- **Custom Policies:** Access is limited by granular read/write policies.
- **Human Approval:** Explicit engineer approval is required for all sensitive actions.

## Get Notified

If you'd like to be notified when the SRE Extension is released, please **star** this repository or fill in this [form](https://forms.gle/1qqfCPv29TZtdj9e8).

## Our environment

Tests were conducted on the [Microservices Demo](https://github.com/GoogleCloudPlatform/microservices-demo) running on GKE, using GCP Cloud Logging and Monitoring for telemetry.

### Incident 5: AI-Generated Architecture Insights (demo03)
- **Postmortem:** [Visual Investigation](demos/online-boutique-visual-investigation/postmortem-final.md)
- **Summary:** Used Gemini's multimodal capabilities to generate and annotate architecture diagrams representing the incident's impact.
- **Why it's cool:** Demonstrates using `nano-banana` to bridge the gap between abstract logs and visual system understanding during a complex service-mesh failure.
