import json
from pathlib import Path
import unittest


class PrivateHttpsUpstreamTests(unittest.TestCase):
    def test_only_existing_gateway_nodeports_and_two_known_hosts(self):
        items=json.loads((Path(__file__).parent/'ingress/resources.json').read_text())['items']
        self.assertEqual({o['kind'] for o in items},{'Service','Gateway','VirtualService'})
        self.assertTrue(all(o['metadata']['namespace']=='istio-system' for o in items))
        service=next(o for o in items if o['kind']=='Service')
        self.assertEqual(service['spec']['type'],'NodePort')
        self.assertEqual(service['spec']['selector'],{'istio':'dr-ingress'})
        self.assertEqual({p['nodePort'] for p in service['spec']['ports']},{31080,31521})
        hosts={h for o in items if o['kind']=='VirtualService' for h in o['spec']['hosts']}
        self.assertEqual(hosts,{'orders-api-dev.cosmotechsolutions.com.br','grafana.cosmotechsolutions.com.br'})
        self.assertNotIn('us-east-1',json.dumps(items))
