# Isolated passive DR — V2-003

Only deploy to the NEW `cosmotech-dr` EKS in account 414053644145/us-east-2.
These files are outside `gitops/**`, `scripts/**` and `tests/**`, so merging this
change does not trigger the primary `deliver-dev` push workflow. Existing DEV
manifests, image releases, promotion policy and primary Application are unchanged.

`rendered/resources.json`: immutable secondary ECR digests copied from approved
primary release evidence, regional queue/table configuration, zero API/Worker
replicas, worker control `pause`, no HPA, no primary Ingress and no static secrets.
Istio routing is ClusterIP/internal only, with strict mTLS. Public traffic/DNS
switching is not part of this deployment. NetworkPolicy requires the destination
VPC CNI network policy agent enabled by the DR Terraform module.

`bootstrap.json`: create a SEPARATE local Argo project/application in the standby;
automatic sync/prune/self-heal are off. Run `render_bootstrap.py --revision <reviewed-full-commit>` before first sync;
the source placeholder cannot resolve a Git revision and fails closed. subsequent activation needs a new
immutable DR-only change and independently verified fencing/integrity evidence.
No primary HPA or Argo ignore-replicas rule is inherited. Do not point this local
project at the primary API server. Apply nothing while the AWS account is restricted.

Images are NOT present in the secondary just because manifests reference them.
Infrastructure `scripts/dr/copy_images.py` provides a gated digest-preserving copy;
verify the destination digest before any pods start. Synthetic replay/inventory
must use the isolated destination table/queues; no primary queue consumption.

Platform, storage/backup, account-release, fencing, end-to-end tests, failover and
failback instructions are maintained in infrastructure `docs/dr/runbooks.md` and
`docs/dr/architecture.md`. Runtime activation/restore tests remain pending AWS release.

Validation: `python disaster-recovery/validate.py`; existing unit tests also pass.
A new validation-only workflow has no AWS identity and no deploy/sync job.

## Durable outbox runtime (continuation)

The companion infrastructure runtime accepts HTTP 202 only after DynamoDB journal
commit. Its API, publisher, metrics exporter and unchanged pinned worker processor
are built into a SEPARATE DR image. No primary application repository or deployment
is changed. Current images/manifests remain legacy, passive and NOT outbox-enabled.

After AWS release, scoped infrastructure creation, source/image scan and immutable
ECR publication, compile the complete replacement bundle with:

```
python disaster-recovery/render_outbox.py --image <verified-Ohio-outbox-repository@sha256:digest>
```

The renderer requires the exact `cosmotech-dr-orders-outbox` repository in Ohio,
keeps ALL replicas zero and both namespace activation files paused. It does not
modify the committed manifests or apply/sync anything. Review/commit the output to
the DR-only rendered path before Argo sync. Publish digest must be verified from
ECR; fixture hashes used in validation do not represent real published images.

Activation requires the same independently fenced epoch in the two namespace
control objects, `mode=run` and an expiry within five minutes, renewed only by an
authorized DR operator. Expiry drains publishers/workers and stops API acceptance;
this is an operational lease, NOT a cross-region fence. Stock/order checkpoints
remain transactional in the restored table; external payment/shipping providers
would require their own idempotency keys. No SQS exactly-once guarantee is made.

## Ohio platform recovery, 2026-11-12

`platform-bootstrap.json` pins the eight Helm releases from `platform-lock.json`.
`render_platform_bootstrap.py --revision <reviewed-full-SHA>` creates local-cluster-only
projects/apps for the platform, five restored PV/PVC pairs, dashboards and paused
Orders/outbox runtime. Sync remains manual, pruning disabled. The platform project
has a separate cluster-resource allowlist; Orders receives no cluster RBAC privilege.

The five restored EBS volumes remain in us-east-2b with Retain and exact CSI volume
IDs. The zonal node pool is managed by Terraform. Never edit affinity to claim an
EBS volume resides elsewhere. Grafana uses the restored database, original four
source UIDs and a separately generated regional admin Secret; do not commit secrets.
Argo ignores runtime Secret data so adoption preserves existing credentials.

Observed recovery: Grafana database healthy, 37 dashboards / two folders, anonymous
search denied; Prometheus/Loki/Tempo data sources healthy. A real OTLP trace and log
were accepted and subsequently queried from Tempo and Loki. This is telemetry
validation, not a regional failover or an RTO/RPO measurement. GLPI/Kestra/Zabbix,
source journal replication, writer fencing, regional routing and real failover/
failback still require validation before declaring the complete platform recovered.
