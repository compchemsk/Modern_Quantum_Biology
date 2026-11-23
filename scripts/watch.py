#!/usr/bin/env python3
"""Daily literature watcher.

Queries OpenAlex, arXiv and Europe PMC for new papers on biological qubits and
related topics, scores them for relevance, drops anything already known, and
opens one GitHub issue per candidate for the curator to /approve or /reject.

Usage
  python scripts/watch.py                # normal run (inside GitHub Actions)
  python scripts/watch.py --dry-run      # print candidates, open no issues
  python scripts/watch.py --days 60      # override the look-back window
  python scripts/watch.py --fixtures tests/fixtures   # offline test with saved API replies
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import common as C

# ============================================================== sources
def _fixture(fixtures: Path | None, name: str):
    if fixtures is None:
        return None
    f = fixtures / name
    if not f.exists():
        return None
    return f.read_text(encoding="utf-8")


def openalex_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def fetch_openalex(cfg: dict, since: dt.date, fixtures: Path | None) -> list[dict]:
    key = os.environ.get("OPENALEX_API_KEY")
    raw = _fixture(fixtures, "openalex.json")
    results = []
    if raw is not None:
        results = json.loads(raw).get("results", [])
    else:
        if not key:
            C.log("  ! OPENALEX_API_KEY not set — OpenAlex skipped (add the free key as a repo secret).")
            return []
        seen_ids = set()
        for q in cfg["queries"]:
            params = {
                "search": f'"{q}"',
                "filter": f"from_publication_date:{since.isoformat()},type:article|preprint|review|letter",
                "per_page": 100,
                "sort": "publication_date:desc",
                "select": "id,doi,display_name,publication_year,publication_date,authorships,"
                          "primary_location,open_access,type,abstract_inverted_index",
                "api_key": key,
                "mailto": cfg.get("contact_email", ""),
            }
            try:
                data = C.http_get("https://api.openalex.org/works", params)
            except Exception as e:
                C.log(f"  ! OpenAlex query '{q}' failed: {e}")
                continue
            for w in data.get("results", []):
                if w["id"] not in seen_ids:
                    seen_ids.add(w["id"])
                    results.append(w)
    out = []
    for w in results:
        loc = w.get("primary_location") or {}
        src = (loc.get("source") or {})
        otype = w.get("type") or "article"
        out.append({
            "title": w.get("display_name") or "",
            "authors": [a["author"]["display_name"] for a in w.get("authorships", []) if a.get("author")],
            "year": w.get("publication_year"),
            "date": w.get("publication_date"),
            "journal": re.sub(r"\s*\(.*?\)\s*$", "", src.get("display_name") or ""),
            "doi": C.norm_doi(w.get("doi")),
            "abstract": openalex_abstract(w.get("abstract_inverted_index")),
            "url": loc.get("landing_page_url"),
            "oa_url": (w.get("open_access") or {}).get("oa_url"),
            "raw_type": otype,
            "source": "OpenAlex",
        })
    C.log(f"  OpenAlex: {len(out)} records")
    return out


ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def fetch_arxiv(cfg: dict, since: dt.date, fixtures: Path | None) -> list[dict]:
    raw = _fixture(fixtures, "arxiv.xml")
    if raw is None:
        phrases = " OR ".join(f'ti:"{q}" OR abs:"{q}"' for q in cfg["queries"])
        cats = " OR ".join(f"cat:{c}" for c in cfg.get("arxiv_categories", []))
        query = f"({phrases})" + (f" AND ({cats})" if cats else "")
        try:
            raw = C.http_get("https://export.arxiv.org/api/query", {
                "search_query": query, "sortBy": "submittedDate", "sortOrder": "descending",
                "max_results": 200}, as_json=False, timeout=90)
        except Exception as e:
            C.log(f"  ! arXiv failed: {e}")
            return []
    root = ET.fromstring(raw)
    out = []
    for e in root.findall("a:entry", ATOM):
        published = (e.findtext("a:published", "", ATOM) or "")[:10]
        if published and dt.date.fromisoformat(published) < since:
            continue
        abs_id = (e.findtext("a:id", "", ATOM) or "").rsplit("/abs/", 1)[-1]
        arxiv_id = re.sub(r"v\d+$", "", abs_id)
        out.append({
            "title": re.sub(r"\s+", " ", e.findtext("a:title", "", ATOM)).strip(),
            "authors": [a.findtext("a:name", "", ATOM) for a in e.findall("a:author", ATOM)],
            "year": int(published[:4]) if published else None,
            "date": published,
            "journal": "arXiv",
            "arxiv": arxiv_id,
            "doi": C.norm_doi(e.findtext("arxiv:doi", None, ATOM)),
            "journal_ref": e.findtext("arxiv:journal_ref", None, ATOM),
            "abstract": re.sub(r"\s+", " ", e.findtext("a:summary", "", ATOM)).strip(),
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "oa_url": f"https://arxiv.org/pdf/{arxiv_id}",
            "raw_type": "preprint",
            "source": "arXiv",
        })
    C.log(f"  arXiv: {len(out)} records")
    return out


def fetch_europepmc(cfg: dict, since: dt.date, fixtures: Path | None) -> list[dict]:
    raw = _fixture(fixtures, "europepmc.json")
    if raw is not None:
        results = json.loads(raw).get("resultList", {}).get("result", [])
    else:
        phrases = " OR ".join(f'TITLE_ABS:"{q}"' for q in cfg["queries"])
        query = f"({phrases}) AND FIRST_PDATE:[{since.isoformat()} TO {C.today().isoformat()}]"
        try:
            data = C.http_get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", {
                "query": query, "format": "json", "resultType": "core", "pageSize": 500})
            results = data.get("resultList", {}).get("result", [])
        except Exception as e:
            C.log(f"  ! Europe PMC failed: {e}")
            return []
    out = []
    for r in results:
        is_preprint = r.get("source") == "PPR"
        journal = ((r.get("journalInfo") or {}).get("journal") or {}).get("title") \
            or (r.get("bookOrReportDetails") or {}).get("publisher") or ""
        authors = [a.get("fullName") for a in (r.get("authorList") or {}).get("author", []) if a.get("fullName")]
        if not authors and r.get("authorString"):
            authors = [s.strip() for s in r["authorString"].rstrip(".").split(",")]
        out.append({
            "title": re.sub(r"<[^>]+>", "", r.get("title") or "").rstrip("."),
            "authors": authors,
            "year": int(r["pubYear"]) if r.get("pubYear") else None,
            "date": r.get("firstPublicationDate"),
            "journal": journal,
            "doi": C.norm_doi(r.get("doi")),
            "abstract": re.sub(r"<[^>]+>", " ", r.get("abstractText") or ""),
            "url": f"https://europepmc.org/article/{r.get('source')}/{r.get('id')}",
            "oa_url": None,
            "raw_type": "preprint" if is_preprint else ("review" if "review" in " ".join(
                ((r.get("pubTypeList") or {}).get("pubType") or [])).lower() else "article"),
            "source": "Europe PMC",
        })
    C.log(f"  Europe PMC: {len(out)} records")
    return out


SOURCES = {"openalex": fetch_openalex, "arxiv": fetch_arxiv, "europepmc": fetch_europepmc}


# ============================================================== pipeline
def merge(records: list[dict]) -> list[dict]:
    """Merge duplicates across sources by DOI / arXiv id / title."""
    by_key: dict[str, dict] = {}
    title_index: dict[str, str] = {}
    for r in records:
        if not r.get("title"):
            continue
        k = C.paper_key(r)
        tkey = C.norm_title(r["title"])
        k = by_key.get(k) and k or title_index.get(tkey, k)
        if k in by_key:
            base = by_key[k]
            for f, v in r.items():
                if v and not base.get(f):
                    base[f] = v
            if len(r.get("abstract") or "") > len(base.get("abstract") or ""):
                base["abstract"] = r["abstract"]
            base["sources"].append(r["source"])
        else:
            r["sources"] = [r["source"]]
            by_key[k] = r
            title_index[tkey] = k
    return list(by_key.values())


def classify_type(r: dict, tier: str | None) -> str:
    if tier == "preprint" or r.get("raw_type") == "preprint":
        return "preprint"
    if r.get("raw_type") == "review":
        return "review"
    if r.get("raw_type") == "letter":
        return "letter"
    return "article"


def short_authors(authors: list[str]) -> str:
    if not authors:
        return "—"
    if len(authors) <= 4:
        return ", ".join(authors)
    return f"{', '.join(authors[:3])}, … , {authors[-1]}"


def tags_for(c: dict) -> list[str]:
    text = f"{c['title']} {c.get('abstract') or ''}"
    terms = []
    for group in ("core", "platform", "bio", "spin"):
        terms += [t for t in C.matched_terms(text, c["hits"][group]) if t not in terms]
    return terms[:6]


def build_issue(c: dict, cfg: dict) -> tuple[str, str, list[str]]:
    entry = {
        "id": c["proposed_id"],
        "title": c["title"],
        "authors": c["authors"][:40] + (["et al."] if len(c["authors"]) > 40 else []),
        "year": c.get("year"),
        "journal": c.get("journal"),
        "doi": c.get("doi"),
        "arxiv": c.get("arxiv"),
        "type": c["type"],
        "category": c["category"],
        "tags": tags_for(c),
        "oa": True if (c.get("oa_url") or c["type"] == "preprint") else None,
        "url": None if c.get("doi") else c.get("url"),
        "note": "",
    }
    link = f"https://doi.org/{c['doi']}" if c.get("doi") else c.get("url")
    tier_badge = {"high_impact": "⭐ high-impact", "specialist": "🔹 specialist", "preprint": "📝 preprint"}[c["tier"]]
    matched = ", ".join(c["hits"]["core"] + c["hits"].get("platform", []) + c["hits"]["bio"] + c["hits"]["spin"]).replace("*", "")
    lines = [
        f"**{c.get('journal') or '—'}** · {c.get('year') or ''} · {tier_badge}",
        "",
        f"**Authors:** {short_authors(c['authors'])}",
        f"**Link:** {link}" + (f"  ·  **Free copy:** {c['oa_url']}" if c.get("oa_url") and c.get("oa_url") != link else ""),
        f"**Relevance score:** {c['score']}  ·  matched: _{matched}_",
        f"**Found via:** {', '.join(sorted(set(c['sources'])))}",
    ]
    if c.get("published_version_of"):
        lines += ["", f"> 🔁 This looks like the published version of **`{c['published_version_of']}`**, "
                      "which is already in the Atlas as a preprint. Approving adds it as a new entry; "
                      "you may then want to delete the preprint entry from `data/papers.yaml`."]
    if cfg.get("include_abstract") and c.get("abstract"):
        ab = c["abstract"][:900] + ("…" if len(c["abstract"]) > 900 else "")
        lines += ["", "<details><summary>Abstract</summary>", "", ab, "", "</details>"]
    cats = ", ".join(f"`{x['key']}`" for x in C.load_categories())
    lines += [
        "",
        "---",
        "### Your decision",
        "| To | Do this |",
        "|---|---|",
        "| ✅ add it | comment **`/approve`** — or add the label **approve** |",
        "| ✅ add it to another section | comment **`/approve lov`** (any section key) |",
        "| ❌ skip it | comment **`/reject`** — or add the label **reject** |",
        "",
        f"Sections: {cats}. You may edit the YAML below before approving; whatever is in it is what gets added.",
        "",
        C.ENTRY_START,
        "```yaml",
        C.entry_to_yaml(entry).strip(),
        "```",
        C.ENTRY_END,
    ]
    tier_label = {"high_impact": "high-impact", "specialist": "specialist", "preprint": "preprint"}[c["tier"]]
    labels = ["candidate", tier_label] + (["published-version"] if c.get("published_version_of") else [])
    short_venue = (c.get("journal") or "").replace("Journal of the American Chemical Society", "JACS")
    title = f"📄 [{short_venue}] {c['title']}"
    return title, "\n".join(lines), labels


def run(args) -> int:
    cfg = C.load_watch_config()
    days = args.days or cfg.get("lookback_days", 21)
    since = C.today() - dt.timedelta(days=days)
    fixtures = Path(args.fixtures) if args.fixtures else None
    C.log(f"Watching literature since {since} ({days} days)")

    records = []
    for name, fn in SOURCES.items():
        if cfg.get("sources", {}).get(name, True):
            records += fn(cfg, since, fixtures)
    cands = merge(records)

    papers = C.load_papers()
    known = {C.paper_key(p) for p in papers}
    known |= {C.norm_doi(p["doi"]) for p in papers if p.get("doi")}
    seen = C.read_keyset(C.SEEN_FILE)
    rejected = C.read_keyset(C.REJECTED_FILE)
    ids = {p["id"] for p in papers}
    preprints = [p for p in papers if p.get("type") == "preprint"]

    accepted_tiers = set(cfg.get("accept_tiers", ["high_impact", "specialist", "preprint"]))
    stats = {"fetched": len(records), "unique": len(cands), "known": 0, "venue": 0, "score": 0}
    keep = []
    for c in cands:
        k = C.paper_key(c)
        alt = {k, C.norm_doi(c.get("doi")) or "", ("arxiv:" + c["arxiv"].lower()) if c.get("arxiv") else ""}
        if alt & (known | seen | rejected):
            stats["known"] += 1
            continue
        tier = C.venue_tier(re.sub(r"\(.*?\)", "", c.get("journal") or ""), cfg)
        if tier not in accepted_tiers:
            stats["venue"] += 1
            continue
        c["tier"] = tier
        c["type"] = classify_type(c, tier)
        c["score"], c["hits"] = C.score_candidate(c["title"], c.get("abstract", ""), cfg)
        if not C.passes(c["score"], c["hits"], cfg):
            stats["score"] += 1
            continue
        # duplicate of an existing entry under another identifier?
        dup = next((p for p in papers if C.title_similarity(p["title"], c["title"]) > 0.92), None)
        if dup and not (dup.get("type") == "preprint" and c["type"] != "preprint"):
            stats["known"] += 1
            continue
        pv = next((p for p in preprints if C.title_similarity(p["title"], c["title"]) > 0.85), None)
        if pv and c["type"] != "preprint":
            c["published_version_of"] = pv["id"]
        c["category"] = C.suggest_category(c["title"], c.get("abstract", ""), c["type"], cfg)
        c["proposed_id"] = C.make_id(c, ids)
        ids.add(c["proposed_id"])
        keep.append(c)

    tier_rank = {"high_impact": 0, "specialist": 1, "preprint": 2}
    keep.sort(key=lambda c: (tier_rank[c["tier"]], -c["score"]))
    cap = cfg.get("max_issues_per_run", 15)
    overflow = keep[cap:]
    keep = keep[:cap]

    C.log(f"  fetched {stats['fetched']} → unique {stats['unique']} → "
          f"known {stats['known']}, off-venue {stats['venue']}, low-score {stats['score']} → "
          f"{len(keep)} candidate(s)" + (f" (+{len(overflow)} held for next run)" if overflow else ""))

    gh = C.GitHub()
    live = gh.enabled and not args.dry_run
    if live:
        for name, (color, desc) in C.LABELS.items():
            gh.ensure_label(name, color, desc)

    C.OUT.mkdir(exist_ok=True)
    report = []
    for c in keep:
        title, body, labels = build_issue(c, cfg)
        report.append(f"## {title}\nlabels: {labels}\n\n{body}\n")
        if live:
            issue = gh.create_issue(title, body, labels)
            C.log(f"  → opened #{issue['number']}: {c['title'][:80]}")
        if live or args.record:
            C.append_line(C.SEEN_FILE, f"{C.paper_key(c)}  # {C.today()} {c['title'][:90]}")
    (C.OUT / "candidates.md").write_text("\n\n".join(report) or "No new candidates.\n", encoding="utf-8")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### BioQubit Atlas watcher — {C.today()}\n\n")
            fh.write(f"Window: {since} → today · fetched {stats['fetched']} · unique {stats['unique']} · "
                     f"already known {stats['known']} · off-venue {stats['venue']} · "
                     f"below score {stats['score']} · **new candidates {len(keep)}**\n\n")
            for c in keep:
                fh.write(f"- [{c['tier']}] {c['title']} — *{c.get('journal')}* (score {c['score']})\n")
    if not live:
        print((C.OUT / "candidates.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="do not open issues")
    ap.add_argument("--record", action="store_true", help="with --dry-run: still write seen.txt")
    ap.add_argument("--days", type=int, help="override lookback_days")
    ap.add_argument("--fixtures", help="directory with saved API replies (offline testing)")
    raise SystemExit(run(ap.parse_args()))
