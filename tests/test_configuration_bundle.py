"""Reject configuration tampering against the exact tested source bundle."""
import copy
import importlib.util
import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch
import pytest
spec=importlib.util.spec_from_file_location('validator',Path(__file__).parents[1]/'scripts/validate_dev_image.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)

@pytest.mark.parametrize('tamper',[None,'configuration','namespace','unrelated','digest'])
def test_complete_source_bundle(tmp_path,tamper):
    app='orders-api';sha='a'*40;digest='sha256:'+'b'*64
    resources={name+'.json':{'metadata':{'namespace':app}} for name in ['deployment','configmap','service','hpa','ingress']}
    resources['deployment.json']['spec']={'template':{'spec':{'containers':[{'image':'414053644145.dkr.ecr.us-east-1.amazonaws.com/aws-eks-istio-lab-dev-orders-api:sha-'+sha+'@'+digest}]}}}
    bundle={'application':app,'source_repository':'rlcosmo/cosmotech-'+app,'source_sha':sha,'resources':resources}
    if tamper=='namespace':bundle['resources']['service.json']['metadata']['namespace']='default'
    if tamper=='digest':bundle['resources']['deployment.json']['spec']['template']['spec']['containers'][0]['image']='evil:latest'
    expected=tmp_path/'expected.json';expected.write_text(json.dumps(bundle))
    actual=copy.deepcopy(bundle)
    if tamper=='configuration':actual['resources']['configmap.json']['data']={'modified':'after tests'}
    prefix='gitops/apps/'+app+'/dev/';proof='gitops/releases/'+app+'-dev.json'
    changed=[prefix+n for n in resources]+[proof]
    if tamper=='unrelated':changed+=['other-application.json']
    def git(*args):
        if args[0]=='diff':return '\n'.join(changed)
        path=args[1].split(':',1)[1]
        return json.dumps(bundle if path==proof else actual['resources'][path.removeprefix(prefix)])
    args=Namespace(application=app,base='base',head='head',expected_sha=sha,expected_digest=digest,expected_manifests=expected)
    with patch.object(validator,'git',side_effect=git):
        if tamper:
            with pytest.raises(SystemExit):validator.validate_bundle(args)
        else:validator.validate_bundle(args)
