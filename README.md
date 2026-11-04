# cosmotech-gitops

Current DEV pilot, explicitly authorized by the owner: no human/GMUD approval is required for Orders API image-only promotion. No approval is fabricated. This supersedes the earlier mandatory-gate configuration for `orders-api-dev` only.

- Policy: gitops/environments/dev/release-policy.json, restricted to the Orders API deployment in namespace orders-api.
- GitHub App validates successful CI, exact SHA/digest and an image-only diff, then merges the PR when DEV_AUTO_PROMOTE=true in cosmotech-orders-api.
- Argo Application: gitops/bootstrap/orders-application.yaml, automatic sync enabled, pruning disabled, self-heal enabled. The dedicated EC2/K3s manages the application EKS cluster.
- The automated validation workflow has no reviewer/Environment jobs. Existing public-index approvals and unrelated service controls are unchanged.

Initial image PR #1 was merged by the App at be3b7bf; previous guard-change PR #2 was closed without merge because the owner changed the DEV policy. Branches/history remain available. No paid GitHub feature or repository visibility change occurred.

Apply the versioned bootstrap Application/AppProject to namespace argocd on the dedicated management K3s when changing delivery policy. These are management resources; application Deployments are reconciled only by Argo CD. Do not use the frozen main-repository manifests to deploy.

To pause: set DEV_AUTO_PROMOTE=false, set auto_promote=false in the DEV policy, set Application syncPolicy.automated.enabled=false and apply the management configuration. For application rollback, propose a previously validated immutable image in GitOps and let Argo reconcile; never force sync/prune or directly patch the EKS Deployment.

## Orders Worker, HPA and application hosts

Worker source/CI: https://github.com/rlcosmo/cosmotech-orders-worker. API and worker
each declare an autoscaling/v2 HPA, Service, probes and shared-ALB HTTPS Ingress:

| Application | Host | HPA |
| --- | --- | --- |
| orders-api-dev | orders-api-dev.cosmotechsolutions.com.br | 1–4, container CPU 70% |
| orders-worker-dev | orders-worker-dev.cosmotechsolutions.com.br | 1–4, container CPU 70% |

The worker host serves only /health/live and /health/ready; business events arrive
through SQS. CPU scaling does not measure queue backlog. A healthy metrics-server
and ContainerResource metrics support are prerequisites. Scale-down waits 300s
and removes at most one replica/minute. More replicas can require extra node
capacity and increase AWS calls. No data schema, retry or retention changes.

Applications omit spec.replicas and bootstrap Applications ignore that field with
RespectIgnoreDifferences=true so Argo does not undo HPA scaling. The project
allows HPA/Ingress and workload tree visibility in exactly the two namespaces.
RBAC is delivered from cosmotech-kubernetes-rbac, not from app source.

Worker activation is deliberately disabled: its historical image lacks an HTTP
listener. Before enabling sync, configure the worker CI OIDC role and GitOps App
secret, successfully publish/promote a health-enabled digest, install the scoped
RBAC, extend the existing Argo cluster registration namespaces, and apply the
reviewed bootstrap project/Application on management K3s. API automated sync
remains defined as before; merge these configuration changes only after RBAC and
bootstrap are ready. No direct kubectl image patch is part of CI.

Cloudflare DNS CNAMEs for the two hosts and the infrastructure WAF allow/rate
rules must be deployed before testing public access. Ingress uses the existing
observability ALB and its wildcard certificate; it declares no new ALB. Hostnames
in Git are desired configuration, not evidence of working DNS/TLS or deployment.
See cosmotech-infrastructure-iac/docs/orders-worker-delivery.md for ordering.

Image-only auto-promotion validates one selected app path and an exact successful
source SHA/digest. API policy stays scoped to API; the worker has a separate
policy and callers use --application orders-worker. General configuration PRs
require review and are outside the image-only promotion path. CI validates HPA,
hosts and service/probe wiring for every application plus negative promotion
tests for extra files, namespace changes, pod changes, unpinned images and wrong
digests. Recovery: pause sync/promotion, revert the previous validated image and
configuration in Git, then observe Argo and HPA. Preserve queues/tables/inventory.
