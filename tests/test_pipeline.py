#!/usr/bin/env python3
"""End-to-end self-test, fully offline (saved API replies in tests/fixtures).

Works on a temporary copy of the repository, so it never touches real data.
Run:  python tests/test_pipeline.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FAILS = []


def check(cond, msg):
    print(("  ✓ " if cond else "  ✗ ") + msg)
    if not cond:
        FAILS.append(msg)


def run(work: Path, *args, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("GITHUB_")}
    e.pop("OPENALEX_API_KEY", None)
    e.update(env or {})
    r = subprocess.run([sys.executable, *args], cwd=work, env=e, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
    return r


def event(work: Path, name: str, payload: dict) -> dict:
    f = work / "out" / f"event-{name}.json"
    f.parent.mkdir(exist_ok=True)
    f.write_text(json.dumps(payload))
    return {"GITHUB_EVENT_NAME": name, "GITHUB_EVENT_PATH": str(f),
            "GITHUB_REPOSITORY": "compchemsk/Modern_Quantum_Biology"}


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    work = tmp / "repo"
    shutil.copytree(REPO, work, ignore=shutil.ignore_patterns(".git", "out", "__pycache__"))
    sys.path.insert(0, str(work / "scripts"))
    import common as C  # noqa: E402  (imported from the temp copy)

    n0 = len(C.load_yaml(work / "data/papers.yaml"))
    # window that includes the 2026 fixtures but excludes the 2019 arXiv record
    days = (dt.date.today() - dt.date(2025, 1, 1)).days

    print("1. Validation")
    check(run(work, "scripts/build.py", "--check").returncode == 0, f"papers.yaml valid ({n0} entries)")

    print("2. Watcher (dry run on fixtures)")
    r = run(work, "scripts/watch.py", "--dry-run", "--fixtures", "tests/fixtures", "--days", str(days))
    out = (work / "out/candidates.md").read_text()
    check(r.returncode == 0, "watcher ran")
    check("Coherent radical-pair spin dynamics" in out, "relevant Nature Comms paper proposed")
    check(out.count("Coherent radical-pair spin dynamics in a cryptochrome") == 2, "OpenAlex + Europe PMC duplicate merged (title + yaml only)")
    check("drug discovery" not in out, "quantum-computing noise rejected")
    check("Journal of Random Studies" not in out, "off-list venue rejected")
    check("A fluorescent-protein spin qubit" not in out, "paper already in Atlas not re-proposed")
    check("pulsed EPR distance" not in out, "routine EPR structural biology filtered out")
    check("published version of **`burd2025magnetic`**" in out, "journal version of a preprint is flagged")
    check("Old radical pair paper" not in out, "records older than the window ignored")
    check("[arXiv] TEST Posner" in out, "venue name '(Cornell University)' cleaned")
    check("MagLOV variants" in out, "bioRxiv preprint via Europe PMC proposed")

    # take the first issue body as GitHub would hold it
    first = out.split("\n## ")[0]
    body = first.split("\n\n", 2)[2] if first.startswith("## ") else first
    title = "TEST Coherent radical-pair spin dynamics in a cryptochrome mutant probed by pulsed magnetic resonance"
    issue = {"number": 7, "body": body, "labels": [{"name": "candidate"}], "title": title}

    print("3. Non-curator cannot approve")
    env = event(work, "issue_comment", {"issue": issue, "comment": {"body": "/approve"}, "sender": {"login": "stranger"}})
    run(work, "scripts/curate.py", "decide", env=env)
    res = json.loads((work / "out/result.json").read_text())
    check(res["action"] == "ignored", "comment from non-curator ignored")
    check(len(C.load_yaml(work / "data/papers.yaml")) == n0, "papers.yaml unchanged")

    print("4. Curator approves into another section")
    env = event(work, "issue_comment", {"issue": issue, "comment": {"body": "/approve methods"},
                                        "sender": {"login": "compchemsk"}})
    r = run(work, "scripts/curate.py", "decide", env=env)
    res = json.loads((work / "out/result.json").read_text())
    papers = C.load_yaml(work / "data/papers.yaml")
    new = [p for p in papers if p["title"] == title]
    check(res["action"] == "approve", "decision recorded as approve")
    check(len(papers) == n0 + 1 and new, "entry appended to papers.yaml")
    check(bool(new) and new[0]["category"] == "methods", "section override /approve methods respected")
    check(title in (work / "README.md").read_text(), "README rebuilt with the new paper")
    check(new and f"@article{{{new[0]['id']}," in (work / "bibliography/bioqubits.bib").read_text(), "BibTeX rebuilt")
    site = json.loads((work / "docs/data/papers.json").read_text())
    check(len(site["papers"]) == n0 + 1, "website data rebuilt")
    check("closes #7" in res.get("commit", ""), "commit message references the issue")

    print("5. Approving twice is harmless")
    run(work, "scripts/curate.py", "decide", env=env)
    res = json.loads((work / "out/result.json").read_text())
    check(res["action"] == "error" and "Already" in res["message"], "duplicate approval refused politely")

    print("6. Curator rejects via label")
    second = out.split("\n## ")[3]
    rej_body = second.split("\n\n", 2)[2]
    issue2 = {"number": 9, "body": rej_body, "labels": [{"name": "candidate"}]}
    env = event(work, "issues", {"action": "labeled", "label": {"name": "reject"}, "issue": issue2,
                                 "sender": {"login": "compchemsk"}})
    run(work, "scripts/curate.py", "decide", env=env)
    res = json.loads((work / "out/result.json").read_text())
    rejected = C.read_keyset(work / "data/rejected.txt")
    check(res["action"] == "reject" and len(rejected) == 1, "rejection recorded in rejected.txt")

    print("7. Watcher remembers decisions")
    run(work, "scripts/watch.py", "--dry-run", "--fixtures", "tests/fixtures", "--days", str(days))
    out2 = (work / "out/candidates.md").read_text()
    check(title not in out2, "approved paper not proposed again")
    check(out2.count("\n## ") + (1 if out2.startswith("## ") else 0) == 3, "rejected paper not proposed again")

    print("8. Bad YAML is reported, not committed")
    bad = {"number": 11, "body": body.replace("category: radical-pair", "category: nonsense")
           .replace("10.9999/test.relevant.1", "10.9999/other"), "labels": [{"name": "candidate"}]}
    env = event(work, "issue_comment", {"issue": bad, "comment": {"body": "/approve"}, "sender": {"login": "compchemsk"}})
    run(work, "scripts/curate.py", "decide", env=env)
    res = json.loads((work / "out/result.json").read_text())
    check(res["action"] == "error" and "unknown category" in res["message"], "invalid section reported back")

    print("9. Curator-only instant add (issue titled 'Add: …')")
    runner = work / "out" / "suggest_runner.py"
    runner.write_text(
        "import sys; sys.path.insert(0, 'scripts')\n"
        "import curate\n"
        "curate.lookup = lambda body: {'title': 'TEST Instant add of a radical pair paper', 'doi': '10.9999/instant.1',\n"
        "    'year': 2026, 'authors': ['Ada Tester'], 'journal': 'Nature Communications', 'raw_type': 'article',\n"
        "    'abstract': 'radical pair cryptochrome magnetic field effect'}\n"
        "raise SystemExit(curate.suggest())\n")
    base = len(C.load_yaml(work / "data/papers.yaml"))
    sug = {"number": 21, "title": "Add: 10.9999/instant.1", "body": "### DOI or arXiv id\n\n10.9999/instant.1",
           "labels": [{"name": "suggestion"}], "user": {"login": "stranger"}}
    run(work, str(runner), env=event(work, "issues", {"action": "opened", "issue": sug}))
    check(len(C.load_yaml(work / "data/papers.yaml")) == base, "'Add:' from a stranger does NOT add anything")
    sug["user"] = {"login": "compchemsk"}
    run(work, str(runner), env=event(work, "issues", {"action": "opened", "issue": sug}))
    res = json.loads((work / "out/result.json").read_text())
    papers = C.load_yaml(work / "data/papers.yaml")
    check(len(papers) == base + 1 and res["action"] == "approve", "'Add:' from the curator adds the paper immediately")
    sug["title"] = "Suggestion: 10.9999/instant.2"
    run(work, str(runner), env=event(work, "issues", {"action": "opened", "issue": sug}))
    check(len(C.load_yaml(work / "data/papers.yaml")) == base + 1, "a normal suggestion from the curator still waits for /approve")

    print("10. Generated site files")
    meta = json.loads((work / "docs/data/site.json").read_text())
    raw = (work / "docs/data/site.json").read_text() + (work / "docs/index.html").read_text() + (work / "docs/assets/app.js").read_text()
    check(meta["repo"] == C.load_yaml(work / "config/site.yaml")["repo"], "site.json carries the repo name from config/site.yaml")
    check("@gmail.com" not in raw and "soumyajitkarmakar.iit" not in raw, "curator email is not written out in the site's source")
    check("Content-Security-Policy" in (work / "docs/index.html").read_text(), "website has a Content-Security-Policy")
    check("<script>" not in (work / "docs/index.html").read_text(), "no inline scripts in the website")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'ALL PASSED' if not FAILS else f'{len(FAILS)} FAILED'}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
