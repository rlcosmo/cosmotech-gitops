# cosmotech-gitops

Canonical Argo CD applications and desired DEV manifests. Manual synchronization only. Do not merge release PRs or synchronize Orders until real GLPI/GMUD and the existing DEV, QA, PO/PM, Infra/SRE gates are approved. Current manifests capture the live deployment without changing its image.

Extracted from [aws-serverless-lab](https://github.com/rlcosmo/aws-serverless-lab) at `6f3e67f9e93d626393b23b6884b031767a63fea0` with original commit ancestry preserved. Original files remain available there as migration snapshots. No infrastructure was recreated by extraction.


## Release block

GitHub rejected required-reviewer protection for this private repository (HTTP 422, billing-plan support) and branch protection readback returned HTTP 403 requiring a compatible plan. Only an empty dev environment was created; no effective reviewer protection is claimed. The release workflow now verifies all four real reviewer rules and branch enforcement before any gate can run; absent/unsupported protection fails closed. Argo CD auto-sync is disabled and no release has been synchronized. Keep repositories private. The owner must enable a plan supporting these exact private-repository protections and configure/read back all four gates before release. No billing change or approval was simulated.
