# about-sre-extension

## Motivation

Incidents in complex production environments, such as large Kubernetes clusters, demand rapid response and deep system understanding. Site Reliability Engineers (SREs) often need to quickly gather and synthesize information from various sources like logs, metrics, and cluster states to diagnose and mitigate issues effectively.

The SRE Extension for Gemini CLI aims to streamline and accelerate this process. Its motivation is to:

1. Reduce Time to Mitigation: By integrating deep expertise in cloud operations (initially focused on GCP and gcloud) and observability directly into the terminal, the extension helps SREs minimize Mean Time To Detection (MTTD) and Resolution (MTTR).
2. Automate Data Aggregation: During an incident, the extension can rapidly collect and correlate data points from Cloud Logging, Cloud Monitoring, and the Kubernetes cluster state, providing a unified view and event timeline.
3. Leverage AI for Insights: The extension uses AI-driven troubleshooting to analyze the aggregated data, generate intelligent hypotheses about potential root causes, and suggest pre-vetted, low-risk mitigation strategies.
4. Ensure Safe Operations: While automating analysis, any proposed changes or mitigations require explicit "human in the loop" confirmation, ensuring engineers retain control and oversight before any production modifications are made.
5. Improve Organizational Learning: Post-incident, the extension facilitates the automatic compilation of blameless postmortems using the data collected during the event, helping to transform transient details into structured, actionable knowledge for the team.

Ultimately, this extension is designed to empower SREs with an intelligent, terminal-native assistant to navigate incidents more efficiently and improve the reliability of their services.


## Results

To test our SRE Extension setup. We have run a simulated incident scenarios:

### Simulated Incident 1: Random 500s (Istio Service Discovery Failure)

- **Postmortem:** [Istio Service Discovery Failure](demos/20260409-demo06a/post-mortem/postmortem-final.md)
- **Summary:** In a compelling demonstration of autonomous operation, the SRE Extension independently investigated a scenario involving HTTP 500 errors and cascading failures in the application. By analyzing logs and cluster state, it identified a faulty Istio `VirtualService` with a 100% abort fault and uncovered a latent instability in the Istio control plane causing name resolver errors. The detailed postmortem linked above was synthesized entirely by the extension, showcasing its ability to handle complex, multi-layered service mesh issues.
- **Root Cause:** A combination of a fault injection policy and Istio control plane instability leading to zero addresses for the product catalog service.
- **Resolution:** The extension identified the faulty `VirtualService` which was then deleted, and suggested restarting the frontend canary to refresh the Istio sidecar config.

### Simulated Incident 2: Online Boutique Cluster Outage

- **Postmortem:** [Online Boutique Cluster Outage](demos/20260414-outage/postmortem-final.md)
- **Summary:** In this complex scenario, the SRE Extension demonstrated its capacity to reconstruct a multi-staged incident involving both application and infrastructure layers. The incident escalated from intermittent errors to a complete site outage. The extension autonomously diagnosed a "poisonous" canary deployment with an environment variable typo and isolated a high-priority VPC firewall rule blocking external traffic. It synthesized a detailed timeline and postmortem, proving its value in reducing MTTR across diverse infrastructure components.
- **Root Cause:** A typo in the canary deployment environment variables and a Priority 1 DENY firewall rule blocking external traffic on ports 80, 443, and 8080.
- **Resolution:** The extension recommended deleting the faulty canary and removing the restrictive firewall rule, restoring full service.


## Execution Safety

During the investigation and mitigation of these simulated incidents, execution safety was strictly enforced:
- **Operator Control:** All investigations and mitigations were controlled and monitored by an SRE operator.
- **Custom Policies:** The SRE Extension operates under custom policies that define allowed read and write actions.
- **Human Approval:** The extension enforces explicit human engineer approval for sensitive or potentially destructive actions, ensuring safe operations.

## Get Notified

This repository serves as an overview of SRE Extension capabilities. If you are interested in the project and would like to be notified when the SRE Extension is released, please **star** this repository. If you want to leave feedback or have any questions, please open the issue or fill in this [form](https://forms.gle/1qqfCPv29TZtdj9e8)

## Our environment

We used the [ Microservices Demo](https://github.com/GoogleCloudPlatform/microservices-demo?tab=readme-ov-file#architecture) repository. The service runs on Google Kubernetes Engine (GKE), and telemetry and logs were stored in GCP Cloud Logging and Monitoring.
