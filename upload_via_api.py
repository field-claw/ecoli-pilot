#!/usr/bin/env python3
"""Upload the ecoli-pilot repo to GitHub via the git-data REST API.

git push over HTTPS is blocked here, and the git-database API 409s on a repo
with zero commits. So we (1) created a tiny initial commit via the contents
API, and (2) here build the real commit (blobs -> tree -> commit -> ref)
on top of it. No leading slash in endpoints (PortableGit rewrites those).
"""
import base64
import json
import os
import subprocess
import sys

REPO = "field-claw/ecoli-pilot"
ROOT = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(ROOT, ".upload_tmp")
os.makedirs(TMP, exist_ok=True)
API = f"repos/{REPO}"  # no leading slash


def gh_api(method, path, input_file=None):
    cmd = ["gh", "api", "-X", method, f"{API}{path}"]
    if input_file:
        cmd += ["--input", input_file]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ERROR {method} {path}: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return json.loads(res.stdout) if res.stdout.strip() else {}


def main():
    # current main HEAD (parent of our commit)
    ref = gh_api("GET", "/git/ref/heads/main")
    parent_sha = ref["object"]["sha"]
    print(f"parent commit: {parent_sha[:10]}")

    # collect real files (exclude .git, .upload_tmp, this script, .gitkeep)
    skip = {".gitkeep", "upload_via_api.py"}
    files = []
    for dp, dn, fns in os.walk(ROOT):
        if ".git" in dn:
            dn.remove(".git")
        if os.path.basename(dp) == ".upload_tmp":
            continue
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if rel in skip or rel.startswith(".upload_tmp/"):
                continue
            files.append(rel)

    print(f"uploading {len(files)} files ...")
    blobs = []
    for rel in files:
        full = os.path.join(ROOT, rel)
        with open(full, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        jf = os.path.join(TMP, "blob.json")
        with open(jf, "w") as f:
            json.dump({"content": b64, "encoding": "base64"}, f)
        out = gh_api("POST", "/git/blobs", jf)
        blobs.append({"path": rel, "mode": "100644",
                      "type": "blob", "sha": out["sha"]})
        print(f"  blob {rel} -> {out['sha'][:10]}")

    tree_jf = os.path.join(TMP, "tree.json")
    with open(tree_jf, "w") as f:
        json.dump({"tree": blobs}, f)
    tree = gh_api("POST", "/git/trees", tree_jf)
    print(f"tree {tree['sha'][:10]} ({len(blobs)} entries)")

    commit_jf = os.path.join(TMP, "commit.json")
    with open(commit_jf, "w") as f:
        json.dump({
            "message": "feat: real E. coli (iML1515) virtual-microbe pilot — 7/7 verify PASS",
            "tree": tree["sha"],
            "parents": [parent_sha],
        }, f)
    commit = gh_api("POST", "/git/commits", commit_jf)
    print(f"commit {commit['sha'][:10]}")

    ref_jf = os.path.join(TMP, "ref.json")
    with open(ref_jf, "w") as f:
        json.dump({"sha": commit["sha"], "force": True}, f)
    gh_api("PATCH", "/git/refs/heads/main", ref_jf)
    print("ref main -> updated")

    # cleanup .gitkeep from initial commit? leave it; it's outside the tree.
    print(f"DONE -> https://github.com/{REPO}")


if __name__ == "__main__":
    main()
