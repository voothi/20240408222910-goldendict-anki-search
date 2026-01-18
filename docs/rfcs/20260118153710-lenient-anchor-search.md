# 20260118153710 - Lenient Anchor Search

## Status
- **ZID**: 20260118153710
- **Release**: v1.52.8
- **Date**: 2026-01-18

## Problem Statement
When performing multi-sentence range searches (paragraph reading mode), the search for start and end "anchors" was too strict. If the text in the Anki database contained punctuation marks (like trailing commas, semicolons, or parentheses) that were not present in the search query, the initial card lookup would fail, returning no results.

Example:
- Query fragment: `Bellugi 1973)`
- Anki content: `Bellugi, 1973),`
- Result: Search for `*Bellugi 1973)*` fails to match the database entry.

## Implementation Details

### Analytics & Decisions
- **Normalization vs. Anchor Search**: Initial investigation showed that full-text normalization (Stage 2) was already correctly removing punctuation. The failure happened earlier, during the **Anchor Search (Stage 1)**, which used literal strings with wildcards for AnkiConnect's `findCards` action.
- **Softening Strategy**: Instead of just stripping punctuation from the ends of the anchor words, a more robust "softening" approach was chosen. All non-alphanumeric characters (including internal punctuation and spaces) are replaced with wildcards (`*`).
- **Performance Impact**: Since Anki (SQLite) already performs a sequential scan for queries starting with a wildcard, adding internal wildcards does not measurably slow down the database search. The number of candidate cards remains similar because the anchors (4 words) are specific enough to prevent excessive matches.

### Changes
1. **New Config Path**: Added `anchor_soft_matching` to `config.ini` (default: `true`).
2. **Helper Function**: Implemented `soften_anchor_query(anchor: str)` which performs regex-based word extraction and wildcard joining.
3. **Logic Update**: The main search loop now softens anchors before querying Anki if the config option is enabled.
4. **Clarification**: Documented the specific effect of this change in the configuration comments to explain how it bypasses punctuation during lookup.

## Automated Testing
- Added `test_soften_anchor_query` to verify the transformation of various punctuation-heavy strings.
- Added `test_anchor_softening_application` to verify the integration of the softening logic within the search flow.
- All 26 tests in `tests/test_anki_search.py` passed successfully.

## Related Requests
- 20260118162130: Request to add tests.
- 20260118163547: Clarification on performance impact.
