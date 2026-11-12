import json
from pathlib import Path
import unittest
from render_platform_bootstrap import render

ROOT = Path(__file__).parent


class RegionalPlatformTests(unittest.TestCase):
    def test_only_local_destinations_and_manual_sync(self):
        bundle = render("a" * 40)
        for obj in bundle["items"]:
            spec = obj["spec"]
            if obj["kind"] == "Application":
                self.assertEqual(spec["destination"]["server"], "https://kubernetes.default.svc")
                self.assertFalse(spec["syncPolicy"]["automated"]["enabled"])
                self.assertFalse(spec["syncPolicy"]["automated"]["prune"])
                if "path" in spec["source"]:
                    self.assertEqual(spec["source"]["targetRevision"], "a" * 40)
            else:
                self.assertTrue(all(d["server"] == "https://kubernetes.default.svc" for d in spec["destinations"]))
        with self.assertRaises(ValueError):
            render("main")

    def test_restored_volume_identity_zone_and_retention(self):
        objects = json.loads((ROOT / "storage/resources.json").read_text())["items"]
        volumes = [o for o in objects if o["kind"] == "PersistentVolume"]
        self.assertEqual(len(volumes), 5)
        for volume in volumes:
            spec = volume["spec"]
            self.assertEqual(spec["persistentVolumeReclaimPolicy"], "Retain")
            self.assertRegex(spec["csi"]["volumeHandle"], r"^vol-[a-f0-9]+$")
            terms = spec["nodeAffinity"]["required"]["nodeSelectorTerms"]
            self.assertTrue(any(e["values"] == ["us-east-2b"] for term in terms for e in term["matchExpressions"]))

    def test_grafana_restored_datasource_uids_do_not_collide(self):
        items = json.loads((ROOT / "platform-bootstrap.json").read_text())["items"]
        monitoring = next(o for o in items if o["metadata"]["name"] == "cosmotech-dr-monitoring")
        grafana = monitoring["spec"]["source"]["helm"]["valuesObject"]["grafana"]
        additional = [d["uid"] for d in grafana["additionalDataSources"]]
        self.assertEqual(set(additional), {"loki", "P214B5B846CF3925F"})
        self.assertEqual(grafana["persistence"]["existingClaim"], "dr-grafana-restored")
        self.assertEqual(grafana["sidecar"]["datasources"]["name"], "prometheus-aws-eks-istio-lab-dev")

    def test_no_raw_secret_objects_in_regional_bundles(self):
        for folder in ["storage", "dashboards", "runtime"]:
            bundle = json.loads((ROOT / folder / "resources.json").read_text())
            self.assertFalse(any(o["kind"] == "Secret" for o in bundle["items"]))
