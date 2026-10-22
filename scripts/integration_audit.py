"""Cross-layer evidence disclosure and local-site integrity (not factual verification)."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def _vcounts():
    return load("data/verified/matches.json")["counts"]


def _vsports():
    rows = load("data/verified/matches.json")["matches"]
    return len({r["sport"] for r in rows})


def findings():
    """Produce review rows from repository evidence, without inventing external facts."""
    rows = [
        ('Integration 83346ec9 / source access', 'UNVERIFIED EXTERNALLY', 'Direct OLBG HTTPS access failed in this session. Existing captures and narratives were not re-verified against live official sites. No daily exhaustive refresh or five verified picks per sport is established.', 'https://www.olbg.com/'),
        ('Current desk / confidence and coverage', 'NEEDS REVIEW', 'The current capture contains 57 fixture rows in 7 sports, not complete worldwide coverage. Its 29 predictions cover four sports; ten sport categories have zero rows. Model fair odds are not available bookmaker prices; 28 of 29 picks are alternate lines, whose actual availability is unverified. High confidence is not externally calibrated.', 'current/flagged.html'),
        ('This session / verification ledger', 'STRUCTURAL ONLY', 'Integration checks do not confirm every sports fact. Read the recorded source-access failure, scope and remaining requirements before treating any dated row as current.', 'research/integration-83346ec9.md'),
        ('Integration / freshness', 'UNVERIFIED', 'The site contains dated 2026-10-21 captures, not a continuously refreshed feed. No exhaustive live bookmaker price feed is claimed.', 'survey/verification.html'),
        ('Scope alignment across layers', 'RESOLVED IN V2/V3', 'All active layers (Root, Verified /verified/, and Survey /survey/) enforce the 17 eligible OLBG sports and block all excluded terms including Hurling (id 26) and UFC/MMA (id 27).', 'verified/flagged.html'),
        ('Timezone preservation', 'VERIFIED POLICY', 'Times are preserved in the exact timezone published by each official feed (UTC for NHL/MLB, US ET for NBA, French local for LNR, venue local for URC, CEST for EHF) without unconfirmed conversion.', 'verified/methodology.html'),
        ('Duplicate-count disclosure', 'NEEDS REVIEW', 'Layers represent distinct audit passes over overlapping sports windows. Do not sum layer row counts to claim unique matches across the repository.', 'verified/audit.html'),
        ('Line-by-line repository audit (RA-01 to RA-10)', 'AUDITED 2026-10-21 · REBUILT 2026-10-22', f'Full primary-source audit remediated a stale Buffalo Sabres goal leader in /site/, purged all third-party Wikipedia/Cricinfo/ESPN citations in /survey/, populated SAC @ LAC game ID 0022600093, and originated {_vcounts()["originated_rows"]} multi-market lines across {_vsports()} sports in /verified/.', 'verified/audit.html'),
    ]
    for pred in load('data/survey/predictions.json'):
        for fact, url in pred['facts_used']:
            rows.append((f"Survey {pred['id']}: {fact}", 'UNVERIFIED IN THIS AUDIT',
                         'Structural script check records the primary governing-body URL cited by this prediction; inspect the linked official source directly for manual verification.', url))
    return rows


def _atlas_row():
    """First-hand Atlas layer row, rendered only when the layer has been built."""
    path = ROOT / 'data' / 'atlas' / 'matches.json'
    if not path.exists():
        return ''
    counts = json.loads(path.read_text())['counts']
    preds = json.loads((ROOT / 'data' / 'atlas' / 'predictions.json').read_text())
    flags = json.loads((ROOT / 'data' / 'atlas' / 'flagged.json').read_text())
    return (
        '<tr><td><a href="atlas/index.html"><strong>Atlas first-hand desk (/atlas/)</strong></a></td>'
        f'<td>{counts["rows"]} rows across {counts["sports"]} sports ({counts["confirmed"]} confirmed '
        f'first-hand against the governing body, {counts["originated"]} originated, '
        f'{counts["blank"]} blank)</td>'
        f'<td><a href="atlas/picks.html">{preds["count"]} written predictions '
        f'({preds["featured_count"]} featured)</a> · '
        f'<a href="atlas/verification.html">verification ledger</a> · '
        f'<a href="atlas/flagged.html">Flagged for Review ({flags["count"]})</a> · '
        f'<a href="atlas/methodology.html">Methodology</a></td></tr>')


def _current_row():
    counts = load('data/current/band.json')['counts']
    capture = load('data/current/matches.json')['captured_at_utc']
    return (
        '<tr><td><a href="current/index.html"><strong>Current capture desk (/current/)</strong></a></td>'
        f'<td>{counts["fixture_rows"]} stored fixtures; {counts["originated_rows"]} originated, '
        f'{counts["blank_rows"]} blank; {counts["sports_with_rows"]} sports with rows. '
        f'Capture: {escape(capture)} (not live).</td>'
        f'<td><a href="current/predictions.html">{counts["band_picks"]} model-band predictions</a> · '
        '<a href="current/flagged.html">Flagged for Review</a> · '
        '<a href="current/sources.html">Official source register</a> · '
        '<a href="research/integration-83346ec9.md">Integration verification limits</a></td></tr>')


def body():
    rows = ''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td><a href="{}">Source / review record</a></td></tr>'.format(*(escape(x, quote=True) for x in row)) for row in findings())
    root = load('data/matches.json')
    verified = load('data/verified/matches.json')
    v_counts = verified['counts']
    events = sum(len(json.loads(f.read_text())) for f in (ROOT / 'data/survey/events').glob('*.json'))
    return f'''<h1>Evidence status &amp; integration review</h1>
<p class="lede">Flagged for Review · checked 22 October 2026. Structural checks verify links, schema invariants, and source allowlists across all published layers.</p>
<div class="notice"><strong>Partial, dated research — not a live complete match feed.</strong> Probabilities and confidence labels are model outputs derived from official governing-body statistics, not guarantees. Any value not confirmed server-side from an official trusted source is left blank (<code>—</code>) and listed on <a href="verified/flagged.html">Verified Flagged for Review</a> and <a href="survey/flagged.html">Survey Flagged for Review</a>.</div>
<h2>Explore every research layer</h2>
<div class="table-wrap"><table><thead><tr><th>Layer</th><th>Stored entries (not unique combined totals)</th><th>Evidence &amp; limitations</th></tr></thead><tbody>
<tr><td><a href="verified/index.html"><strong>Verified Multi-Sport Desk (/verified/)</strong></a></td><td>{v_counts['total_rows']} verified rows ({v_counts['originated_rows']} originated lines across {_vsports()} sports · {v_counts['unlined_rows']} blank/flagged)</td><td><a href="verified/predictions.html">{len(load('data/verified/predictions.json')['predictions'])} written predictions ({len(load('data/verified/band.json')['selections'])} band)</a> · <a href="verified/flagged.html">Flagged for Review</a> · <a href="verified/audit.html">Line-by-Line Repo Audit</a></td></tr>
<tr><td><a href="live/index.html">Live slate (/live/)</a></td><td>{len(load('data/live/lines.json')['rows'])} fresh 2026-10-21 fixtures (URC R5 + MLB World Series G1-G3)</td><td><a href="live/flagged.html">Live review queue</a> · <a href="live/picks.html">Live picks &amp; predictions</a></td></tr>
<tr><td><a href="index.html">Root dashboard (/)</a></td><td>{len(root['matches'])} fixtures</td><td><a href="flagged.html">Root review queue</a> · <a href="sources.html">Source register</a></td></tr>
<tr><td><a href="site/index.html">Evidence desk v2 (/site/)</a></td><td>25 NHL/NBA fixtures (updated 2026-10-21)</td><td><a href="site/flagged.html">Desk review queue</a> · <a href="site/sources.html">Desk sources</a></td></tr>
<tr><td><a href="survey/index.html">All-sport survey (/survey/)</a></td><td>{events} inventoried entries across all 17 eligible sports (26 lines · 119 unlined)</td><td><a href="survey/flagged.html">Survey review queue</a> · <a href="survey/verification.html">Verification register</a></td></tr>
{_atlas_row()}
{_current_row()}
</tbody></table></div>
<h2>Cross-layer findings &amp; narrative claims needing review</h2>
<p>All existing layers are preserved and cross-linked. Rows below summarize cross-layer status and enumerate every survey narrative fact alongside its official source link for manual review.</p>
<div class="table-wrap"><table><thead><tr><th>Entry / claim</th><th>Status</th><th>Finding</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Automation boundary</h2><p>CI rebuilds selected static layers (<code>/verified/</code>, <code>/</code>, <code>/survey/</code>, and <code>/site/</code>), enforces <code>git diff --exit-code</code> against stale generated HTML, checks local file targets across all published HTML layers (not external facts or URL fragments), and runs full unit tests.</p>'''


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and ((tag in ('a', 'link') and key == 'href') or (tag in ('script', 'img') and key == 'src')):
                self.targets.append(value)


def local_link_errors(root=ROOT):
    errors = []
    # Discover every published layer; an allowlist silently misses new desks.
    pages = [p for p in root.rglob('*.html')
             if not any(part.startswith('.') or part in ('node_modules', '__pycache__')
                        for part in p.relative_to(root).parts)]
    for page in pages:
        parser = Links()
        parser.feed(page.read_text())
        for href in parser.targets:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if target.is_dir():
                target /= 'index.html'
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                errors.append(f'{page.relative_to(root)}: {href}')
    return errors


if __name__ == '__main__':
    errors = local_link_errors()
    for error in errors:
        print('BROKEN', error)
    print(f'Cross-layer local link errors: {len(errors)}. Structural check only; external facts not re-verified.')
    raise SystemExit(bool(errors))
