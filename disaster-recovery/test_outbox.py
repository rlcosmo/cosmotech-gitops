import unittest
from render_outbox import render,validate

IMAGE='414053644145.dkr.ecr.us-east-2.amazonaws.com/cosmotech-dr-orders-outbox@sha256:'+'a'*64

class PassiveOutboxTests(unittest.TestCase):
    def test_scope_paused_state_roles_and_suspend(self):
        bundle=render(IMAGE);validate(bundle)
        pods={r['metadata']['name']:r for r in bundle['items'] if r['kind']=='Deployment'}
        self.assertEqual(set(pods),{'orders-api','orders-worker','dr-outbox-publisher','dr-outbox-metrics'})
        for name,mode in [('orders-api','api'),('orders-worker','worker'),('dr-outbox-publisher','publisher')]:
            self.assertEqual(pods[name]['spec']['template']['spec']['containers'][0]['command'][-1],mode)
        job=next(r for r in bundle['items'] if r['kind']=='Job')
        self.assertTrue(job['spec']['suspend'])
        self.assertNotIn('--execute',job['spec']['template']['spec']['containers'][0]['command'])

    def test_primary_mutable_and_wrong_repository_images_rejected(self):
        for image in [IMAGE.replace('us-east-2','us-east-1'),IMAGE.split('@')[0]+':latest',IMAGE.replace('orders-outbox','orders-api')]:
            with self.assertRaises(ValueError):render(image)
