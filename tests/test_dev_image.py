"""Exercise promotion restrictions against real Git diffs."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/validate_dev_image.py'


class ImagePromotionTests(unittest.TestCase):
    def check_promotion(self, app, mutate, expected):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()

            git('init', '-q')
            git('config', 'user.name', 'test')
            git('config', 'user.email', 'test@example.invalid')
            path = f'gitops/apps/{app}/dev/deployment.json'
            file = root / path
            file.parent.mkdir(parents=True)
            image = f'414053644145.dkr.ecr.us-east-1.amazonaws.com/aws-eks-istio-lab-dev-{app}'
            base = {'metadata': {'name': app, 'namespace': app}, 'spec': {'template': {'spec': {
                'containers': [{'name': app, 'image': image + ':old'}]}}}}
            file.write_text(json.dumps(base))
            policy_path = root / 'gitops/environments/dev' / ('release-policy.json' if app == 'orders-api' else 'orders-worker-release-policy.json')
            policy_path.parent.mkdir(parents=True)
            policy_path.write_text(json.dumps({'environment': 'dev', 'application': app + '-dev',
                'namespace': app, 'approval_required': False, 'auto_promote': True, 'allowed_paths': [path]}))
            git('add', '.')
            git('commit', '-qm', 'base')
            base_sha = git('rev-parse', 'HEAD')
            value = copy.deepcopy(base)
            value['spec']['template']['spec']['containers'][0]['image'] = image + ':sha-' + 'a' * 40 + '@sha256:' + 'b' * 64
            mutate(value, root)
            file.write_text(json.dumps(value))
            git('add', '.')
            git('commit', '-qm', 'candidate')
            result = subprocess.run(['python3', str(SCRIPT), '--application', app, '--base', base_sha,
                '--head', 'HEAD', '--expected-sha', 'a' * 40, '--expected-digest', 'sha256:' + 'b' * 64],
                cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode == 0, expected, result.stdout + result.stderr)

    def test_both_applications_accept_matching_immutable_images(self):
        for app in ('orders-api', 'orders-worker'):
            with self.subTest(app=app):
                self.check_promotion(app, lambda value, root: None, True)

    def test_reject_extra_file(self):
        self.check_promotion('orders-worker', lambda value, root: (root / 'unexpected').write_text('x'), False)

    def test_reject_changed_namespace(self):
        self.check_promotion('orders-worker', lambda value, root: value['metadata'].update(namespace='default'), False)

    def test_reject_other_pod_changes(self):
        self.check_promotion('orders-worker', lambda value, root: value['spec'].update(replicas=50), False)

    def test_reject_unpinned_image(self):
        self.check_promotion('orders-worker', lambda value, root: value['spec']['template']['spec']['containers'][0].update(image='evil:latest'), False)

    def test_reject_digest_from_other_successful_run(self):
        self.check_promotion('orders-worker', lambda value, root: value['spec']['template']['spec']['containers'][0].update(
            image=value['spec']['template']['spec']['containers'][0]['image'].replace('b' * 64, 'c' * 64)), False)
