"""Cross-layer evidence disclosure and local-site integrity (not factual verification)."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def findings():
    """Produce review rows from repository evidence, without inventing external facts."""
    rows = [
        ('Integration / freshness', 'UNVERIFIED', 'The site contains dated captures, not a continuously refreshed feed. No exhaustive current slate or all-market coverage has been established.', 'survey/verification.html'),
        ('Scope disagreement', 'NEEDS REVIEW', 'Root config includes 17 sports; the survey includes 15 and excludes Greyhounds and Gaelic Football. Do not interpret either layer as complete coverage of the brief.', 'survey/flagged.html'),
        ('Timezone disagreement', 'NEEDS REVIEW', 'Earlier logs describe viewer-local times; the survey claims US Eastern. A single fixture comparison cannot establish a universal OLBG timezone. Unconfirmed times must not be converted.', 'survey/flagged.html'),
        ('Duplicate-count risk', 'NEEDS REVIEW', 'The layers are not deduplicated. Afghanistan v Bangladesh and New Zealand v India appear in both root and survey records. Do not add the layer totals to claim unique matches.', 'sports/cricket.html'),
        ('Source taxonomy disagreement', 'NEEDS REVIEW', 'scripts/config.py includes Hurling id 26, while the survey says there is no Hurling node. Neither claim was freshly resolved in this session.', 'survey/sports.html'),
        ('Capture chronology', 'NEEDS REVIEW', 'Root matches generated_at precedes inputs_captured_at. These timestamps cannot by themselves demonstrate a reproducible collection chronology.', 'data/matches.json'),
        ('Official-source spot check, 2026-10-21', 'LIMITED CHECK', 'The NHL score feed returned PHI at BUF and FLA at OTT, both starting 2026-10-21T23:30:00Z. No other fixture or strength input was freshly verified by this check.', 'https://api-web.nhle.com/v1/score/2026-10-21'),
    ]
    for pred in load('data/survey/predictions.json'):
        for fact, url in pred['facts_used']:
            rows.append((f"Survey {pred['id']}: {fact}", 'UNVERIFIED IN THIS AUDIT',
                         'Existing narrative claim; a URL is not evidence that the claim was checked. Some links are secondary publishers, which do not satisfy the official-only requirement. Reverify against a primary source before relying on this prediction.', url))
    return rows


def body():
    rows = ''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td><a href="{}">Source / review record</a></td></tr>'.format(*(escape(x, quote=True) for x in row)) for row in findings())
    root = load('data/matches.json')
    events = sum(len(json.loads(f.read_text())) for f in (ROOT / 'data/survey/events').glob('*.json'))
    return f'''<h1>Evidence status &amp; integration review</h1>
<p class="lede">Flagged for Review · checked 21 October 2026. Structural checks do not verify sporting facts or betting performance.</p>
<div class="notice"><strong>Partial, dated research — not a live complete match feed.</strong> Probabilities and confidence labels are model outputs, not officially verified facts or guarantees. Missing official confirmation remains unverified. No new betting recommendations are issued by this audit.</div>
<h2>Explore every research layer</h2>
<div class="table-wrap"><table><thead><tr><th>Layer</th><th>Stored entries (not unique combined totals)</th><th>Evidence &amp; limitations</th></tr></thead><tbody>
<tr><td><a href="index.html">Root dashboard</a></td><td>{len(root['matches'])} fixtures</td><td><a href="flagged.html">Root review queue</a> · <a href="sources.html">Source register</a></td></tr>
<tr><td><a href="site/index.html">Evidence desk</a></td><td>Separate NHL/NBA analysis; overlaps root</td><td><a href="site/flagged.html">Desk review queue</a> · <a href="site/sources.html">Desk sources</a></td></tr>
<tr><td><a href="survey/index.html">All-sport survey</a></td><td>{events} inventoried entries, including unverified listings</td><td><a href="survey/flagged.html">Survey review queue</a> · <a href="survey/verification.html">Verification register</a></td></tr>
</tbody></table></div>
<h2>Cross-layer findings &amp; narrative claims needing review</h2>
<p>All existing data is preserved. Rows below disclose unresolved contradictions and enumerate survey narrative claims needing fresh official confirmation. They must not be presented as newly verified facts.</p>
<div class="table-wrap"><table><thead><tr><th>Entry / claim</th><th>Status</th><th>Finding</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Automation boundary</h2><p>CI rebuilds all three static layers, checks local links and tests model invariants. It does not fetch or validate live official schedules. A production collector needs source-specific retrieval, raw evidence capture, timestamps, expiry rules and a fail-closed publication gate. Until that exists, this site cannot honestly claim automatic, up-to-date coverage for every sport and market.</p>'''


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
    pages = list(root.glob('*.html'))
    for folder in ('sports', 'site', 'survey'):
        pages.extend((root / folder).rglob('*.html'))
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
    print(f'Cross-layer local link errors: {len(errors)}. External facts not checked.')
    raise SystemExit(bool(errors))
