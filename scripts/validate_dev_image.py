"""Validate only the owner-authorized DEV image promotion path."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

PATTERN = (r'414053644145\.dkr\.ecr\.us-east-1\.amazonaws\.com/'
           r'aws-eks-istio-lab-dev-orders-api:sha-([0-9a-f]{40})@(sha256:[0-9a-f]{64})')


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True).strip()


def validate_bundle(args):
    application = args.application
    bundle = json.loads(args.expected_manifests.read_text())
    proof = f'gitops/releases/{application}-dev.json'
    prefix = f'gitops/apps/{application}/dev/'
    names = {'deployment.json','configmap.json','service.json','hpa.json','ingress.json'}
    if bundle['application'] != application or bundle['source_repository'] != 'rlcosmo/cosmotech-'+application or not re.fullmatch('[0-9a-f]{40}', bundle['source_sha']):
        raise SystemExit('Unexpected application source provenance')
    if args.expected_sha and bundle['source_sha'] != args.expected_sha:
        raise SystemExit('Configuration differs from the tested source SHA')
    if set(bundle['resources']) != names:
        raise SystemExit('Incomplete application resource bundle')
    changed=set(git('diff','--name-only',args.base+'...'+args.head).splitlines())
    if not changed or not changed <= {prefix+n for n in names} | {proof} or proof not in changed:
        raise SystemExit('Changes outside the application delivery bundle')
    policy_name='release-policy.json' if application=='orders-api' else 'orders-worker-release-policy.json'
    policy=json.loads(Path('gitops/environments/dev',policy_name).read_text())
    if policy.get('configuration_source') != f'rlcosmo/cosmotech-{application}:deploy/dev' or policy['approval_required'] or not policy['auto_promote']:
        raise SystemExit('Application configuration promotion is not enabled')
    actual=json.loads(git('show',args.head+':'+proof))
    if actual != bundle:
        raise SystemExit('Release provenance differs from the tested bundle')
    for name, expected in bundle['resources'].items():
        if expected['metadata']['namespace'] != application:
            raise SystemExit('Cross-namespace resource is forbidden')
        actual=json.loads(git('show',args.head+':'+prefix+name))
        if actual != expected:
            raise SystemExit('Promoted configuration differs from the tested bundle: '+name)
    image=bundle['resources']['deployment.json']['spec']['template']['spec']['containers'][0]['image']
    match=re.fullmatch(PATTERN.replace('orders-api',application),image)
    if not match or match[1] != bundle['source_sha'] or (args.expected_digest and match[2] != args.expected_digest):
        raise SystemExit('Immutable image differs from the tested artifact')
    print(json.dumps({'application':application,'source_sha':bundle['source_sha'],'approval_required':False,'resources':len(names),'result':'passed'}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--application', choices=['orders-api', 'orders-worker'], default='orders-api')
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--expected-sha')
    parser.add_argument('--expected-digest')
    parser.add_argument('--expected-manifests', type=Path)
    args = parser.parse_args()
    application = args.application
    if args.expected_manifests:
        validate_bundle(args)
        return
    deployment = f'gitops/apps/{application}/dev/deployment.json'
    pattern = PATTERN.replace('orders-api', application)
    policy_file = 'release-policy.json' if application == 'orders-api' else 'orders-worker-release-policy.json'
    policy = json.loads(Path('gitops/environments/dev', policy_file).read_text())
    if not (policy['environment'] == 'dev' and policy['application'] == application + '-dev'
            and policy['namespace'] == application and policy['approval_required'] is False
            and policy['auto_promote'] is True and policy['allowed_paths'] == [deployment]):
        raise SystemExit('DEV automatic promotion is not enabled for this exact path')
    changed = git('diff', '--name-only', args.base + '...' + args.head).splitlines()
    if changed != [deployment]:
        raise SystemExit('Promotion must change only the selected DEV deployment')
    base = json.loads(git('show', args.base + ':' + deployment))
    head = json.loads(git('show', args.head + ':' + deployment))
    if head['metadata'].get('namespace') != application or head['metadata']['name'] != application:
        raise SystemExit('Unexpected deployment target')
    old_image = base['spec']['template']['spec']['containers'][0].pop('image')
    image = head['spec']['template']['spec']['containers'][0].pop('image')
    match = re.fullmatch(pattern, image)
    if base != head or image == old_image or match is None:
        raise SystemExit('Only a changed immutable SHA-tagged image is permitted')
    if args.expected_sha and match[1] != args.expected_sha:
        raise SystemExit('Image SHA differs from successful CI source')
    if args.expected_digest and match[2] != args.expected_digest:
        raise SystemExit('Image digest differs from successful CI artifact')
    print(json.dumps({'environment': 'dev', 'application': application + '-dev',
                      'approval_required': False, 'image': image, 'result': 'passed'}))


if __name__ == '__main__':
    main()
