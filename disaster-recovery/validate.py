"""Offline Kubernetes/GitOps scope, image and passive-state validation."""
import json
from pathlib import Path
import re
root=Path(__file__).parent
objects=json.loads((root/'rendered/resources.json').read_text())['items']
lock=json.loads((root/'release-lock.json').read_text())
assert lock['region']=='us-east-2' and lock['mode']=='passive'
for obj in objects:
    assert obj['kind'] not in {'Secret','Ingress','HorizontalPodAutoscaler','ClusterRole','ClusterRoleBinding'}
    assert obj['metadata'].get('namespace',obj['metadata']['name']) in {'orders-api','orders-worker'}
    assert 'us-east-1' not in json.dumps(obj)
    if obj['kind']=='Deployment':
        assert obj['spec']['replicas']==0
        pod=obj['spec']['template']['spec']
        assert pod['securityContext']['runAsNonRoot']
        for c in pod['containers']:
            assert re.fullmatch(r'414053644145\.dkr\.ecr\.us-east-2\.amazonaws\.com/[a-z0-9-]+@sha256:[a-f0-9]{64}',c['image'])
            assert c['image']==lock['images'][obj['metadata']['name']]
            assert c['securityContext']['readOnlyRootFilesystem']
            assert c['readinessProbe'] and c['livenessProbe']
boot=json.loads((root/'bootstrap.json').read_text())['items'][-1]
assert boot['spec']['destination']['server']=='https://kubernetes.default.svc'
assert boot['spec']['source']['path']=='disaster-recovery/rendered'
assert not boot['spec']['syncPolicy']['automated']['enabled']
print('PASS: passive DR manifests, local cluster, immutable secondary digests, no primary endpoints/secrets/HPA/Ingress')
