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
