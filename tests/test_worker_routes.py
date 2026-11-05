"""Prevent widening the worker's public surface while allowing synthetic connectivity."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('manifest_validation',Path(__file__).parents[1]/'scripts/validate_app_manifests.py')
validation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


class WorkerRoutesTests(unittest.TestCase):
    def routes(self):
        return [{'path':p,'pathType':'Exact'} for p in ['/health/live','/health/ready','/diagnostics/ping']]

    def test_exact_health_and_ping_are_allowed(self):
        validation.validate_worker_routes(self.routes())

    def test_prefix_matching_is_rejected(self):
        routes=self.routes();routes[-1]['pathType']='Prefix'
        with self.assertRaises(AssertionError):validation.validate_worker_routes(routes)

    def test_business_route_is_rejected(self):
        routes=self.routes();routes[-1]['path']='/orders'
        with self.assertRaises(AssertionError):validation.validate_worker_routes(routes)

    def test_missing_health_is_rejected(self):
        with self.assertRaises(AssertionError):validation.validate_worker_routes(self.routes()[:-1])
