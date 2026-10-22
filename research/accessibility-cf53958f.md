# `/portal/` keyboard and assistive-technology audit

**Session:** `arena/cf53958f-olbg2`  
**Checked:** 2026-10-22 UTC  
**Scope:** presentation and interaction only. No fixture, source, price, market, prediction, or confidence data was edited or re-verified.

## Baseline inspection

I inspected the `/portal/` generator (`scripts/portal_build.py`), its filtering script and stylesheet, and all 26 checked-in portal HTML pages. The static source/link verifier passed before any UI changes:

```text
python3 scripts/portal_verify.py
26 HTML pages; 707 table rows with HTTPS source links; 1,536 internal links/fragments;
17 eligible sports; 220 originated rows; 24 blank rows; 34 predictions; 38 flagged items.
```

A small HTML-parser inventory of the same 26 pages found:

| Surface | Baseline result | User impact |
|---|---:|---|
| Search and filter controls | 41 controls on 20 filtered pages; 0 associated labels and 0 control IDs | Screen readers and speech input may not get a dependable control name; placeholder text alone is not a label. |
| Dynamic result count | 20 counters updated by JavaScript; 0 had a status role or live-region property | Users who do not see the filtered table may not hear that the result count changed. |
| Horizontal table containers | 42 `overflow-x:auto` wrappers; 0 keyboard-focusable or named regions | Off-screen columns can be difficult to reach with a keyboard on narrow screens. |
| Table headers | 42 tables and 293 `<th>` cells; 0 explicit `scope` attributes | The browser recognizes header cells, but explicit column scope makes the intended relationships clearer and more robust. |
| Portal navigation | 26 primary `<nav>` elements; 0 accessible names and 0 `aria-current="page"` markers | Landmark and current-page context are less explicit to assistive technology. |
| Keyboard orientation | No skip-to-main link and no portal-authored `:focus-visible` rule | Repeated navigation takes extra keyboard stops; focus styling relies on browser defaults. |

These are source-based observations, not a formal WCAG conformance claim. No screen-reader or cross-browser manual interaction test was available in this pass.

## Standards references

- W3C WAI Forms Tutorial, **Labeling Controls**: labels should be programmatically associated with controls; its explicit-label method matches a label's `for` with the control's `id`. [https://www.w3.org/WAI/tutorials/forms/labels/](https://www.w3.org/WAI/tutorials/forms/labels/)
- W3C WAI, **WCAG 2.2 Understanding 4.1.3 Status Messages**: a dynamic message such as “18 results returned” can be exposed without moving focus. [https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
- W3C WAI, **WCAG 2.2 Understanding 2.4.7 Focus Visible**: keyboard users need a visible focus indicator. [https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)
- W3C WAI, **Tables Tutorial**: table headers and data cells need structural markup so assistive technology can preserve row/column context; captions are useful in most situations. [https://www.w3.org/WAI/tutorials/tables/](https://www.w3.org/WAI/tutorials/tables/)

## Implemented UI-only correction

The generator and existing portal assets now provide associated search/filter labels, polite result-count announcements, a visible no-results state, named keyboard-focusable table-scroll regions, table captions and explicit column scopes, named navigation landmarks with a current-page marker, a skip-to-main link, a two-color focus-visible treatment, and mobile-stacked filter fields. The script uses the `hidden` property for filtered rows so hidden results are removed from both visual and accessibility-tree presentation. A short `<noscript>` note explains that the table remains available when filtering is inactive.

**Post-change structural results:** all 26 pages have a skip link, named navigation landmark(s), and exactly one current-page marker; all 41 of 41 filter controls have explicit labels and point to their result table; all 20 result counters use `role="status"`, `aria-live="polite"`, and `aria-atomic="true"`; all 20 filters have an empty-result message; all 42 tables have a caption and all 293 headers use `scope="col"`; all 42 horizontally scrollable table regions are named and keyboard-focusable.

`python3 scripts/portal_build.py` was run twice and the generated HTML checksums were identical. SHA-256 inventories of `data/portal/*.json` were unchanged. `python3 scripts/portal_verify.py` passes with **707/707** source-linked table rows and **1,562** internal links/fragments. The new accessibility suite (5 tests) and prior portal suite (4 tests) pass. After rebasing onto `origin/main` at `cdbcf03`, the complete repository suite passed **190 tests**.

These are static structural checks, not automated browser interaction, screen-reader testing, or a formal WCAG conformance claim. No match fact or source assertion was verified or changed by this UI work.
