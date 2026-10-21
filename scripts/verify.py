#!/usr/bin/env python3
"""Line-by-line verification of the built site and the data behind it.

Exits non-zero if any check fails, so it can gate a deploy. Every check prints
what it examined and what it found.
"""
import json, pathlib, re, sys, html.parser, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, DOCS = ROOT / "data", ROOT / "docs"
fails, warns = [], []


def check(cond, msg):
    print(f"  {'PASS' if cond else 'FAIL'}  {msg}")
    if not cond:
        fails.append(msg)


class LinkParser(html.parser.HTMLParser):
    """Collects hrefs, and for tables marked data-require-source collects the
    per-row record of whether the row contains a source link or an explicit
    UNVERIFIED badge. Explanatory tables are not marked and are not checked."""

    def __init__(self):
        super().__init__()
        self.hrefs, self.rows = [], []
        self._stack, self._tracked, self._cells, self._in_td, self._cell = [], False, [], False, False
        self._body_cells = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._tracked = "data-require-source" in a
            self._stack.append(self._tracked)
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
            if self._in_td and self._tracked:
                self._cell = True
        if tag == "span" and self._in_td and self._tracked and "badge-unv" in (a.get("class") or ""):
            self._cell = True
        if tag == "tr" and self._tracked:
            self._cells, self._body_cells = [], 0
        if tag in ("td", "th"):
            self._in_td, self._cell = True, False
            if tag == "td":
                self._body_cells += 1

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._in_td = False
            if self._tracked:
                self._cells.append(self._cell)
        elif tag == "tr" and self._tracked and self._cells and self._body_cells:
            self.rows.append(self._cells)
        elif tag == "table" and self._stack:
            self._stack.pop()
            self._tracked = any(self._stack)


print("=" * 72)
print("1. Internal link integrity")
print("=" * 72)
allhtml = sorted(DOCS.rglob("*.html"))
print(f"  scanned {len(allhtml)} generated pages")
broken = []
ext = 0
for f in allhtml:
    txt = f.read_text()
    for h in re.findall(r'href="([^"]+)"', txt):
        if h.startswith(("http://", "https://", "mailto:")):
            ext += 1
            continue
        if h.startswith("#") or not h.strip():
            continue
        target = (f.parent / h.split("#")[0]).resolve()
        if not target.exists():
            broken.append(f"{f.relative_to(DOCS)} -> {h}")
check(not broken, f"all internal links resolve ({ext} external links present)")
for x in broken[:20]:
    print(f"        broken: {x}")

print()
print("=" * 72)
print("2. Every data-table row carries a source link or an UNVERIFIED badge")
print("=" * 72)
norow_src = []
total_rows = 0
for f in allhtml:
    p = LinkParser()
    p.feed(f.read_text())
    for cells in p.rows:
        total_rows += 1
        if not any(cells):
            norow_src.append(f"{f.relative_to(DOCS)}")
print(f"  scanned {total_rows} table rows across {len(allhtml)} pages")
check(not norow_src, "no table row is missing a source or an explicit UNVERIFIED marker")
for x in collections.Counter(norow_src).most_common(10):
    print(f"        rows without a source in {x[0]}: {x[1]}")

print()
print("=" * 72)
print("3. Data integrity")
print("=" * 72)
sports = json.loads((DATA / "sports.json").read_text())
inc = [s for s in sports if s["included"]]
n_ev, no_src, no_time = 0, [], []
for f in sorted((DATA / "events").glob("*.json")):
    for e in json.loads(f.read_text()):
        n_ev += 1
        if not e.get("source_url"):
            no_src.append((f.stem, e["match"]))
        if not e.get("listed_time") or not e.get("as_of") or not e.get("retrieved_via"):
            no_time.append((f.stem, e["match"]))
check(not no_src, f"all {n_ev} inventory rows carry an OLBG provenance URL")
check(not no_time, f"all {n_ev} inventory rows carry listed_time, as_of and retrieved_via")
check(len(sports) == 22, f"OLBG sport taxonomy has 22 entries (found {len(sports)})")
check(len(inc) == 15, f"15 sports in scope (found {len(inc)})")
check(all(s["listing_url"] for s in inc), "every in-scope sport has a listing URL")

lines = json.loads((DATA / "lines.json").read_text())["lines"]
bad = [r["match"] for r in lines if not (r.get("rating_source") or
       any(m.get("basis_source") for m in r["markets"]))]
check(not bad, f"all {len(lines)} originated lines cite a rating or basis source")
bad2 = [r["match"] for r in lines if r.get("pick_probability") is None or r.get("pick") is None]
check(not bad2, "every originated line has a pick and a probability")
bad3 = [r["match"] for r in lines
        if any(m.get("our_line") is None and not m.get("unverified") for m in r["markets"]
               if "Total" in m["name"] or "Handicap" in m["name"])]
check(not bad3, "every null line cell is explicitly marked unverified (never silently blank)")

preds = json.loads((DATA / "predictions.json").read_text())
short = [p["id"] for p in preds if p["word_count"] < 30]
wc = ", ".join("{}={}w".format(p["id"], p["word_count"]) for p in preds)
check(not short, "all {} predictions are at least 30 words ({})".format(len(preds), wc))
nofact = [p["id"] for p in preds if not p["facts_used"] or any(not u for _, u in p["facts_used"])]
check(not nofact, "every prediction fact carries a source URL")
conf = collections.Counter(r["confidence"] for r in lines)
hp = {p["match"] for p in preds}
hc = {r["match"] for r in lines if r["confidence"] == "high"}
check(hp == hc, f"a prediction exists for every high-confidence pick and for no other "
                f"(high={sorted(hc)})")

flags = json.loads((DATA / "flags.json").read_text())
f15 = next(f for f in flags if f["id"] == "F-15")
modelled = {(r["sport"], r["match"]) for r in lines}
inv = {(f.stem, e["match"]) for f in sorted((DATA / "events").glob("*.json"))
       for e in json.loads(f.read_text())}
check(n_ev == len(lines) + len(f15["items"]),
      f"inventory reconciles: {n_ev} = {len(lines)} modelled + {len(f15['items'])} flagged")
check(all(i.get("reason") and i.get("source_url") for i in f15["items"]),
      f"all {len(f15['items'])} unverified rows state a reason and a provenance link")
ids = [f["id"] for f in flags]
check(len(ids) == len(set(ids)), f"flag ids are unique ({len(ids)} flags)")

print()
print("=" * 72)
print("4. Deterministic rebuild")
print("=" * 72)
import hashlib, subprocess
def digest():
    parts = sorted("{}:{}".format(p.relative_to(DOCS), hashlib.sha256(p.read_bytes()).hexdigest())
                   for p in DOCS.rglob("*") if p.is_file())
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


h1 = digest()
subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")],
               check=True, capture_output=True)
h2 = digest()
check(h1 == h2, "rebuilding the site from the same data is byte-identical")

print()
print("=" * 72)
if fails:
    print(f"VERIFICATION FAILED: {len(fails)} check(s)")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("VERIFICATION PASSED: all checks green")
print(f"  {len(allhtml)} pages | {n_ev} events | {len(lines)} lines | {len(preds)} predictions | {len(flags)} flags")
print("=" * 72)
