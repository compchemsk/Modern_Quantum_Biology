#!/usr/bin/env python3
"""Turn a curator's decision on a candidate issue into a change to the Atlas.

Run by .github/workflows/curate.yml and suggest.yml.

  python scripts/curate.py decide      # read the GitHub event; apply /approve or /reject
  python scripts/curate.py finalize    # after the commit is pushed: comment + close the issue
  python scripts/curate.py suggest     # someone opened a "Suggest a paper" issue: fetch metadata
  python scripts/curate.py add <DOI|arXiv id> [--category KEY]   # local use: add a paper by hand

Only users listed under `curators:` in config/watch.yaml (default: the repo owner)
can approve or reject. Everyone else's commands are ignored.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

import common as C
import build
import watch

RESULT = C.OUT / "result.json"


# ------------------------------------------------------------------ helpers
def load_event() -> tuple[str, dict]:
    name = os.environ.get("GITHUB_EVENT_NAME", "")
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        sys.exit("GITHUB_EVENT_PATH not set — this mode runs inside GitHub Actions.")
    with open(path, encoding="utf-8") as fh:
        return name, json.load(fh)


def curators(cfg: dict) -> set[str]:
    owner = (os.environ.get("GITHUB_REPOSITORY", "/").split("/")[0]).lower()
    names = {c.lower() for c in (cfg.get("curators") or [])}
    return names | ({owner} if owner else set())


def parse_command(text: str) -> tuple[str | None, str | None]:
    """'/approve lov' -> ('approve', 'lov'); '/reject off-topic' -> ('reject', 'off-topic')."""
    m = re.match(r"^\s*/(approve|reject)\b[ \t]*([^\n]*)", text or "", flags=re.I)
    if not m:
        return None, None
    return m.group(1).lower(), (m.group(2).strip() or None)


def write_result(**kw):
    C.OUT.mkdir(exist_ok=True)
    RESULT.write_text(json.dumps(kw, indent=2, ensure_ascii=False), encoding="utf-8")


def find_entry(issue: dict, gh: C.GitHub) -> dict | None:
    entry = C.extract_entry_block(issue.get("body") or "")
    if entry:
        return entry
    if gh.enabled:  # suggestion issues: the bot posts the block as a comment
        for cm in reversed(gh.comments(issue["number"])):
            entry = C.extract_entry_block(cm.get("body") or "")
            if entry:
                return entry
    return None


def add_entry(entry: dict, category: str | None = None) -> tuple[bool, str]:
    """Validate + append to papers.yaml. Returns (ok, message)."""
    papers = C.load_papers()
    cats = {c["key"] for c in C.load_categories()}
    entry = {k: v for k, v in entry.items() if v not in (None, "", [])}
    if category:
        entry["category"] = category
    if entry.get("doi"):
        entry["doi"] = C.norm_doi(entry["doi"])
    ids = {p["id"] for p in papers}
    if not entry.get("id") or entry["id"] in ids:
        entry["id"] = C.make_id(entry, ids)
    entry["added"] = C.today()
    errs = C.validate_entry(entry, cats)
    if errs:
        return False, "Could not add — " + "; ".join(errs)
    key = C.paper_key(entry)
    if any(C.paper_key(p) == key for p in papers):
        return False, "Already in the Atlas — nothing to do."
    with open(C.PAPERS_FILE, "a", encoding="utf-8") as fh:
        fh.write("\n" + C.entry_to_yaml(entry))
    build.build()
    return True, entry["id"]


# ------------------------------------------------------------------ modes
def decide() -> int:
    cfg = C.load_watch_config()
    event_name, ev = load_event()
    issue = ev.get("issue") or {}
    sender = (ev.get("sender") or {}).get("login", "")
    labels = {l["name"] for l in issue.get("labels", [])}

    if event_name == "issue_comment":
        action, arg = parse_command((ev.get("comment") or {}).get("body", ""))
    elif event_name == "issues" and ev.get("action") == "labeled":
        lab = (ev.get("label") or {}).get("name")
        action, arg = (lab, None) if lab in ("approve", "reject") else (None, None)
    else:
        action, arg = None, None

    if not action:
        C.log("No curator command in this event — nothing to do.")
        write_result(action="none")
        return 0
    if sender.lower() not in curators(cfg):
        C.log(f"Ignoring /{action} from {sender}: not a curator.")
        write_result(action="ignored", issue=issue.get("number"), sender=sender)
        return 0
    if "candidate" not in labels:
        C.log("Issue is not a candidate — ignoring.")
        write_result(action="none")
        return 0

    gh = C.GitHub()
    num = issue["number"]
    if action == "approve":
        entry = find_entry(issue, gh)
        if not entry:
            write_result(action="error", issue=num,
                         message="I could not find the YAML entry block in this issue.")
            return 0
        ok, msg = add_entry(entry, arg)
        if ok:
            write_result(action="approve", issue=num, id=msg, title=entry.get("title"),
                         commit=f"Add {msg}: {entry.get('title', '')[:60]} (closes #{num})")
        else:
            write_result(action="error", issue=num, message=msg)
    else:  # reject
        entry = find_entry(issue, gh) or {}
        key = C.paper_key(entry) if entry else f"issue:{num}"
        reason = f" — {arg}" if arg else ""
        C.append_line(C.REJECTED_FILE, f"{key}  # {C.today()} #{num} {entry.get('title', '')[:80]}{reason}")
        write_result(action="reject", issue=num, commit=f"Reject candidate #{num}")
    return 0


def finalize() -> int:
    if not RESULT.exists():
        return 0
    r = json.loads(RESULT.read_text(encoding="utf-8"))
    gh = C.GitHub()
    if not gh.enabled or r.get("action") in ("none", "ignored"):
        return 0
    num = r["issue"]
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if r["action"] == "approve":
        gh.comment(num, f"✅ Added to the Atlas as **`{r['id']}`**. "
                        f"README, BibTeX and website are updated.")
        gh.add_labels(num, ["added"])
        gh.remove_label(num, "candidate")
        gh.close(num, "completed")
    elif r["action"] == "reject":
        gh.comment(num, "❌ Not added. It is recorded in `data/rejected.txt` and will not be proposed again.")
        gh.add_labels(num, ["rejected"])
        gh.remove_label(num, "candidate")
        gh.close(num, "not_planned")
    elif r["action"] == "error":
        gh.comment(num, f"⚠️ {r['message']}\n\nFix the YAML block in the issue body "
                        f"(or the section key) and comment `/approve` again.")
        gh.remove_label(num, "approve")
    return 0


# ---------------------------------------------------------- suggest / add
ID_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)|(?:arxiv[:\s]*|arxiv\.org/abs/)(\d{4}\.\d{4,5})", re.I)


def lookup(identifier: str) -> dict | None:
    """Fetch metadata for a DOI (OpenAlex, then Crossref) or an arXiv id."""
    m = ID_RE.search(identifier)
    if not m:
        if re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", identifier.strip()):
            m = re.match(r"()(\d{4}\.\d{4,5})", identifier.strip())
        else:
            return None
    doi, arx = (m.group(1) or "").rstrip(".,);"), m.group(2)
    if arx:
        raw = C.http_get("https://export.arxiv.org/api/query", {"id_list": arx}, as_json=False)
        e = ET.fromstring(raw).find("a:entry", watch.ATOM)
        if e is None:
            return None
        pub = e.findtext("a:published", "", watch.ATOM)
        return {"title": re.sub(r"\s+", " ", e.findtext("a:title", "", watch.ATOM)).strip(),
                "authors": [a.findtext("a:name", "", watch.ATOM) for a in e.findall("a:author", watch.ATOM)],
                "year": int(pub[:4]), "journal": "arXiv", "arxiv": arx,
                "abstract": e.findtext("a:summary", "", watch.ATOM), "raw_type": "preprint",
                "url": f"https://arxiv.org/abs/{arx}", "oa_url": f"https://arxiv.org/pdf/{arx}"}
    doi = C.norm_doi(doi)
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        try:
            w = C.http_get(f"https://api.openalex.org/works/doi:{doi}", {"api_key": key})
            src = ((w.get("primary_location") or {}).get("source") or {})
            return {"title": w.get("display_name"), "doi": doi, "year": w.get("publication_year"),
                    "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
                    "journal": src.get("display_name") or "", "raw_type": w.get("type"),
                    "abstract": watch.openalex_abstract(w.get("abstract_inverted_index")),
                    "oa_url": (w.get("open_access") or {}).get("oa_url")}
        except Exception as e:
            C.log(f"OpenAlex lookup failed ({e}); trying Crossref")
    w = C.http_get(f"https://api.crossref.org/works/{doi}")["message"]
    year = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
    ctype = {"posted-content": "preprint"}.get(w.get("type"), "article")
    return {"title": (w.get("title") or [""])[0], "doi": doi, "year": year,
            "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in w.get("author", [])],
            "journal": (w.get("container-title") or [""])[0] or (w.get("institution") or [{}])[0].get("name", ""),
            "volume": w.get("volume"), "pages": w.get("page"), "raw_type": ctype,
            "abstract": re.sub(r"<[^>]+>", " ", w.get("abstract") or "")}


def to_candidate(meta: dict, cfg: dict) -> dict:
    papers = C.load_papers()
    c = dict(meta)
    c["tier"] = C.venue_tier(re.sub(r"\(.*?\)", "", c.get("journal") or ""), cfg) or "specialist"
    c["type"] = watch.classify_type(c, c["tier"])
    c["score"], c["hits"] = C.score_candidate(c["title"], c.get("abstract", ""), cfg)
    c["category"] = C.suggest_category(c["title"], c.get("abstract", ""), c["type"], cfg)
    c["proposed_id"] = C.make_id(c, {p["id"] for p in papers})
    c["sources"] = ["manual suggestion"]
    return c


def suggest() -> int:
    """A "Suggest a paper" issue was opened.

    Anyone: the bot fetches the metadata, posts a ready entry and labels it a candidate.
    Curator with a title starting "Add:": the paper is added straight away (the
    curator opening the issue *is* the approval). The workflow commits and closes it.
    """
    cfg = C.load_watch_config()
    _, ev = load_event()
    issue = ev["issue"]
    gh = C.GitHub()
    author = ((issue.get("user") or {}).get("login") or "").lower()
    add_now = issue.get("title", "").strip().lower().startswith("add:") and author in curators(cfg)
    body = issue.get("body") or ""
    try:
        meta = lookup(body)
        err = "no DOI or arXiv id found in the issue"
    except Exception as e:
        meta, err = None, str(e)
    if not meta:
        if gh.enabled:
            gh.comment(issue["number"], f"🤖 I couldn't fetch this paper ({err}). "
                                        "Please check the DOI / arXiv id and edit the issue.")
        write_result(action="none")
        return 0
    c = to_candidate(meta, cfg)
    _, block, _ = watch.build_issue(c, cfg)
    if add_now:
        entry = C.extract_entry_block(block)
        for k in ("volume", "pages"):
            if meta.get(k):
                entry[k] = str(meta[k])
        ok, msg = add_entry(entry)
        if ok:
            write_result(action="approve", issue=issue["number"], id=msg, title=entry.get("title"),
                         commit=f"Add {msg}: {entry.get('title', '')[:60]} (closes #{issue['number']})")
        else:
            write_result(action="error", issue=issue["number"], message=msg)
        if gh.enabled:
            gh.add_labels(issue["number"], ["candidate"])
        return 0
    note = "" if C.passes(c["score"], c["hits"], cfg) else \
        "\n\n> ℹ️ The relevance filter would not have caught this one automatically — the curator decides."
    if gh.enabled:
        gh.comment(issue["number"], "🤖 Here is the entry I prepared:\n\n" + block + note)
        gh.add_labels(issue["number"], ["candidate"])
    write_result(action="none")
    return 0


def add_local(identifier: str, category: str | None) -> int:
    cfg = C.load_watch_config()
    meta = lookup(identifier)
    if not meta:
        sys.exit("Could not resolve that identifier.")
    c = to_candidate(meta, cfg)
    _, block, _ = watch.build_issue(c, cfg)
    entry = C.extract_entry_block(block)
    if meta.get("volume"):
        entry["volume"] = str(meta["volume"])
    if meta.get("pages"):
        entry["pages"] = str(meta["pages"])
    ok, msg = add_entry(entry, category)
    print(("Added " if ok else "") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["decide", "finalize", "suggest", "add"])
    ap.add_argument("identifier", nargs="?")
    ap.add_argument("--category")
    a = ap.parse_args()
    if a.mode == "add":
        if not a.identifier:
            ap.error("add needs a DOI or arXiv id")
        raise SystemExit(add_local(a.identifier, a.category))
    raise SystemExit({"decide": decide, "finalize": finalize, "suggest": suggest}[a.mode]())
