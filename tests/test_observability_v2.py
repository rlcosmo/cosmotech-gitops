"""Check the exact reviewed alert/dashboard bundle and its ownership boundary."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def read(path):return json.loads((ROOT/path).read_text())

class ObservabilityV2Tests(unittest.TestCase):
    def test_bundle_retains_reviewed_observability_bytes(self):
        source=read('gitops/releases/v2-sqs-workers-source.json')
        self.assertEqual(source['commit'],'4b1512ce14fe3310e47afffa0e69cba3734f3072')
        folder=ROOT/'gitops/observability/v2-sqs-workers'
        self.assertEqual({p.name for p in folder.iterdir()},set(source['files']))
        for name,record in source['files'].items():
            self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),record['sha256'])
        rules=read('gitops/observability/v2-sqs-workers/alerts.json')
        names=[r['alert'] for g in rules['spec']['groups'] for r in g['rules']]
        self.assertEqual(set(names),{'CosmoTechSQSEvidenceUnavailable','CosmoTechSQSBacklog',
            'CosmoTechSQSOldMessages','CosmoTechSQSDLQ','CosmoTechWorkerFailures',
            'CosmoTechWorkerRetries','CosmoTechWorkerSlow','CosmoTechWorkerScrapeUnavailable'})
        self.assertEqual(len(names),8)
        self.assertEqual(rules['metadata']['labels']['release'],'prometheus')

    def test_reconciler_cannot_own_workloads_or_storage(self):
        project=read('gitops/bootstrap/observability-v2-project.json')['spec']
        app=read('gitops/bootstrap/observability-v2-application.json')['spec']
        self.assertEqual(project['clusterResourceWhitelist'],[])
        self.assertEqual(project['namespaceResourceWhitelist'],[{'group':'','kind':'ConfigMap'},
            {'group':'monitoring.coreos.com','kind':'PrometheusRule'}])
        self.assertEqual(project['destinations'],[app['destination']])
        self.assertEqual(app['destination']['namespace'],'observability')
        self.assertFalse(app['syncPolicy']['automated']['prune'])
        self.assertTrue(app['syncPolicy']['automated']['selfHeal'])
        self.assertTrue(project['signatureKeys'])
        for name in ['alerts.json','dashboard.json']:
            obj=read('gitops/observability/v2-sqs-workers/'+name)
            self.assertEqual(obj['metadata']['namespace'],'observability')
            self.assertEqual(obj['metadata']['name'],'cosmotech-v2-sqs-workers')
