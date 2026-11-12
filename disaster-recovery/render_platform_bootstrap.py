"""Pin the regional platform and paused runtime to a reviewed Git commit."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).parent


def render(revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("A reviewed full Git commit is required")
    bundle = json.loads((ROOT / "platform-bootstrap.json").read_text())
    for obj in bundle["items"]:
        if obj["kind"] == "Application" and "path" in obj["spec"]["source"]:
            obj["spec"]["source"]["targetRevision"] = revision
    runtime = json.loads((ROOT / "bootstrap.json").read_text())
    app = runtime["items"][-1]
    app["spec"]["source"].update(targetRevision=revision, path="disaster-recovery/runtime")
    bundle["items"].extend(runtime["items"])
    return bundle


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    print(json.dumps(render(parser.parse_args().revision), indent=2))
