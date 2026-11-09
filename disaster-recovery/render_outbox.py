"""Compile a PASSIVE outbox runtime overlay after verified Ohio image publication.
No Kubernetes/GitHub/AWS mutation. The current primary delivery paths are untouched.
"""
import argparse
import copy
import json
from pathlib import Path
import re

IMAGE = r'414053644145\.dkr\.ecr\.us-east-2\.amazonaws\.com/cosmotech-dr-orders-outbox@sha256:[a-f0-9]{64}'


def render(image):
    if not re.fullmatch(IMAGE,image):raise ValueError('Verified immutable Ohio outbox image required')
    bundle=json.loads((Path(__file__).parent/'rendered/resources.json').read_text())
    control={'mode':'pause','region':'us-east-2','epoch':0,'expires_at':0}
    for ns in ['orders-api','orders-worker']:
        bundle['items'].append({'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'dr-writer-activation','namespace':ns},'data':{'activation.json':json.dumps(control)}})
    deployments={v['metadata']['name']:v for v in bundle['items'] if v['kind']=='Deployment'}
    for name,mode in [('orders-api','api'),('orders-worker','worker')]:
        dep=deployments[name];dep['spec']['replicas']=0
        dep['metadata']['annotations']={'cosmotech.io/dr-contract':'durable-outbox-v1'}
        pod=dep['spec']['template']['spec'];container=pod['containers'][0]
        container.update(image=image,command=['python','-m','src.disaster_recovery.runtime',mode])
        container['env']=[{'name':'AWS_REGION','value':'us-east-2'},{'name':'DR_OUTBOX_TABLE','value':'cosmotech-dr-outbox'},
            {'name':'DR_QUEUE_URL','value':'https://sqs.us-east-2.amazonaws.com/414053644145/cosmotech-dr-passive-orders'},
            {'name':'DR_ACTIVATION_FILE','value':'/dr-control/activation.json'},{'name':'RELEASE_VERSION','value':image.split('@')[1]}]
        container['volumeMounts']=[{'name':'dr-control','mountPath':'/dr-control','readOnly':True}]
        pod['volumes']=[{'name':'dr-control','configMap':{'name':'dr-writer-activation'}}]
    for name,mode,account in [('dr-outbox-publisher','publisher','dr-outbox-publisher'),('dr-outbox-metrics','metrics','dr-outbox-metrics')]:
        bundle['items'].append({'apiVersion':'v1','kind':'ServiceAccount','metadata':{'name':account,'namespace':'orders-api'}})
        dep=copy.deepcopy(deployments['orders-api']);dep['metadata'].update(name=name,labels={'app':name})
        dep['spec']['selector']['matchLabels']={'app':name}
        dep['spec']['template']['metadata']['labels']={'app':name}
        pod=dep['spec']['template']['spec'];pod['serviceAccount']=pod['serviceAccountName']=account
        c=pod['containers'][0];c.update(name=name,command=['python','-m','src.disaster_recovery.runtime',mode])
        c['resources']={'requests':{'cpu':'50m','memory':'128Mi'},'limits':{'cpu':'300m','memory':'256Mi'}}
        for field in ['ports','readinessProbe','livenessProbe','startupProbe']:
            c.pop(field,None)
        if mode=='metrics':
            dep['spec']['template']['metadata']['annotations']={'sidecar.istio.io/inject':'false'}
            c['ports']=[{'containerPort':9090,'name':'metrics'}]
            c['livenessProbe']={'httpGet':{'path':'/health/live','port':'metrics'},'periodSeconds':10}
        bundle['items'].append(dep)
    bundle['items'] += [
        {'apiVersion':'v1','kind':'Service','metadata':{'name':'dr-outbox-metrics','namespace':'orders-api','labels':{'app':'dr-outbox-metrics'}},'spec':{'type':'ClusterIP','selector':{'app':'dr-outbox-metrics'},'ports':[{'name':'metrics','port':9090,'targetPort':'metrics'}]}},
        {'apiVersion':'monitoring.coreos.com/v1','kind':'ServiceMonitor','metadata':{'name':'dr-outbox-metrics','namespace':'orders-api','labels':{'release':'monitoring'}},'spec':{'selector':{'matchLabels':{'app':'dr-outbox-metrics'}},'endpoints':[{'port':'metrics','path':'/metrics','interval':'60s'}]}},
        {'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':{'name':'dr-observability-scrape','namespace':'orders-api'},'spec':{'podSelector':{'matchLabels':{'app':'dr-outbox-metrics'}},'policyTypes':['Ingress'],'ingress':[{'from':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'observability'}}}],'ports':[{'protocol':'TCP','port':9090}]}]}}
    ]
    # Private recovery evidence stays on encrypted/Retain storage, never a ConfigMap.
    bundle['items'] += [
        {'apiVersion':'v1','kind':'ServiceAccount','metadata':{'name':'dr-outbox-reconciler','namespace':'orders-api'}},
        {'apiVersion':'v1','kind':'PersistentVolumeClaim','metadata':{'name':'dr-recovery-evidence','namespace':'orders-api'},'spec':{'storageClassName':'gp3-retain','accessModes':['ReadWriteOnce'],'resources':{'requests':{'storage':'5Gi'}}}},
        {'apiVersion':'batch/v1','kind':'Job','metadata':{'name':'dr-journal-replay-preparation','namespace':'orders-api'},'spec':{'suspend':True,'backoffLimit':0,'template':{'metadata':{'labels':{'app':'dr-journal-reconciler'},'annotations':{'sidecar.istio.io/inject':'false'}},'spec':{'restartPolicy':'Never','serviceAccountName':'dr-outbox-reconciler','securityContext':{'runAsNonRoot':True,'runAsUser':10001,'runAsGroup':10001,'fsGroup':10001,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'plan-only','image':image,'command':['python','scripts/dr/apply_replay.py','--source','/recovery/source.json','--report','/recovery/report.json','--epoch','0'],'env':[{'name':'AWS_REGION','value':'us-east-2'},{'name':'DR_OUTBOX_TABLE','value':'cosmotech-dr-outbox'}],'resources':{'requests':{'cpu':'50m','memory':'128Mi'},'limits':{'cpu':'300m','memory':'256Mi'}},'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'volumeMounts':[{'name':'recovery','mountPath':'/recovery'}]}],'volumes':[{'name':'recovery','persistentVolumeClaim':{'claimName':'dr-recovery-evidence'}}]}}}}
    ]
    return bundle


def validate(bundle):
    assert 'us-east-1' not in json.dumps(bundle)
    for obj in bundle['items']:
        assert obj['kind'] not in {'Secret','ClusterRole','ClusterRoleBinding','HorizontalPodAutoscaler','Ingress'}
        if obj['kind']=='Deployment':
            assert obj['spec']['replicas']==0
            assert re.fullmatch(IMAGE,obj['spec']['template']['spec']['containers'][0]['image'])
        if obj['kind']=='Job':
            assert obj['spec']['suspend'] is True
            assert '--execute' not in obj['spec']['template']['spec']['containers'][0]['command']
        if obj['kind']=='ConfigMap' and obj['metadata']['name']=='dr-writer-activation':
            assert json.loads(obj['data']['activation.json'])['mode']=='pause'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',required=True)
    result=render(p.parse_args().image);validate(result);print(json.dumps(result,indent=2))
