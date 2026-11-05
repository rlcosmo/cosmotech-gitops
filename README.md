# cosmotech-gitops

Current DEV policy, explicitly authorized by the owner: API and worker deploy automatically after successful CI, with no human/GMUD approval. Approval stages will be implemented later. Technical tests, scan, immutable images and exact image-only promotion validation remain mandatory.

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

The main-branch deliver-dev workflow obtains its own short-lived OIDC role and
invokes the fixed CosmoTech-Sync-Orders-GitOps SSM document on the existing Argo
host. It reconciles versioned AppProject/Application configuration and checks
Synced/Healthy at the exact main revision. It never patches EKS Deployment images.
Only the fixed document and dedicated host can be reached by this CI role.
Namespaced application delivery remains owned by Argo CD.

Cloudflare DNS already resolves both hosts to the existing ALB. The infrastructure
WAF rules permit these exact hosts with per-IP rate limits, preserving all existing
rules. Worker serves health only; API is the SQS entrypoint.

Image-only auto-promotion validates one selected app path and an exact successful
source SHA/digest. API policy stays scoped to API; the worker has a separate
policy and callers use --application orders-worker. General configuration changes run manifest validation and deploy automatically
from main without reviewer gates; the image bot remains limited to image-only
changes. CI validates HPA,
hosts and service/probe wiring for every application plus negative promotion
tests for extra files, namespace changes, pod changes, unpinned images and wrong
digests. Recovery: pause sync/promotion, revert the previous validated image and
configuration in Git, then observe Argo and HPA. Preserve queues/tables/inventory.

## Origem das aplicações

A configuração oficial das aplicações fica em `deploy/dev` dos repositórios `cosmotech-orders-api` e `cosmotech-orders-worker`. Os diretórios `gitops/apps/*/dev` são espelhos gerados pela esteira a partir do SHA que passou pelos testes, incluindo imagem imutável, ConfigMap, Service, HPA e Ingress. `gitops/releases` registra a proveniência do conjunto completo; a promoção automática confere cada arquivo contra o conjunto construído no CI de origem.
