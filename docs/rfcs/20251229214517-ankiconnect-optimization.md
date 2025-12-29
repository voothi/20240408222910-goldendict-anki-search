# RFC: AnkiConnect Performance Optimization

**ZID**: 20251229214517  
**Version**: v1.46.12  
**Date**: 2025-12-29

## Summary

Optimize AnkiConnect API usage in `anki-search.py` by adding helper functions, improving error handling, and implementing TCP connection reuse.

## Implementation Details

### Analysis

Compared `anki-search.py` with a reference import script to identify optimization opportunities:

1. Code had duplicate payload construction patterns
2. No centralized error handling for AnkiConnect responses
3. No connection error messages specific to Anki not running
4. Each HTTP request opened new TCP connection

### Decisions

1. **Helper Functions** - Created `make_ac_request()`, `parse_ac_response()`, `invoke_ac()`, `invoke_multi_ac()` for consistent API interaction
2. **Configuration Constants** - Added `ANKI_CONNECT_URL` and `BATCH_SIZE` at module level
3. **Connection Reuse** - Added `requests.Session()` to reuse TCP connection between calls
4. **Error Handling** - Clear "[E] Anki is not running" message on connection failure

### Changes

| File | Change |
|------|--------|
| `anki-search.py` | Added 4 helper functions, Session, refactored `open_in_anki_browser()` and `search_word_in_decks()` |

## Verification

- Script loads without errors
- `--help` displays correctly
- Query execution works correctly
- Connection reuse reduces overhead between sequential API calls
