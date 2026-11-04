"""Validate only the owner-authorized DEV image promotion path."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

DEPLOYMENT = 'gitops/apps/orders-api/dev/deployment.json'
PATTERN = (r'414053644145\.dkr\.ecr\.us-east-1\.amazonaws\.com/'
           r'aws-eks-istio-lab-dev-orders-api:sha-([0-9a-f]{40})@(sha256:[0-9a-f]{64})')


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--expected-sha')
    parser.add_argument('--expected-digest')
    args = parser.parse_args()
    policy = json.loads(Path('gitops/environments/dev/release-policy.json').read_text())
    if not (policy['environment'] == 'dev' and policy['application'] == 'orders-api-dev'
            and policy['namespace'] == 'orders-api' and policy['approval_required'] is False
            and policy['auto_promote'] is True and policy['allowed_paths'] == [DEPLOYMENT]):
        raise SystemExit('DEV automatic promotion is not enabled for this exact path')
    changed = git('diff', '--name-only', args.base + '...' + args.head).splitlines()
    if changed != [DEPLOYMENT]:
        raise SystemExit('Promotion must change only the Orders API DEV deployment')
    base = json.loads(git('show', args.base + ':' + DEPLOYMENT))
    head = json.loads(git('show', args.head + ':' + DEPLOYMENT))
    if head['metadata'].get('namespace') != 'orders-api' or head['metadata']['name'] != 'orders-api':
        raise SystemExit('Unexpected deployment target')
    old_image = base['spec']['template']['spec']['containers'][0].pop('image')
    image = head['spec']['template']['spec']['containers'][0].pop('image')
    match = re.fullmatch(PATTERN, image)
    if base != head or image == old_image or match is None:
        raise SystemExit('Only a changed immutable SHA-tagged image is permitted')
    if args.expected_sha and match[1] != args.expected_sha:
        raise SystemExit('Image SHA differs from successful CI source')
    if args.expected_digest and match[2] != args.expected_digest:
        raise SystemExit('Image digest differs from successful CI artifact')
    print(json.dumps({'environment': 'dev', 'application': 'orders-api-dev',
                      'approval_required': False, 'image': image, 'result': 'passed'}))


if __name__ == '__main__':
    main()
