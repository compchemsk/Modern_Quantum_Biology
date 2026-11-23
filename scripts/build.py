#!/usr/bin/env python3
"""Regenerate README section, BibTeX and website data from data/papers.yaml.

  python scripts/build.py           # rebuild everything
  python scripts/build.py --check   # validate only; non-zero exit on problems (used in CI)
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import string
import sys
import unicodedata

import common as C

README = C.ROOT / "README.md"
BIB = C.ROOT / "bibliography" / "bioqubits.bib"
DATA_DIR = C.ROOT / "docs" / "data"
TEMPLATES = C.ROOT / "templates"
START, END = "<!-- ATLAS:START -->", "<!-- ATLAS:END -->"
TYPE_ICON = {"preprint": "📝", "review": "📚", "perspective": "💬", "letter": "✉️", "book-chapter": "📖"}


# ---------------------------------------------------------------- validation
def validate(papers: list[dict], cats: list[dict]) -> list[str]:
    keys = {c["key"] for c in cats}
    errs, ids, dois = [], collections.Counter(), collections.Counter()
    for i, p in enumerate(papers):
        tag = p.get("id") or f"entry #{i + 1}"
        errs += [f"{tag}: {e}" for e in C.validate_entry(p, keys)]
        ids[p.get("id")] += 1
        if p.get("doi"):
            dois[C.norm_doi(p["doi"])] += 1
    errs += [f"duplicate id '{k}'" for k, n in ids.items() if n > 1]
    errs += [f"duplicate DOI '{k}'" for k, n in dois.items() if n > 1]
    return errs


# ---------------------------------------------------------------- formatting
def link(p: dict) -> str:
    if p.get("doi"):
        return f"https://doi.org/{p['doi']}"
    if p.get("arxiv"):
        return f"https://arxiv.org/abs/{p['arxiv']}"
    return p.get("url", "")


def authors_short(a: list[str]) -> str:
    a = [x for x in (a or []) if x != "et al."]
    if not a:
        return ""
    if len(a) <= 3:
        return ", ".join(a)
    return f"{a[0]}, {a[1]}, … {a[-1]}"


def md_escape(s: str) -> str:
    return str(s).replace("|", "\\|").replace("*", "\\*").replace("_", "\\_")


def sort_key(p):
    return (-int(p.get("year") or 0), p.get("title", "").lower())


def readme_block(papers: list[dict], cats: list[dict]) -> str:
    by_cat = collections.defaultdict(list)
    for p in papers:
        by_cat[p["category"]].append(p)
    years = [int(p["year"]) for p in papers if p.get("year")]
    n_oa = sum(1 for p in papers if p.get("oa"))
    n_pre = sum(1 for p in papers if p.get("type") == "preprint")
    out = [
        f"**{len(papers)} papers** · {min(years)}–{max(years)} · {n_oa} free to read 🔓 · "
        f"{n_pre} preprints 📝 · updated {C.today().isoformat()}",
        "",
        "| Section | Papers |",
        "|---|:---:|",
    ]
    for c in cats:
        if by_cat.get(c["key"]):
            anchor = re.sub(r"[^a-z0-9 -]", "", c["title"].lower()).replace(" ", "-")
            out.append(f"| {c['emoji']} [{c['title']}](#{anchor}) | {len(by_cat[c['key']])} |")
    out += ["", "### 🆕 Latest additions", ""]
    latest = sorted(papers, key=lambda p: (str(p.get("added", "")), int(p.get("year") or 0)), reverse=True)[:5]
    for p in latest:
        out.append(f"- [{md_escape(p['title'])}]({link(p)}) — *{md_escape(p['journal'])}*, {p['year']}")
    for c in cats:
        items = sorted(by_cat.get(c["key"], []), key=sort_key)
        if not items:
            continue
        out += ["", f"## {c['title']}", "", f"*{c['blurb']}*", "",
                "| Year | Paper | Journal |", "|:---:|---|---|"]
        for p in items:
            icons = "".join(filter(None, [TYPE_ICON.get(p.get("type")), "🔓" if p.get("oa") else None]))
            title = f"[{md_escape(p['title'])}]({link(p)})" + (f" {icons}" if icons else "")
            who = md_escape(authors_short(p["authors"]))
            out.append(f"| {p['year']} | {title}<br>{who} | *{md_escape(p['journal'])}* |")
    out += ["", "<sub>📝 preprint · 📚 review · ✉️ letter · 🔓 free to read legally</sub>"]
    return "\n".join(out)


def write_readme(block: str):
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README.md lacks the ATLAS:START / ATLAS:END markers")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    README.write_text(f"{head}{START}\n{block}\n{END}{tail}", encoding="utf-8")


# ---------------------------------------------------------------- bibtex
def tex(s: str) -> str:
    s = str(s)
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_")):
        s = s.replace(a, b)
    return s


def bib_name(n: str) -> str:
    if n == "et al.":
        return "others"
    parts = n.split()
    if len(parts) < 2:
        return n
    particles = {"van", "von", "der", "de", "den", "da", "di", "le", "la"}
    i = len(parts) - 1
    while i > 1 and parts[i - 1].lower() in particles:
        i -= 1
    return f"{' '.join(parts[i:])}, {' '.join(parts[:i])}"


def bibtex(papers: list[dict]) -> str:
    out = [f"% BioQubit Atlas — {len(papers)} entries — generated {C.today()} by scripts/build.py\n"
           "% Do not edit by hand: edit data/papers.yaml instead.\n"]
    for p in sorted(papers, key=lambda p: p["id"]):
        kind = "misc" if p.get("type") == "preprint" else "article"
        f = {"title": "{" + tex(p["title"]) + "}",
             "author": " and ".join(bib_name(a) for a in p["authors"]),
             "year": p["year"]}
        if kind == "article":
            f["journal"] = tex(p["journal"])
        else:
            f["howpublished"] = tex(p["journal"])
        for k in ("volume", "pages"):
            if p.get(k):
                f[k] = str(p[k]).replace("–", "--")
        if p.get("doi"):
            f["doi"] = p["doi"]
        if p.get("arxiv"):
            f["eprint"], f["archivePrefix"] = p["arxiv"], "arXiv"
        if p.get("tags"):
            f["keywords"] = tex(", ".join(p["tags"]))
        body = ",\n".join(f"  {k:<12} = {{{v}}}" for k, v in f.items())
        out.append(f"@{kind}{{{p['id']},\n{body}\n}}\n")
    return "\n".join(out)


# ---------------------------------------------------------------- site
def site_json(papers: list[dict], cats: list[dict]) -> str:
    rows = []
    for p in sorted(papers, key=sort_key):
        r = {k: p.get(k) for k in ("id", "title", "authors", "year", "journal", "volume", "pages",
                                    "doi", "arxiv", "type", "category", "tags", "oa", "note")}
        r["link"] = link(p)
        r["added"] = str(p.get("added", ""))
        rows.append({k: v for k, v in r.items() if v not in (None, "", [])})
    return json.dumps({"generated": C.today().isoformat(), "categories": cats, "papers": rows},
                      ensure_ascii=False, indent=1, default=str)


# ---------------------------------------------------------------- templates
def template_vars(site: dict) -> dict:
    cur = site["curator"]
    return {"title": site["title"], "tagline": site["tagline"], "owner": site["owner"], "repo": site["repo"],
            "repo_url": site["repo_url"], "pages_url": site["pages_url"], "curator_name": cur["name"],
            "curator_affiliation": cur["affiliation"], "curator_website": cur["website"]}


def render(name: str, site: dict) -> str:
    return string.Template((TEMPLATES / name).read_text(encoding="utf-8")).safe_substitute(template_vars(site))


def resources_md(res: dict, site: dict) -> str:
    out = ["# 📚 Books, reviews, software & people", "",
           f"Background for the [{site['title']}]({site['pages_url']}): what to read to get into the field, "
           "the tools used to simulate it, and where the community meets. "
           "Generated from `config/resources.yaml` — edit that file, not this one.", "",
           "> 🧭 **Suggested path for a newcomer**"]
    out += [f"> {i}. {step}" for i, step in enumerate(res.get("path", []), 1)]
    out += ["", "## Books", ""]
    for g in res.get("books", []):
        out += [f"### {g['group']}", "", "| Book | Why read it |", "|---|---|"]
        for b in g["items"]:
            pub = f", {b['publisher']}" if b.get("publisher") else ""
            out.append(f"| {b['authors']}, ***{b['title']}***{pub} ({b['year']}) | {b['why']} |")
        out.append("")
    out += ["## Landmark reviews & papers", "", "| Reference | One line |", "|---|---|"]
    for r in res.get("reviews", []):
        doi = f" [doi:{r['doi']}](https://doi.org/{r['doi']})" if r.get("doi") else ""
        out.append(f"| {r['cite']}, “{r['title']}”.{doi} | {r['why']} |")
    out += ["", "## Software", "", "| Tool | What it does |", "|---|---|"]
    for t in res.get("software", []):
        out.append(f"| **[{t['name']}]({t['url']})** | {t['what']} |")
    out += ["", "## Community", "", "| | |", "|---|---|"]
    for c in res.get("community", []):
        name = f"[{c['name']}]({c['url']})" if c.get("url") else c["name"]
        out.append(f"| **{name}** | {c['what']} |")
    return "\n".join(out) + "\n"


def site_meta(site: dict) -> str:
    cur = site["curator"]
    meta = {"title": site["title"], "tagline": site["tagline"], "owner": site["owner"], "repo": site["repo"],
            "repo_url": site["repo_url"], "pages_url": site["pages_url"],
            "curator": {"name": cur["name"], "affiliation": cur["affiliation"], "website": cur["website"],
                        "scholar": cur.get("scholar", ""),
                        # stored reversed so plain-text harvesters don't see an address
                        "c": [cur["email_domain"][::-1], cur["email_user"][::-1]]}}
    return json.dumps(meta, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- main
def write(path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(check_only: bool = False) -> int:
    papers, cats = C.load_papers(), C.load_categories()
    errs = validate(papers, cats)
    if errs:
        print("Validation failed:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    if check_only:
        print(f"OK — {len(papers)} valid entries")
        return 0
    site = C.load_site()
    res = C.load_yaml(C.CONFIG / "resources.yaml")
    readme = render("README.md.tmpl", site)
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    write(README, f"{head}{START}\n{readme_block(papers, cats)}\n{END}{tail}")
    write(C.ROOT / "CITATION.cff", render("CITATION.cff.tmpl", site))
    write(C.ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml", render("issue-config.yml.tmpl", site))
    write(C.ROOT / "RESOURCES.md", resources_md(res, site))
    write(BIB, bibtex(papers))
    write(DATA_DIR / "papers.json", site_json(papers, cats))
    write(DATA_DIR / "resources.json", json.dumps(res, ensure_ascii=False, indent=1, default=str))
    write(DATA_DIR / "site.json", site_meta(site))
    index = C.ROOT / "docs" / "index.html"
    if index.exists():  # social previews need absolute URLs
        html = index.read_text(encoding="utf-8")
        html = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf'\g<1>{site["pages_url"]}assets/og.png\g<2>', html)
        html = re.sub(r'(<meta property="og:url" content=")[^"]*(")', rf'\g<1>{site["pages_url"]}\g<2>', html)
        index.write_text(html, encoding="utf-8")
    print(f"Built README, CITATION, RESOURCES, BibTeX and website data for {len(papers)} papers "
          f"→ {site['pages_url']}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    raise SystemExit(build(ap.parse_args().check))
