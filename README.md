> View this on GitHub: [https://github.com/palladius/about-sre-extension](https://github.com/palladius/about-sre-extension)

# About SRE Extension

## Motivation

SRE Extension is now LIVE since 2026-04-16! Check https://github.com/gemini-cli-extensions/sre 

The SRE Extension for Gemini CLI streamlines incident response by integrating deep cloud expertise and observability directly into the terminal. It automates data aggregation from Cloud Logging, Monitoring, and Kubernetes to provide a unified timeline, uses AI to generate hypotheses and suggest low-risk mitigations, and facilitates the automatic creation of blameless postmortems—all while maintaining human-in-the-loop control for safe operations.

## Results

We have validated the SRE Extension across several simulated incident scenarios:

### Incident 1: Frontend Canary Typo (Bluegreen - demo01) (March 30, 2026)
- **Postmortem:** [View Report](demos/20260330-bluegreen-typo/postmortem-final.md)
- **Summary:** A typo in the frontend-canary environment variable caused 11 hours of intermittent 500 errors.
- **Why it's cool:** Features an amazing "U-Shape" traffic graph showing the impact and the satisfying recovery after the patch.

### Incident 2: The "Four-Headed Hydra" Complex Failure (April 2, 2026)
- **Postmortem:** [Four-Headed Hydra Postmortem](demos/20260402-four-headed-hydra/postmortem-final2.md)
- **Summary:** Investigated a "Hydra" of failures including OTel collector misconfiguration, an Istio "blackhole," and GKE node churn.
- **Why it's cool:** Uses high-resolution incident visualizations and an engaging, emoji-rich narrative that showcases the AI's "personality."

### Incident 3: AI-Generated Architecture Insights (demo03) (April 2, 2026)
- **Postmortem:** [Visual Investigation](demos/20260402-visual-investigation/postmortem-final.md)
- **Summary:** Used Gemini's multimodal capabilities to generate and annotate architecture diagrams representing the incident's impact.
- **Why it's cool:** Demonstrates using `nano-banana` to bridge the gap between abstract logs and visual system understanding during a complex service-mesh failure.

### Incident 4: The "Triple-Threat" Simultaneous Outage (April 4, 2026)
- **Postmortem:** [Triple-Threat Investigation](demos/20260404-triple-threat/postmortem-final.md)
- **Summary:** Handled three overlapping failures: a rogue firewall rule, an Istio fault injection, and a deployment typo, using event correlation to distinguish network vs. app layers.
- **Why it's cool:** Features complex, annotation-heavy graphs proving deep technical correlation across the entire stack.

### Incident 5: Random 500s (Istio Service Discovery Failure) (April 9, 2026)
- **Postmortem:** [Istio Service Discovery Failure](demos/20260409-demo06a/post-mortem/postmortem-final.md)
- **Summary:** Independently investigated HTTP 500 errors and identified a faulty Istio `VirtualService` with a 100% abort fault, uncovering a latent instability in the Istio control plane.

### Incident 6: Online Boutique Cluster Outage (Firewall & Canary) (April 14, 2026)
- **Postmortem:** [Online Boutique Cluster Outage](demos/20260414-outage/postmortem-final.md)
- **Summary:** Autonomously diagnosed a "poisonous" canary deployment with an environment variable typo and isolated a VPC firewall rule blocking external traffic.

### Incident 7: Next26 demo with Alejandro (April 24, 2026)
- **Postmortem:** [Checkout Outage and Intermittent Frontend 500s](demos/next26-demo-with-alejandro/postmortem-final.md)
- **Summary:** Investigated a dual-failure scenario involving a total checkout outage due to a restrictive NetworkPolicy and intermittent 500 errors from a misconfigured canary deployment.
- **Why it's cool:** Showcases precise RCA using audit logs and connectivity timeout patterns to correlate multiple concurrent failures.

### Incident 8: The Edinburgh Investigation 🏴󠁧󠁢󠁳󠁣󠁴󠁿 - Checkout Outage (May 19, 2026)
- **Postmortem:** [Edinburgh Investigation Postmortem](demos/20260519-edinbra-investigation/postmortem-final.md)
- **Summary:** Investigated a total checkout failure triggered by a misconfigured `NetworkPolicy` and a broken canary deployment, showcasing rapid root cause analysis and mitigation.
- **Why it's cool:** Demonstrates end-to-end incident handling, from identifying dropped traffic and 500 errors to removing a "poisonous" network policy to restore 100% checkout availability.

### Incident 9: 🎬 The "Director's Cut" Checkout Outage (May 20, 2026)
- **Postmortem:** [Official Video Postmortem](demos/20260520-official-video-investigation/postmortem-final.md)
- **Summary:** Investigated a total checkout failure and a broken canary homepage. It was a tale of two tragedies: a poisonous NetworkPolicy and a configuration typo, brought to you in stunning high definition.
- **Why it's cool:** "Lights, Camera, Mitigation!" This is the official video investigation—recorded live for your viewing pleasure. Grab some popcorn and watch Gemini CLI perform rapid RCA and slay the outage monster on YouTube.

### Incident 10: 🏎️🎩 The FIRST Antigravity PostMortem (May 28, 2026)
- **Postmortem:** [First agy Postmortem](showcases/online-boutique-first-agy-pomo/postmortem-final.md)
- **Summary:** The historical first SRE investigation and PostMortem completed under the Antigravity CLI (`agy`) harness, diagnosing a restrictive Calico NetworkPolicy and canary pod DNS typo.
- **Why it's cool:** Features a high-fidelity dual-axis graph clearly overlaying the flat-lined checkout block (0% success rate) with the canary-depressed overall traffic success rate (~67%).

### Incident 11: GDG Cloud Zurich Demo (May 28, 2026)
- **Postmortem:** [GDG Cloud Zurich Postmortem](showcases/20260528-gdg-cloud-zrh-checkout-canary/postmortem-final.md)
- **Summary:** Handled a live GKE checkout outage (NetworkPolicy block) and a broken canary release (DNS name resolver typo)—spotted with the help of customer SRE Vlodimir—in front of 150 people at GDG Cloud Zurich.
- **Why it's cool:** Completed end-to-end diagnosis, hotfix, and high-fidelity graph generation completely live under 3 minutes, showing a beautiful recovery curve.

### Incident 12: Dual Outage In-Depth Analysis (June 1, 2026)
- **Postmortem:** [Dual Outage Postmortem](showcases/20260601-onlineboutique-dualoutage/postmortem-final.md)
- **Summary:** An in-depth telemetry analysis of a concurrent GKE checkout blackout (Calico blocking port 5050) and a flaky product catalog canary (DNS typo).
- **Why it's cool:** Features high-resolution transaction resampling demonstrating how round-robin balancing mathematically results in a measured ~60% success rate on the canary endpoint.

### Incident 13: GKE Outage Multi-Endpoint & Flaky Canary (June 1, 2026)
- **Postmortem:** [Bespoke 3-Panel Postmortem](showcases/INC20260601-outage/postmortem-final.md)
- **Summary:** Diagnosed a 100% GKE checkout blackout due to a restrictive ingress NetworkPolicy alongside a flaky catalog canary (DNS typo).
- **Why it's cool:** Displays a high-fidelity 3-panel incident graph cleanly overlaying the separate checkout and catalog availability drops on top of traffic.

## Execution Safety

Safety is strictly enforced:
- **Operator Control:** All mitigations are monitored by an SRE operator.
- **Custom Policies:** Access is limited by granular read/write policies.
- **Human Approval:** Explicit engineer approval is required for all sensitive actions.

## Get Notified

If you'd like to be notified when the SRE Extension is released, please **star** this repository or fill in this [form](https://forms.gle/1qqfCPv29TZtdj9e8).

## Our environment

Tests were conducted on the [Microservices Demo](https://github.com/GoogleCloudPlatform/microservices-demo) running on GKE, using GCP Cloud Logging and Monitoring for telemetry.
