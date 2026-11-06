# CosmoTech — GitOps com Argo CD

Repositório de configuração e entrega declarativa das aplicações **Orders API** e **Orders Worker** no Amazon EKS. O GitHub Actions valida e publica imagens; o GitHub App propõe alterações de imagem; o Argo CD aplica as versões desejadas no cluster.

## Política atual de DEV

A política DEV autorizada permite publicação automática após CI bem-sucedido, **sem aprovação humana ou GMUD** nesta fase. Aprovações poderão ser incorporadas posteriormente. Testes, análise de segurança, imagens imutáveis e validação exata de alterações de imagem continuam obrigatórios.

- Política API: `gitops/environments/dev/release-policy.json`, restrita ao Deployment Orders API no namespace `orders-api`.
- GitHub App: confere CI, SHA/digest e diff exclusivo de imagem; mescla a proposta quando `DEV_AUTO_PROMOTE=true` na API.
- Application: `gitops/bootstrap/orders-application.yaml`, com sincronização automática e autocorreção habilitadas, mas sem pruning.
- O Argo CD roda em K3s numa EC2 dedicada de gerenciamento e reconcilia o EKS.

A proposta inicial de imagem PR #1 foi mesclada no commit `be3b7bf`. A PR #2 de alteração de proteção foi encerrada sem merge após mudança da política DEV. O histórico permanece disponível.

## Como alterar a política de entrega

Revise a política versionada e aplique os recursos bootstrap Application/AppProject no namespace `argocd` do K3s de gerenciamento. **Não utilize os manifests congelados do repositório principal** para fazer deploy. Deployments de aplicações devem ser reconciliados somente pelo Argo CD.

Para suspender a automação, configure `DEV_AUTO_PROMOTE=false`, `auto_promote=false` na política DEV e `syncPolicy.automated.enabled=false` na Application; aplique a configuração de gerenciamento. Para rollback, proponha no GitOps uma imagem imutável anterior validada. Não force sync/prune nem edite diretamente o Deployment EKS.

## Aplicações, hosts e escalabilidade

| Aplicação | Host HTTPS | Capacidade |
| --- | --- | --- |
| Orders API | `orders-api-dev.cosmotechsolutions.com.br` | Verificar HPA vigente |
| Orders Worker | `orders-worker-dev.cosmotechsolutions.com.br` | Verificar HPA vigente |

O histórico descrevia HPA entre 1 e 4 réplicas com alvo CPU de 70%; os READMEs atuais das aplicações documentam **duas réplicas fixas em DEV**. Consulte sempre o manifesto sincronizado antes de alterar capacidade. O Worker expõe apenas `/health/live` e `/health/ready`; eventos de negócio entram pela API e seguem via SQS. CPU não representa backlog da fila. A redução de escala tem estabilização de 300 segundos; mais réplicas podem elevar custos.

Os manifests de aplicações omitem `spec.replicas` para não disputar escala com o HPA. O Argo ignora esse campo com `RespectIgnoreDifferences=true`. Permissões RBAC para HPA, Ingress e visualização dos workloads são mantidas em [cosmotech-kubernetes-rbac](https://github.com/rlcosmo/cosmotech-kubernetes-rbac), limitadas aos namespaces necessários.

## Entrega e verificações

O workflow `deliver-dev` na branch `main` obtém credenciais OIDC temporárias e chama o documento SSM `CosmoTech-Sync-Orders-GitOps` no host Argo existente. Reconcilia AppProject/Application versionados e verifica `Synced/Healthy` na revisão exata de `main`. Essa role CI só alcança o documento e host permitidos; não altera imagens diretamente no EKS.

Os dois hosts já resolvem pelo Cloudflare DNS para o ALB existente. O WAF permite esses hosts com limites de requisições por IP, preservando regras anteriores.

A promoção de imagens é separada por aplicação: a API mantém sua própria política e o Worker usa `--application orders-worker`. Mudanças gerais de configuração passam por validação de manifests e entrega automática de `main`; o bot de imagens só altera referências de imagem. A validação cobre HPA, hosts, Services, probes e cenários negativos como arquivos extras, mudança de namespace, alterações indevidas em Pods e digest incorreto.

## Recuperação

1. Suspenda sincronização e promoção automática.
2. Reverta imagem e configuração para uma versão previamente validada no Git.
3. Observe o estado do Argo CD, HPA, endpoints e logs.
4. Preserve filas SQS, tabelas DynamoDB e inventário; não apague dados para corrigir rollout.

## Origem das aplicações

A configuração oficial das aplicações fica em `deploy/dev` dos repositórios `cosmotech-orders-api` e `cosmotech-orders-worker`. Os diretórios `gitops/apps/*/dev` são espelhos gerados pela esteira a partir do SHA que passou pelos testes, incluindo imagem imutável, ConfigMap, Service, HPA e Ingress. `gitops/releases` registra a proveniência do conjunto completo; a promoção automática confere cada arquivo contra o conjunto construído no CI de origem.
