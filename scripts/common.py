"""Shared helpers for the BioQubit Atlas scripts (stdlib + PyYAML only)."""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
PAPERS_FILE = DATA / "papers.yaml"
SEEN_FILE = DATA / "seen.txt"
REJECTED_FILE = DATA / "rejected.txt"
OUT = ROOT / "out"

ENTRY_START = "<!-- atlas-entry:start -->"
ENTRY_END = "<!-- atlas-entry:end -->"

REQUIRED_FIELDS = ("id", "title", "authors", "year", "journal", "type", "category")
TYPES = ("article", "preprint", "review", "letter", "perspective", "book-chapter")


# --------------------------------------------------------------------------- io
def log(*a):
    print(*a, file=sys.stderr, flush=True)


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_papers() -> list[dict]:
    return load_yaml(PAPERS_FILE) or []


def load_categories() -> list[dict]:
    return load_yaml(CONFIG / "categories.yaml")


def load_watch_config() -> dict:
    return load_yaml(CONFIG / "watch.yaml")


def load_site() -> dict:
    s = load_yaml(CONFIG / "site.yaml")
    s["repo_url"] = f"https://github.com/{s['owner']}/{s['repo']}"
    s["pages_url"] = f"https://{s['owner'].lower()}.github.io/{s['repo']}/"
    return s


def read_keyset(path: Path) -> set[str]:
    """Lines like '10.1038/xyz  # comment' -> {'10.1038/xyz'} (normalised)."""
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            keys.add(line.lower())
    return keys


def append_line(path: Path, line: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line.rstrip("\n") + "\n")


def today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


# ------------------------------------------------------------------ normalising
def norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return doi.lower() or None


def norm_title(title: str | None) -> str:
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", title)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"<[^>]+>", " ", t)  # strip <i>, <sub> etc.
    t = re.sub(r"[^a-z0-9]+", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def norm_text(text: str) -> str:
    """Lower-case, strip accents/markup, hyphens -> spaces (for keyword scoring)."""
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"<[^>]+>", " ", t).lower()
    t = re.sub(r"[‐-―\-]", " ", t)
    return re.sub(r"\s+", " ", t)


def paper_key(p: dict) -> str:
    """Stable identity: DOI if present, else arXiv id, else normalised title."""
    if p.get("doi"):
        return norm_doi(p["doi"])
    if p.get("arxiv"):
        return "arxiv:" + p["arxiv"].lower()
    return "title:" + norm_title(p.get("title"))


# ------------------------------------------------------------- keyword matching
_pattern_cache: dict[str, re.Pattern] = {}


def phrase_pattern(phrase: str) -> re.Pattern:
    """'radical pair*' -> prefix match; 'fad' -> whole word only."""
    if phrase not in _pattern_cache:
        p = norm_text(phrase).strip()
        prefix = p.endswith("*")
        p = p.rstrip("*").strip()
        body = re.escape(p).replace(r"\ ", r"\s+")
        tail = "" if prefix else r"(?![a-z0-9])"
        _pattern_cache[phrase] = re.compile(r"(?<![a-z0-9])" + body + tail)
    return _pattern_cache[phrase]


def find_phrases(text: str, phrases) -> list[str]:
    nt = norm_text(text)
    return [ph for ph in phrases if phrase_pattern(ph).search(nt)]


WEIGHTS = {"core": 4, "platform": 4, "bio": 2, "spin": 2, "negative": -6}


def score_candidate(title: str, abstract: str, cfg: dict) -> tuple[int, dict]:
    """Return (score, {'core': [...], 'bio': [...], ...}). Title hits count double."""
    kw = cfg["keywords"]
    hits, score = {}, 0
    for group, weight in WEIGHTS.items():
        in_title = set(find_phrases(title, kw.get(group, [])))
        in_body = set(find_phrases(abstract or "", kw.get(group, [])))
        found = sorted(in_title | in_body)
        hits[group] = found
        for ph in found:
            score += weight * (2 if ph in in_title else 1)
    return score, hits


def passes(score: int, hits: dict, cfg: dict) -> bool:
    if (hits.get("core") or hits.get("platform")) and score >= cfg.get("min_score", 6):
        return True
    if hits.get("bio") and hits.get("spin") and score >= cfg.get("min_score_without_core", 14):
        return True
    return False


GENERIC_TAGS = {"protein*", "enzyme*", "qubit*", "magnetic resonance", "in vivo", "living cell*", "live cell*"}


def matched_terms(text: str, phrases) -> list[str]:
    """The actual words matched (so 'entangle*' -> 'entanglement'), minus generic ones."""
    nt = norm_text(text)
    out = []
    for ph in phrases:
        if ph in GENERIC_TAGS:
            continue
        m = phrase_pattern(ph).search(nt)
        if m:
            end = m.end()
            while end < len(nt) and nt[end].isalnum():
                end += 1
            term = nt[m.start():end]
            if term not in out:
                out.append(term)
    return out


def suggest_category(title: str, abstract: str, ptype: str, cfg: dict) -> str:
    if ptype == "review":
        return "reviews"
    text = f"{title} {abstract or ''}"
    for phrase, cat in cfg.get("category_hints", []):
        if find_phrases(text, [phrase]):
            return cat
    return "radical-pair"


def venue_tier(venue: str | None, cfg: dict) -> str | None:
    if not venue:
        return None
    v = norm_title(venue)
    for tier, names in cfg["venues"].items():
        for n in names:
            if norm_title(n) == v:
                return tier
    return None


# ------------------------------------------------------------------- ids, yaml
def make_id(p: dict, existing: set[str]) -> str:
    first = (p.get("authors") or ["anon"])[0]
    surname = norm_title(first).split(" ")[-1] if first else "anon"
    stop = {"a", "an", "the", "of", "in", "on", "for", "and", "to", "with", "by", "from", "is", "are"}
    word = next((w for w in norm_title(p.get("title")).split() if w not in stop), "paper")
    base = f"{surname}{p.get('year', '')}{word}"
    pid, n = base, 2
    while pid in existing:
        pid, n = f"{base}{chr(96 + n)}", n + 1
    return pid


FIELD_ORDER = ["id", "title", "authors", "year", "journal", "volume", "pages", "doi", "arxiv",
               "type", "category", "tags", "oa", "url", "note", "added"]


def entry_to_yaml(entry: dict) -> str:
    ordered = {k: entry[k] for k in FIELD_ORDER if k in entry and entry[k] not in (None, "", [])}
    for k, v in entry.items():
        if k not in ordered and v not in (None, "", []):
            ordered[k] = v
    return yaml.safe_dump([ordered], sort_keys=False, allow_unicode=True, width=10_000)


def validate_entry(e: dict, categories: set[str]) -> list[str]:
    errs = [f"missing field '{f}'" for f in REQUIRED_FIELDS if not e.get(f)]
    if e.get("category") and e["category"] not in categories:
        errs.append(f"unknown category '{e['category']}' (valid: {', '.join(sorted(categories))})")
    if e.get("type") and e["type"] not in TYPES:
        errs.append(f"unknown type '{e['type']}' (valid: {', '.join(TYPES)})")
    if e.get("authors") and not isinstance(e["authors"], list):
        errs.append("authors must be a list")
    if not e.get("doi") and not e.get("arxiv") and not e.get("url"):
        errs.append("need at least one of doi / arxiv / url")
    return errs


def extract_entry_block(text: str) -> dict | None:
    """Pull the YAML entry out of an issue body / comment."""
    if not text or ENTRY_START not in text:
        return None
    chunk = text.split(ENTRY_START, 1)[1].split(ENTRY_END, 1)[0]
    m = re.search(r"```(?:yaml)?\s*\n(.*?)```", chunk, flags=re.S)
    raw = m.group(1) if m else chunk
    data = yaml.safe_load(raw)
    if isinstance(data, list):
        data = data[0] if data else None
    return data if isinstance(data, dict) else None


# --------------------------------------------------------------------- http
USER_AGENT = "BioQubitAtlas/1.0 (literature watcher; GitHub Actions)"


def http_get(url: str, params: dict | None = None, headers: dict | None = None,
             retries: int = 3, timeout: int = 45, as_json: bool = True):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    h = {"User-Agent": USER_AGENT}
    h.update(headers or {})
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8")
                return json.loads(body) if as_json else body
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (400, 401, 403, 404):
                break
        except Exception as e:  # network hiccup
            last = e
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET failed: {url[:160]} -> {last}")


# ------------------------------------------------------------------- github
class GitHub:
    """Tiny GitHub REST client using the Actions-provided GITHUB_TOKEN."""

    def __init__(self, token: str | None = None, repo: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or os.environ.get("GITHUB_REPOSITORY")
        self.api = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.repo)

    def _req(self, method: str, path: str, payload=None, ok=(200, 201, 204)):
        url = f"{self.api}/repos/{self.repo}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode() or "null"
                return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in ok:
                return None
            raise RuntimeError(f"GitHub {method} {path} -> {e.code}: {e.read().decode()[:300]}")

    def ensure_label(self, name: str, color: str, description: str = ""):
        try:
            self._req("POST", "/labels", {"name": name, "color": color, "description": description})
        except RuntimeError as e:
            if "422" not in str(e):  # 422 = already exists
                raise

    def create_issue(self, title: str, body: str, labels: list[str]) -> dict:
        return self._req("POST", "/issues", {"title": title[:250], "body": body, "labels": labels})

    def comment(self, number: int, body: str):
        return self._req("POST", f"/issues/{number}/comments", {"body": body})

    def add_labels(self, number: int, labels: list[str]):
        return self._req("POST", f"/issues/{number}/labels", {"labels": labels})

    def remove_label(self, number: int, label: str):
        try:
            self._req("DELETE", f"/issues/{number}/labels/{urllib.parse.quote(label)}")
        except RuntimeError:
            pass

    def close(self, number: int, reason: str = "completed"):
        return self._req("PATCH", f"/issues/{number}", {"state": "closed", "state_reason": reason})

    def comments(self, number: int) -> list[dict]:
        return self._req("GET", f"/issues/{number}/comments?per_page=100") or []


LABELS = {
    "candidate": ("0e8a16", "Paper proposed by the watcher, awaiting curator decision"),
    "approve": ("2ea44f", "Curator: add this paper to the Atlas"),
    "reject": ("b60205", "Curator: do not add"),
    "added": ("5319e7", "Added to the Atlas"),
    "rejected": ("cccccc", "Not added"),
    "suggestion": ("fbca04", "Paper suggested by a person"),
    "high-impact": ("d93f0b", "Flagship venue"),
    "specialist": ("c2e0c6", "Specialist journal"),
    "preprint": ("bfdadc", "Preprint server"),
    "published-version": ("1d76db", "Possibly the journal version of a preprint already in the Atlas"),
}
