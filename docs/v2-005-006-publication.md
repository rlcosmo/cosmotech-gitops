# V2-005 / V2-006 — prepared publication, operationally blocked

**Do not merge this draft until AWS access and the operational prerequisites below are verified.** The existing Argo application automatically syncs main. This branch does not change any Application, project permission, workflow, approval/release policy, Orders workload, node group, storage, Power Manager or DR resource.

Observability source PRs #7, #8 and #9 passed CI and merged; original audited ConfigMaps use source commit `53159b7dce2364399e64b9fbbb2afee9456148de`, and the GMUD timeline uses `af42adbf821faeb490c4ed92df0367852f7d2cfa` in `rlcosmo/cosmotech-observability`. The source provenance manifest retains the exact old dashboard and eight alert-rule bytes, and adds per-file commit/SHA256 for four new/revised ConfigMaps.

The four ConfigMaps contain:

- `cosmotech-gmud-24h`: one new governed GMUD 24h dashboard; no existing dashboard duplicate.
- `cosmotech-worker-canary-dashboard`: the existing Canary UID with separate inflight and draining targets, preserving all 12 panels.
- `grafana-dashboard-lab`: existing account cost/tool dashboards preserved, with corrected retention documentation only.
- `prometheus-kube-prometheus-grafana-overview`: existing Grafana UID and panels, replacing the absent legacy alert evaluation metric by the actual alert-state gauge.

The existing chart dashboard ConfigMaps are deliberately retained by name, and existing manually managed Canary UID is adopted into provisioning. Do not introduce a second provisioned file with the same UID. A future Helm chart upgrade must retain these reviewed overrides. Prune stays disabled; no original dashboard is deleted.

The GMUD observer runs on the existing private ITSM host and reads native signed GLPI changes using the existing read adapter. The rolling window uses original UTC business event times, not retry deliveries or synthetic counter initialization. Approval/deployment/closure are separate. Actual completed deployment requires recorded technical validation. The source also includes the private Nginx endpoint, systemd units, installer, ServiceMonitor endpoint manifest and controlled offline tests. This Argo project intentionally cannot own ServiceMonitors; that additive endpoint must be applied through the existing observability owner after validating the host collector. No RBAC expansion is included.

## Blocking evidence and resume gate

The last successful baseline (2026-11-09) contains 37 dashboards / 461 panels, 15 native GLPI Changes, 13 signed governed GMUDs and zero governed events in the previous 24h. This is dated evidence, **not current state**. The prepared new dashboard is expected at `https://grafana.cosmotechsolutions.com.br/d/cosmotech-gmud-24h`; the URL has not been operationally verified.

AWS sign-in subsequently reported account suspension. AWS API credentials are invalid and EKS/Grafana became unreachable. The user-provided suspension page does not establish whether the cause is billing or another account issue. No workaround was attempted. AWS account owner must resolve the suspension through the official account/support process.

Before merging:

1. Verify authenticated AWS access, live EKS/Grafana/Prometheus/Tempo/Loki/Collector and existing Zabbix incident recovery. Do not change protected infrastructure.
2. Read SSM command `be62d75e-3717-483c-9c42-f666cde27319`; terminal installation result is unknown. Do not replay blindly. Verify installed hashes, timer and real `/gmud-metrics` output.
3. Compare current native GLPI records and real metrics. Zero is valid only with successful fresh collection. Apply only the reviewed additive ServiceMonitor endpoint from observability source after confirming its current owner/configuration.
4. Keep all CI checks passing, merge this PR, then verify the signed main revision is Argo Synced/Healthy. Verify existing UIDs remain and one GMUD UID is added.
5. Run all panel and variable queries again, check the three corrected panels, and capture real updated Grafana screens. Test fixtures must never be published as real metrics or events.
6. Record final per-panel classifications and operational acceptance; neither V2-005 nor V2-006 is complete until these checks pass.

## Baseline capture

[Actual authenticated Canary capture before changes](evidence/v2-005-006/baseline-canary.png). This is the original live dashboard, not a mockup or a screenshot of the unpublished GMUD dashboard. New screenshots are blocked by the account suspension.

Full sanitized baseline and prepared-source documentation: `cosmotech-observability/docs/evidence/v2-005-006/` and `docs/v2-005-006-gmud-and-audit.md`.

## Completed offline validation

47 observability tests passed locally and in CI (runs `42654492901`, `42686788436`, `42687387911`). GitOps source integrity and application constraints passed all 13 tests locally, plus both draft PR CI checks. The historical fixture reconciles 13 changes / five automatic / eight manual approvals / ten validated deploys / three rollbacks, with no fixture events emitted to live telemetry. Timeline seconds are converted to Grafana milliseconds, and rolling-hour buckets include partial boundary hours. Source failure removes old business zeros and logs no credential content.

Account suspension still blocks all final operational acceptance, new dashboard captures and fresh counts. The installation command result and current pods/datasources/Argo/Zabbix state remain unknown.
