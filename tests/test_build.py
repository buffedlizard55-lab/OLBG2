import copy
import json
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build import DATA, OUT, build, validate, link

class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ('a', 'link'):
            self.links += [value for key, value in attrs if key in ('href',)]

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())

    def test_snapshot_valid(self):
        validate(self.data)

    def test_excluded_sport_rejected(self):
        modified = copy.deepcopy(self.data)
        modified['events'][0]['sport'] = 'Football'
        with self.assertRaises(ValueError):
            validate(modified)

    def test_high_confidence_requires_prediction(self):
        modified = copy.deepcopy(self.data)
        modified['events'][0]['confidence'] = 'high'
        modified['events'][0]['winner'] = 'Buffalo Sabres'
        with self.assertRaises(ValueError):
            validate(modified)

    def test_unsafe_url_rejected(self):
        with self.assertRaises(ValueError):
            link('javascript:alert(1)', 'bad')

    def test_generated_local_links_resolve(self):
        build()
        for page in OUT.rglob('*.html'):
            parser = LocalLinks()
            parser.feed(page.read_text())
            for target in parser.links:
                if urlparse(target).scheme or target.startswith('#'):
                    continue
                path = (page.parent / unquote(urlparse(target).path)).resolve()
                self.assertTrue(path.is_relative_to(OUT.resolve()))
                self.assertTrue(path.is_file(), f'{page}: {target}')

    def test_all_navigation_targets_exist(self):
        build()
        for target in ('index.html', 'flagged.html', 'sports/ice-hockey.html', 'sports/basketball.html', 'sports/tennis.html', 'sports/baseball.html', 'methodology.html', 'assets/style.css'):
            self.assertTrue((OUT / target).is_file(), target)

if __name__ == '__main__':
    unittest.main()
