# V2 SQS/Worker reconciliation

`gitops/observability/v2-sqs-workers` contains the byte-identical alert rules and dashboard from the pinned canonical observability commit in `gitops/releases/v2-sqs-workers-source.json`. Changes to PromQL/dashboard definitions belong in cosmotech-observability first; update this release bundle after its CI passes.

Bootstrap only the two objects from this directory after review/CI and install the `argocd-observability-v2.json` Role/RoleBinding from cosmotech-kubernetes-rbac. The role permits patch/update of those names only; it cannot create or delete objects. Deletion needs deliberate bootstrap again. Then install the two observability-v2 project/application manifests in the management Argo namespace. They use the existing cluster/repository identity and signature verification, with automatic self-heal and pruning disabled. No workloads, volumes, namespace, networking or credentials are managed here.

Check Application revision and Synced/Healthy, live PrometheusRule names and manager annotation, then Prometheus `/api/v1/rules` for all eight healthy rules and authenticated Grafana dashboard/datasource requests. Kubernetes reconciliation alone does not certify rule evaluation while Prometheus or Grafana is unavailable.
