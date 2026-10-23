# Line-by-line repository audit — 23 October 2026

Session `arena/b8a1ce4c-olbg2`. Read from the merged tree at `2999cc0` (PR #139).

## Method

1. `git fetch origin '+refs/heads/*'` and list every remote head by commit time.
2. Read the full local `COORDINATION.md` (3,6xx lines) and the claims pushed in the previous five
   minutes.
3. Run the repository suite before touching anything.
4. Cross-read the claims of the two active sessions against their file scopes.
5. Spot-check every published layer's headline numbers against its own data files where cheap.

## Findings

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| A-01 | Three unresolved merge-conflict blocks remain committed in `COORDINATION.md`: six marker lines at 3216/3307, 3437/3549, 3609/3628. | `grep -n '^=======$\|^>>>>>>>' COORDINATION.md` → 6 | Flagged, not edited: other sessions' records. |
| A-02 | 34 published layers/directories now exist. Row counts overlap heavily; the README warns against summing but no machine-readable index enforces it. | `ls -d */` | Disclosed on `/desk/audit.html`. |
| A-03 | README describes a 17-sport taxonomy; this brief names 15 (Aussie Rules and eSports excluded). Both scopes are live without a stated mapping. | README.md | Flagged. |
| A-04 | Earlier desks publish “25 high-confidence picks” (`/hub/`) and “85 in-band picks” (`/vanguard/`) under their own gates. Those figures are not comparable with this desk's 8. | `python3 scripts/hub_verify.py`; `/vanguard/index.html` | Disclosed. |
| A-05 | Full suite passes on the untouched tree: 467 tests OK. | `python3 -m unittest discover -s tests` | Clear. |
| A-06 | Two sessions (`33e9eee7`, `8226c94a`) claim the same root integration files. | COORDINATION.md claims at 16:15:55 and 16:16:00 UTC | This session edits no shared file; request logged. |

## Verification performed on this session's own layer

- `scripts/desk_verify.py` → 2,511 checks, 0 errors.
- `python3 -m unittest tests.test_desk_b8a1ce4c` → 12 tests OK.
- Every table row on `/desk/matches.html`, `/desk/lines.html` and `/desk/olbg.html` resolves to an
  https source (asserted by the verifier, not by eye).
- Every number quoted in a prediction must appear in that prediction's stored fact list; the verifier
  fails the build otherwise. This caught nine unsupported figures during development.

## Not verified in this session

- No ATP, NBA, PDC, WST, EHF, CEV, PGA, DP World Tour, GBGB or GAA page produced usable numeric data
  (404, 500, or client-rendered shells). Those sports therefore carry consensus prices only.
- No injury report from any league was captured. No injury sentence was written.
