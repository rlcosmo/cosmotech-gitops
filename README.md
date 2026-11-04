# cosmotech-gitops

Current DEV pilot, explicitly authorized by the owner: no human/GMUD approval is required for Orders API image-only promotion. No approval is fabricated. This supersedes the earlier mandatory-gate configuration for `orders-api-dev` only.

- Policy: gitops/environments/dev/release-policy.json, restricted to the Orders API deployment in namespace orders-api.
- GitHub App validates successful CI, exact SHA/digest and an image-only diff, then merges the PR when DEV_AUTO_PROMOTE=true in cosmotech-orders-api.
- Argo Application: gitops/bootstrap/orders-application.yaml, automatic sync enabled, pruning disabled, self-heal enabled. The dedicated EC2/K3s manages the application EKS cluster.
- The automated validation workflow has no reviewer/Environment jobs. Existing public-index approvals and unrelated service controls are unchanged.

Initial image PR #1 was merged by the App at be3b7bf; previous guard-change PR #2 was closed without merge because the owner changed the DEV policy. Branches/history remain available. No paid GitHub feature or repository visibility change occurred.

Apply the versioned bootstrap Application/AppProject to namespace argocd on the dedicated management K3s when changing delivery policy. These are management resources; application Deployments are reconciled only by Argo CD. Do not use the frozen main-repository manifests to deploy.

To pause: set DEV_AUTO_PROMOTE=false, set auto_promote=false in the DEV policy, set Application syncPolicy.automated.enabled=false and apply the management configuration. For application rollback, propose a previously validated immutable image in GitOps and let Argo reconcile; never force sync/prune or directly patch the EKS Deployment.
